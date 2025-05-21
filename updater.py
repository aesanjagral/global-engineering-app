import os
import sys
import requests
import subprocess
import tkinter as tk
from tkinter import messagebox
import json

class Updater:
    def __init__(self):
        self.current_version = "1.0.0"  # Current version of your app
        self.github_repo = "aesanjagral/global-engineering-app"  # Replace YOUR_GITHUB_USERNAME with your actual GitHub username
        self.update_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        
    def check_for_updates(self):
        try:
            response = requests.get(self.update_url)
            if response.status_code == 200:
                latest_version = response.json()["tag_name"]
                if latest_version > self.current_version:
                    return True, latest_version
            return False, None
        except Exception as e:
            print(f"Update check failed: {str(e)}")
            return False, None

    def download_update(self, version):
        try:
            # Create a temporary directory for the update
            temp_dir = os.path.join(os.environ["TEMP"], "app_update")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Download the new version
            download_url = f"https://github.com/{self.github_repo}/releases/download/{version}/app.exe"
            response = requests.get(download_url, stream=True)
            
            if response.status_code == 200:
                update_file = os.path.join(temp_dir, "app.exe")
                with open(update_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return update_file
            return None
        except Exception as e:
            print(f"Download failed: {str(e)}")
            return None

    def install_update(self, update_file):
        try:
            # Create a batch file to handle the update
            batch_file = os.path.join(os.environ["TEMP"], "update.bat")
            with open(batch_file, "w") as f:
                f.write(f"""
                @echo off
                timeout /t 2 /nobreak
                del "{sys.executable}"
                copy "{update_file}" "{sys.executable}"
                start "" "{sys.executable}"
                del "{update_file}"
                del "%~f0"
                """)
            
            # Run the batch file
            subprocess.Popen([batch_file], shell=True)
            sys.exit()
        except Exception as e:
            print(f"Installation failed: {str(e)}")
            return False

def show_update_dialog():
    updater = Updater()
    has_update, version = updater.check_for_updates()
    
    if has_update:
        root = tk.Tk()
        root.withdraw()
        
        if messagebox.askyesno("Update Available", 
                              f"New version {version} is available. Would you like to update now?"):
            update_file = updater.download_update(version)
            if update_file:
                updater.install_update(update_file)
            else:
                messagebox.showerror("Update Failed", "Failed to download the update.")
        root.destroy() 