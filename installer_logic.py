
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

    print("\n[+++] PyBash Installed Successfully!")
    print("[!] Please restart your terminal to use the 'pybash_app' command.")
    input("Press Enter to finish...")

if __name__ == '__main__':
    install()
