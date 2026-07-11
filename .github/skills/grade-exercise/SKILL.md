---
name: grade-exercise
description: 'Run the full grading pipeline for an OS course exercise (Ex1-Ex4): extract submissions, run the correct grader under WSL or Windows Python, and verify CSV output. Use when asked to grade, re-grade, score, or run the grader for an exercise, or to process a new submission batch.'
argument-hint: 'Exercise number (Ex1-Ex4) and optional submissions folder'
---

# Grade an Exercise

End-to-end grading for a single OS course exercise. Each exercise has a different
grader script and runtime (WSL vs Windows Python) — this skill picks the right one.

## When to Use

- "Grade Ex3" / "re-grade Ex1" / "score the new batch for Ex4"
- A new Moodle archive was dropped into an exercise's `submissions/` folder
- You need to run a grader and confirm the CSV was produced

## Per-Exercise Reference

| Exercise  | Grader command                           | Runtime                      | Output                                           |
| --------- | ---------------------------------------- | ---------------------------- | ------------------------------------------------ |
| Ex1       | `wsl python3 test_script.py`             | WSL (compiles C)             | `grading_results/grading_summary[_detailed].csv` |
| Ex2 part1 | `wsl python3 test_os2_part1.py`          | WSL (compiles C)             | `grading_results/grades.csv`                     |
| Ex2 part2 | `python test_os2_part2.py`               | Windows Python (PDF)         | `part2_extracted_answers.csv`                    |
| Ex3       | `python os3_grader.py submissions`       | Windows Python (regex)       | `os3_grades_<timestamp>.csv`                     |
| Ex4       | `python hw4_2026_checker.py submissions` | Windows Python (regex + PDF) | `hw4_grades_<timestamp>.csv`                     |

Run all commands from inside the exercise folder (`cd ExN` first). Graders accept the
submissions folder name as an optional argument (default `submissions`).

## Procedure

1. **Confirm inputs.** Identify the exercise (`Ex1`–`Ex4`) and which submissions
   folder to grade (default `submissions`; alternatives: `subs/`, `subs-26b/`, `subs-2026B/`).
2. **Extract if needed.** If the folder still contains `.zip`/`.tar.gz` archives, run
   from the repo root: `python extract_submissions_from_zip.py ExN/<folder>`.
   Never modify files already inside `submissions/`.
3. **Activate venv** for Windows-side scripts (Ex2 part2, Ex3, Ex4):
   `& .venv\Scripts\Activate.ps1`.
4. **Run the grader** from the table above (`cd ExN` first). Use WSL for Ex1 and
   Ex2 part1. Allow time for compilation; graders use ~5s per-student timeouts.
5. **Verify output.** Confirm the expected CSV exists in `grading_results/` (Ex1/Ex2)
   or as a new timestamped file (Ex3/Ex4). Do NOT overwrite or delete prior
   timestamped CSVs.
6. **Summarize.** Report counts: graded, compile failures, errors, and the output path.

## Safety

- Treat student names/IDs as sensitive — never post externally.
- Write only to `grading_results/`; `submissions/` is read-only input.
- If a grader crashes, capture the error and fix the grader script — never edit a
  student submission to make it pass.
