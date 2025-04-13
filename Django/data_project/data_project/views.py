from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .models import UserDataFile, Visualization, EncryptedUserProfile, SlideImage
from .forms import DataFileUploadForm, VisualizationForm, SignUpForm, LoginForm, DatabaseConnectionForm
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import sqlite3
import json
import numpy as np
from decimal import Decimal
import os
from django.conf import settings
from django.urls import reverse
import time
import urllib.parse

def home(request):
    """View for the home page showing carousel slides"""
    slides = SlideImage.objects.filter(is_active=True)
    return render(request, 'data_project/home.html', {'slides': slides})

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            # Log the user in after signup
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to Data Visualization Tool.')
            return redirect('index')
        else:
            # Check if email or username error exists in the form errors
            if 'username' in form.errors and 'This username is already taken.' in str(form.errors['username']):
                messages.error(request, 'This username is already taken. Please login or use a different username.')
                return redirect('login')
            elif 'email' in form.errors and 'This email is already registered.' in str(form.errors['email']):
                messages.error(request, 'This email is already registered. Please login.')
                return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'data_project/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('index')
            else:
                # Check if username exists but password is wrong
                from django.contrib.auth.models import User
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'Invalid password. Please try again.')
                else:
                    # Redirect to registration page with a warning message
                    messages.warning(request, 'User not found. Please register first.')
                    return redirect('signup')
    else:
        form = LoginForm()
    return render(request, 'data_project/login.html', {'form': form})

@login_required
def index(request):
    return render(request, 'data_project/index.html')

@login_required
def dashboard(request):
    # Get user's data files
    user_files = UserDataFile.objects.filter(user=request.user).order_by('-uploaded_at')
    
    # File statistics for chart
    file_counts = {
        'csv': 0,
        'excel': 0,
        'db': 0,
        'online': 0  # Combined count for all online databases
    }
    
    # Get file counts by type
    file_stats = UserDataFile.objects.filter(user=request.user).values('file_type').annotate(count=Count('id'))
    for stat in file_stats:
        file_type = stat['file_type']
        if file_type in ['mysql', 'postgres', 'mssql']:
            file_counts['online'] += stat['count']
        elif file_type in file_counts:
            file_counts[file_type] = stat['count']
    
    # Visualization statistics for chart
    viz_counts = {
        'bar': 0,
        'line': 0,
        'scatter': 0,
        'pie': 0,
        'histogram': 0
    }
    
    # Get visualization counts by type
    viz_stats = Visualization.objects.filter(data_file__user=request.user).values('viz_type').annotate(count=Count('id'))
    for stat in viz_stats:
        viz_type = stat['viz_type']
        if viz_type in viz_counts:
            viz_counts[viz_type] = stat['count']
    
    # Calculate total visualizations
    total_visualizations = Visualization.objects.filter(data_file__user=request.user).count()
    
    context = {
        'user_files': user_files,
        'file_counts': file_counts,
        'viz_counts': viz_counts,
        'total_visualizations': total_visualizations
    }
    
    return render(request, 'data_project/dashboard.html', context)

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = DataFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            data_file = form.save(commit=False)
            data_file.user = request.user
            data_file.save()
            messages.success(request, 'File uploaded successfully!')
            return redirect('file_detail', file_id=data_file.id)
    else:
        form = DataFileUploadForm()
    return render(request, 'data_project/upload_file.html', {'form': form})

def build_connection_string(file_type, username, password, host, port, db_name):
    """
    Builds a connection string for various database types with proper URL encoding
    for credentials that might contain special characters
    
    Args:
        file_type: Type of database ('mysql', 'postgres', 'mssql')
        username: Database username
        password: Database password
        host: Database hostname or IP
        port: Database port
        db_name: Database name
        
    Returns:
        Connection string formatted for SQLAlchemy
    """
    encoded_username = urllib.parse.quote_plus(username)
    encoded_password = urllib.parse.quote_plus(password)
    
    if file_type == 'mysql':
        return f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/{db_name}"
    elif file_type == 'postgres':
        return f"postgresql://{encoded_username}:{encoded_password}@{host}:{port}/{db_name}"
    elif file_type == 'mssql':
        return f"mssql+pyodbc://{encoded_username}:{encoded_password}@{host}:{port}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server"
    else:
        raise ValueError(f"Unsupported database type: {file_type}")

