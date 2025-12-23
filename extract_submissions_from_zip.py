"""
Script for extracting student submissions for Operating Systems course.
Extracts zip and tar.gz files in submission folders if no C files are present.
Handles nested folders inside archives by moving contents up to submission folder.
"""

import os
import shutil
import zipfile
import tarfile
from pathlib import Path


def flatten_nested_folders(submission_folder: Path) -> None:
    """
    If the archive extracted a single folder containing the actual files,
    move all contents from that nested folder up to the submission folder.
    
    Args:
        submission_folder: Path to the student's submission folder
    """
    # Check if there are C files directly in the submission folder
    direct_c_files = list(submission_folder.glob("*.c"))
    if direct_c_files:
        return  # Files are already at the right level
    
    # Look for subdirectories that might contain the actual submission
    subdirs = [d for d in submission_folder.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    for subdir in subdirs:
        # Check if this subdirectory contains C files
        nested_c_files = list(subdir.glob("*.c"))
        if nested_c_files:
            print(f"[FLATTEN] {submission_folder.name}: Moving files from nested folder '{subdir.name}'")
            
            # Move all contents from the nested folder to the submission folder
            for item in subdir.iterdir():
                dest = submission_folder / item.name
                if dest.exists():
                    # If file already exists, skip or handle conflict
                    print(f"[WARN] {submission_folder.name}: '{item.name}' already exists, skipping")
                    continue
                shutil.move(str(item), str(dest))
            
            # Remove the now-empty nested folder
            try:
                subdir.rmdir()
            except OSError:
                # Folder not empty, might have hidden files
                pass


def extract_archive_if_needed(submission_folder: Path) -> None:
    """
    Check if a submission folder contains C files.
    If not, extract any zip or tar.gz files found in the folder.
    Also handles nested folders inside archives.
    
    Args:
        submission_folder: Path to the student's submission folder
    """
    # Check for existing C files in the folder (including nested)
    c_files = list(submission_folder.glob("*.c"))
    nested_c_files = list(submission_folder.glob("**/*.c"))
    
    if c_files:
        print(f"[SKIP] {submission_folder.name}: Already has {len(c_files)} C file(s)")
        return
    
    if nested_c_files and not c_files:
        # C files exist but in nested folders - flatten them
        print(f"[INFO] {submission_folder.name}: Found C files in nested folders, flattening...")
        flatten_nested_folders(submission_folder)
        return
    
    # Find archive files in the folder
    zip_files = list(submission_folder.glob("*.zip"))
    tar_gz_files = list(submission_folder.glob("*.tar.gz")) + list(submission_folder.glob("*.tgz"))
    
    if not zip_files and not tar_gz_files:
        print(f"[WARN] {submission_folder.name}: No C files and no archive files found")
        return
    
    # Extract each zip file
    for zip_path in zip_files:
        try:
            print(f"[EXTRACT] {submission_folder.name}: Extracting {zip_path.name}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(submission_folder)
            print(f"[OK] {submission_folder.name}: Successfully extracted {zip_path.name}")
        except zipfile.BadZipFile:
            print(f"[ERROR] {submission_folder.name}: {zip_path.name} is not a valid zip file")
        except Exception as e:
            print(f"[ERROR] {submission_folder.name}: Failed to extract {zip_path.name} - {e}")
    
    # Extract each tar.gz file
    for tar_path in tar_gz_files:
        try:
            print(f"[EXTRACT] {submission_folder.name}: Extracting {tar_path.name}...")
            with tarfile.open(tar_path, 'r:gz') as tar_ref:
                tar_ref.extractall(submission_folder)
            print(f"[OK] {submission_folder.name}: Successfully extracted {tar_path.name}")
        except tarfile.TarError as e:
            print(f"[ERROR] {submission_folder.name}: {tar_path.name} is not a valid tar.gz file - {e}")
        except Exception as e:
            print(f"[ERROR] {submission_folder.name}: Failed to extract {tar_path.name} - {e}")
    
    # After extraction, check for nested folders and flatten if needed
    flatten_nested_folders(submission_folder)


def process_submissions(submissions_dir: str = "submissions") -> None:
    """
    Process all student submission folders.
    
    Args:
        submissions_dir: Path to the submissions directory
    """
    submissions_path = Path(submissions_dir)
    
    if not submissions_path.exists():
        print(f"Error: Submissions directory '{submissions_dir}' does not exist")
        return
    
    if not submissions_path.is_dir():
        print(f"Error: '{submissions_dir}' is not a directory")
        return
    
    # Get all subdirectories (student folders)
    student_folders = [f for f in submissions_path.iterdir() if f.is_dir()]
    
    if not student_folders:
        print(f"No student folders found in '{submissions_dir}'")
        return
    
    print(f"Found {len(student_folders)} student submission(s)\n")
    print("-" * 60)
    
    for folder in sorted(student_folders):
        extract_archive_if_needed(folder)
    
    print("-" * 60)
    print("\nProcessing complete!")


if __name__ == "__main__":
    process_submissions()
