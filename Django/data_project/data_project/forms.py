from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import UserDataFile, Visualization, EncryptedUserProfile
import base64, hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os
import secrets
import pandas as pd
import json

class EncryptionMixin:
    """
    Mixin to handle encryption and decryption of user data
    """
    def _get_encryption_key(self, password):
        # Use password to create a 32-byte key (for AES-256)
        return hashlib.sha256(password.encode()).digest()
    
    def encrypt_data(self, data, password):
        if not data:
            return None
        
        key = self._get_encryption_key(password)
        # Generate a random initialization vector
        iv = secrets.token_bytes(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Convert data to string if not already
        if not isinstance(data, str):
            data = str(data)
            
        # Pad data to be a multiple of block size
        padded_data = pad(data.encode(), AES.block_size)
        
        # Encrypt data
        encrypted_data = cipher.encrypt(padded_data)
        
        # Combine IV and encrypted data and return as binary data for BinaryField
        return iv + encrypted_data
    
    def decrypt_data(self, encrypted_data, password):
        if not encrypted_data:
            return ""
            
        key = self._get_encryption_key(password)
        
        try:
            # Extract IV (first 16 bytes) and encrypted data
            iv = encrypted_data[:16]
            encrypted_bytes = encrypted_data[16:]
            
            # Create cipher and decrypt
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
            
            return decrypted_data.decode('utf-8')
        except Exception as e:
            # If decryption fails, return empty string or handle error
            return ""

class SignUpForm(UserCreationForm, EncryptionMixin):
    email = forms.EmailField(max_length=254, required=True)
    full_name = forms.CharField(max_length=100, required=False, help_text="Optional: Your full name")
    phone = forms.CharField(max_length=20, required=False, help_text="Optional: Your phone number")
    
    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'phone', 'password1', 'password2')
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Create encrypted profile
            encrypted_profile = EncryptedUserProfile(
                user=user,
                encrypted_email=self.encrypt_data(self.cleaned_data['email'], self.cleaned_data['password1']),
                encrypted_full_name=self.encrypt_data(self.cleaned_data.get('full_name', ''), self.cleaned_data['password1']),
                encrypted_phone=self.encrypt_data(self.cleaned_data.get('phone', ''), self.cleaned_data['password1'])
            )
            encrypted_profile.save()
        
        return user

