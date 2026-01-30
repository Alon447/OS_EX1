# OS Exercise 3 Grading System - Setup Complete

## What Was Created

### Main Grading Script: `os3_grader.py`

- **All-in-one** automated grader for Exercise 3 (2026)
- Checks all 4 parts: Queue (50), Module (40), Script (5), Makefile (5)
- Generates Excel report with detailed errors
- Simple and focused on key issues

### Documentation

- **README.md** - Quick start guide and grading criteria
- **HW3_DIFFERENCES.md** - Detailed comparison of 2025 vs 2026
- **p_solution/** - Reference implementations (from professor)

## How to Use

### 1. Extract Submissions

```bash
cd c:\Users\alon4\Projects\OS
python extract_submissions_from_zip.py Ex3/submissions
```

### 2. Run Grading

```bash
cd Ex3
python os3_grader.py submissions
```

### 3. Check Results

- Opens Excel file `os3_grades_YYYYMMDD_HHMMSS.xlsx`
- Columns: Student | Queue (50) | Module (40) | Script (5) | Makefile (5) | Total | Errors

## Grading Breakdown (per Professor)

- **50 points:** Queue implementation (os3q.c)
- **40 points:** Kernel module (os3mod.c)
- **5 points:** Script (os3mod.sh)
- **5 points:** Makefile

## Key Changes from 2025

### Part A

- File: `mylist.c` → `os3q.c`
- Type: Linked list → Queue
- Data type: `int` → `long`
- New function: `sum()` (returns sum of all queue elements)

### Part B

- File: `mymod.c` → `os3mod.c`
- Parameters: Single syscall → Array of syscalls
- Message timing: BEFORE → AFTER syscall execution
- Wait time: 3 seconds → 4 seconds
- Script args: 1 → 3 arguments
- Buffer size: 15 → 12 characters (+null = 13)

## Major Deductions (Auto-Check)

### Part A - Queue (50 pts)

- Has main() → -50 (auto-fail this part)
- Missing/broken sum() → -8
- Using int instead of long → -5
- malloc/free in critical section → -5 each
- Static/global variables → -8
- Missing condition variables → -10

### Part B - Module (40 pts)

- No array parameter → -8
- Message BEFORE syscall → -8
- No invalid syscall check → -8
- No GPL license → -4
- Wrong sleep time → -3

### Part C - Script (5 pts)

- Wrong number of args → -3
- Missing make/insmod → -2

### Part D - Makefile (5 pts)

- Missing obj-m → -3
- Missing clean → -2

## Important Note from Professor

> "בחלק הראשון (התור), כדי להריץ את הקוד צריך לעשות include לקובץ C שהם מגישים"
>
> For Part A (queue), to run/test the code you need to `#include` the student's C file (not just the .h) because the struct definition is in the .c file.

## Files Reference

```
Ex3/
├── os3_grader.py          ← Main grading script (NEW)
├── README.md              ← Quick guide
├── HW3_DIFFERENCES.md     ← Detailed 2025 vs 2026 comparison
├── p_solution/
│   ├── os3q.c            ← Reference queue implementation
│   └── os3mod.c          ← Reference kernel module
├── 2025_solution/         ← Last year's scripts (reference)
└── submissions/           ← Student submissions
```

## Next Steps

1. **Test the grader**: Run on a few submissions to verify
2. **Adjust deductions**: Modify point values in `os3_grader.py` if needed
3. **Manual review**: Check edge cases that automated grader might miss
4. **Final grading**: Run on all submissions and review Excel output

## Script Simplicity

The grader is intentionally simple:

- No complex pattern matching
- Focused on critical errors only
- Easy to modify point values
- Clear error messages
- Single Excel output for review

## Customization

To adjust deductions, edit the dictionaries at the top of `os3_grader.py`:

- `queue_criteria` - Part A deductions
- `module_criteria` - Part B deductions
- `script_criteria` - Part C deductions
- `makefile_criteria` - Part D deductions

Each entry: `'key': ('description', points, 'severity')`
