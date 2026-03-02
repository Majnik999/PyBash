import os
import sys
import shutil
import subprocess
import platform
import ctypes

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def build_setup():
    if os.name != 'nt':
        print("[!] Setup builder is only for Windows.")
        return

    print("[-] Building PyBash Setup Tool...")
    
    # 1. Build the main application as a directory (--onedir)
    # This is faster to start than onefile and better for installed programs
    print("[-] Compiling application binary...")
    build_app_cmd = [
        "pyinstaller", "--onedir", "--name=pybash_app", "--noconfirm",
        "--add-data", "core;core", "--add-data", "plugins;plugins",
        "pybash.py"
    ]
    subprocess.check_call(build_app_cmd)

    # 2. Create the Installer Script Logic
    # This script will be compiled into the "Setup.exe"
    installer_script = """
import os
import shutil
import subprocess
import sys
import winreg

APP_NAME = "PyBash"
INSTALL_DIR = os.path.join(os.environ['LOCALAPPDATA'], APP_NAME)
SOURCE_DIR = "pybash_app"

def install():
    print(f"Installing {APP_NAME} to {INSTALL_DIR}...")
    
    if os.path.exists(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR)
    
    shutil.copytree(SOURCE_DIR, INSTALL_DIR)
    
    # Add to PATH
    print("Adding to User PATH...")
    path_to_add = INSTALL_DIR
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_ALL_ACCESS) as key:
            existing_path, _ = winreg.QueryValueEx(key, 'Path')
            if path_to_add not in existing_path:
                new_path = existing_path + ';' + path_to_add
                winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
                print("[+] Successfully added to PATH.")
            else:
                print("[*] Already in PATH.")
    except Exception as e:
        print(f"[!] Failed to update PATH: {e}")

    print("\\n[+++] PyBash Installed Successfully!")
    print("[!] Please restart your terminal to use the 'pybash_app' command.")
    input("Press Enter to finish...")

if __name__ == '__main__':
    install()
"""
    with open("installer_logic.py", "w") as f:
        f.write(installer_script)

    # 3. Build the Installer itself
    print("[-] Compiling Installer executable...")
    build_installer_cmd = [
        "pyinstaller", "--onefile", "--name=PyBash_Setup", "--noconfirm",
        "--add-data", "dist/pybash_app;pybash_app",
        "installer_logic.py"
    ]
    subprocess.check_call(build_installer_cmd)

    print("\n[+] Setup Tool Built!")
    print(f"[+] Installer located at: {os.path.abspath('dist/PyBash_Setup.exe')}")

if __name__ == "__main__":
    build_setup()
