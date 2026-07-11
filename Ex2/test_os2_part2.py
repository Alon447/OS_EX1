import os
import sys
import re
from collections import Counter
try:
    import PyPDF2
except ImportError:
    print("PyPDF2 is not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2
import csv

# Fix encoding for Windows terminal
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Correct answers
CORRECT_Q1 = 278  # Part a
CORRECT_Q2 = 516  # Part b

# Common answers to track
COMMON_Q1_ANSWERS = [274, 275, 276, 277, 278, 279, 280, 281, 282]
COMMON_Q2_ANSWERS = [512, 513, 514, 515, 516, 517, 518]

# Points deduction
Q1_DEDUCTION = 2
Q2_DEDUCTION = 3

# Feedback messages (Hebrew)
Q1_FEEDBACK = "סעיף 1:\nמספר הכניסות אמור להיות 278"
Q2_FEEDBACK = """סעיף 2:
במקרה המקסימלי, 1MB הם 513 דפים, המיפויים של 513 דפים מתפזרים על פני 2 טבלאות ברמה התחתונה.
ברמה האמצעית יש רק 2 טבלאות ואחת מהן כבר בשימוש, כך שבמקרה המקסימלי נוסיף רק עוד טבלה
אחת ברמה האמצעית. 
ברמה העליונה יש טבלה יחידה שבהכרח קיימת כבר.
נקבל סה""כ 516 מסגרות (513 מההקצאה ו3- של טבלת הדפים).

"

התשובה הנכונה: 516"""

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return None

def check_for_specific_answers(text, q1_answers_to_track, q2_answers_to_track):
    """
    Check if the text contains any of the specific answers.
    Returns tuple: (q1_found_answer, q2_found_answer, q1_is_correct, q2_is_correct)
    """
    if text is None:
        return None, None, False, False
    
    # Find all numbers in the text.
    # NOTE: a simple \b\d+\b fails on Hebrew-glued numbers like "נקבל516" or
    # "הוא278" because Hebrew letters are \w in Python, so there is no word
    # boundary between the letter and the digit and the number is dropped.
    # Use digit-only lookarounds so numbers are extracted regardless of any
    # adjacent (Hebrew/Latin) letters. Strip thousands separators first.
    cleaned = re.sub(r'(?<=\d),(?=\d{3}\b)', '', text)
    numbers = [int(n) for n in re.findall(r'(?<!\d)\d+(?!\d)', cleaned)]
    
    # Check if correct answers appear anywhere in the text
    q1_is_correct = CORRECT_Q1 in numbers
    q2_is_correct = CORRECT_Q2 in numbers
    
    # Find which answer to report (prefer correct answer if found)
    q1_found = None
    q2_found = None
    
    if q1_is_correct:
        q1_found = CORRECT_Q1
    else:
        # Find any tracked answer
        for num in numbers:
            if num in q1_answers_to_track:
                q1_found = num
                break
    
    if q2_is_correct:
        q2_found = CORRECT_Q2
    else:
        # Find any tracked answer
        for num in numbers:
            if num in q2_answers_to_track:
                q2_found = num
                break
    
    return q1_found, q2_found, q1_is_correct, q2_is_correct

def analyze_student_pdfs(submissions_folder):
    """Analyze all student PDFs in the submissions folder."""
    results = []
    q1_answers = []
    q2_answers = []
    
    # Get all student folders
    student_folders = [f for f in os.listdir(submissions_folder) 
                      if os.path.isdir(os.path.join(submissions_folder, f))]
    
    print(f"Found {len(student_folders)} student submissions")
    
    for student_name in sorted(student_folders):
        student_path = os.path.join(submissions_folder, student_name)
        
        # Look for PDF files (skip macOS '._' AppleDouble metadata files,
        # which are not real PDFs and fail to parse)
        pdf_files = [f for f in os.listdir(student_path)
                     if f.endswith('.pdf') and not f.startswith('._')]
        
        if not pdf_files:
            results.append({
                'student': student_name,
                'pdf_found': False,
                'q1_correct': False,
                'q1_answer': None,
                'q2_correct': False,
                'q2_answer': None,
                'both_correct': False,
                'points_deducted': 0,
                'comments': ''
            })
            continue
        
        # Use the first PDF file found
        pdf_path = os.path.join(student_path, pdf_files[0])
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        
        # Check for answers
        q1_answer, q2_answer, q1_correct, q2_correct = check_for_specific_answers(
            text, COMMON_Q1_ANSWERS, COMMON_Q2_ANSWERS
        )
        
        # Track answers for distribution
        if q1_answer is not None:
            q1_answers.append(q1_answer)
        if q2_answer is not None:
            q2_answers.append(q2_answer)
        
        # Calculate points deducted
        points_deducted = 0
        if not q1_correct and q1_answer is not None:
            points_deducted += Q1_DEDUCTION
        if not q2_correct and q2_answer is not None:
            points_deducted += Q2_DEDUCTION
        
        # Build comments
        comments = []
        if not q1_correct and q1_answer is not None:
            comments.append(Q1_FEEDBACK)
        if not q2_correct and q2_answer is not None:
            comments.append(Q2_FEEDBACK)
        
        comment_text = '\n\n'.join(comments)
        
        results.append({
            'student': student_name,
            'pdf_found': True,
            'q1_correct': q1_correct,
            'q1_answer': q1_answer,
            'q2_correct': q2_correct,
            'q2_answer': q2_answer,
            'both_correct': q1_correct and q2_correct,
            'points_deducted': points_deducted,
            'comments': comment_text
        })
    
    # Print distribution of answers
    print("\n=== Answer Distribution ===")
    print("\nQ1 (Part a) Answers:")
    q1_counter = Counter(q1_answers)
    for answer, count in q1_counter.most_common():
        marker = " ✓ CORRECT" if answer == CORRECT_Q1 else ""
        print(f"  {answer}: {count} students{marker}")
    
    print("\nQ2 (Part b) Answers:")
    q2_counter = Counter(q2_answers)
    for answer, count in q2_counter.most_common():
        marker = " ✓ CORRECT" if answer == CORRECT_Q2 else ""
        print(f"  {answer}: {count} students{marker}")
    
    return results

def save_results_to_csv(results, output_file):
    """Save results to CSV file."""
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['Student Name', 'PDF Found', 'Q1 Correct', 'Q1 Answer Found', 
                     'Q2 Correct', 'Q2 Answer Found', 'Both Correct', 'Points Deducted', 'Comments']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow({
                'Student Name': result['student'],
                'PDF Found': 'Yes' if result['pdf_found'] else 'No',
                'Q1 Correct': 'Yes' if result['q1_correct'] else 'No',
                'Q1 Answer Found': result['q1_answer'] if result['q1_answer'] is not None else 'Not found',
                'Q2 Correct': 'Yes' if result['q2_correct'] else 'No',
                'Q2 Answer Found': result['q2_answer'] if result['q2_answer'] is not None else 'Not found',
                'Both Correct': 'Yes' if result['both_correct'] else 'No',
                'Points Deducted': result['points_deducted'],
                'Comments': result['comments']
            })
    
    print(f"\nResults saved to {output_file}")

def main():
    # submissions_folder = "submissions"
    submissions_folder = "subs-26b"
    output_csv = "grading_results/part2_extracted_answers.csv"
    
    if not os.path.exists(submissions_folder):
        print(f"Error: {submissions_folder} folder not found!")
        return
    
    # Analyze all submissions
    results = analyze_student_pdfs(submissions_folder)
    
    # Save to CSV
    save_results_to_csv(results, output_csv)
    
    # Print summary
    total = len(results)
    pdfs_found = sum(1 for r in results if r['pdf_found'])
    q1_correct = sum(1 for r in results if r['q1_correct'])
    q2_correct = sum(1 for r in results if r['q2_correct'])
    both_correct = sum(1 for r in results if r['both_correct'])
    
    print("\n=== Summary ===")
    print(f"Total students: {total}")
    print(f"PDFs found: {pdfs_found}/{total}")
    print(f"Q1 correct: {q1_correct}/{pdfs_found} ({100*q1_correct/pdfs_found:.1f}%)")
    print(f"Q2 correct: {q2_correct}/{pdfs_found} ({100*q2_correct/pdfs_found:.1f}%)")
    print(f"Both correct: {both_correct}/{pdfs_found} ({100*both_correct/pdfs_found:.1f}%)")

if __name__ == "__main__":
    main()
