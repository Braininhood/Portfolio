# Virtual Environment Usage Guide

## ⚠️ Important: Always Use Virtual Environment Python

**Problem:** Using system Python instead of virtual environment Python causes `ModuleNotFoundError` for packages installed in the venv.

**Solution:** Always use the virtual environment Python for Django commands.

---

## ✅ Correct Commands (Windows PowerShell)

### Option 1: Use Virtual Environment Python Directly

```powershell
# System check
.\venv\Scripts\python.exe manage.py check

# Run server
.\venv\Scripts\python.exe manage.py runserver

# Run migrations
.\venv\Scripts\python.exe manage.py migrate

# Create superuser
.\venv\Scripts\python.exe manage.py createsuperuser

# Make migrations
.\venv\Scripts\python.exe manage.py makemigrations
```

### Option 2: Activate Virtual Environment First

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Now you can use regular python command
python manage.py check
python manage.py runserver
python manage.py migrate
```

### Option 3: Use Convenience Scripts

```powershell
# System check
.\check.ps1

# Run server
.\runserver.ps1
```

---

## ❌ Incorrect Commands (Will Cause Errors)

```powershell
# DON'T use system Python directly (causes ModuleNotFoundError)
python manage.py check  # ❌ Uses system Python, not venv Python

# DON'T use python without activating venv
python manage.py runserver  # ❌ Will fail if venv not activated
```

---

## 🔍 How to Verify You're Using the Correct Python

### Check Python Location
```powershell
# Should show venv Python path
.\venv\Scripts\python.exe --version
# Output: Python 3.14.0 (or your venv Python version)

# Should show venv location
.\venv\Scripts\python.exe -c "import sys; print(sys.executable)"
# Output: D:\MultiBook\backend\venv\Scripts\python.exe
```

### Check Installed Packages
```powershell
# Should show all packages including django-environ
.\venv\Scripts\pip.exe list

# Verify django-environ is installed
.\venv\Scripts\pip.exe show django-environ
# Output: Name: django-environ, Version: 0.12.0
```

---

## ✅ Verification Commands

### Test System Check
```powershell
cd D:\MultiBook\backend
.\venv\Scripts\python.exe manage.py check
# Should show: "System check identified 9 issues (0 silenced)."
# All 9 are warnings, not errors - this is CORRECT!
```

### Test Server Start
```powershell
cd D:\MultiBook\backend
.\venv\Scripts\python.exe manage.py runserver
# Should start server on http://127.0.0.1:8000/
```

---

## 📝 Common Issues and Solutions

### Issue 1: ModuleNotFoundError: No module named 'environ'
**Cause:** Using system Python instead of venv Python  
**Solution:** Use `.\venv\Scripts\python.exe manage.py check` or activate venv first

### Issue 2: ModuleNotFoundError: No module named 'django'
**Cause:** Using system Python instead of venv Python  
**Solution:** Use `.\venv\Scripts\python.exe manage.py check` or activate venv first

### Issue 3: Permission denied when activating venv
**Cause:** PowerShell execution policy  
**Solution:** Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

## 🎯 Best Practices

1. **Always use venv Python:** Use `.\venv\Scripts\python.exe` or activate venv first
2. **Check before running:** Verify packages are installed with `.\venv\Scripts\pip.exe list`
3. **Use convenience scripts:** Use `.\check.ps1` and `.\runserver.ps1` for common commands
4. **Activate venv in terminal:** If working in the same terminal session, activate once

---

## 🔧 Convenience Scripts Created

### `check.ps1`
Quick system check using venv Python:
```powershell
.\check.ps1
```

### `runserver.ps1`
Quick server start using venv Python:
```powershell
.\runserver.ps1
```

---

## ✅ Verification Status

- ✅ `django-environ` is installed in venv (v0.12.0)
- ✅ System check passes with venv Python (9 warnings, 0 errors)
- ✅ All packages from `requirements.txt` are installed in venv
- ✅ Virtual environment is properly configured

---

**Last Updated:** Week 1 Day 6-7  
**Status:** ✅ All commands work correctly when using venv Python
