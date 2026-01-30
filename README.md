# Operating Systems Course - Grading System

Automated grading tools for Operating Systems course assignments.

## Requirements

- **Windows with WSL** - For compiling and running C code
- **Python 3** - Installed on Windows (and WSL for grading scripts)

## Python Utilities (Root Folder)

### extract_submissions_from_zip.py

Extracts student submission archives (.tar.gz and .zip files) from Moodle download folders. Automatically flattens nested directories to find the actual submission files.

**Usage:**

```cmd
# Extract from default 'submissions' folder in current directory
python extract_submissions_from_zip.py

# Extract from a specific folder (e.g., Ex1/submissions)
python extract_submissions_from_zip.py Ex1/submissions

# Extract from Ex2
python extract_submissions_from_zip.py Ex2/submissions
```

### extract_pdf.py

Simple utility to extract text from PDF files using PyPDF2.

## Exercise Folders

- **Ex1/** - Shell assignment grading (HW1)
- **Ex2/** - Advanced shell grading (HW2)
- **Ex3/** - Assignment 3 materials

Each exercise folder has its own README with specific instructions.

- **Prompt**: `$$ ` (dollar-dollar-space)
- **Background character**: `%` (percent sign)
- **Buffer size**: 2048 bytes
- **Args array**: 200 elements (max 199 words)
- **Source file**: `os1.c`
- **Executable**: `os1`

## Troubleshooting

### "No os1.c files found"

- Run the extraction script first: `python extract_submissions_from_zip.py`

### WSL not available

- Install WSL: `wsl --install` (requires admin privileges)
- Or use a Linux VM/machine to run the grading

### Compilation errors

- Check if `gcc` is installed in WSL: `wsl -e gcc --version`
- Install if needed: `wsl -e sudo apt install build-essential`

### Timeout errors

- Default timeout is 5 seconds per test
- Modify `TIMEOUT` variable in `test_script.py` if needed

## Configuration

Edit `test_script.py` to modify:

```python
TIMEOUT = 5              # Seconds per test
OUTPUT_DIR = "grading_results"
SUBMISSION_DIR = "submissions"
COMPILER = "gcc"
COMPILER_FLAGS = "-Wall"
```
