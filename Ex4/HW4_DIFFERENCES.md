# HW4 Differences: 2026 vs 2025

## Summary of Changes

This document outlines the key differences between HW4_2026 and HW4_2025 for Part A (Kernel Module).

---

## Part A - Kernel Module Changes

### 1. File Names

| Item               | HW4_2025        | HW4_2026       |
| ------------------ | --------------- | -------------- |
| Main C file        | `encdev.c`      | `os4mod.c`     |
| Header file        | `encdev.h`      | `os4mod.h`     |
| Shell script       | `encdev.sh`     | `os4mod.sh`    |
| PDF answers        | `myanswers.pdf` | `os4.pdf`      |
| Submission checker | `checksub.py`   | `checksub4.py` |

### 2. Encryption Method

| Aspect               | HW4_2025                    | HW4_2026               |
| -------------------- | --------------------------- | ---------------------- |
| Cipher type          | **Caesar cipher**           | **XOR cipher**         |
| Write operation      | Add key to each byte        | XOR each byte with key |
| Read operation       | Subtract key from each byte | XOR each byte with key |
| Description (Hebrew) | צופן קיסר                   | צופן XOR               |

### 3. Initial Encryption Key

| Item              | HW4_2025 | HW4_2026 |
| ----------------- | -------- | -------- |
| Initial key value | **0**    | **0xFF** |

### 4. IOCTL Command

| Item         | HW4_2025        | HW4_2026        |
| ------------ | --------------- | --------------- |
| Command name | `IOCTL_SET_KEY` | `IOCTL_XOR_KEY` |

### 5. Shell Script

| Aspect         | HW4_2025                         | HW4_2026                                 |
| -------------- | -------------------------------- | ---------------------------------------- |
| Arguments      | 1 (target folder only)           | 3 (folder, size, count)                  |
| Size/Count     | Hardcoded: `size=1024, count=10` | From arguments 2 and 3                   |
| Example        | (not shown)                      | `sudo ./os4mod.sh ~/kmod 4 1024 10`      |
| Load condition | (not specified)                  | Only load module if compilation succeeds |

### 6. Tar Submission Command

**2025:**

```bash
tar czf <yourid>.tar.gz encdev.c encdev.h Makefile encdev.sh myanswers.pdf
```

**2026:**

```bash
tar czf <yourid>.tar.gz os4mod.c os4mod.h Makefile os4mod.sh os4.pdf
```

---

## Part B - Disk Questions

### Question 2 (Minor wording change)

| HW4_2025                         | HW4_2026                                       |
| -------------------------------- | ---------------------------------------------- |
| "שתי רצועות באותו משטח"          | "שתי רצועות **שונות** באותו משטח"              |
| (Two tracks on the same surface) | (Two **different** tracks on the same surface) |

Also in 2026 step b:

- 2026 specifies "העברת **מידע בלבד**" (data transfer **only**) more explicitly

---

## Additional Notes for Grading

### New Checks for 2026

1. **Wrong initial key**: Students should initialize key to 0xFF, not 0
2. **Wrong encryption method**: Should use XOR (^), not addition/subtraction
3. **Wrong IOCTL command**: Should use IOCTL_XOR_KEY, not IOCTL_SET_KEY

### Unchanged Requirements

- Memory cleanup (kfree for every kmalloc)
- unregister_chrdev in cleanup_module
- Parameter validation (size, count)
- Minor number validation
- register_chrdev error checking
- All required functions (open, release, read, write, ioctl, llseek)
- Proper function names (init_module, cleanup_module)
- Memory allocation error handling

---

## Checker Files

- **2025 checker**: `2025_solution/hw4_checker.py` - checks for `encdev.c`
- **2026 checker**: `hw4_2026_checker.py` - checks for `os4mod.c` with XOR-specific validations

Run the 2026 checker:

```bash
python hw4_2026_checker.py submissions
```