def read_file_data(data_file, table_name=None):
    file_type = data_file.file_type
    
    if file_type == 'csv':
        file_path = data_file.file.path
        df = pd.read_csv(file_path)
    elif file_type == 'excel':
        file_path = data_file.file.path
        # Handle Excel files with multiple sheets
        if table_name:  # 'table_name' is used for sheet names in Excel files too
            try:
                df = pd.read_excel(file_path, sheet_name=table_name)
            except Exception:
                # Fallback to first sheet if specified sheet doesn't exist
                df = pd.read_excel(file_path)
        else:
            # Default to first sheet if none specified
            df = pd.read_excel(file_path)
    elif file_type == 'db':
        file_path = data_file.file.path
        conn = sqlite3.connect(file_path)
        # Get all tables
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
        if not tables.empty:
            # If table_name is specified and exists, use it
            if table_name and table_name in tables['name'].values:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            else:
                # Use first table as default
                default_table = tables.iloc[0, 0]
                df = pd.read_sql_query(f"SELECT * FROM {default_table}", conn)
            conn.close()
        else:
            return None
    elif file_type in ['mysql', 'postgres', 'mssql']:
        # Remote database connection
        import sqlalchemy
        
        # Get connection details
        host = data_file.db_host
        port = data_file.db_port
        db_name = data_file.db_name
        username = data_file.db_username
        password = data_file.db_password
        
        try:
            # Create connection string
            connection_string = build_connection_string(file_type, username, password, host, port, db_name)
            
            # Create engine and connection
            engine = sqlalchemy.create_engine(connection_string)
            conn = engine.connect()
            
            # If no table specified, get list of tables
            if not table_name:
                if file_type == 'mysql':
                    tables_query = "SHOW TABLES"
                elif file_type == 'postgres':
                    tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                elif file_type == 'mssql':
                    tables_query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
                
                tables = pd.read_sql(tables_query, conn)
                default_table = tables.iloc[0, 0]
                table_name = default_table
            
            # Read data from specified table
            df = pd.read_sql_table(table_name, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            return None
    else:
        return None
    
    return df

@login_required
def file_detail(request, file_id):
    data_file = get_object_or_404(UserDataFile, pk=file_id, user=request.user)
    visualizations = Visualization.objects.filter(data_file=data_file)
    
    try:
        # Handle table or sheet selection
        selected_table = request.GET.get('table')
        df = read_file_data(data_file, selected_table)
        
        if df is None:
            messages.error(request, 'Unable to read file data')
            return redirect('dashboard')
            
        preview_data = df.head(10).to_html(classes='table table-striped table-bordered')
        columns = df.columns.tolist()
        
        # For databases and Excel files, provide table/sheet selection option
        tables = []
        if data_file.file_type == 'db':
            conn = sqlite3.connect(data_file.file.path)
            tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
            tables = tables_df['name'].tolist()
            conn.close()
        elif data_file.file_type == 'excel':
            # Get all sheet names from the Excel file
            excel_file = pd.ExcelFile(data_file.file.path)
            tables = excel_file.sheet_names
        elif data_file.file_type in ['mysql', 'postgres', 'mssql']:
            # Remote database connection to get table list
            import sqlalchemy
            
            # Get connection details
            host = data_file.db_host
            port = data_file.db_port
            db_name = data_file.db_name
            username = data_file.db_username
            password = data_file.db_password  # In production, decrypt this
            
            try:
                # Get connection string and appropriate table query
                connection_string = build_connection_string(data_file.file_type, username, password, host, port, db_name)
                
                # Set the appropriate query and column name based on database type
                if data_file.file_type == 'mysql':
                    tables_query = "SHOW TABLES"
                    col_name = 0  # The column index containing table names
                elif data_file.file_type == 'postgres':
                    tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                    col_name = 'table_name'
                elif data_file.file_type == 'mssql':
                    tables_query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
                    col_name = 'TABLE_NAME'
                
                # Create engine and get table list
                engine = sqlalchemy.create_engine(connection_string)
                with engine.connect() as conn:
                    tables_df = pd.read_sql(tables_query, conn)
                    
                # Extract table names from the result
                if isinstance(col_name, int):
                    tables = tables_df.iloc[:, col_name].tolist()
                else:
                    tables = tables_df[col_name].tolist()
                    
            except Exception as e:
                messages.error(request, f'Error connecting to database: {str(e)}')
                tables = []
        
        data_info = {
            'rows': len(df),
            'columns': len(columns),
            'column_names': ', '.join(columns[:10]) + ('...' if len(columns) > 10 else ''),
            'preview': preview_data
        }
        
        context = {
            'data_file': data_file,
            'data_info': data_info,
            'visualizations': visualizations,
            'columns': columns,
            'tables': tables,
            'selected_table': selected_table,
            'table_type': 'Table' if data_file.file_type in ['db', 'mysql', 'postgres', 'mssql'] else 'Sheet'
        }
        
        return render(request, 'data_project/file_detail.html', context)
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
        return redirect('dashboard')

@login_required
def create_visualization(request, file_id):
    data_file = get_object_or_404(UserDataFile, pk=file_id, user=request.user)
    
    try:
        # Get selected table from request
        selected_table = request.GET.get('table') or request.POST.get('table')
        
        # For SQLite databases, check if a table is selected
        if data_file.file_type == 'db':
            conn = sqlite3.connect(data_file.file.path)
            tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
            tables = tables_df['name'].tolist()
            conn.close()
            
            if tables and not selected_table:
                # If no table is selected but tables exist, redirect to file detail with message
                messages.warning(request, 'Please select a table before creating visualizations for database files.')
                return redirect('file_detail', file_id=file_id)
        
        df = read_file_data(data_file, selected_table)
        
        if df is None:
            messages.error(request, 'Unable to read file data')
            return redirect('file_detail', file_id=file_id)
            
        columns = df.columns.tolist()
        
        # Detect column types for better visualization suggestions
        column_types = {}
        for col in columns:
            # Check if column is numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                column_types[col] = 'numeric'
            # Check if column is datetime
            elif pd.api.types.is_datetime64_dtype(df[col]):
                column_types[col] = 'datetime'
            # Try to convert to datetime if it looks like a date
            elif df[col].dtype == 'object' and df[col].str.match(r'^\d{4}-\d{2}-\d{2}').any():
                try:
                    pd.to_datetime(df[col], errors='raise')
                    column_types[col] = 'datetime'
                except:
                    column_types[col] = 'categorical'
            # Otherwise, it's likely categorical
            else:
                column_types[col] = 'categorical'
        
        if request.method == 'POST':
            form = VisualizationForm(request.POST, columns=columns, column_types=column_types, data_file=data_file)
            if form.is_valid():
                title = form.cleaned_data['title']
                viz_type = form.cleaned_data['viz_type']
                x_col = form.cleaned_data['x_column']
                y_col = form.cleaned_data.get('y_column', '')
                
                # Check for exact duplicate visualizations
                existing_viz = Visualization.objects.filter(
                    data_file=data_file,
                    title=title,
                    viz_type=viz_type,
                    x_column=x_col,
                    y_column=y_col
                ).exists()
                
                if existing_viz:
                    messages.warning(request, f'A visualization with the same title, type, and columns already exists. Please use a different title or configuration.')
                    return render(request, 'data_project/create_visualization.html', {
                        'form': form,
                        'data_file': data_file,
                        'example_images': generate_example_visualizations(df, column_types),
                        'selected_table': selected_table
                    })
                
                visualization = form.save(commit=False)
                visualization.data_file = data_file
                
                # Store the source table name for database files
                if data_file.file_type == 'db' and selected_table:
                    visualization.source_table = selected_table
                
                # Create visualization image
                plt.figure(figsize=(10, 6))
                x_col = form.cleaned_data['x_column']
                y_col = form.cleaned_data['y_column']
                title = form.cleaned_data['title']
                viz_type = form.cleaned_data['viz_type']
                
                # Check if the selected columns contain valid data for plotting
                x_data = df[x_col]
                
                # For visualizations that require numeric data, convert if possible
                if viz_type in ['bar', 'line', 'scatter'] and column_types.get(x_col) != 'numeric' and y_col and column_types.get(y_col) == 'numeric':
                    # This is OK - x can be categorical when y is numeric
                    pass
                elif viz_type in ['scatter', 'histogram'] and column_types.get(x_col) != 'numeric':
                    # Try to convert non-numeric data to numeric
                    try:
                        df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
                        if df[x_col].isna().all():
                            messages.error(request, f'Column "{x_col}" could not be converted to numeric data required for {viz_type} plot')
                            return redirect('create_visualization', file_id=file_id)
                    except:
                        messages.error(request, f'Column "{x_col}" must contain numeric data for {viz_type} plot')
                        return redirect('create_visualization', file_id=file_id)
                
                # If y-column is provided, check it too
                if y_col:
                    y_data = df[y_col]
                    if viz_type in ['scatter', 'line'] and column_types.get(y_col) != 'numeric':
                        try:
                            df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                            if df[y_col].isna().all():
                                messages.error(request, f'Column "{y_col}" could not be converted to numeric data required for {viz_type} plot')
                                return redirect('create_visualization', file_id=file_id)
                        except:
                            messages.error(request, f'Column "{y_col}" must contain numeric data for {viz_type} plot')
                            return redirect('create_visualization', file_id=file_id)
                
                try:
                    if viz_type == 'bar':
                        if y_col:
                            # For bar charts, if x is not numeric but y is, this works fine
                            ax = df.plot(kind='bar', x=x_col, y=y_col)
                            # Improve x-axis labels when there are many categories
                            if len(df[x_col].unique()) > 10:
                                plt.xticks(rotation=90)
                                plt.tight_layout()
                        else:
                            # Value counts for single column
                            value_counts = df[x_col].value_counts().sort_index()
                            ax = value_counts.plot(kind='bar')
                            plt.xlabel(x_col)
                            plt.ylabel('Count')
                    elif viz_type == 'line':
                        if y_col:
                            ax = df.plot(kind='line', x=x_col, y=y_col)
                        else:
                            # For line charts with only x, plot the values directly if numeric
                            if column_types.get(x_col) == 'numeric':
                                ax = df[x_col].plot(kind='line')
                            else:
                                # If not numeric, use index as x and count occurrences
                                value_counts = df[x_col].value_counts().sort_index()
                                ax = value_counts.plot(kind='line')
                                plt.xlabel(x_col)
                                plt.ylabel('Count')
                    elif viz_type == 'scatter':
                        if y_col:
                            ax = df.plot(kind='scatter', x=x_col, y=y_col)
                        else:
                            messages.error(request, 'Scatter plot requires both X and Y columns')
                            return redirect('create_visualization', file_id=file_id)
                    elif viz_type == 'pie':
                        # For pie charts, get value counts and use top 10 categories if there are many
                        value_counts = df[x_col].value_counts()
                        if len(value_counts) > 10:
                            # Too many categories, take top 10 and group the rest
                            top_n = value_counts.nlargest(9)
                            other_count = value_counts[~value_counts.index.isin(top_n.index)].sum()
                            pie_data = pd.concat([top_n, pd.Series({'Other': other_count})])
                            ax = pie_data.plot(kind='pie', autopct='%1.1f%%')
                        else:
                            ax = value_counts.plot(kind='pie', autopct='%1.1f%%')
                        plt.ylabel('')  # Remove y-label for pie charts
                    elif viz_type == 'histogram':
                        # For histograms, ensure data is numeric
                        if pd.api.types.is_numeric_dtype(df[x_col]):
                            ax = df[x_col].plot(kind='hist', bins=20)
                        else:
                            # Try to convert to numeric
                            numeric_data = pd.to_numeric(df[x_col], errors='coerce')
                            if numeric_data.notna().any():
                                ax = numeric_data.plot(kind='hist', bins=20)
                            else:
                                messages.error(request, f'Column "{x_col}" does not contain numeric data for histogram')
                                return redirect('create_visualization', file_id=file_id)
                    
                    plt.title(title)
                    plt.grid(True, linestyle='--', alpha=0.7)
                    
                    # Save figure
                    buffer = io.BytesIO()
                    plt.savefig(buffer, format='png')
                    buffer.seek(0)
                    
                    # Create a unique filename with timestamp and visualization type to prevent overwrites
                    timestamp = int(time.time())
                    viz_filename = f'viz_{data_file.id}_{viz_type}_{timestamp}_{visualization.title.replace(" ", "_")}.png'
                    viz_path = os.path.join('visualizations', viz_filename)
                    
                    # Save to media
                    full_path = os.path.join(settings.MEDIA_ROOT, 'visualizations')
                    os.makedirs(full_path, exist_ok=True)
                    
                    with open(os.path.join(settings.MEDIA_ROOT, viz_path), 'wb') as f:
                        f.write(buffer.getvalue())
                    
                    visualization.image = viz_path
                    visualization.save()
                    
                    plt.close()
                    
                    messages.success(request, 'Visualization created successfully!')
                    return redirect('file_detail', file_id=file_id)
                except Exception as e:
                    messages.error(request, f'Error creating visualization: {str(e)}')
                    return redirect('create_visualization', file_id=file_id)
        else:
            form = VisualizationForm(columns=columns, column_types=column_types, data_file=data_file)
        
        # Create example visualizations for each type
        example_images = generate_example_visualizations(df, column_types)
        
        return render(request, 'data_project/create_visualization.html', {
            'form': form,
            'data_file': data_file,
            'example_images': example_images,
            'selected_table': selected_table
        })
    except Exception as e:
        messages.error(request, f'Error creating visualization: {str(e)}')
        return redirect('file_detail', file_id=file_id)

def generate_example_visualizations(df, column_types):
    """Generate example visualizations for different chart types"""
    examples = {}
    
    try:
        # Find suitable columns for examples
        numeric_cols = [col for col, type_name in column_types.items() if type_name == 'numeric']
        categorical_cols = [col for col, type_name in column_types.items() if type_name == 'categorical']
        
        if not numeric_cols or not categorical_cols:
            return {}  # Can't generate examples without proper columns
            
        x_cat = categorical_cols[0]  # First categorical column for x-axis
        y_num = numeric_cols[0]      # First numeric column for y-axis
        
        # Bar Chart Example
        plt.figure(figsize=(5, 3))
        df.sample(min(5, len(df))).plot(kind='bar', x=x_cat, y=y_num)
        plt.title('Bar Chart Example')
        plt.tight_layout()
        bar_img = get_image_as_base64(plt)
        plt.close()
        examples['bar'] = bar_img
        
        # Line Chart Example
        plt.figure(figsize=(5, 3))
        df.sample(min(5, len(df))).sort_values(x_cat).plot(kind='line', x=x_cat, y=y_num)
        plt.title('Line Chart Example')
        plt.tight_layout()
        line_img = get_image_as_base64(plt)
        plt.close()
        examples['line'] = line_img
        
        # Scatter Plot Example
        if len(numeric_cols) >= 2:
            plt.figure(figsize=(5, 3))
            df.sample(min(20, len(df))).plot(kind='scatter', x=numeric_cols[0], y=numeric_cols[1])
            plt.title('Scatter Plot Example')
            plt.tight_layout()
            scatter_img = get_image_as_base64(plt)
            plt.close()
            examples['scatter'] = scatter_img
        
        # Pie Chart Example
        plt.figure(figsize=(5, 3))
        df[x_cat].value_counts().head(5).plot(kind='pie')
        plt.title('Pie Chart Example')
        plt.tight_layout()
        pie_img = get_image_as_base64(plt)
        plt.close()
        examples['pie'] = pie_img
        
        # Histogram Example
        plt.figure(figsize=(5, 3))
        df[y_num].plot(kind='hist')
        plt.title('Histogram Example')
        plt.tight_layout()
        hist_img = get_image_as_base64(plt)
        plt.close()
        examples['histogram'] = hist_img
        
    except Exception as e:
        print(f"Error generating examples: {str(e)}")
        pass
        
    return examples

def get_image_as_base64(plt):
    """Convert matplotlib plot to base64 string"""
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic

@login_required
def clean_data(request, file_id):
    data_file = get_object_or_404(UserDataFile, pk=file_id, user=request.user)
    
    try:
        # Get selected table from request
        selected_table = request.GET.get('table') or request.POST.get('table')
        
        # For SQLite databases, check if a table is selected
        if data_file.file_type == 'db':
            conn = sqlite3.connect(data_file.file.path)
            tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
            tables = tables_df['name'].tolist()
            conn.close()
            
            if tables and not selected_table:
                # If no table is selected but tables exist, redirect to file detail with message
                messages.warning(request, 'Please select a table before cleaning database files.')
                return redirect('file_detail', file_id=file_id)
        
        df = read_file_data(data_file, selected_table)
        
        if df is None:
            messages.error(request, 'Unable to read file data')
            return redirect('dashboard')
        
        # For SQLite databases, identify which table we're working with
        table_name = None
        if data_file.file_type == 'db':
            conn = sqlite3.connect(data_file.file.path)
            tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
            tables = tables_df['name'].tolist()
            conn.close()
            
            if selected_table and selected_table in tables:
                table_name = selected_table
            elif tables:
                table_name = tables[0]  # Default to first table
        
        # Get column data types for validation and display
        column_types = {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                column_types[col] = 'numeric'
            elif pd.api.types.is_datetime64_dtype(df[col]):
                column_types[col] = 'datetime'
            else:
                column_types[col] = 'text'
        
        # Perform basic cleaning
        if request.method == 'POST':
            # Handle specific cleaning actions based on form submission
            action = request.POST.get('action')
            column = request.POST.get('column')
            
            if not column and action not in ['drop_all_na', 'drop_all_duplicates', 'trim_all_text']:
                messages.error(request, 'Please select a column to clean.')
                context = {
                    'data_file': data_file,
                    'columns': df.columns.tolist(),
                    'na_counts': df.isna().sum().to_dict(),
                    'duplicate_counts': {col: df.duplicated(subset=[col]).sum() for col in df.columns},
                    'selected_table': selected_table,
                    'column_types': column_types,
                    'outliers': detect_outliers(df)
                }
                return render(request, 'data_project/clean_data.html', context)
            
            # Missing value handling
            if action == 'drop_na' and column:
                original_row_count = len(df)
                df = df.dropna(subset=[column])
                dropped_rows = original_row_count - len(df)
                messages.info(request, f'Dropped {dropped_rows} rows with missing values in column "{column}".')
                
            elif action == 'fill_na' and column:
                value = request.POST.get('value', '')
                
                if not value:
                    messages.error(request, 'Please provide a value to fill missing data.')
                    context = {
                        'data_file': data_file,
                        'columns': df.columns.tolist(),
                        'na_counts': df.isna().sum().to_dict(),
                        'duplicate_counts': {col: df.duplicated(subset=[col]).sum() for col in df.columns},
                        'selected_table': selected_table,
                        'column_types': column_types,
                        'outliers': detect_outliers(df),
                        'form_data': {'column': column, 'action': action}
                    }
                    return render(request, 'data_project/clean_data.html', context)
                
                # Check column type for appropriate handling
                is_numeric = pd.api.types.is_numeric_dtype(df[column])
                missing_count = df[column].isna().sum()
                
                try:
                    if is_numeric:
                        # Handle special statistical values for numeric columns
                        if value.lower() == 'mean':
                            fill_value = df[column].mean()
                            df[column] = df[column].fillna(fill_value)
                            messages.success(request, f'Filled {missing_count} missing values in column "{column}" with mean ({fill_value:.2f}).')
                            
                        elif value.lower() == 'median':
                            fill_value = df[column].median()
                            df[column] = df[column].fillna(fill_value)
                            messages.success(request, f'Filled {missing_count} missing values in column "{column}" with median ({fill_value:.2f}).')
                            
                        elif value.lower() == 'mode':
                            fill_value = df[column].mode()[0]
                            df[column] = df[column].fillna(fill_value)
                            messages.success(request, f'Filled {missing_count} missing values in column "{column}" with mode ({fill_value}).')
                            
                        elif value.lower() == 'min':
                            fill_value = df[column].min()
                            df[column] = df[column].fillna(fill_value)
                            messages.success(request, f'Filled {missing_count} missing values in column "{column}" with minimum ({fill_value}).')
                            
                        elif value.lower() == 'max':
                            fill_value = df[column].max()
                            df[column] = df[column].fillna(fill_value)
                            messages.success(request, f'Filled {missing_count} missing values in column "{column}" with maximum ({fill_value}).')
                            
                        else:
                            # Try to convert to numeric
                            try:
                                fill_value = float(value)
                                df[column] = df[column].fillna(fill_value)
                                messages.success(request, f'Filled {missing_count} missing values in column "{column}" with {fill_value}.')
                            except ValueError:
                                messages.error(request, f'Column "{column}" is numeric. Please provide a number or use "mean", "median", "mode", "min", or "max".')
                                context = {
                                    'data_file': data_file,
                                    'columns': df.columns.tolist(),
                                    'na_counts': df.isna().sum().to_dict(),
                                    'duplicate_counts': {col: df.duplicated(subset=[col]).sum() for col in df.columns},
                                    'selected_table': selected_table,
                                    'column_types': column_types,
                                    'outliers': detect_outliers(df),
                                    'form_data': {'column': column, 'action': action}
                                }
                                return render(request, 'data_project/clean_data.html', context)
                    else:
                        # For non-numeric columns, just use the provided text
                        df[column] = df[column].fillna(value)
                        messages.success(request, f'Filled {missing_count} missing values in column "{column}" with "{value}".')
                except Exception as e:
                    messages.error(request, f'Error filling values: {str(e)}')
            
            elif action == 'fill_interpolate' and column:
                if pd.api.types.is_numeric_dtype(df[column]):
                    original_na_count = df[column].isna().sum()
                    df[column] = df[column].interpolate(method='linear')
                    filled_count = original_na_count - df[column].isna().sum()
                    messages.success(request, f'Interpolated {filled_count} missing values in column "{column}".')
                else:
                    messages.error(request, f'Column "{column}" is not numeric. Interpolation only works for numeric columns.')
            
            # Duplicate handling
            elif action == 'drop_duplicates' and column:
                original_row_count = len(df)
                df = df.drop_duplicates(subset=[column])
                dropped_rows = original_row_count - len(df)
                messages.info(request, f'Dropped {dropped_rows} duplicate rows based on column "{column}".')
            
            # Outlier handling
            elif action in ['remove_outliers', 'cap_outliers'] and column:
                if not pd.api.types.is_numeric_dtype(df[column]):
                    messages.error(request, f'Column "{column}" is not numeric. Outlier handling only works for numeric columns.')
                else:
                    # Get outlier detection method and parameters
                    outlier_method = request.POST.get('outlier_method', 'iqr')
                    
                    # Detect outliers
                    if outlier_method == 'iqr':
                        Q1 = df[column].quantile(0.25)
                        Q3 = df[column].quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        outlier_mask = (df[column] < lower_bound) | (df[column] > upper_bound)
                    elif outlier_method == 'zscore':
                        from scipy import stats
                        z_scores = np.abs(stats.zscore(df[column], nan_policy='omit'))
                        outlier_mask = z_scores > 3
                    elif outlier_method == 'percentile':
                        lower_percentile = float(request.POST.get('lower_percentile', 5))
                        upper_percentile = float(request.POST.get('upper_percentile', 95))
                        lower_bound = df[column].quantile(lower_percentile / 100)
                        upper_bound = df[column].quantile(upper_percentile / 100)
                        outlier_mask = (df[column] < lower_bound) | (df[column] > upper_bound)
                    
                    outlier_count = outlier_mask.sum()
                    
                    if action == 'remove_outliers':
                        df = df[~outlier_mask]
                        messages.success(request, f'Removed {outlier_count} outliers from column "{column}".')
                    else:  # cap_outliers
                        if outlier_count > 0:
                            df.loc[df[column] < lower_bound, column] = lower_bound
                            df.loc[df[column] > upper_bound, column] = upper_bound
                            messages.success(request, f'Capped {outlier_count} outliers in column "{column}" (values outside {lower_bound:.2f} to {upper_bound:.2f}).')
                        else:
                            messages.info(request, f'No outliers found in column "{column}" to cap.')
            
            # Data transformation
            elif action == 'normalize' and column:
                if not pd.api.types.is_numeric_dtype(df[column]):
                    messages.error(request, f'Column "{column}" is not numeric. Normalization only works for numeric columns.')
                else:
                    min_val = df[column].min()
                    max_val = df[column].max()
                    if max_val == min_val:
                        messages.error(request, f'Cannot normalize column "{column}" because all values are the same.')
                    else:
                        df[column] = (df[column] - min_val) / (max_val - min_val)
                        messages.success(request, f'Normalized column "{column}" to 0-1 scale.')
            
            elif action == 'standardize' and column:
                if not pd.api.types.is_numeric_dtype(df[column]):
                    messages.error(request, f'Column "{column}" is not numeric. Standardization only works for numeric columns.')
                else:
                    mean = df[column].mean()
                    std = df[column].std()
                    if std == 0:
                        messages.error(request, f'Cannot standardize column "{column}" because standard deviation is 0.')
                    else:
                        df[column] = (df[column] - mean) / std
                        messages.success(request, f'Standardized column "{column}" (mean=0, std=1).')
            
            elif action == 'log_transform' and column:
                if not pd.api.types.is_numeric_dtype(df[column]):
                    messages.error(request, f'Column "{column}" is not numeric. Log transformation only works for numeric columns.')
                else:
                    # Check for negative or zero values
                    min_val = df[column].min()
                    if min_val <= 0:
                        # Apply log(x+1) transformation
                        df[column] = np.log1p(df[column] - min_val + 1)
                        messages.success(request, f'Applied log(x+1) transformation to column "{column}".')
                    else:
                        # Apply standard log transformation
                        df[column] = np.log(df[column])
                        messages.success(request, f'Applied log transformation to column "{column}".')
            
            elif action == 'bin_values' and column:
                if not pd.api.types.is_numeric_dtype(df[column]):
                    messages.error(request, f'Column "{column}" is not numeric. Binning only works for numeric columns.')
                else:
                    num_bins = int(request.POST.get('num_bins', 5))
                    add_labels = request.POST.get('bin_labels') == 'true'
                    
                    if add_labels:
                        # Create bin labels
                        labels = [f'Bin {i+1}' for i in range(num_bins)]
                        df[f'{column}_binned'] = pd.qcut(df[column], q=num_bins, labels=labels, duplicates='drop')
                        messages.success(request, f'Binned column "{column}" into {num_bins} categories with labels.')
                    else:
                        # Create numeric bins (0 to num_bins-1)
                        df[f'{column}_binned'] = pd.qcut(df[column], q=num_bins, labels=False, duplicates='drop')
                        messages.success(request, f'Binned column "{column}" into {num_bins} numeric categories.')
            
            # Text processing
            elif action == 'trim_text' and column:
                if pd.api.types.is_numeric_dtype(df[column]):
                    messages.error(request, f'Column "{column}" is numeric. Text trimming only works for text columns.')
                else:
                    df[column] = df[column].astype(str).str.strip()
                    messages.success(request, f'Trimmed whitespace from column "{column}".')
            
            elif action == 'lowercase' and column:
                if pd.api.types.is_numeric_dtype(df[column]):
                    messages.error(request, f'Column "{column}" is numeric. Case conversion only works for text columns.')
                else:
                    df[column] = df[column].astype(str).str.lower()
                    messages.success(request, f'Converted column "{column}" to lowercase.')
            
            elif action == 'uppercase' and column:
                if pd.api.types.is_numeric_dtype(df[column]):
                    messages.error(request, f'Column "{column}" is numeric. Case conversion only works for text columns.')
                else:
                    df[column] = df[column].astype(str).str.upper()
                    messages.success(request, f'Converted column "{column}" to uppercase.')
            
            elif action == 'replace_text' and column:
                find_text = request.POST.get('find_text', '')
                replace_text = request.POST.get('replace_text', '')
                use_regex = request.POST.get('regex_search') == 'true'
                
                if not find_text:
                    messages.error(request, 'Please provide text to find.')
                else:
                    if use_regex:
                        df[column] = df[column].astype(str).str.replace(find_text, replace_text, regex=True)
                    else:
                        df[column] = df[column].astype(str).str.replace(find_text, replace_text, regex=False)
                    messages.success(request, f'Replaced text in column "{column}".')
            
            # Type conversion
            elif action == 'to_numeric' and column:
                try:
                    df[column] = pd.to_numeric(df[column], errors='coerce')
                    non_numeric_count = df[column].isna().sum()
                    if non_numeric_count > 0:
                        messages.warning(request, f'Converted column "{column}" to numeric, but {non_numeric_count} values could not be converted and were set to NaN.')
                    else:
                        messages.success(request, f'Successfully converted column "{column}" to numeric type.')
                except Exception as e:
                    messages.error(request, f'Error converting to numeric: {str(e)}')
            
            elif action == 'to_datetime' and column:
                try:
                    date_format = request.POST.get('date_format', '')
                    if date_format:
                        df[column] = pd.to_datetime(df[column], format=date_format, errors='coerce')
                    else:
                        df[column] = pd.to_datetime(df[column], errors='coerce')
                    
                    invalid_dates = df[column].isna().sum()
                    if invalid_dates > 0:
                        messages.warning(request, f'Converted column "{column}" to datetime, but {invalid_dates} values could not be converted and were set to NaT.')
                    else:
                        messages.success(request, f'Successfully converted column "{column}" to datetime type.')
                except Exception as e:
                    messages.error(request, f'Error converting to datetime: {str(e)}')
            
            elif action == 'to_category' and column:
                df[column] = df[column].astype('category')
                categories = len(df[column].cat.categories)
                messages.success(request, f'Converted column "{column}" to categorical type with {categories} categories.')
            
            # Batch operations
            elif action == 'drop_all_na':
                original_row_count = len(df)
                df = df.dropna()
                dropped_rows = original_row_count - len(df)
                messages.info(request, f'Dropped {dropped_rows} rows that contained any missing values.')
            
            elif action == 'drop_all_duplicates':
                original_row_count = len(df)
                df = df.drop_duplicates()
                dropped_rows = original_row_count - len(df)
                messages.info(request, f'Dropped {dropped_rows} completely duplicate rows.')
            
            elif action == 'trim_all_text':
                # Get all object (string) columns
                string_cols = df.select_dtypes(include=['object']).columns.tolist()
                for col in string_cols:
                    df[col] = df[col].astype(str).str.strip()
                messages.info(request, f'Trimmed whitespace from {len(string_cols)} text columns.')
            
            # Save the cleaned dataframe
            if data_file.file_type == 'csv':
                df.to_csv(data_file.file.path, index=False)
            elif data_file.file_type == 'excel':
                df.to_excel(data_file.file.path, index=False)
            elif data_file.file_type == 'db':
                # For SQLite, we need to recreate the table
                conn = sqlite3.connect(data_file.file.path)
                if table_name:
                    # Save with 'replace' to overwrite the existing table
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    conn.close()
                    messages.success(request, f'Table "{table_name}" cleaned successfully!')
                else:
                    conn.close()
                    messages.error(request, 'No table specified for cleaning.')
            else:
                messages.success(request, 'Data cleaned successfully!')
            
            # Preserve table selection when redirecting
            if data_file.file_type == 'db' and table_name:
                return redirect(f"{reverse('file_detail', args=[file_id])}?table={table_name}")
            else:
                return redirect('file_detail', file_id=file_id)
        
        # Get data info for display
        na_counts = df.isna().sum().to_dict()
        duplicate_counts = {col: df.duplicated(subset=[col]).sum() for col in df.columns}
        
        # Detect potential outliers in numeric columns
        outliers = detect_outliers(df)
        
        context = {
            'data_file': data_file,
            'columns': df.columns.tolist(),
            'na_counts': na_counts,
            'duplicate_counts': duplicate_counts,
            'outliers': outliers,
            'selected_table': selected_table,
            'column_types': column_types
        }
        
        return render(request, 'data_project/clean_data.html', context)
    except Exception as e:
        messages.error(request, f'Error cleaning data: {str(e)}')
        return redirect('file_detail', file_id=file_id)

@login_required
def batch_clean(request, file_id):
    """Handle batch cleaning operations"""
    data_file = get_object_or_404(UserDataFile, pk=file_id, user=request.user)
    
    try:
        # Get selected table from request
        selected_table = request.POST.get('table')
        
        df = read_file_data(data_file, selected_table)
        
        if df is None:
            messages.error(request, 'Unable to read file data')
            return redirect('dashboard')
        
        # For SQLite databases, identify which table we're working with
        table_name = None
        if data_file.file_type == 'db':
            conn = sqlite3.connect(data_file.file.path)
            tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
            tables = tables_df['name'].tolist()
            conn.close()
            
            if selected_table and selected_table in tables:
                table_name = selected_table
            elif tables:
                table_name = tables[0]  # Default to first table
        
        # Process batch operations
        operations_performed = []
        
        # Drop all rows with any missing values
        if request.POST.get('drop_all_na'):
            original_row_count = len(df)
            df = df.dropna()
            dropped_rows = original_row_count - len(df)
            if dropped_rows > 0:
                operations_performed.append(f'Dropped {dropped_rows} rows with missing values')
        
        # Drop all duplicate rows
        if request.POST.get('drop_all_duplicates'):
            original_row_count = len(df)
            df = df.drop_duplicates()
            dropped_rows = original_row_count - len(df)
            if dropped_rows > 0:
                operations_performed.append(f'Dropped {dropped_rows} duplicate rows')
        
        # Trim whitespace from all text columns
        if request.POST.get('trim_all_text'):
            # Get all object (string) columns
            string_cols = df.select_dtypes(include=['object']).columns.tolist()
            for col in string_cols:
                df[col] = df[col].astype(str).str.strip()
            operations_performed.append(f'Trimmed whitespace from {len(string_cols)} text columns')
        
        # Save the cleaned dataframe
        if data_file.file_type == 'csv':
            df.to_csv(data_file.file.path, index=False)
        elif data_file.file_type == 'excel':
            df.to_excel(data_file.file.path, index=False)
        elif data_file.file_type == 'db':
            # For SQLite, we need to recreate the table
            conn = sqlite3.connect(data_file.file.path)
            if table_name:
                # Save with 'replace' to overwrite the existing table
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                conn.close()
            else:
                conn.close()
                messages.error(request, 'No table specified for cleaning.')
        
        if operations_performed:
            messages.success(request, 'Batch cleaning completed: ' + ', '.join(operations_performed))
        else:
            messages.info(request, 'No batch operations were selected.')
        
        # Preserve table selection when redirecting
        if data_file.file_type == 'db' and table_name:
            return redirect(f"{reverse('file_detail', args=[file_id])}?table={table_name}")
        else:
            return redirect('file_detail', file_id=file_id)
    
    except Exception as e:
        messages.error(request, f'Error in batch cleaning: {str(e)}')
        return redirect('file_detail', file_id=file_id)

def detect_outliers(df):
    """Helper function to detect potential outliers in numeric columns using IQR method"""
    outliers = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        # Ignore columns with all NaN values
        if df[col].isna().all():
            continue
        
        # Use IQR method to detect outliers
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        # Define outlier boundaries
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Count outliers
        outlier_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
        
        if outlier_count > 0:
            outliers[col] = outlier_count
    
    return outliers

def user_logout(request):
    """Custom logout view that handles both GET and POST requests"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('home')
    else:
        # If it's a GET request, show the logout confirmation page
        return render(request, 'data_project/logout.html')

@login_required
def delete_file(request, file_id):
    """View to handle file deletion"""
    if request.method == 'POST':
        data_file = get_object_or_404(UserDataFile, pk=file_id, user=request.user)
        file_title = data_file.title
        
        # Delete associated visualizations and their image files
        visualizations = Visualization.objects.filter(data_file=data_file)
        for viz in visualizations:
            if viz.image:
                # Get the full path to the image file
                image_path = os.path.join(settings.MEDIA_ROOT, viz.image.name)
                if os.path.isfile(image_path):
                    os.remove(image_path)
        
        # Delete visualization records
        visualizations.delete()
        
        # Delete the data file
        if data_file.file:
            if os.path.isfile(data_file.file.path):
                os.remove(data_file.file.path)
        
        # Delete the database record
        data_file.delete()
        
        messages.success(request, f'File "{file_title}" has been deleted successfully.')
        return redirect('dashboard')
    
    # If it's a GET request, show confirmation page
    data_file = get_object_or_404(UserDataFile, pk=file_id, user=request.user)
    return render(request, 'data_project/confirm_delete.html', {'data_file': data_file})

@login_required
def delete_visualization(request, viz_id):
    """View to handle visualization deletion"""
    if request.method == 'POST':
        viz = get_object_or_404(Visualization, pk=viz_id, data_file__user=request.user)
        file_id = viz.data_file.id
        selected_table = request.GET.get('table')
        
        # Delete the image file if it exists
        if viz.image:
            image_path = os.path.join(settings.MEDIA_ROOT, viz.image.name)
            if os.path.isfile(image_path):
                os.remove(image_path)
        
        # Delete the visualization
        viz.delete()
        
        messages.success(request, 'Visualization deleted successfully.')
        
        # Redirect back to file detail, preserving table selection if applicable
        if selected_table:
            return redirect(f"{reverse('file_detail', args=[file_id])}?table={selected_table}")
        else:
            return redirect('file_detail', file_id=file_id)
    
    # If someone tries to access via GET, redirect to dashboard
    return redirect('dashboard')

@login_required
def connect_database(request):
    """View to handle remote database connections"""
    if request.method == 'POST':
        form = DatabaseConnectionForm(request.POST)
        if form.is_valid():
            # Create data file entry but don't save yet
            data_file = form.save(commit=False)
            data_file.user = request.user
            
            # Test connection before saving
            try:
                import sqlalchemy
                
                # Get connection details
                file_type = data_file.file_type
                host = data_file.db_host
                port = data_file.db_port
                db_name = data_file.db_name
                username = data_file.db_username
                password = data_file.db_password
                
                # Build connection string using utility function
                connection_string = build_connection_string(file_type, username, password, host, port, db_name)
                
                # Test connection
                engine = sqlalchemy.create_engine(connection_string)
                conn = engine.connect()
                conn.close()
                
                # Save if connection successful
                data_file.save()
                messages.success(request, f'Successfully connected to {data_file.get_file_type_display()}!')
                return redirect('file_detail', file_id=data_file.id)
                
            except Exception as e:
                messages.error(request, f'Error connecting to database: {str(e)}')
    else:
        form = DatabaseConnectionForm()
    
    return render(request, 'data_project/connect_database.html', {'form': form})

@login_required
def preview_visualization(request, file_id):
    """API endpoint to generate a visualization preview"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    data_file = get_object_or_404(UserDataFile, pk=file_id, user=request.user)
    
    try:
        # Get form parameters
        viz_type = request.POST.get('viz_type')
        x_col = request.POST.get('x_column')
        y_col = request.POST.get('y_column', '')
        selected_table = request.POST.get('table')
        
        # Validate required parameters
        if not viz_type or not x_col:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
            
        # Read data
        df = read_file_data(data_file, selected_table)
        if df is None or df.empty:
            return JsonResponse({'error': 'Unable to read data'}, status=400)
            
        # Generate preview
        plt.figure(figsize=(8, 5))
        
        # Detect column types
        column_types = {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                column_types[col] = 'numeric'
            elif pd.api.types.is_datetime64_dtype(df[col]):
                column_types[col] = 'datetime'
            else:
                column_types[col] = 'categorical'
        
        try:
            if viz_type == 'bar':
                if y_col:
                    # For bar charts, if x is not numeric but y is, this works fine
                    ax = df.plot(kind='bar', x=x_col, y=y_col)
                    # Improve x-axis labels when there are many categories
                    if len(df[x_col].unique()) > 10:
                        plt.xticks(rotation=90)
                        plt.tight_layout()
                else:
                    # Value counts for single column
                    value_counts = df[x_col].value_counts().sort_index()
                    ax = value_counts.plot(kind='bar')
                    plt.xlabel(x_col)
                    plt.ylabel('Count')
            elif viz_type == 'line':
                if y_col:
                    ax = df.plot(kind='line', x=x_col, y=y_col)
                else:
                    # For line charts with only x, plot the values directly if numeric
                    if column_types.get(x_col) == 'numeric':
                        ax = df[x_col].plot(kind='line')
                    else:
                        # If not numeric, use index as x and count occurrences
                        value_counts = df[x_col].value_counts().sort_index()
                        ax = value_counts.plot(kind='line')
                        plt.xlabel(x_col)
                        plt.ylabel('Count')
            elif viz_type == 'scatter':
                if y_col:
                    ax = df.plot(kind='scatter', x=x_col, y=y_col)
                else:
                    return JsonResponse({'error': 'Scatter plot requires both X and Y columns'}, status=400)
            elif viz_type == 'pie':
                # For pie charts, get value counts and use top 10 categories if there are many
                value_counts = df[x_col].value_counts()
                if len(value_counts) > 10:
                    # Too many categories, take top 10 and group the rest
                    top_n = value_counts.nlargest(9)
                    other_count = value_counts[~value_counts.index.isin(top_n.index)].sum()
                    pie_data = pd.concat([top_n, pd.Series({'Other': other_count})])
                    ax = pie_data.plot(kind='pie', autopct='%1.1f%%')
                else:
                    ax = value_counts.plot(kind='pie', autopct='%1.1f%%')
                plt.ylabel('')  # Remove y-label for pie charts
            elif viz_type == 'histogram':
                # For histograms, ensure data is numeric
                if pd.api.types.is_numeric_dtype(df[x_col]):
                    ax = df[x_col].plot(kind='hist', bins=20)
                else:
                    # Try to convert to numeric
                    numeric_data = pd.to_numeric(df[x_col], errors='coerce')
                    if numeric_data.notna().any():
                        ax = numeric_data.plot(kind='hist', bins=20)
                    else:
                        return JsonResponse({'error': f'Column "{x_col}" does not contain numeric data for histogram'}, status=400)
            
            plt.title("Visualization Preview")
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            # Convert to base64
            image_data = get_image_as_base64(plt)
            plt.close()
            
            return JsonResponse({
                'success': True,
                'image': image_data
            })
            
        except Exception as e:
            plt.close()
            return JsonResponse({'error': str(e)}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def advanced_visualization(request, file_id):
    """View for creating advanced visualizations with more options"""
    data_file = get_object_or_404(UserDataFile, pk=file_id, user=request.user)
    
    try:
        # Get selected table from request
        selected_table = request.GET.get('table') or request.POST.get('table')
        
        # For SQLite databases, check if a table is selected
        if data_file.file_type == 'db':
            conn = sqlite3.connect(data_file.file.path)
            tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
            tables = tables_df['name'].tolist()
            conn.close()
            
            if tables and not selected_table:
                # If no table is selected but tables exist, redirect to file detail with message
                messages.warning(request, 'Please select a table before creating visualizations for database files.')
                return redirect('file_detail', file_id=file_id)
        
        df = read_file_data(data_file, selected_table)
        
        if df is None:
            messages.error(request, 'Unable to read file data')
            return redirect('file_detail', file_id=file_id)
            
        columns = df.columns.tolist()
        
        # Detect column types for better visualization suggestions
        column_types = {}
        for col in columns:
            # Check if column is numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                column_types[col] = 'numeric'
            # Check if column is datetime
            elif pd.api.types.is_datetime64_dtype(df[col]):
                column_types[col] = 'datetime'
            # Try to convert to datetime if it looks like a date
            elif df[col].dtype == 'object' and df[col].str.match(r'^\d{4}-\d{2}-\d{2}').any():
                try:
                    pd.to_datetime(df[col], errors='raise')
                    column_types[col] = 'datetime'
                except:
                    column_types[col] = 'categorical'
            # Otherwise, it's likely categorical
            else:
                column_types[col] = 'categorical'
        
        if request.method == 'POST':
            # Handle advanced visualization creation
            title = request.POST.get('title')
            viz_type = request.POST.get('viz_type')
            x_col = request.POST.get('x_column')
            y_col = request.POST.get('y_column', '')
            z_col = request.POST.get('z_column', '')  # For 3D plots
            color_col = request.POST.get('color_column', '')  # For coloring points
            size_col = request.POST.get('size_column', '')  # For bubble charts
            
            # Visualization options
            figsize_width = float(request.POST.get('figsize_width', 10))
            figsize_height = float(request.POST.get('figsize_height', 6))
            palette = request.POST.get('color_palette', 'viridis')
            title_fontsize = int(request.POST.get('title_fontsize', 14))
            axis_fontsize = int(request.POST.get('axis_fontsize', 12))
            legend_position = request.POST.get('legend_position', 'best')
            plot_style = request.POST.get('plot_style', 'default')
            grid = request.POST.get('grid') == 'on'
            transparent_bg = request.POST.get('transparent_bg') == 'on'
            
            # Validation checks
            if not title or not viz_type or not x_col:
                messages.error(request, 'Missing required fields: title, visualization type, and X-axis column are required.')
                return redirect('advanced_visualization', file_id=file_id)
            
            # For specific visualization types, validate required fields
            if viz_type in ['scatter', 'line', 'bubble'] and not y_col:
                messages.error(request, f'{viz_type.capitalize()} plots require Y-axis column.')
                return redirect('advanced_visualization', file_id=file_id)
            
            if viz_type == 'bubble' and not size_col:
                messages.error(request, 'Bubble charts require a size column.')
                return redirect('advanced_visualization', file_id=file_id)
            
            if viz_type == '3d_scatter' and (not y_col or not z_col):
                messages.error(request, '3D scatter plots require X, Y, and Z columns.')
                return redirect('advanced_visualization', file_id=file_id)
            
            # Create a new visualization object
            visualization = Visualization(
                title=title,
                data_file=data_file,
                viz_type=viz_type,
                x_column=x_col,
                y_column=y_col
            )
            
            # Store source table for database files
            if data_file.file_type == 'db' and selected_table:
                visualization.source_table = selected_table
            
            # Create the visualization with matplotlib
            try:
                # Set plot style
                plt.style.use(plot_style)
                
                # Create figure with specified size
                plt.figure(figsize=(figsize_width, figsize_height))
                
                # Create the specific type of visualization
                if viz_type == 'bar':
                    create_bar_chart(df, x_col, y_col, color_col, palette)
                elif viz_type == 'line':
                    create_line_chart(df, x_col, y_col, color_col, palette)
                elif viz_type == 'scatter':
                    create_scatter_plot(df, x_col, y_col, color_col, size_col, palette)
                elif viz_type == 'pie':
                    create_pie_chart(df, x_col, y_col, palette)
                elif viz_type == 'histogram':
                    create_histogram(df, x_col, color_col, palette)
                elif viz_type == 'heatmap':
                    create_heatmap(df, x_col, y_col, z_col, palette)
                elif viz_type == 'bubble':
                    create_bubble_chart(df, x_col, y_col, size_col, color_col, palette)
                elif viz_type == 'box':
                    create_box_plot(df, x_col, y_col, color_col, palette)
                elif viz_type == 'violin':
                    create_violin_plot(df, x_col, y_col, color_col, palette)
                elif viz_type == '3d_scatter':
                    create_3d_scatter(df, x_col, y_col, z_col, color_col, palette)
                
                # Apply common settings
                plt.title(title, fontsize=title_fontsize)
                plt.xlabel(x_col, fontsize=axis_fontsize)
                if viz_type not in ['pie', 'heatmap']:
                    plt.ylabel(y_col if y_col else 'Count', fontsize=axis_fontsize)
                
                if grid:
                    plt.grid(True, linestyle='--', alpha=0.7)
                
                # Add legend if applicable
                if color_col and viz_type not in ['pie', 'heatmap']:
                    plt.legend(title=color_col, loc=legend_position)
                
                # Save the figure
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', transparent=transparent_bg)
                buffer.seek(0)
                
                # Create a unique filename with timestamp
                timestamp = int(time.time())
                viz_filename = f'viz_{data_file.id}_{viz_type}_{timestamp}_{visualization.title.replace(" ", "_")}.png'
                viz_path = os.path.join('visualizations', viz_filename)
                
                # Ensure the directory exists
                full_path = os.path.join(settings.MEDIA_ROOT, 'visualizations')
                os.makedirs(full_path, exist_ok=True)
                
                # Save to file
                with open(os.path.join(settings.MEDIA_ROOT, viz_path), 'wb') as f:
                    f.write(buffer.getvalue())
                
                visualization.image = viz_path
                visualization.save()
                
                plt.close()
                
                messages.success(request, 'Advanced visualization created successfully!')
                return redirect('file_detail', file_id=file_id)
                
            except Exception as e:
                messages.error(request, f'Error creating visualization: {str(e)}')
                return redirect('advanced_visualization', file_id=file_id)
        
        # Generate example visualizations for each type
        example_images = generate_example_visualizations(df, column_types)
        
        context = {
            'data_file': data_file,
            'columns': columns,
            'column_types': column_types,
            'example_images': example_images,
            'selected_table': selected_table,
            'color_palettes': [
                'viridis', 'plasma', 'inferno', 'magma', 'cividis',
                'Spectral', 'coolwarm', 'RdYlBu', 'RdBu',
                'Blues', 'Greens', 'Reds', 'Purples', 'Oranges'
            ],
            'plot_styles': [
                'default', 'classic', 'bmh', 'ggplot', 'seaborn', 'seaborn-dark',
                'seaborn-colorblind', 'seaborn-deep', 'seaborn-pastel', 'tableau-colorblind10'
            ],
            'legend_positions': [
                'best', 'upper right', 'upper left', 'lower left', 'lower right',
                'right', 'center left', 'center right', 'lower center', 'upper center'
            ]
        }
        
        return render(request, 'data_project/advanced_visualization.html', context)
        
    except Exception as e:
        messages.error(request, f'Error preparing visualization: {str(e)}')
        return redirect('file_detail', file_id=file_id)

@login_required
def custom_visualization_preview(request, file_id):
    """API endpoint to generate a preview of a custom visualization"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    data_file = get_object_or_404(UserDataFile, pk=file_id, user=request.user)
    
    try:
        # Get visualization parameters
        viz_type = request.POST.get('viz_type')
        x_col = request.POST.get('x_column')
        y_col = request.POST.get('y_column', '')
        z_col = request.POST.get('z_column', '')
        color_col = request.POST.get('color_column', '')
        size_col = request.POST.get('size_column', '')
        selected_table = request.POST.get('table')
        palette = request.POST.get('color_palette', 'viridis')
        plot_style = request.POST.get('plot_style', 'default')
        grid = request.POST.get('grid') == 'on'
        
        # Validate parameters
        if not viz_type or not x_col:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        # For scatter plots, line charts, and bubble charts, y-axis is required
        if viz_type in ['scatter', 'line', 'bubble'] and not y_col:
            return JsonResponse({'error': f'{viz_type.capitalize()} plots require Y-axis column'}, status=400)
        
        # For 3D scatter plots, y and z axes are required
        if viz_type == '3d_scatter' and (not y_col or not z_col):
            return JsonResponse({'error': '3D scatter plots require X, Y, and Z columns'}, status=400)
        
        # For bubble charts, size column is required
        if viz_type == 'bubble' and not size_col:
            return JsonResponse({'error': 'Bubble charts require a size column'}, status=400)
        
        # Read data
        df = read_file_data(data_file, selected_table)
        if df is None or df.empty:
            return JsonResponse({'error': 'Unable to read data'}, status=400)
        
        # Set plot style
        plt.style.use(plot_style)
        
        # Create the visualization
        plt.figure(figsize=(8, 5))
        
        try:
            # Create specific chart type
            if viz_type == 'bar':
                create_bar_chart(df, x_col, y_col, color_col, palette)
            elif viz_type == 'line':
                create_line_chart(df, x_col, y_col, color_col, palette)
            elif viz_type == 'scatter':
                create_scatter_plot(df, x_col, y_col, color_col, size_col, palette)
            elif viz_type == 'pie':
                create_pie_chart(df, x_col, y_col, palette)
            elif viz_type == 'histogram':
                create_histogram(df, x_col, color_col, palette)
            elif viz_type == 'heatmap':
                create_heatmap(df, x_col, y_col, z_col, palette)
            elif viz_type == 'bubble':
                create_bubble_chart(df, x_col, y_col, size_col, color_col, palette)
            elif viz_type == 'box':
                create_box_plot(df, x_col, y_col, color_col, palette)
            elif viz_type == 'violin':
                create_violin_plot(df, x_col, y_col, color_col, palette)
            elif viz_type == '3d_scatter':
                create_3d_scatter(df, x_col, y_col, z_col, color_col, palette)
            
            # Add title and labels
            plt.title('Preview')
            plt.xlabel(x_col)
            if viz_type not in ['pie', 'heatmap']:
                plt.ylabel(y_col if y_col else 'Count')
            
            if grid:
                plt.grid(True, linestyle='--', alpha=0.7)
            
            # Add legend if applicable
            if color_col and viz_type not in ['pie', 'heatmap']:
                plt.legend(title=color_col)
            
            plt.tight_layout()
            
            # Convert to base64
            image_data = get_image_as_base64(plt)
            plt.close()
            
            return JsonResponse({
                'success': True,
                'image': image_data
            })
            
        except Exception as e:
            plt.close()
            return JsonResponse({'error': str(e)}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Helper functions for creating different chart types
def create_bar_chart(df, x_col, y_col, color_col, palette):
    if y_col:
        if color_col:
            # Grouped bar chart
            groups = df.groupby([x_col, color_col])[y_col].mean().unstack()
            groups.plot(kind='bar', colormap=palette)
        else:
            # Standard bar chart
            df.plot(kind='bar', x=x_col, y=y_col, colormap=palette)
    else:
        # Value counts for single column
        value_counts = df[x_col].value_counts().sort_index()
        value_counts.plot(kind='bar', colormap=palette)

def create_line_chart(df, x_col, y_col, color_col, palette):
    if color_col:
        # Multiple lines grouped by color column
        for name, group in df.groupby(color_col):
            plt.plot(group[x_col], group[y_col], label=name)
    else:
        df.plot(kind='line', x=x_col, y=y_col, colormap=palette)

def create_scatter_plot(df, x_col, y_col, color_col, size_col, palette):
    if color_col:
        # Colored scatter plot
        scatter = plt.scatter(
            df[x_col], 
            df[y_col], 
            c=df[color_col] if pd.api.types.is_numeric_dtype(df[color_col]) else None,
            s=df[size_col] if size_col and pd.api.types.is_numeric_dtype(df[size_col]) else 50,
            alpha=0.7,
            cmap=palette
        )
        
        # If color column is categorical, create a legend
        if not pd.api.types.is_numeric_dtype(df[color_col]):
            for name, group in df.groupby(color_col):
                plt.scatter(
                    group[x_col], 
                    group[y_col], 
                    label=name,
                    s=group[size_col] if size_col and pd.api.types.is_numeric_dtype(df[size_col]) else 50,
                    alpha=0.7
                )
        else:
            # Add a colorbar for numeric color values
            plt.colorbar(scatter, label=color_col)
    else:
        # Simple scatter plot
        plt.scatter(
            df[x_col], 
            df[y_col], 
            s=df[size_col] if size_col and pd.api.types.is_numeric_dtype(df[size_col]) else 50,
            alpha=0.7
        )

def create_pie_chart(df, x_col, y_col, palette):
    if y_col:
        # Use provided y-column for values
        pie_data = df.groupby(x_col)[y_col].sum()
    else:
        # Count occurrences of x values
        pie_data = df[x_col].value_counts()
    
    # Limit to top 10 categories if there are too many
    if len(pie_data) > 10:
        top_n = pie_data.nlargest(9)
        other_count = pie_data[~pie_data.index.isin(top_n.index)].sum()
        pie_data = pd.concat([top_n, pd.Series({'Other': other_count})])
    
    pie_data.plot(kind='pie', autopct='%1.1f%%', colormap=palette)
    plt.ylabel('')  # Remove y-label for pie charts

def create_histogram(df, x_col, color_col, palette):
    if not pd.api.types.is_numeric_dtype(df[x_col]):
        # Try to convert to numeric
        numeric_data = pd.to_numeric(df[x_col], errors='coerce')
        if numeric_data.notna().any():
            if color_col and pd.api.types.is_categorical_dtype(df[color_col]) or df[color_col].nunique() < 10:
                # Separate histograms by color category
                for name, group in df.groupby(color_col):
                    group_data = pd.to_numeric(group[x_col], errors='coerce')
                    plt.hist(group_data.dropna(), alpha=0.5, label=name, bins=20)
            else:
                plt.hist(numeric_data.dropna(), bins=20, color='skyblue')
        else:
            raise ValueError(f"Column {x_col} cannot be converted to numeric data for histogram")
    else:
        if color_col and (pd.api.types.is_categorical_dtype(df[color_col]) or df[color_col].nunique() < 10):
            # Separate histograms by color category
            for name, group in df.groupby(color_col):
                plt.hist(group[x_col], alpha=0.5, label=name, bins=20)
        else:
            df[x_col].plot(kind='hist', bins=20, colormap=palette)

def create_heatmap(df, x_col, y_col, z_col, palette):
    if not z_col:
        # Create a pivot table of counts
        heatmap_data = pd.crosstab(df[y_col], df[x_col])
    else:
        # Create a pivot table with z values
        heatmap_data = df.pivot_table(values=z_col, index=y_col, columns=x_col, aggfunc='mean')
    
    # Plot heatmap
    plt.imshow(heatmap_data, cmap=palette, aspect='auto')
    plt.colorbar(label=z_col if z_col else 'Count')
    
    # Set x and y ticks
    tick_spacing = max(1, len(heatmap_data.columns) // 10)  # Limit to about 10 labels
    plt.xticks(range(0, len(heatmap_data.columns), tick_spacing), 
              [str(x) for x in heatmap_data.columns[::tick_spacing]], 
              rotation=45)
    
    tick_spacing = max(1, len(heatmap_data.index) // 10)
    plt.yticks(range(0, len(heatmap_data.index), tick_spacing), 
              [str(y) for y in heatmap_data.index[::tick_spacing]])

def create_bubble_chart(df, x_col, y_col, size_col, color_col, palette):
    # Normalize size for bubble chart (between 20 and 500)
    if size_col and pd.api.types.is_numeric_dtype(df[size_col]):
        size_values = df[size_col]
        if size_values.min() != size_values.max():  # Avoid division by zero
            sizes = 20 + 480 * (size_values - size_values.min()) / (size_values.max() - size_values.min())
        else:
            sizes = 100  # Default size if all values are the same
    else:
        sizes = 100
        
    if color_col:
        scatter = plt.scatter(
            df[x_col], 
            df[y_col], 
            s=sizes,
            c=df[color_col] if pd.api.types.is_numeric_dtype(df[color_col]) else None,
            alpha=0.6,
            cmap=palette
        )
        
        if pd.api.types.is_numeric_dtype(df[color_col]):
            plt.colorbar(scatter, label=color_col)
        else:
            # If color column is categorical, create a legend
            for name, group in df.groupby(color_col):
                if size_col and pd.api.types.is_numeric_dtype(df[size_col]):
                    group_sizes = 20 + 480 * (group[size_col] - size_values.min()) / (size_values.max() - size_values.min())
                else:
                    group_sizes = 100
                    
                plt.scatter(
                    group[x_col], 
                    group[y_col], 
                    s=group_sizes,
                    label=name,
                    alpha=0.6
                )
    else:
        plt.scatter(df[x_col], df[y_col], s=sizes, alpha=0.6)
    
    # Add a reference bubble in the legend for size
    if size_col and pd.api.types.is_numeric_dtype(df[size_col]):
        # Add invisible points for size reference
        for size, label in [(50, 'Small'), (200, 'Medium'), (400, 'Large')]:
            plt.scatter([], [], s=size, alpha=0.4, label=f'{label} {size_col}')

def create_box_plot(df, x_col, y_col, color_col, palette):
    if not y_col:
        # Single boxplot for x column
        if pd.api.types.is_numeric_dtype(df[x_col]):
            plt.boxplot(df[x_col].dropna())
            plt.xticks([1], [x_col])
        else:
            raise ValueError(f"Column {x_col} must be numeric for a box plot without a category column")
    else:
        # Boxplot of y grouped by x
        if pd.api.types.is_numeric_dtype(df[y_col]):
            if color_col:
                # Box plot with color grouping
                boxplot_data = []
                labels = []
                
                for (x_val, color_val), group in df.groupby([x_col, color_col]):
                    boxplot_data.append(group[y_col].dropna())
                    labels.append(f"{x_val}, {color_val}")
                
                plt.boxplot(boxplot_data)
                plt.xticks(range(1, len(labels) + 1), labels, rotation=45)
            else:
                # Simple box plot grouped by x
                boxplot_data = [group[y_col].dropna() for _, group in df.groupby(x_col)]
                plt.boxplot(boxplot_data)
                plt.xticks(range(1, len(df[x_col].unique()) + 1), df[x_col].unique(), rotation=45)
        else:
            raise ValueError(f"Column {y_col} must be numeric for a box plot")

def create_violin_plot(df, x_col, y_col, color_col, palette):
    if not y_col:
        # Cannot create a violin plot without both x (categorical) and y (numeric)
        raise ValueError("Violin plots require both X (categorical) and Y (numeric) columns")
    
    if not pd.api.types.is_numeric_dtype(df[y_col]):
        raise ValueError(f"Column {y_col} must be numeric for a violin plot")
    
    try:
        from scipy import stats
        import seaborn as sns
        
        # Use seaborn for better violin plots
        if color_col:
            sns.violinplot(x=x_col, y=y_col, hue=color_col, data=df, palette=palette)
        else:
            sns.violinplot(x=x_col, y=y_col, data=df, palette=palette)
    except ImportError:
        # Fallback to a box plot if seaborn is not available
        create_box_plot(df, x_col, y_col, color_col, palette)
        # Instead, just print a warning to the console
        print("Warning: Seaborn library not available. Showing box plot instead of violin plot.")

def create_3d_scatter(df, x_col, y_col, z_col, color_col, palette):
    # Create a 3D axis
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    if color_col and pd.api.types.is_numeric_dtype(df[color_col]):
        scatter = ax.scatter(
            df[x_col], 
            df[y_col], 
            df[z_col],
            c=df[color_col],
            cmap=palette,
            alpha=0.7
        )
        plt.colorbar(scatter, label=color_col)
    elif color_col:
        # Categorical color column
        for name, group in df.groupby(color_col):
            ax.scatter(
                group[x_col], 
                group[y_col], 
                group[z_col],
                label=name,
                alpha=0.7
            )
        ax.legend()
    else:
        ax.scatter(df[x_col], df[y_col], df[z_col], alpha=0.7)
    
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_zlabel(z_col)
