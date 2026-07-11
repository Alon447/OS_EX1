"""Combine Ex2 Part 1 (shell tests, grades.csv) and Part 2 (theory PDF,
part2_extracted_answers.csv) into a single final grades CSV.

Part 1: shell grader score (out of 100).
Part 2: theory deductions (Q1 wrong: -2, Q2 wrong: -3).
Final grade = Part 1 score - Part 2 deductions (min 0).

Message column format:
  part 1:
  <error description>
  <points deducted>

  part 2:
  <error description>
  <points deducted>
(sections only appear if there are mistakes in that part)
"""
import csv
import re
import os

PART1_CSV = 'grading_results/grades.csv'
PART2_CSV = 'grading_results/part2_extracted_answers.csv'
OUT = 'grading_results/final_grades.csv'

# Manual Part 2 overrides for students whose PDF could not be parsed automatically.
MANUAL_PART2 = {
    '108325': (False, False, 'Q1=277 (wrong), Q2=0 frames (wrong)'),
    '108344': (True,  False, 'Q1=278 (ok), Q2=513 (wrong)'),
    '108317': (True,  False, 'Q1=278 (ok), Q2=514 (wrong)'),
}
Q1_DEDUCTION = 2
Q2_DEDUCTION = 3


def student_id(folder):
    m = re.search(r'_(\d+)_assignsubmission_file', folder)
    return m.group(1) if m else folder


def student_display_name(folder):
    return folder.rsplit('_', 3)[0]


def build_part1_info(ra):
    """Return (grade, mistakes_str, deduction_str) for part 1."""
    if not ra:
        return 0, 'No submission found', '-100'
    if ra['Compiled'] == 'NO':
        return 0, 'Did not compile / no os2.c submitted', '-100'

    grade = float(ra['Total Points'])
    lost = 100 - grade
    if lost == 0:
        return grade, '', ''

    # Build per-test failure descriptions
    errors_raw = ra.get('Errors', '').strip()
    mistakes = []
    if errors_raw:
        for part in errors_raw.split(' | '):
            part = part.strip()
            if part:
                mistakes.append(part)
    return grade, '\n'.join(mistakes), f'-{lost:g}'


def build_part2_info(rb, sid):
    """Return (deduction, mistakes_str, deduction_str) for part 2."""
    # Manual override
    if sid in MANUAL_PART2:
        m_q1, m_q2, note = MANUAL_PART2[sid]
        ded = (0 if m_q1 else Q1_DEDUCTION) + (0 if m_q2 else Q2_DEDUCTION)
        mistakes = []
        if not m_q1:
            mistakes.append('Q1 wrong (correct answer: 278)')
        if not m_q2:
            mistakes.append('Q2 wrong (correct answer: 516)')
        return ded, '\n'.join(mistakes), f'-{ded}' if ded else ''

    if not rb or rb['PDF Found'] == 'No':
        return 0, '', ''  # no PDF - no deduction

    q1_correct = rb['Q1 Correct'] == 'Yes'
    q2_correct = rb['Q2 Correct'] == 'Yes'
    ded = 0
    mistakes = []
    if not q1_correct:
        ded += Q1_DEDUCTION
        mistakes.append('Q1 wrong (correct answer: 278)')
    if not q2_correct:
        ded += Q2_DEDUCTION
        mistakes.append('Q2 wrong (correct answer: 516)')
    return ded, '\n'.join(mistakes), f'-{ded}' if ded else ''


def build_message(p1_mistakes, p1_ded_str, p2_mistakes, p2_ded_str):
    """Build the student-facing message column."""
    parts = []
    if p1_mistakes:
        parts.append(f'part 1:\n{p1_mistakes}\n{p1_ded_str}')
    if p2_mistakes:
        parts.append(f'part 2:\n{p2_mistakes}\n{p2_ded_str}')
    return '\n\n'.join(parts)


def main():
    # Load Part 1 results
    a = {}
    with open(PART1_CSV, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            a[r['Student']] = r

    # Load Part 2 results
    b = {}
    with open(PART2_CSV, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            b[r['Student Name']] = r

    all_keys = sorted(set(a) | set(b))

    rows = []
    for k in all_keys:
        ra = a.get(k)
        rb = b.get(k)
        sid = student_id(k)
        name = student_display_name(k)

        p1_grade, p1_mistakes, p1_ded_str = build_part1_info(ra)
        p2_deduction, p2_mistakes, p2_ded_str = build_part2_info(rb, sid)

        p2_grade = 5 - p2_deduction  # part 2 is worth 5 points total (Q1=2, Q2=3)
        final = max(0, p1_grade - p2_deduction)

        message = build_message(p1_mistakes, p1_ded_str, p2_mistakes, p2_ded_str)

        rows.append({
            'Student ID': sid,
            'Name': name,
            'Part 1 Grade': f'{p1_grade:g}',
            'Part 1 Mistakes': p1_mistakes,
            'Part 1 Deduction': p1_ded_str if p1_ded_str else '0',
            'Part 2 Grade': f'{p2_grade:g}',
            'Part 2 Mistakes': p2_mistakes,
            'Part 2 Deduction': p2_ded_str if p2_ded_str else '0',
            'Final Grade': f'{final:g}',
            'Message': message,
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Summary
    finals = [float(r['Final Grade']) for r in rows]
    print(f'Wrote {OUT} with {len(rows)} students')
    print(f'Mean: {sum(finals)/len(finals):.1f}  |  Min: {min(finals):g}  Max: {max(finals):g}')
    p1_perfect = sum(1 for r in rows if float(r['Part 1 Grade']) == 100)
    p2_deducted = sum(1 for r in rows if r['Part 2 Deduction'] != '0')
    print(f'Part 1 perfect: {p1_perfect}/{len(rows)}')
    print(f'Part 2 deductions: {p2_deducted}/{len(rows)}')


if __name__ == '__main__':
    main()
