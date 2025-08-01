import os
import shutil
from datetime import datetime

# Path to the file or folder you want to back up
SOURCE_PATH = r'C:\Users\fuach\OneDrive\Desktop\WMS\Wholesale_Management_Sytem\wholesale.db'
# Path to the backup directory
BACKUP_DIR = r'C:\Users\fuach\OneDrive\Desktop\WMS\Wholesale_Management_Sytem\backup'

def make_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = os.path.basename(SOURCE_PATH.rstrip(r'\/'))
    backup_name = f"{base_name}_{timestamp}"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if os.path.isdir(SOURCE_PATH):
        shutil.copytree(SOURCE_PATH, backup_path)
    else:
        shutil.copy2(SOURCE_PATH, backup_path)
    print(f"Backup created at {backup_path}")

if __name__ == "__main__":
    make_backup()