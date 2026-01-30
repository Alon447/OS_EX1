# Exercise 1 - Basic Shell (HW1)

Grading system for the basic shell assignment.

## What This Exercise Tests

**Part A:** Shell script (`os1.sh`) functionality

- Directory creation
- File creation with proper formatting
- C code compilation

**Part B:** Custom shell (`os1.c`) implementation

- Shell prompt (`$$ `)
- Basic command execution
- Background processes
- Invalid command handling

## Files

### test_script.py

Main grading script that:

- Compiles student C code
- Runs automated tests on both `os1.sh` and `os1.c`
- Generates detailed grading reports

**Usage:**

```bash
wsl python3 test_script.py
```

## Folder Structure

- **submissions/** - Student submission folders (extracted)
- **p_solution/** - Reference solution files
- **grading_results/** - Generated after running tests
   - `grading_summary.csv` - All student grades
   - `report_<student>.txt` - Individual test results

## Quick Workflow

1. Extract submissions using root `extract_submissions_from_zip.py`
2. Run `wsl python3 test_script.py`
3. Check `grading_results/` folder for results
