import argparse
import shutil
from pathlib import Path
from tqdm import tqdm
import os


def copy_files_to_subfolders(subset_folder: Path, target_folder: Path):
    """
    Copy files from the subset folder to the corresponding subfolders in the target folder.
    The filenames in the subset folder follow 'subfoldername_motionxglobal.mp4'.
    
    Args:
        subset_folder (Path): Path to the subset folder containing files.
        target_folder (Path): Path to the target folder with subfolders.
    """
    # Ensure paths exist
    if not subset_folder.exists():
        raise FileNotFoundError(f"Subset folder not found: {subset_folder}")
    if not target_folder.exists():
        raise FileNotFoundError(f"Target folder not found: {target_folder}")

    # Get all .mp4 files in the subset folder
    files = list(subset_folder.glob("*.mp4"))
    print(f"Found {len(files)} .mp4 files in the subset folder: {subset_folder}")

    for file in tqdm(files, desc="Copying files"):
        if file.is_file():
            # Extract the subfolder name by removing '_motionxglobal' and the extension
            subfolder_name = file.stem.replace('_mxglobal', '')  # Remove '_motionxglobal'

            # Define the path to the corresponding subfolder
            subfolder_path = target_folder / subfolder_name

            # Check if subfolder exists in the target folder
            if subfolder_path.exists() and subfolder_path.is_dir():
                # Copy the file into the subfolder
                destination_path = subfolder_path / file.name
                shutil.copy2(file, destination_path)
                print(f"Copied: {file} -> {destination_path}")
            else:
                print(f"Warning: Subfolder not found for '{file.name}' at {subfolder_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy files to corresponding subfolders in target folder.")
    parser.add_argument("--subset", type=str, required=True, help="Path to the subset folder containing files.")
    args = parser.parse_args()


    # Convert arguments to Path objects
    subset_folder = Path('./motionxvis/'+args.subset)
    target_folder = Path('./gvhmr_out')
 
    # Run the file copying function
    copy_files_to_subfolders(subset_folder, target_folder)

