# Operating Systems Course — Grading System

Automated grading tools for OS course homework. Each exercise (`Ex1`–`Ex4`) is graded
by a Python script that compiles/scans student submissions and produces CSV reports.

## Environment

- **OS:** Windows with **WSL**. C compilation and shell tests must run under WSL
  (`wsl python3 <script>`). Source-only/regex graders (Ex3, Ex4) and PDF/extraction
  utilities run on Windows Python (`python <script>`).
- **Python venv:** `.venv` at repo root. Activate before running Windows-side scripts.
- Dependencies used by graders: `PyMuPDF`/`PyPDF2` (PDF text), `pandas` (CSV reports).

## Repository Structure

Each `ExN/` folder follows the same layout:

- `submissions/` — extracted student folders (grader input)
- `grading_results/` — generated CSV reports (grader output)
- `p_solution/` — professor reference solution
- `2025_solution/` — previous-year solution, for comparison/debugging
- `subs/`, `subs-26b/`, `subs-2026B/` — alternative submission batches
- `README.md` — per-exercise point breakdown and workflow

Root utilities:

- `extract_submissions_from_zip.py` — extracts/flattens Moodle `.zip`/`.tar.gz` archives
- `extract_pdf.py`, `extract_*_pdfs.py` — PDF text extraction helpers

## Grader Scripts (per exercise)

| Exercise | Script                                   | Run with                                             | Method                              | Output                                                      |
| -------- | ---------------------------------------- | ---------------------------------------------------- | ----------------------------------- | ----------------------------------------------------------- |
| Ex1      | `test_script.py`                         | `wsl python3 test_script.py`                         | compile + run 12 shell/binary tests | `grading_results/grading_summary[_detailed].csv`            |
| Ex2      | `test_os2_part1.py`, `test_os2_part2.py` | `wsl python3 ...` (part1) / `python ...` (part2 PDF) | shell interaction + PDF parse       | `grading_results/grades.csv`, `part2_extracted_answers.csv` |
| Ex3      | `os3_grader.py`                          | `python os3_grader.py submissions`                   | regex scan of source                | `os3_grades_<timestamp>.csv`                                |
| Ex4      | `hw4_2026_checker.py`                    | `python hw4_2026_checker.py [folder]`                | regex scan + PDF parse              | `hw4_grades_<timestamp>.csv`                                |

Graders accept the submissions folder as an argument (default `submissions`).
All use subprocess calls with a ~5s timeout and per-student error capture.

## Conventions

- **Submission folder names:** `<Hebrew Name>_<Student ID>_assignsubmission_file/`.
  Preserve Hebrew names exactly; never rename. The numeric `<Student ID>` is the key.
- **Expected source filenames** differ per year/exercise — check the exercise README
  (e.g. Ex1 `os1.c`/`os1.sh`, Ex3 `os3q.c`/`os3mod.c`/`os3mod.sh`, Ex4 `os4mod.c`/`os4.pdf`).
- **Timestamped CSVs (Ex3/Ex4)** accumulate one file per run — do NOT overwrite or
  delete prior runs unless asked. Ex1/Ex2 overwrite their single CSV.
- Year differences are documented in `Ex3/HW3_DIFFERENCES.md` and `Ex4/HW4_DIFFERENCES.md`.

## Grading Workflow

1. Place Moodle archive(s) under `ExN/submissions/`.
2. Extract: `python extract_submissions_from_zip.py ExN/submissions`.
3. Grade: run the exercise's grader (see table; WSL for Ex1/Ex2 part1).
4. Review CSV in `ExN/grading_results/`.

## Safety

- This repo contains **real student submissions**. Treat names/IDs as sensitive; do not
  exfiltrate or post them externally.
- Never modify files inside `submissions/` — they are graded input. Write only to
  `grading_results/`.
- Do not delete prior timestamped result CSVs without explicit confirmation.
