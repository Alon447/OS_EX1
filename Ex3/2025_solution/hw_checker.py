#!/usr/bin/env python3
import os
import sys
import tarfile
import tempfile
import shutil
import re
from pathlib import Path
import pandas as pd
from datetime import datetime
from openpyxl.styles import Alignment

class SubmissionChecker:
    def __init__(self):
        self.deduction_criteria = {
            'malloc_after_lock': {
                'description': 'malloc() called after pthread_mutex_lock()',
                'hebrew_description': 'קריאה ל-malloc() אחרי pthread_mutex_lock() - הקצאת זיכרון בתוך critical section',
                'explanation': 'הקצאת זיכרון (malloc) צריכה להתבצע לפני נעילת המוטקס כדי למזער את הזמן שהמוטקס נעול',
                'severity': 'minor',
                'points': -2,
                'pattern': None  # Will be checked with custom logic
            },
            'lock_for_size_read': {
                'description': 'Lock used to read single size value',
                'hebrew_description': 'שימוש במוטקס לקריאת ערך גודל יחיד',
                'explanation': 'קריאת ערך מספרי בודד היא אטומית בדרך כלל ולא דורשת נעילה. המוטקס צריך להיות בשימוש רק לעדכונים מורכבים',
                'severity': 'minor',
                'points': -1,
                'pattern': None  # Will be checked with custom logic
            },
            'free_before_unlock': {
                'description': 'free() called before pthread_mutex_unlock()',
                'hebrew_description': 'קריאה ל-free() לפני pthread_mutex_unlock()',
                'explanation': 'שחרור זיכרון צריך להתבצע אחרי ביטול נעילת המוטקס כדי למזער את הזמן שהמוטקס נעול',
                'severity': 'minor',
                'points': -2,
                'pattern': None  # Will be checked with custom logic
            },
            'items_not_freed': {
                'description': 'Existing items not freed in destroy',
                'hebrew_description': 'רשימה לא משחררת את כל הפריטים ב-destroy',
                'explanation': 'פונקציית הריסה צריכה לשחרר את כל הצמתים ברשימה כדי למנוע זליגת זכרון',
                'severity': 'minor',
                'points': -2,
                'pattern': None  # Will be checked with custom logic
            },
            'has_main_function': {
                'description': 'Contains main() function (major deduction / skip question)',
                'hebrew_description': 'קובץ מכיל פונקציית main()',
                'explanation': 'הקובץ לא צריך לכלול פונקציית main כיון שמדובר בספרייה שתשמש אפליקציות אחרות',
                'severity': 'major',
                'points': -10,
                'pattern': r'int\s+main\s*\('
            }
        }
        
    def extract_tar_file(self, tar_path, extract_to):
        """Extract tar file to temporary directory"""
        try:
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(extract_to)
            return True
        except Exception as e:
            print(f"Error extracting {tar_path}: {e}")
            return False
    
    def find_mylist_c(self, directory):
        """Find mylist.c file in the extracted directory"""
        for root, dirs, files in os.walk(directory):
            if 'mylist.c' in files:
                return os.path.join(root, 'mylist.c')
        return None
    
    def read_file_content(self, file_path):
        """Read and return file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def check_malloc_after_lock(self, content):
        """Check if malloc is called after pthread_mutex_lock"""
        # Look for patterns where malloc appears after pthread_mutex_lock in the same function
        functions = re.findall(r'void\s+mylist_insert_[ht][ea][ai][ld]\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        for func_content in functions:
            # Check if malloc appears after pthread_mutex_lock
            lock_pos = func_content.find('pthread_mutex_lock')
            malloc_pos = func_content.find('malloc')
            
            if lock_pos != -1 and malloc_pos != -1 and malloc_pos > lock_pos:
                return True
        return False
    
    def check_lock_for_size_read(self, content):
        """Check if lock is used unnecessarily for reading size in mylist_size function"""
        # Extract mylist_size function
        size_func_match = re.search(r'int\s+mylist_size\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        if size_func_match:
            func_content = size_func_match.group(1)
            # Check if pthread_mutex_lock is used in size function
            if 'pthread_mutex_lock' in func_content:
                return True
        return False
    
    def check_free_before_unlock(self, content):
        """Check if free() is called before pthread_mutex_unlock"""
        # Look for patterns in remove functions
        remove_functions = re.findall(r'int\s+mylist_remove_[ht][ea][ai][ld]\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        for func_content in remove_functions:
            # Find positions of unlock and free
            unlock_pos = func_content.find('pthread_mutex_unlock')
            free_pos = func_content.find('free(')
            
            if unlock_pos != -1 and free_pos != -1 and free_pos < unlock_pos:
                return True
        return False
    
    def check_items_not_freed(self, content):
        """Check if items are not freed in destroy function"""
        # Extract mylist_destroy function
        destroy_func_match = re.search(r'void\s+mylist_destroy\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        if destroy_func_match:
            func_content = destroy_func_match.group(1)
            # Check if there's a loop to free items
            has_loop = bool(re.search(r'while\s*\([^)]*\)|for\s*\([^)]*\)', func_content))
            has_free = 'free(' in func_content
            
            # If no loop or no free, items might not be freed properly
            if not (has_loop and has_free):
                return True
        return False
    
    def check_has_main_function(self, content):
        """Check if main function exists"""
        pattern = self.deduction_criteria['has_main_function']['pattern']
        return bool(re.search(pattern, content))
    
    def analyze_submission(self, content):
        """Analyze a single submission for all deduction criteria"""
        results = {}
        
        # Check each criterion
        results['malloc_after_lock'] = self.check_malloc_after_lock(content)
        results['lock_for_size_read'] = self.check_lock_for_size_read(content)
        results['free_before_unlock'] = self.check_free_before_unlock(content)
        results['items_not_freed'] = self.check_items_not_freed(content)
        results['has_main_function'] = self.check_has_main_function(content)
        
        return results
    
    def process_student_folder(self, student_folder):
        """Process a single student's folder"""
        student_name = os.path.basename(student_folder)
        
        # First, check if mylist.c already exists in the student folder
        mylist_path = self.find_mylist_c(student_folder)
        
        if mylist_path:
            # mylist.c found directly in student folder
            content = self.read_file_content(mylist_path)
            if content is None:
                return student_name, None, "Failed to read mylist.c"
            
            # Analyze content
            results = self.analyze_submission(content)
            return student_name, results, None
        
        # mylist.c not found, look for tar.gz file to extract
        tar_files = [f for f in os.listdir(student_folder) if f.endswith('.tar.gz')]
        
        if not tar_files:
            return student_name, None, "No mylist.c or tar.gz file found"
        
        if len(tar_files) > 1:
            return student_name, None, "Multiple tar.gz files found"
        
        tar_path = os.path.join(student_folder, tar_files[0])
        
        # Extract tar file directly into student folder
        if not self.extract_tar_file(tar_path, student_folder):
            return student_name, None, "Failed to extract tar file"
        
        # Now look for mylist.c in the student folder (including newly extracted files)
        mylist_path = self.find_mylist_c(student_folder)
        if not mylist_path:
            return student_name, None, "mylist.c not found even after extraction"
        
        # Read content
        content = self.read_file_content(mylist_path)
        if content is None:
            return student_name, None, "Failed to read mylist.c"
        
        # Analyze content
        results = self.analyze_submission(content)
        
        return student_name, results, None
    
    def process_all_submissions(self, general_folder):
        """Process all submissions in the general folder"""
        results = {}
        
        if not os.path.exists(general_folder):
            print(f"Error: General folder '{general_folder}' does not exist")
            return results
        
        # Get all student folders
        student_folders = [f for f in os.listdir(general_folder) 
                          if os.path.isdir(os.path.join(general_folder, f))]
        
        print(f"Found {len(student_folders)} student folders")
        
        for student_folder in student_folders:
            student_path = os.path.join(general_folder, student_folder)
            student_name, analysis_results, error = self.process_student_folder(student_path)
            
            if error:
                results[student_name] = {'error': error}
                print(f"❌ {student_name}: {error}")
            else:
                results[student_name] = analysis_results
                issues = [k for k, v in analysis_results.items() if v]
                if issues:
                    print(f"⚠️  {student_name}: Found issues - {', '.join(issues)}")
                else:
                    print(f"✅ {student_name}: No issues found")
        
        return results
    
    def generate_report(self, results):
        """Generate a detailed report of all findings"""
        print("\n" + "="*80)
        print("DETAILED ANALYSIS REPORT - דוח ניתוח מפורט")
        print("="*80)
        
        total_students = len(results)
        students_with_issues = 0
        issue_counts = {criteria: 0 for criteria in self.deduction_criteria.keys()}
        total_points_deducted = {}
        
        for student_name, student_results in results.items():
            if 'error' in student_results:
                continue
                
            has_issues = any(student_results.values())
            student_points = 0
            
            if has_issues:
                students_with_issues += 1
                print(f"\n📋 {student_name}:")
                
                for issue, found in student_results.items():
                    if found:
                        criteria = self.deduction_criteria[issue]
                        severity_icon = "🔴" if criteria['severity'] == 'major' else "🟡"
                        points = criteria['points']
                        student_points += abs(points)
                        
                        print(f"  {severity_icon} {criteria['hebrew_description']} ({points} נקודות)")
                        print(f"      הסבר: {criteria['explanation']}")
                        print(f"      {criteria['description']}")
                        issue_counts[issue] += 1
                
                total_points_deducted[student_name] = student_points
                print(f"    📊 סך הפסד נקודות: {student_points}")
            else:
                total_points_deducted[student_name] = 0
        
        print(f"\n📊 SUMMARY - סיכום:")
        print(f"Total students processed - סך סטודנטים: {total_students}")
        print(f"Students with issues - סטודנטים עם בעיות: {students_with_issues}")
        print(f"Students without issues - סטודנטים ללא בעיות: {total_students - students_with_issues}")
        
        # Calculate average points deducted
        if total_students > 0:
            avg_deduction = sum(total_points_deducted.values()) / total_students
            print(f"Average points deducted - ממוצע נקודות הפסד: {avg_deduction:.1f}")
        
        print(f"\n📈 ISSUE BREAKDOWN - פירוט בעיות:")
        for issue, count in issue_counts.items():
            criteria = self.deduction_criteria[issue]
            severity_icon = "🔴" if criteria['severity'] == 'major' else "🟡"
            percentage = (count / total_students) * 100 if total_students > 0 else 0
            total_points_for_issue = abs(criteria['points']) * count
            print(f"  {severity_icon} {criteria['hebrew_description']}")
            print(f"      {count} students ({percentage:.1f}%) - {criteria['points']} points each")
            print(f"      Total points deducted for this issue: {total_points_for_issue}")
            print(f"      {criteria['explanation']}")
            print()
        
        # Show students with highest deductions
        if total_points_deducted:
            print(f"\n🎯 TOP DEDUCTIONS - הפסדי נקודות גבוהים:")
            sorted_deductions = sorted(total_points_deducted.items(), key=lambda x: x[1], reverse=True)
            for student, points in sorted_deductions[:5]:  # Top 5
                if points > 0:
                    print(f"  {student}: {points} נקודות הפסד")
    
    def generate_excel_report(self, results, output_dir=None):
        """Generate an Excel report with detailed results"""
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Prepare data for Excel
        excel_data = []
        
        for student_name, student_results in results.items():
            if 'error' in student_results:
                # Handle error cases
                row = {
                    'Student Name': student_name,
                    'Errors Found In Part 1': f"Processing Error: {student_results['error']}",
                    'Total Points Deducted Part 1': 0
                }
                excel_data.append(row)
                continue
            
            # Calculate total points deducted and build error description
            total_points = 0
            errors_list = []
            
            for issue, found in student_results.items():
                if found:
                    criteria = self.deduction_criteria[issue]
                    points_deducted = abs(criteria['points'])
                    total_points += points_deducted
                    
                    # Format error description
                    error_text = f"{criteria['description']} ({criteria['points']})\n"
                    error_text += f"{criteria['explanation']}\n"
                    
                    errors_list.append(error_text)
            
            # Combine all errors into one cell
            if errors_list:
                all_errors = "\n\n".join(errors_list)
            else:
                all_errors = ""
            
            row = {
                'Student Name': student_name,
                'Errors Found': all_errors,
                'Total Points Deducted': total_points
            }
            excel_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"homework_analysis_{timestamp}.xlsx"
        excel_path = os.path.join(output_dir, excel_filename)
        
        # Create Excel writer with multiple sheets
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Main results sheet
            df.to_excel(writer, sheet_name='Results', index=False)
            
            # Format the Excel file for better readability
            workbook = writer.book
            worksheet = writer.sheets['Results']
            
            # Set column widths
            worksheet.column_dimensions['A'].width = 30  # Student Name
            worksheet.column_dimensions['B'].width = 80  # Errors Found
            worksheet.column_dimensions['C'].width = 20  # Total Points
            
            # Enable text wrapping for the errors column
            for row in range(2, len(df) + 2):  # Start from row 2 (after header)
                cell = worksheet[f'B{row}']
                cell.alignment = Alignment(wrap_text=True, vertical='top')
            
            # Summary sheet
            self._create_summary_sheet(writer, results)
            
            # Criteria explanation sheet
            self._create_criteria_sheet(writer)
        
        print(f"\n📊 Excel report generated: {excel_path}")
        return excel_path
    
    def _create_summary_sheet(self, writer, results):
        """Create a summary sheet with statistics"""
        total_students = len(results)
        students_with_issues = 0
        issue_counts = {criteria: 0 for criteria in self.deduction_criteria.keys()}
        total_points_deducted = {}
        
        for student_name, student_results in results.items():
            if 'error' in student_results:
                total_points_deducted[student_name] = 0
                continue
                
            has_issues = any(student_results.values())
            student_points = 0
            
            if has_issues:
                students_with_issues += 1
                
                for issue, found in student_results.items():
                    if found:
                        criteria = self.deduction_criteria[issue]
                        student_points += abs(criteria['points'])
                        issue_counts[issue] += 1
            
            total_points_deducted[student_name] = student_points
        
        # Create summary data
        summary_data = [
            ['Metric', 'Value', 'Hebrew'],
            ['Total Students', total_students, 'סך סטודנטים'],
            ['Students with Issues', students_with_issues, 'סטודנטים עם בעיות'],
            ['Students without Issues', total_students - students_with_issues, 'סטודנטים ללא בעיות'],
            ['Average Points Deducted', sum(total_points_deducted.values()) / total_students if total_students > 0 else 0, 'ממוצע נקודות הפסד'],
            ['', '', ''],
            ['Issue Breakdown', 'Count', 'פירוט בעיות']
        ]
        
        for issue, count in issue_counts.items():
            criteria = self.deduction_criteria[issue]
            percentage = (count / total_students) * 100 if total_students > 0 else 0
            summary_data.append([
                criteria['hebrew_description'],
                f"{count} ({percentage:.1f}%)",
                f"{criteria['points']} points each"
            ])
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False, header=False)
    
    def _create_criteria_sheet(self, writer):
        """Create a sheet explaining all criteria"""
        criteria_data = []
        
        for issue, criteria in self.deduction_criteria.items():
            criteria_data.append({
                'Issue Code': issue,
                'Hebrew Description': criteria['hebrew_description'],
                'English Description': criteria['description'],
                'Explanation': criteria['explanation'],
                'Severity': criteria['severity'],
                'Points Deducted': criteria['points']
            })
        
        criteria_df = pd.DataFrame(criteria_data)
        criteria_df.to_excel(writer, sheet_name='Criteria', index=False)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build path to another folder
    general_folder = os.path.join(current_dir, "submissions")
    

    # Alternative: you can still use command line argument if provided
    if len(sys.argv) == 2:
        general_folder = sys.argv[1]
    
    print(f"Processing submissions in: {general_folder}")
    
    checker = SubmissionChecker()
    results = checker.process_all_submissions(general_folder)
    checker.generate_report(results)
    
    # Generate Excel report
    try:
        excel_path = checker.generate_excel_report(results, current_dir)
        print(f"📁 Excel file saved to: {excel_path}")
    except ImportError:
        print("❌ Error: pandas and openpyxl are required for Excel export.")
        print("Install them with: pip install pandas openpyxl")
    except Exception as e:
        print(f"❌ Error generating Excel file: {e}")

if __name__ == "__main__":
    main()
