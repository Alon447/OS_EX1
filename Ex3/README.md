# Exercise 3 - Queue & Kernel Module (HW3-2026)

Simplified grading system for OS Exercise 3.

## Grading Distribution

- **50 points:** Queue implementation (os3q.c)
- **40 points:** Kernel module (os3mod.c)
- **5 points:** Script (os3mod.sh)
- **5 points:** Makefile
- **Total: 100 points**

## Quick Start

### 1. Extract All Submissions

```bash
python ../extract_submissions_from_zip.py submissions
```

### 2. Run Automated Grading

```bash
python os3_grader.py submissions
```

Generates Excel file with all grades and detected issues.

## What's Tested

**Part A:** Thread-safe Queue (`os3q.c`) - 50 pts

- Queue with pointer-based linked list
- Thread safety (mutex + condition variables)
- Operations: enqueue, dequeue, size, **sum**
- Data type: `long` (not int!)
- No static/global variables

**Part B:** Kernel Module (`os3mod.c`) - 40 pts

- Replace **multiple** syscalls (array parameter)
- Message printed **AFTER** syscall
- 4-second wait before cleanup

**Part C:** Script (`os3mod.sh`) - 5 pts

- Handles 3 arguments
- Copies files, compiles, loads module

**Part D:** Makefile - 5 pts

- Proper kernel module targets

## Main Differences from 2025

**Part A:** `mylist.c` → `os3q.c`

- Linked list → **Queue**
- `int` → **`long`**
- Added **`sum()`** function

**Part B:** `mymod.c` → `os3mod.c`

- Single syscall → **Multiple** (array param)
- Message **BEFORE** → **AFTER**
- 3 sec → **4 sec** wait
- 1 arg → **3 args** in script
- 15 char → **12 char** buffer (+null)

## Automated Grader: os3_grader.py

Single script checks all 4 parts, outputs Excel with grades.

**Major Deductions:**

- Part A: main() function (-50), missing sum (-8), static/global vars (-8)
- Part B: no array param (-8), msg before syscall (-8), no validation (-8)
- Part C: wrong args (-3), no make/insmod (-2)
- Part D: no obj-m (-3)

## Files

## Files

- **os3_grader.py** - **USE THIS** - All-in-one automated grader for all 4 parts
- **p_solution/** - Reference implementation
- **2025_solution/** - Last year's scripts (reference)
- **HW3_DIFFERENCES.md** - Detailed 2025 vs 2026 comparison
- ~~queue_checker.py~~ - Old partial checker (use os3_grader.py instead)

## Important Notes

⚠️ **From Professor:** To compile Part A for testing, you must `#include` the student's os3q.c file (struct definition is in .c, not .h).

## Folder Structure

- **submissions/** - Student submissions
- **p_solution/** - Reference solutions (os3q.c, os3mod.c)
- **2025_solution/** - Previous year's graders

## Submission Format

```bash
tar czf <student_id>.tar.gz os3q.c os3mod.c Makefile os3mod.sh
```

## Quick Workflow

1. Extract: `python ../extract_submissions_from_zip.py submissions`
2. Grade: `python os3_grader.py submissions`
3. Check Excel output

## Common Deduction Points

### Part A

- Has main() function: **-100 points** (auto-fail)
- malloc() after lock: -2 points
- Lock for single value read: -1 point
- free() before unlock: -2 points
- Items not freed in destroy: -2 points
- Missing/wrong sum() function: -5 points
- Using int instead of long: -2 points
- Static/global variables: -5 points

### Part B

- Missing required files: -4 points
- Missing GPL license: -3 points
- Invalid syscall handling: -4 points
- Wrong sleep time (not 4 seconds): -2 points
- Buffer size not 13 (12+null): -1 point
- Missing KERN_INFO: -1 point per occurrence
- Message printed BEFORE instead of AFTER: major deduction
