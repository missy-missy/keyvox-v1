import os
import sys
import subprocess
import shutil

# --- Configuration ---
# Suffix for the file in secure storage (the actual hidden file)
SECURE_SUFFIX = ".kvy_secure" 
# Name for the visible launcher file in the original location (the 'locked' file)
LAUNCHER_SUFFIX = ".locked_launcher" 
LOCKED_FOLDER_NAME = ".KeyVox_Locked_Files"

def _get_lock_storage_dir():
    """Determines a secure, hidden, and persistent directory for locked files."""
    try:
        # Use APPDATA for Windows systems for better hiding, or HOME directory as fallback
        if sys.platform.startswith('win'):
            base_path = os.environ.get('APPDATA')
        else:
            base_path = os.path.expanduser('~')
            
        # Create the hidden folder path inside the determined base path
        lock_dir = os.path.join(base_path, LOCKED_FOLDER_NAME)
        
        if not os.path.exists(lock_dir):
            os.makedirs(lock_dir, exist_ok=True)
            
        return lock_dir
    except Exception as e:
        print(f"Error determining secure storage path: {e}")
        # Fallback to the current directory if everything else fails
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "fallback_locked_storage")

def _open_file_in_os(filepath):
    """Opens a file using the operating system's default handler."""
    try:
        if sys.platform.startswith('win'):
            # os.startfile will execute the .bat file or open the restored file
            os.startfile(filepath)
        elif sys.platform == 'darwin':
            subprocess.run(['open', filepath], check=True)
        else:
            subprocess.run(['xdg-open', filepath], check=True)
        return True
    except Exception as e:
        print(f"Failed to open file in OS: {e}")
        return False

def _create_launcher(original_filepath_without_ext, secure_locked_filepath):
    """
    Creates a launcher script (e.g., .bat) at the original location.
    The launcher calls the main app.py in interceptor mode.
    """
    script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    app_py_path = os.path.join(script_dir, "app.py")
    
    # Path for the launcher file (uses a common script extension)
    launcher_path = original_filepath_without_ext + LAUNCHER_SUFFIX 
    
    # The actual path of the Python interpreter (use sys.executable for robustness)
    python_exe = sys.executable 

    # Determine the script content based on OS
    if sys.platform.startswith('win'):
        # For Windows: Create a simple batch script (.bat)
        # Note: 'start /b' can be used to run silently, but we need the console for debug/errors.
        launcher_content = f"""
@echo off
"{python_exe}" "{app_py_path}" "{secure_locked_filepath}"
rem The exit code (0 for success, 1 for failure) is handled by app.py
exit /b %errorlevel%
"""
        launcher_path += ".bat"
    else:
        # For Linux/macOS: Create a simple shell script
        launcher_content = f"""
#!/bin/bash
"{python_exe}" "{app_py_path}" "{secure_locked_filepath}"
exit $?
"""
        launcher_path += ".sh"

    try:
        with open(launcher_path, 'w') as f:
            f.write(launcher_content.strip())
        
        # Make the script executable on Unix-like systems
        if not sys.platform.startswith('win'):
            os.chmod(launcher_path, 0o755)
            
        print(f"Created launcher file: {launcher_path}")
        return True, launcher_path
    except Exception as e:
        return False, f"Error creating launcher script: {e}"


def lock_file(original_filepath):
    """
    Moves the original file to secure storage and creates a launcher script
    in its place to trigger the authentication flow.
    """
    original_filepath = os.path.abspath(original_filepath)
    if not os.path.exists(original_filepath):
        return False, "Original file not found."
        
    original_base, original_filename = os.path.split(original_filepath)
    original_filename_without_ext, original_ext = os.path.splitext(original_filename)

    lock_dir = _get_lock_storage_dir()
    
    # 1. Define the secure path for the locked file (uses the original full path for uniqueness)
    unique_locked_name = original_filepath.replace(os.path.sep, '_').replace(':', '') + SECURE_SUFFIX
    secure_locked_filepath = os.path.join(lock_dir, unique_locked_name)
    
    # 2. Check if a launcher or original file already exists at the location
    if os.path.exists(secure_locked_filepath):
        return False, "A securely locked file with this name already exists. Unlock it first."

    # 3. Move the original file to secure storage (This removes it from the original location)
    try:
        shutil.move(original_filepath, secure_locked_filepath)
    except Exception as e:
        return False, f"Could not move file to secure storage: {e}"

    # 4. Create the visible launcher file in the original file's place
    success, result_path = _create_launcher(os.path.join(original_base, original_filename_without_ext), secure_locked_filepath)

    if not success:
        # Critical failure: The original file is gone. Try to move it back!
        try:
            shutil.move(secure_locked_filepath, original_filepath)
            return False, f"Failed to create launcher. File restored. Error: {result_path}"
        except Exception:
            return False, f"Failed to create launcher AND failed to restore file. Manually check: {secure_locked_filepath}. Error: {result_path}"

    # Returns True and the secure path, which must be stored by the calling app logic.
    return True, secure_locked_filepath


def unlock_file(secure_locked_filepath):
    """
    Restores the file from secure storage to its original location and deletes the launcher.
    """
    if not secure_locked_filepath or not os.path.exists(secure_locked_filepath):
        return False, "Locked file path is invalid or does not exist in secure storage."
        
    locked_filename = os.path.basename(secure_locked_filepath)
    
    # 1. Reverse the naming to find the original path
    original_path_with_sep = locked_filename.removesuffix(SECURE_SUFFIX).replace('_', os.path.sep)
    
    # Reconstruct the drive letter on Windows if necessary
    if sys.platform.startswith('win') and ':' not in original_path_with_sep:
        original_filepath = original_path_with_sep[0] + ':' + original_path_with_sep[1:]
    else:
        original_filepath = original_path_with_sep

    # Correct any residual path issues
    original_filepath = original_filepath.lstrip(os.path.sep)
    
    # Define the original file's base name and the launcher paths
    original_base, original_filename = os.path.split(original_filepath)
    original_filename_without_ext, original_ext = os.path.splitext(original_filename)

    launcher_base_path = os.path.join(original_base, original_filename_without_ext) + LAUNCHER_SUFFIX

    launcher_paths = [
        launcher_base_path + ".bat", # Windows
        launcher_base_path + ".sh"   # Linux/macOS
    ]
    
    # 2. Restore the file from secure storage to its original location
    try:
        original_base_dir = os.path.dirname(original_filepath)
        if not os.path.exists(original_base_dir):
            os.makedirs(original_base_dir, exist_ok=True)

        shutil.move(secure_locked_filepath, original_filepath)
    except Exception as e:
        return False, f"Could not restore original file. Please manually retrieve it from: {secure_locked_filepath}. Error: {e}"

    # 3. Delete the launcher file
    for path in launcher_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Removed launcher file: {path}")
            except Exception as e:
                # Not a critical error, but log it
                print(f"Warning: Failed to delete launcher file {path}. Error: {e}")

    # 4. Open the file 
    if not _open_file_in_os(original_filepath):
        return True, f"File unlocked, but failed to open automatically. Path: {original_filepath}"
        
    return True, original_filepath