class LoginForm(forms.Form):
    """
    Form for user login with username and password
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Basic validation - actual authentication done in view
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long")
        
        return cleaned_data

class DataFileUploadForm(forms.ModelForm):
    class Meta:
        model = UserDataFile
        fields = ('title', 'file')
    
    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if uploaded_file:
            file_name = uploaded_file.name.lower()
            file_ext = file_name.split('.')[-1]
            
            # Automatically determine file type
            if file_ext in ['csv']:
                self.instance.file_type = 'csv'
            elif file_ext in ['xls', 'xlsx', 'xlsm']:
                self.instance.file_type = 'excel'
            elif file_ext in ['db', 'sqlite', 'sqlite3']:
                self.instance.file_type = 'db'
            else:
                # Try to detect contents
                try:
                    # Check if it's a CSV by trying to read it
                    content = uploaded_file.read(1024)  # Read a sample of the file
                    uploaded_file.seek(0)  # Reset file pointer
                    
                    # Check if it appears to be a CSV
                    if b',' in content and b'\n' in content:
                        # Count commas vs tabs to decide if it's CSV
                        if content.count(b',') > content.count(b'\t'):
                            self.instance.file_type = 'csv'
                        else:
                            raise forms.ValidationError("Unrecognized file type. Please upload a CSV, Excel, or SQLite database file.")
                    elif content.startswith(b'SQLite format'):
                        self.instance.file_type = 'db'
                    elif content.startswith(b'PK\x03\x04'):  # Excel files are actually ZIP files
                        self.instance.file_type = 'excel'
                    else:
                        raise forms.ValidationError("Unrecognized file type. Please upload a CSV, Excel, or SQLite database file.")
                except Exception as e:
                    raise forms.ValidationError(f"Error detecting file type: {str(e)}")
                
        return uploaded_file

class DatabaseConnectionForm(forms.ModelForm, EncryptionMixin):
    db_password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True, label="Confirm Password")
    
    class Meta:
        model = UserDataFile
        fields = ('title', 'file_type', 'db_host', 'db_port', 'db_name', 'db_username', 'db_password')
        widgets = {
            'db_password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Create a filtered list of database choices
        db_choices = [choice for choice in UserDataFile.FILE_TYPES if choice[0] in ['mysql', 'postgres', 'mssql']]
        self.fields['file_type'].choices = db_choices
        self.fields['file_type'].label = "Database Type"
        
        # Default ports
        self.fields['db_port'].help_text = "Default ports: MySQL (3306), PostgreSQL (5432), SQL Server (1433)"
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('db_password')
        password_confirm = cleaned_data.get('db_password_confirm')
        
        if password and password_confirm and password != password_confirm:
            self.add_error('db_password_confirm', "Passwords don't match")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Encrypt the password before saving
        if 'db_password' in self.cleaned_data and self.cleaned_data['db_password']:
            # In a real implementation, we'd need a secure key for encryption
            # Here we're using a placeholder approach
            password = self.cleaned_data['db_password']
            encryption_key = settings.SECRET_KEY  # Use Django's secret key or a dedicated key
            # Here you would encrypt the password
            # instance.db_password = self.encrypt_data(password, encryption_key)
            
        if commit:
            instance.save()
        
        return instance

class VisualizationForm(forms.ModelForm):
    class Meta:
        model = Visualization
        fields = ('title', 'viz_type', 'x_column', 'y_column')
        
    def __init__(self, *args, **kwargs):
        # Extract custom parameters before calling parent's __init__
        self.columns = kwargs.pop('columns', [])
        self.data_file = kwargs.pop('data_file', None)
        self.column_types = kwargs.pop('column_types', {})
        
        # Now call parent's __init__ with cleaned kwargs
        super().__init__(*args, **kwargs)
        
        # Update title field with warning text
        self.fields['title'].help_text = "Give your visualization a unique title. Using duplicate titles might cause confusion."
        
        # Add automatic file type detection
        if self.data_file:
            self.fields['file_type'] = forms.CharField(
                widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
                required=False,
                initial=self.data_file.get_file_type_display()
            )
            
            # Check for existing titles
            existing_titles = Visualization.objects.filter(
                data_file=self.data_file
            ).values_list('title', flat=True)
            
            if existing_titles:
                existing_str = ", ".join([f'"{title}"' for title in existing_titles[:5]])
                if len(existing_titles) > 5:
                    existing_str += f", and {len(existing_titles)-5} more"
                self.fields['title'].help_text += f" Existing visualization titles: {existing_str}"
        
        # Populate column choices based on the file data
        if self.columns:
            # Create column choices with type information in the group
            numeric_columns = [(col, f"{col} (Numeric)") for col in self.columns if self.column_types.get(col) == 'numeric']
            categorical_columns = [(col, f"{col} (Categorical)") for col in self.columns if self.column_types.get(col) == 'categorical']
            date_columns = [(col, f"{col} (Date/Time)") for col in self.columns if self.column_types.get(col) == 'datetime']
            other_columns = [(col, col) for col in self.columns if col not in [c[0] for c in numeric_columns + categorical_columns + date_columns]]
            
            # X-axis column field with grouped options
            self.fields['x_column'] = forms.ChoiceField(
                choices=[('', '-- Select X-Axis Column --')] + 
                         ([(None, 'Date/Time Columns')] + date_columns if date_columns else []) +
                         ([(None, 'Categorical Columns')] + categorical_columns if categorical_columns else []) +
                         ([(None, 'Numeric Columns')] + numeric_columns if numeric_columns else []) +
                         ([(None, 'Other Columns')] + other_columns if other_columns else []),
                widget=forms.Select(attrs={'class': 'form-control'})
            )
            
            # Y-axis column field with grouped options but mainly numeric
            self.fields['y_column'] = forms.ChoiceField(
                choices=[('', '-- None (Optional) --')] + 
                         ([(None, 'Numeric Columns (Recommended)')] + numeric_columns if numeric_columns else []) +
                         ([(None, 'Other Columns')] + categorical_columns + date_columns + other_columns if categorical_columns + date_columns + other_columns else []),
                required=False,
                widget=forms.Select(attrs={'class': 'form-control'})
            ) 