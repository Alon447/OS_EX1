# Exercise 2 - Advanced Shell (HW2)

Grading system for the advanced shell assignment with I/O redirection and pipes.

## What This Exercise Tests

- Shell prompt
- Basic commands (ls, pwd, echo)
- Input redirection (`<`)
- Output redirection (`>`)
- Single pipes (`|`)
- Double pipes (`|` `|`)

## Grading Scripts

### test_os2_part1.py — Shell tests (Part 1)

Compiles and tests shell functionality. Runs under WSL.

```bash
wsl python3 test_os2_part1.py           # all students
wsl python3 test_os2_part1.py --test    # first 10 only
```

**Output:** `grading_results/grades.csv`

### test_os2_part2.py — Theory PDF grading (Part 2)

Extracts answers from student PDFs and grades Q1/Q2. Runs on Windows.

```bash
python test_os2_part2.py
```

**Output:** `grading_results/part2_extracted_answers.csv`

### combine_grades.py — Final grades

Merges Part 1 and Part 2 results into a single CSV with per-student messages.

```bash
python combine_grades.py
```

**Output:** `grading_results/final_grades.csv`

## Folder Structure

- **subs-26b/** — Current (2026B) student submissions
- **submissions/** — 2025 student submissions (archived)
- **subs/** — Misc/test submissions
- **p_solution/** — Reference solution
- **grading_results/** — All grading output CSVs
- **part2_grading/** — Additional part 2 materials

## Quick Workflow

1. Extract submissions using root `extract_submissions_from_zip.py`
2. Run Part 1 tests: `wsl python3 test_os2_part1.py`
3. Run Part 2 grading: `python test_os2_part2.py`
4. Combine: `python combine_grades.py`
5. Review `grading_results/final_grades.csv`

6. **Compile (if needed):**

   ```bash
   gcc os2.c -o os2 -Wall
   ```

7. **Run the shell:**

   ```bash
   ./os2
   ```

8. **Test commands manually:**
   ```bash
   $$ ls
   $$ pwd
   $$ echo hello_world
   $$ cat {test.txt       # Input redirection
   $$ echo test }out.txt  # Output redirection
   $$ echo hello ! grep hello      # Single pipe
   $$ echo test ! grep t ! wc -w   # Double pipe
   $$ exit
   ```

---

## What the Tests Check

| Test                | Points  | Description                          |
| ------------------- | ------- | ------------------------------------ |
| **Shell Prompt**    | 5       | Shows `$$ ` before each command      |
| **ls**              | 5       | Lists files in directory             |
| **pwd**             | 5       | Shows current directory              |
| **echo**            | 5       | Prints text                          |
| **Input Redirect**  | 20      | `cat {filename` reads from file      |
| **Output Redirect** | 20      | `echo text }filename` writes to file |
| **Single Pipe**     | 20      | `cmd1 ! cmd2` pipes output           |
| **Double Pipe**     | 20      | `cmd1 ! cmd2 ! cmd3` chains pipes    |
| **TOTAL**           | **100** |                                      |

---

## Important Syntax Rules

- **Redirection:** `{filename` and `}filename` (no space after operator)
- **Pipe:** `!` (space before and after the `!`)
- **Example:** `echo hello }output.txt ! cat {output.txt`

---

## Common Student Issues

- Wrong redirection syntax (adding spaces after `{` or `}`)
- Double pipe not implemented
- Output redirection creates empty files
- Missing shell prompt

---

## HW2-2026 Requirements

The student shell must implement:

1. **Shell Prompt**: Display `$$$ ` before each command
2. **Command Execution**: Execute basic Linux commands with arguments
3. **Input Redirection (`{`)**: Redirect input from file using `{filename`
4. **Output Redirection (`}`)**: Redirect output to file using `}filename`
5. **Pipe (`!`)**: Support single and double pipes for command chaining
6. **Parallel Process Creation**: Pipe should create two child processes (not parent-child-grandchild)
7. **Combined Operations**: Support mixing pipes and redirections
