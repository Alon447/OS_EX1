# Exercise 3 - Queue & Kernel Module (HW3-2026)

Grading system for HW3. There are **two versions** of this assignment:

- **`HW3_2026.pdf` (two parts):** Queue (`os3q.c`, 50) + kernel module / script /
  Makefile (50). Grade with `--parts 2` (default).
- **`HW3_2026b.pdf` (one part):** the **queue only** (`os3q.c`), graded **out of 100**.
  No kernel module. Grade with `--parts 1`. **This is the `subs-26b` batch.**

The queue requirements are identical in both versions.

## What This Exercise Tests

**Part A — Thread-safe Queue (`os3q.c`)** — both versions

- Pointer-based linked-list queue (no arrays), value type `long`
- Bounded queue with a max size set at init
- Thread safety via mutex + condition variables (no semaphores / atomics)
- Operations: `init`, `destroy`, `enqueue`, `dequeue`, `size`, `sum`
- No static/global variables, no `main()`

**Part B — Kernel Module (`os3mod.c`) + Script + Makefile** — two-part version only

- Replaces one or more syscalls (`mkdir`, `chdir`, `close`, `dup`) via an `int` array param + a `text` string param
- Prints the message **after** running the original syscall
- Validates syscall numbers; restores on error; waits 4 seconds before cleanup
- `os3mod.sh` takes 3 arguments (copy → compile+load → clean)
- `Makefile` builds the kernel module

## Grading Scripts

### os3_grader.py — Automated grader

Regex/static analysis of the submitted files. Auto-extracts each student's tar.gz.

```bash
python os3_grader.py subs-26b --parts 1    # queue only, out of 100 (HW3_2026b)
python os3_grader.py submissions --parts 2 # two-part 50/50 (HW3_2026, default)
```

**Output:** `grading_results/os3_grades_<timestamp>.csv`

- `--parts 2`: Student, Part A: Queue (50), Part A Errors, Part B: Module+Script+Makefile (50), Part B Errors, Total
- `--parts 1`: Student, Queue (100), Queue Errors, Total

### combine_grades.py — Final grades

Transforms the latest `os3_grades_*.csv` into a final grades CSV in the same
format used by Ex2, with a per-student `Message` column. It auto-detects whether
the grader ran in one-part or two-part mode.

```bash
python combine_grades.py
```

**Output:** `grading_results/final_grades.csv`

- two-part: Student ID, Name, Part A Grade/Mistakes/Deduction, Part B Grade/Mistakes/Deduction, Final Grade, Message
- one-part: Student ID, Name, Part A Grade/Mistakes/Deduction, Final Grade, Message

## Folder Structure

- **subs-26b/** — Current (2026B) student submissions
- **submissions/** — 2025 student submissions (archived)
- **p_solution/** — Reference solution (`os3q.c`, `os3mod.c`)
- **2025_solution/** — Last year's graders (reference)
- **grading_results/** — All grading output CSVs
- **HW3_DIFFERENCES.md** — Detailed 2025 vs 2026 comparison
- **GRADER_VERIFICATION.md** — Grader checks mapped to spec requirements

## Quick Workflow

1. Extract submissions (run with UTF-8 so Hebrew names don't crash the printer):
   ```powershell
   $env:PYTHONIOENCODING='utf-8'; python ..\extract_submissions_from_zip.py subs-26b
   ```
2. Grade: `python os3_grader.py subs-26b --parts 1`  (subs-26b is the queue-only 2026b version)
3. Combine: `python combine_grades.py`
4. Review `grading_results/final_grades.csv`

## Grading Distribution

**Two-part version (`HW3_2026`, `--parts 2`):**

| Part      | Component                  | Points  |
| --------- | -------------------------- | ------- |
| **A**     | Queue (`os3q.c`)           | 50      |
| **B**     | Kernel module (`os3mod.c`) | 40      |
| **B**     | Script (`os3mod.sh`)       | 5       |
| **B**     | Makefile                   | 5       |
| **TOTAL** |                            | **100** |

**One-part version (`HW3_2026b`, `--parts 1`):** Queue (`os3q.c`) only = **100 points**.
The same queue deductions apply against a base of 100. Adding `main()` zeros the
whole grade (0/100).

## Submission Format

```bash
# two-part (HW3_2026)
tar czf <student_id>.tar.gz os3q.c os3mod.c Makefile os3mod.sh
# one-part (HW3_2026b)
tar czf <student_id>.tar.gz os3q.c
```

The filename is the 9-digit student ID. The archive contains exactly the required
files (no folders, no hidden files).

## Common Deduction Points

### Part A — Queue

- **Has `main()`: disqualifies the entire Part A (0/50)**
- Missing/broken `sum()` function: -8
- Uses static/global variables: -8
- Missing/wrong condition variables: -10
- Using `int` instead of `long`: -5
- `malloc()` inside critical section: -5
- `free()` before unlock: -5
- Lock used for a simple value read (`size`/`sum`): -3
- `destroy()` doesn't free remaining items: -5

### Part B — Module / Script / Makefile

- Missing GPL license: -4
- Not using array parameter (`module_param_array`): -8
- Message printed BEFORE syscall instead of after: -8
- Missing copy-from-user (`get_user`): -8
- Missing invalid-syscall validation: -8
- Missing restore-on-init-error: -8
- Wrong sleep time (not 4 seconds): -3
- Buffer size not 13 (12 chars + null): -3
- Missing `KERN_INFO`: -3
- Script doesn't handle 3 arguments: -3
- Script missing make/insmod: -2
- Makefile missing `obj-m`: -3

## Main Differences from 2025

See `HW3_DIFFERENCES.md`. Summary:

- **Part A:** `mylist.c` → `os3q.c`; linked list → **queue**; `int` → **`long`**; added **`sum()`**
- **Part B:** `mymod.c` → `os3mod.c`; single syscall → **multiple** (array param);
  message **before** → **after**; 3 sec → **4 sec** wait; 1 arg → **3 args** in script;
  15 → **12** char buffer (+null)

## Notes on the subs-26b Batch (2026B)

- This batch uses **`HW3_2026b.pdf` — the queue-only version**, graded out of 100.
  Grade it with `--parts 1`. (Do **not** penalize the missing kernel module: it isn't
  part of this version.)
- A handful of students also included `os3mod.c`/`Makefile`/`os3mod.sh` (from the
  two-part version); those extra files are ignored in one-part mode.
- `ירון מירולוז (124851)` submitted a **RAR** file misnamed `.tar.gz` — extract with
  UnRAR/WinRAR (contained only `os3q.c`).
- `יובל גבאי (124828)` submitted only a PDF; `יואב וינשטיין (124858)` submitted HW1
  files (`os1.*`) — both scored 0 (see `Message` notes in `final_grades.csv`).
