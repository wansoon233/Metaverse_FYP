import shutil
import glob
import os

# Pattern to find the folders
folder_pattern = "Eplus-5zone-mixed-continuous-v1-res*"

# Find all matching folders
folders = glob.glob(folder_pattern)

print(f"Found {len(folders)} trash folders.")

for folder in folders:
    try:
        shutil.rmtree(folder) # Deletes the folder and everything inside
        print(f"Deleted: {folder}")
    except Exception as e:
        print(f"Error deleting {folder}: {e}")

print("✅ Cleanup complete. Project folder is clean.")
