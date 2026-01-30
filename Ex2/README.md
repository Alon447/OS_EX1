# Exercise 2 - Advanced Shell (HW2)

Grading system for the advanced shell assignment with I/O redirection and pipes.

## What This Exercise Tests

- Shell prompt
- Basic commands (ls, pwd, echo)
- Input redirection (`<`)
- Output redirection (`>`)
- Single pipes (`|`)
- Double pipes (`|` `|`)

## Files

### test_os2.py

Main grading script that tests shell functionality and generates grades.

**Usage:**

```bash
# Test all students
wsl python3 test_os2.py

# Test first 10 only
wsl python3 test_os2.py --test
```

**Results:** `grading_results/grades.csv`

### extract_part2_answers.py

Extracts answers from student PDF submissions for theoretical questions. Automatically grades questions 1 and 2, generates CSV with results and feedback.

**Usage:**

```bash
python extract_part2_answers.py
```

**Output:** `part2_extracted_answers.csv`

## Folder Structure

- **submissions/** - Student submission folders
- **p_solution/** - Reference solution
- **grading_results/** - Test results from `test_os2.py`
- **part2_grading/** - Additional grading materials

## Quick Workflow

1. Extract submissions using root `extract_submissions_from_zip.py`
2. Run automated tests: `wsl python3 test_os2.py`
3. Extract PDF answers: `python extract_part2_answers.py`
4. Check results in CSV files

5. **Compile (if needed):**

   ```bash
   gcc os2.c -o os2 -Wall
   ```

6. **Run the shell:**

   ```bash
   ./os2
   ```

7. **Test commands manually:**
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
