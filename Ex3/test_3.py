#!/usr/bin/env python3
from os3_grader import OS3Grader

grader = OS3Grader()

students = [
    r'submissions\דניאל הרשקו_50102_assignsubmission_file',
    r'submissions\דמיטרי קרייצרק_49992_assignsubmission_file',
    r'submissions\רותם עדימור_50107_assignsubmission_file'
]

for s in students:
    result = grader.grade_student(s)
    part_b = result['module_points'] + result['script_points'] + result['makefile_points']
    print(f"\n{result['name']}")
    print(f"  Part A: {result['queue_points']}/50")
    print(f"  Part B: {part_b}/50")
    print(f"  Total: {result['total']}/100")
    if result['errors']:
        print(f"  Errors:")
        for e in result['errors']:
            print(f"    - {e}")
