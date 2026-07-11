"""Transform the latest os3_grader.py output (os3_grades_<timestamp>.csv) into a
final grades CSV in the same format used by Ex2 (grading_results/final_grades.csv).

Ex3 has two parts (matching the two חלקים of HW3-2026):
  Part A: thread-safe Queue (os3q.c)                     - 50 points
  Part B: kernel module + script + Makefile              - 50 points
          (os3mod.c 40, os3mod.sh 5, Makefile 5)

Final grade = Part A + Part B.

Message column format (sections only appear if that part lost points):
  part A - Queue (50):
  <mistakes>
  <points deducted>

  part B - Module+Script+Makefile (50):
  <mistakes>
  <points deducted>
"""
import csv
import glob
import os
import re

RESULTS_DIR = 'grading_results'
OUT = os.path.join(RESULTS_DIR, 'final_grades.csv')

PART_A_MAX = 50
PART_B_MAX = 50

# Manual notes for submissions that need human-readable context.
# id -> note appended to the message (does not change the auto grade).
MANUAL_NOTES = {
    '124828': 'Submitted only HW3.pdf - no code files',
    '124858': 'Submitted HW1 files (os1.c/os1.sh/os1.pdf) - wrong assignment',
}


def latest_raw_csv():
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, 'os3_grades_*.csv')))
    if not files:
        raise SystemExit('No os3_grades_*.csv found. Run os3_grader.py first.')
    return files[-1]


def student_id(folder):
    m = re.search(r'_(\d+)_assignsubmission_file', folder)
    return m.group(1) if m else folder


def student_display_name(folder):
    return folder.rsplit('_', 3)[0]


def clean_part_a(errors_raw):
    """Return list of readable Part A mistake lines."""
    out = []
    for line in errors_raw.splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.replace('[Queue] ', '')
        if line == 'File not found':
            line = 'os3q.c not submitted'
        out.append(line)
    return out


def clean_part_b(errors_raw):
    """Return list of readable Part B mistake lines, collapsing the
    'all three files missing' case into a single clear note."""
    lines = [l.strip() for l in errors_raw.splitlines() if l.strip()]
    not_found = {
        '[Module] File not found',
        '[Script] File not found',
        '[Makefile] File not found',
    }
    if not_found.issubset(set(lines)):
        remaining = [l for l in lines if l not in not_found]
        out = ['Part B not submitted (os3mod.c, Makefile, os3mod.sh missing)']
        for line in remaining:
            out.append(_relabel_b(line))
        return out
    return [_relabel_b(l) for l in lines]


def _relabel_b(line):
    line = line.replace('[Module] ', 'Module: ')
    line = line.replace('[Script] ', 'Script: ')
    line = line.replace('[Makefile] ', 'Makefile: ')
    line = line.replace('File not found', 'file not submitted')
    return line


def build_message(a_mistakes, a_ded, b_mistakes, b_ded):
    parts = []
    if a_mistakes:
        parts.append(f'part A - Queue (50):\n' + '\n'.join(a_mistakes) + f'\n{a_ded}')
    if b_mistakes:
        parts.append(
            f'part B - Module+Script+Makefile (50):\n'
            + '\n'.join(b_mistakes) + f'\n{b_ded}'
        )
    return '\n\n'.join(parts)


def main():
    raw = latest_raw_csv()
    with open(raw, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    single_part = 'Queue (100)' in (fieldnames or [])
    if single_part:
        out_rows = _build_single_part(rows)
    else:
        out_rows = _build_two_part(rows)

    out_rows.sort(key=lambda x: x['Name'])

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(OUT, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    finals = [r['Final Grade'] for r in out_rows]
    mode = 'queue-only /100 (HW3_2026b)' if single_part else 'two-part 50/50 (HW3_2026)'
    print(f'Source: {raw}')
    print(f'Mode:   {mode}')
    print(f'Wrote {OUT} with {len(out_rows)} students')
    print(f'Mean: {sum(finals)/len(finals):.1f}  |  Min: {min(finals)}  Max: {max(finals)}')
    zeros = sum(1 for r in out_rows if r['Final Grade'] == 0)
    perfect = sum(1 for r in out_rows if r['Final Grade'] == 100)
    print(f'Perfect (100): {perfect}  |  Zero: {zeros}')


def _build_single_part(rows):
    """Queue-only assignment (HW3_2026b): queue graded out of 100."""
    out_rows = []
    for r in rows:
        folder = r['Student']
        sid = student_id(folder)
        name = student_display_name(folder)

        grade = int(float(r['Queue (100)']))
        lost = 100 - grade
        mistakes = clean_part_a(r.get('Queue Errors', ''))
        ded = f'-{lost:g}' if lost else '0'

        parts = []
        if mistakes:
            parts.append('Queue (100):\n' + '\n'.join(mistakes) + f'\n{ded}')
        message = '\n\n'.join(parts)

        note = MANUAL_NOTES.get(sid)
        if note:
            message = (message + '\n\n' if message else '') + f'note: {note}'

        out_rows.append({
            'Student ID': sid,
            'Name': name,
            'Part A Grade': grade,
            'Part A Mistakes': '\n'.join(mistakes),
            'Part A Deduction': ded,
            'Final Grade': grade,
            'Message': message,
        })
    return out_rows


def _build_two_part(rows):
    """Two-part assignment (HW3_2026): Part A (50) + Part B (50)."""
    out_rows = []
    for r in rows:
        folder = r['Student']
        sid = student_id(folder)
        name = student_display_name(folder)

        a_grade = int(float(r['Part A: Queue (50)']))
        b_grade = int(float(r['Part B: Module+Script+Makefile (50)']))

        a_lost = PART_A_MAX - a_grade
        b_lost = PART_B_MAX - b_grade

        a_mistakes = clean_part_a(r.get('Part A Errors', ''))
        b_mistakes = clean_part_b(r.get('Part B Errors', ''))

        a_ded = f'-{a_lost:g}' if a_lost else '0'
        b_ded = f'-{b_lost:g}' if b_lost else '0'

        message = build_message(
            a_mistakes, a_ded if a_lost else '',
            b_mistakes, b_ded if b_lost else '',
        )

        note = MANUAL_NOTES.get(sid)
        if note:
            message = (message + '\n\n' if message else '') + f'note: {note}'

        final = a_grade + b_grade

        out_rows.append({
            'Student ID': sid,
            'Name': name,
            'Part A Grade': a_grade,
            'Part A Mistakes': '\n'.join(a_mistakes),
            'Part A Deduction': a_ded,
            'Part B Grade': b_grade,
            'Part B Mistakes': '\n'.join(b_mistakes),
            'Part B Deduction': b_ded,
            'Final Grade': final,
            'Message': message,
        })
    return out_rows


if __name__ == '__main__':
    main()
