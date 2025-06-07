#!/usr/bin/env python3
"""
Quick script to fix common linting issues
"""
import os
import re

def fix_file(filepath):
    """Fix common linting issues in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove trailing whitespace
        lines = content.split('\n')
        fixed_lines = [line.rstrip() for line in lines]
        
        # Fix long lines (simple approach for some cases)
        for i, line in enumerate(fixed_lines):
            if len(line) > 79:
                # Simple fixes for some patterns
                if 'list_display' in line and '[' in line:
                    # Break long list_display lines
                    parts = line.split('[', 1)
                    if len(parts) == 2:
                        indent = ' ' * (len(parts[0]) + 1)
                        items = parts[1].rstrip(']').split(', ')
                        if len(items) > 3:
                            fixed_lines[i] = parts[0] + '['
                            for j, item in enumerate(items):
                                if j == 0:
                                    fixed_lines[i] += item + ','
                                elif j == len(items) - 1:
                                    fixed_lines.insert(i + j, indent + item + ']')
                                else:
                                    fixed_lines.insert(i + j, indent + item + ',')
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))
            if not content.endswith('\n'):
                f.write('\n')
        
        print(f"Fixed: {filepath}")
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")

# Fix Python files with issues
files_to_fix = [
    'server/djangoapp/models.py',
    'server/djangoapp/views.py',
    'server/start_services.py'
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        fix_file(file_path)

print("Linting fixes completed!") 