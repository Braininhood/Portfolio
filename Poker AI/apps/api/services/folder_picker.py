"""Cross-platform native folder picker (Windows, macOS, Linux)."""

from __future__ import annotations

import platform
import subprocess


def pick_folder_sync(*, title: str = "Select folder with hand histories") -> str:
    """Return absolute folder path, or empty string if cancelled."""
    system = platform.system()
    if system == "Darwin":
        path = _pick_macos(title)
        if path:
            return path
    elif system == "Windows":
        path = _pick_windows(title)
        if path:
            return path
    else:
        path = _pick_linux(title)
        if path:
            return path
    return _pick_tkinter(title)


def _pick_macos(title: str) -> str:
    prompt = title.replace('"', '\\"')
    script = f'POSIX path of (choose folder with prompt "{prompt}")'
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _pick_windows(title: str) -> str:
    safe_title = title.replace("'", "''")
    ps = f"""
Add-Type -AssemblyName System.Windows.Forms
$dlg = New-Object System.Windows.Forms.FolderBrowserDialog
$dlg.Description = '{safe_title}'
$dlg.ShowNewFolderButton = $true
if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{
  Write-Output $dlg.SelectedPath
}}
""".strip()
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-STA", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _pick_linux(title: str) -> str:
    for cmd in (
        ["zenity", "--file-selection", "--directory", f"--title={title}"],
        ["kdialog", "--getexistingdirectory", "."],
        ["yad", "--file", "--directory", f"--title={title}"],
    ):
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except FileNotFoundError:
            continue
        if proc.returncode != 0:
            continue
        out = proc.stdout.strip()
        if out:
            return out
    return ""


def _pick_tkinter(title: str) -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        msg = (
            "No folder picker available. Install zenity (Linux) or use a Python build "
            "with tkinter, or paste the folder path manually."
        )
        raise RuntimeError(msg) from exc
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    path = filedialog.askdirectory(title=title, mustexist=True)
    root.destroy()
    return str(path).strip() if path else ""
