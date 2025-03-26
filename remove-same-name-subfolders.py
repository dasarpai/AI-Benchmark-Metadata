import os
import shutil

def remove_self_named_subfolders(root_path):
    for foldername in os.listdir(root_path):
        folder_path = os.path.join(root_path, foldername)

        # Check if it's a directory
        if os.path.isdir(folder_path):
            for subfoldername in os.listdir(folder_path):
                subfolder_path = os.path.join(folder_path, subfoldername)

                # If the subfolder is also a directory and has same name as parent
                if os.path.isdir(subfolder_path) and subfoldername == foldername:
                    print(f"Removing: {subfolder_path}")
                    shutil.rmtree(subfolder_path)

# Example usage
root_directory = r"paperswithcode\See_all_1951_tasks"  # Change this to your actual path
remove_self_named_subfolders(root_directory)
