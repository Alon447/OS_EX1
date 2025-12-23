# OS1 Shell Assignment Grader

Automated grading system for the Operating Systems course shell assignment (HW1-2026).

## Requirements

-  **Windows with WSL (Windows Subsystem for Linux)** - Required for compiling and running C code
-  **Python 3** - Installed in both Windows and WSL
-  **GCC** - C compiler (available in WSL Ubuntu by default)

## Project Structure

```
OS_EX1/
├── submissions/                    # Student submission folders
│   └── <student_name>_<id>_assignsubmission_file/
│       ├── <id>.tar.gz            # Original submission archive
│       ├── os1.c                  # Student's shell implementation
│       ├── os1.sh                 # Student's shell script
│       └── os1.pdf                # Student's answers
├── p_solution/                     # Lecturer's reference solution
│   ├── os1.c
│   └── os1.sh
├── grading_results/                # Output directory (created after grading)
│   ├── grading_summary.txt        # Summary of all grades
│   ├── grading_summary.csv        # CSV export of grades
│   ├── report_<student>.txt       # Individual student reports
│   └── clean_outputs/             # Clean test outputs for comparison
├── extract_submissions_from_zip.py # Extraction script
├── test_script.py                  # Main grading script
└── README.md                       # This file
```

## Usage

### Step 1: Extract Student Submissions

First, extract all `.tar.gz` archives from student submission folders:

```cmd
python extract_submissions_from_zip.py
```

This will:

-  Find all student submission folders in `submissions/`
-  Extract any `.tar.gz` or `.zip` files
-  Flatten nested folders if needed

### Step 2: Run the Grading Script

Since this grading script compiles and runs C code (Linux executables), you need to run it through WSL:

```cmd
wsl -e python3 test_script.py
```

Or alternatively, open WSL terminal and run:

```bash
cd /mnt/c/Users/<your_username>/Projects/OS_EX1
python3 test_script.py
```

### Step 3: View Results

After grading completes, check the `grading_results/` folder:

-  **`grading_summary.xlsx`** - Excel file with Part A and Part B errors in separate columns (sorted by student ID)
-  **`grading_summary.csv`** - Simple CSV summary
-  **`grading_summary.txt`** - Quick overview of all student scores
-  **`report_<student>.txt`** - Detailed test results per student

## Test Cases

### Part A: os1.sh Script Tests

| Test                | Description                                              |
| ------------------- | -------------------------------------------------------- |
| Directory creation  | Creates directory named by arg1                          |
| greeting.txt format | Creates greeting.txt with "Hey $USER! My name is <NAME>" |
| Compilation         | Compiles os1.c to os1exe with -Wall flag                 |
| ls -la output       | Lists files in directory from arg3                       |

### Part B: os1.c Shell Tests

| Test               | Description                                   |
| ------------------ | --------------------------------------------- |
| Shell prompt       | Uses correct `$$ ` prompt                     |
| `ls`               | Basic command execution                       |
| `ls -l`            | Command with arguments                        |
| `echo hello world` | Command with multiple arguments               |
| `sleep 1 %`        | Background process execution and PID printing |
| `pwd`              | Current directory command                     |
| `invalid_command`  | Handling of invalid commands                  |
| `cat os1.c`        | File display                                  |

## HW1-2026 Requirements

The student shell must implement:

-  **Prompt**: `$$ ` (dollar-dollar-space)
-  **Background character**: `%` (percent sign)
-  **Buffer size**: 2048 bytes
-  **Args array**: 200 elements (max 199 words)
-  **Source file**: `os1.c`
-  **Executable**: `os1`

## Troubleshooting

### "No os1.c files found"

-  Run the extraction script first: `python extract_submissions_from_zip.py`

### WSL not available

-  Install WSL: `wsl --install` (requires admin privileges)
-  Or use a Linux VM/machine to run the grading

### Compilation errors

-  Check if `gcc` is installed in WSL: `wsl -e gcc --version`
-  Install if needed: `wsl -e sudo apt install build-essential`

### Timeout errors

-  Default timeout is 5 seconds per test
-  Modify `TIMEOUT` variable in `test_script.py` if needed

## Configuration

Edit `test_script.py` to modify:

```python
TIMEOUT = 5              # Seconds per test
OUTPUT_DIR = "grading_results"
SUBMISSION_DIR = "submissions"
COMPILER = "gcc"
COMPILER_FLAGS = "-Wall"
```
