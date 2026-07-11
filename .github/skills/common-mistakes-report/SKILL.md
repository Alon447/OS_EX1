---
name: common-mistakes-report
description: 'Analyze a grading-results CSV for an OS exercise and produce a ranked summary of the most frequent student mistakes and error messages. Use when asked for common mistakes, error trends, a class-wide summary, point-loss breakdown, or "what did most students get wrong".'
argument-hint: 'Exercise number and/or path to a grading_results CSV'
---

# Common Mistakes Report

Turn a grader's per-student CSV into a class-level view of the most common errors,
so the lecturer can spot systemic misunderstandings and adjust teaching.

## When to Use

- "What did most students get wrong in Ex3?"
- "Summarize the common errors / point losses for this batch"
- "Which test failed the most often?"

## Input

A grading CSV in `ExN/grading_results/` (Ex1/Ex2) or a timestamped
`os3_grades_*.csv` / `hw4_grades_*.csv` (Ex3/Ex4). Each row is one student; error
columns hold free-text messages (e.g. "missing mutex", "wrong buffer size",
"compilation failed"). When several timestamped files exist, use the newest unless
told otherwise.

## Procedure

1. **Locate the CSV.** If not given, list `ExN/grading_results/` and pick the latest
   relevant file.
2. **Load with pandas** (activate `.venv` first). Identify the error/feedback columns
   and the per-part score columns.
3. **Aggregate errors.** Split multi-error cells, normalize whitespace/casing, and
   count frequency of each distinct error message across all students.
4. **Aggregate point loss.** For each scored part, count how many students lost points
   and the average points lost — this ranks impact, not just frequency.
5. **Produce the report** with:
   - Total students, count graded, count with compile failures.
   - Top 10 most frequent error messages (message + count + % of class).
   - Per-part point-loss table (part, students affected, avg points lost).
   - A short "likely root causes" note tying errors to the exercise's known pitfalls
     (see `ExN/README.md` and `ExN/HW*_DIFFERENCES.md`).
6. **Output** as a Markdown summary in chat. Only write a file if explicitly asked;
   if so, write to `ExN/grading_results/` and never overwrite a grades CSV.

## Safety

- Aggregate by error type, not by student name. Do not list individual students unless
  asked; treat names/IDs as sensitive.
- Read-only: never modify the source grades CSV or any submission.
