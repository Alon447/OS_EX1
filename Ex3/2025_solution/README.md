# Homework 3 Checker - Unified System

This unified system checks both Part A (mylist.c) and Part B (kernel module) of Homework 3.

## Files Overview

1. **hw_checker.py** - Part A checker (mylist.c implementation)
2. **kernel_checker.py** - Part B checker (kernel module implementation)
3. **unified_hw_checker.py** - Unified checker that combines both parts

## Usage

### Individual Checkers

#### Part A Only (mylist.c)

```bash
python hw_checker.py [folder_name]
```

#### Part B Only (kernel module)

```bash
python kernel_checker.py [folder_name]
```

### Unified Checker (Recommended)

```bash
python unified_hw_checker.py [folder_name]
```

If no folder is specified, it defaults to "submissions" in the current directory.

## Output

All checkers generate Excel reports with:

-  Detailed error descriptions in Hebrew and English
-  Point deductions for each issue
-  Summary statistics
-  Criteria explanations

### Unified Checker Output

The unified checker generates a comprehensive Excel file with:

-  **HW3 Complete Results**: Combined results for both parts
-  **Summary**: Statistics for both parts
-  **Part A Criteria**: Explanation of Part A deduction criteria
-  **Part B Criteria**: Explanation of Part B deduction criteria

## Folder Structure Expected

```
submissions/
├── student1/
│   ├── mylist.c (or tar.gz containing it)
│   ├── mymod.c
│   ├── Makefile
│   └── mymod.sh
├── student2/
│   └── ...
└── ...
```

## Dependencies

```bash
pip install pandas openpyxl
```

## Deduction Criteria

### Part A (mylist.c)

-  malloc() after pthread_mutex_lock() (-2 points)
-  Lock used for single size read (-1 point)
-  free() before pthread_mutex_unlock() (-2 points)
-  Items not freed in destroy (-2 points)
-  Contains main() function (-10 points)

### Part B (kernel module)

-  Missing required files (-5 points)
-  Missing includes (-4 points)
-  Missing GPL license (-3 points)
-  Missing init/cleanup functions (-3 points)
-  Missing parameters (-3 points each)
-  Missing function pointers (-5 points)
-  Missing syscall validation (-8 points)
-  Missing error handling (-5 points)
-  Missing syscall table manipulation (-7 points)
-  Missing user memory copying (-5 points)
-  Missing KERN_INFO (-3 points)
-  Wrong buffer size (-2 points)
-  Missing string termination (-2 points)
-  Missing 3 second sleep (-3 points)
-  Makefile issues (-5 points each)
-  Script issues (-2 to -5 points each)

## Features

-  **Automated Processing**: Handles tar.gz extraction automatically
-  **Flexible File Detection**: Finds required files in subdirectories
-  **Comprehensive Error Reporting**: Detailed explanations in Hebrew and English
-  **Excel Export**: Professional reports with multiple sheets
-  **Summary Statistics**: Class performance overview
-  **Error Categorization**: Major vs minor issues
-  **Point Deduction System**: Consistent scoring across all criteria
