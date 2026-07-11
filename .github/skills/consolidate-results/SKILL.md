---
name: consolidate-results
description: 'Merge multiple timestamped grading CSVs (Ex3 os3_grades_*, Ex4 hw4_grades_*) into a single per-student summary, tracking score changes across re-grade runs. Use when asked to consolidate, merge, combine runs, compare grading runs, track regrades, or build a final grades sheet.'
argument-hint: 'Exercise number (Ex3 or Ex4) or a grading_results folder'
---

# Consolidate Grading Results

Ex3 and Ex4 write a new timestamped CSV every run, so re-grades accumulate. This skill
merges them into one authoritative per-student sheet and shows how scores changed.

## When to Use

- "Consolidate the Ex3 grading runs into one sheet"
- "Compare the latest two grading runs / track regrade changes"
- "Build the final grades CSV for Ex4"

## Input

The timestamped CSVs in `ExN/grading_results/`:
`os3_grades_YYYYMMDD_HHMMSS.csv` (Ex3) or `hw4_grades_YYYYMMDD_HHMMSS.csv` (Ex4).
The numeric **Student ID** (from the submission folder name) is the join key.

## Procedure

1. **Collect runs.** List the timestamped CSVs and parse the timestamp from each
   filename to order them oldest → newest.
2. **Load with pandas** (activate `.venv` first). Extract the Student ID key from each
   row consistently across runs.
3. **Determine final grade.** By default take each student's score from the **newest**
   run in which they appear (latest regrade wins). Note students missing from the
   newest run.
4. **Track changes.** Compare the two most recent runs and flag students whose total
   changed, with old → new score and the delta.
5. **Build the consolidated sheet** with columns: Student ID, Name, final total,
   per-part scores, source run timestamp, and a "changed since previous run" flag.
6. **Write output** to `ExN/grading_results/consolidated_<exercise>_<timestamp>.csv`.
   Do NOT overwrite or delete the original timestamped run files — only add a new
   consolidated file. Confirm the path and report a short change summary in chat.

## Safety

- Never delete prior timestamped CSVs (course audit trail) without explicit confirmation.
- Read the source CSVs only; submissions remain untouched.
- Treat names/IDs as sensitive.
