#!/usr/bin/env python3
"""
Unified Homework 3 Checker
Combines both Part A (mylist.c) and Part B (kernel module) checks
"""

import os
import sys
from datetime import datetime
import pandas as pd
from openpyxl.styles import Alignment

# Import both checkers
from hw_checker import SubmissionChecker as PartAChecker
from kernel_checker import KernelModuleChecker as PartBChecker

class UnifiedHomeworkChecker:
    def __init__(self):
        self.part_a_checker = PartAChecker()
        self.part_b_checker = PartBChecker()
        
    def process_all_submissions(self, submissions_folder: str) -> dict:
        """Process all submissions for both parts"""
        if not os.path.exists(submissions_folder):
            print(f"Error: Submissions folder '{submissions_folder}' does not exist")
            return {}
        
        # Get all student directories
        student_dirs = [d for d in os.listdir(submissions_folder) 
                       if os.path.isdir(os.path.join(submissions_folder, d))]
        
        print(f"Found {len(student_dirs)} student folders")
        print(f"Processing both Part A and Part B for each student...")
        
        results = {}
        
        for student_dir in student_dirs:
            student_path = os.path.join(submissions_folder, student_dir)
            
            try:
                # Process Part A
                part_a_result = self._process_part_a(student_path, student_dir)
                
                # Process Part B  
                part_b_result = self._process_part_b(student_path)
                
                results[student_dir] = {
                    'part_a': part_a_result,
                    'part_b': part_b_result
                }
                
                # Quick feedback
                a_issues = 0 if 'error' in part_a_result else len([k for k, v in part_a_result.items() if v and k != 'error'])
                b_issues = 0 if 'error' in part_b_result else len([k for k, v in part_b_result['deductions'].items() if v])
                
                print(f"✓ {student_dir}: Part A: {a_issues} issues, Part B: {b_issues} issues")
                
            except Exception as e:
                print(f"✗ {student_dir}: Error - {str(e)}")
                results[student_dir] = {
                    'part_a': {'error': str(e)},
                    'part_b': {'error': str(e)}
                }
        
        return results
    
    def _process_part_a(self, student_path: str, student_dir: str) -> dict:
        """Process Part A (mylist.c) for a student"""
        try:
            student_name, analysis_results, error = self.part_a_checker.process_student_folder(student_path)
            
            if error:
                return {'error': error}
            else:
                return analysis_results
        except Exception as e:
            return {'error': str(e)}
    
    def _process_part_b(self, student_path: str) -> dict:
        """Process Part B (kernel module) for a student"""
        try:
            result = self.part_b_checker.check_submission(student_path)
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def generate_unified_excel_report(self, results: dict, output_dir: str = None) -> str:
        """Generate a comprehensive Excel report for both parts"""
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Prepare data for Excel
        excel_data = []
        
        for student_name, student_results in results.items():
            part_a_result = student_results['part_a']
            part_b_result = student_results['part_b']
            
            # Initialize row data
            row = {'Student Name': student_name}
            
            # Process Part A
            if 'error' in part_a_result:
                row['Part A Errors'] = f"Processing Error: {part_a_result['error']}"
                row['Part A Points Deducted'] = 0
            else:
                # Calculate Part A deductions and build error description
                a_total_points = 0
                a_errors_list = []
                
                for issue, found in part_a_result.items():
                    if found and issue in self.part_a_checker.deduction_criteria:
                        criteria = self.part_a_checker.deduction_criteria[issue]
                        points_deducted = abs(criteria['points'])
                        a_total_points += points_deducted
                        
                        error_text = f"{criteria['description']} ({criteria['points']}) \n "
                        error_text += f"{criteria['explanation']}"
                        a_errors_list.append(error_text)
                
                row['Part A Errors'] = "\n\n".join(a_errors_list) if a_errors_list else ""
                row['Part A Points Deducted'] = a_total_points
            
            # Process Part B
            if 'error' in part_b_result:
                row['Part B Errors'] = f"Processing Error: {part_b_result['error']}"
                row['Part B Points Deducted'] = 0
            else:
                # Calculate Part B deductions and build error description
                b_total_deductions = part_b_result.get('total_deductions', 0)
                b_errors_list = []
                
                if 'deductions' in part_b_result:
                    for deduction_key, has_issue in part_b_result['deductions'].items():
                        if has_issue and deduction_key in self.part_b_checker.deduction_criteria:
                            criteria = self.part_b_checker.deduction_criteria[deduction_key]
                            
                            error_text = f"{criteria['description']} ({criteria['points']}) \n "
                            error_text += f"{criteria['explanation']}"
                            b_errors_list.append(error_text)
                
                row['Part B Errors'] = "\n\n".join(b_errors_list) if b_errors_list else ""
                row['Part B Points Deducted'] = b_total_deductions
            
            # Calculate totals and exercise final score
            row['Total Points Deducted'] = row['Part A Points Deducted'] + row['Part B Points Deducted']
            row['Exercise Final Score'] = 100 - row['Total Points Deducted']
            
            # Create unified errors column
            all_errors = []
            if row['Part A Errors']:
                all_errors.append(f"חלק א: \n\n{row['Part A Errors']}")
            if row['Part B Errors']:
                all_errors.append(f"חלק ב: \n\n{row['Part B Errors']}")
            row['All Errors'] = "\n\n".join(all_errors) if all_errors else ""
            
            excel_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"hw3_unified_analysis_{timestamp}.xlsx"
        excel_path = os.path.join(output_dir, excel_filename)
        
        # Create Excel writer with multiple sheets
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Main results sheet
            df.to_excel(writer, sheet_name='HW3 Complete Results', index=False)
            
            # Format the Excel file for better readability
            workbook = writer.book
            worksheet = writer.sheets['HW3 Complete Results']
            
            # Set column widths
            worksheet.column_dimensions['A'].width = 25  # Student Name
            worksheet.column_dimensions['B'].width = 60  # Part A Errors
            worksheet.column_dimensions['C'].width = 20  # Part A Points Deducted
            worksheet.column_dimensions['D'].width = 60  # Part B Errors
            worksheet.column_dimensions['E'].width = 20  # Part B Points Deducted
            worksheet.column_dimensions['F'].width = 20  # Total Points Deducted
            worksheet.column_dimensions['G'].width = 20  # Exercise Final Score
            worksheet.column_dimensions['H'].width = 80  # All Errors
            
            # Enable text wrapping for the errors columns
            for row in range(2, len(df) + 2):  # Start from row 2 (after header)
                for col in ['B', 'D', 'H']:  # Part A, Part B, and All Errors columns
                    cell = worksheet[f'{col}{row}']
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
            
            # Summary sheet
            self._create_unified_summary_sheet(writer, results)
            
            # Part A criteria sheet
            self._create_part_a_criteria_sheet(writer)
            
            # Part B criteria sheet  
            self._create_part_b_criteria_sheet(writer)
        
        print(f"\n\n📊 Unified Excel report generated: {excel_path}")
        return excel_path
    
    def _create_unified_summary_sheet(self, writer, results: dict):
        """Create a summary sheet with statistics for both parts"""
        total_students = len(results)
        
        # Part A statistics
        a_students_with_issues = 0
        a_issue_counts = {criteria: 0 for criteria in self.part_a_checker.deduction_criteria.keys()}
        a_total_points_deducted = {}
        
        # Part B statistics
        b_students_with_issues = 0
        b_issue_counts = {criteria: 0 for criteria in self.part_b_checker.deduction_criteria.keys()}
        b_total_points_deducted = {}
        
        for student_name, student_results in results.items():
            # Process Part A stats
            part_a_result = student_results['part_a']
            if 'error' in part_a_result:
                a_total_points_deducted[student_name] = 0
            else:
                student_points = 0
                has_issues = any(part_a_result.values())
                
                if has_issues:
                    a_students_with_issues += 1
                    
                    for issue, found in part_a_result.items():
                        if found and issue in self.part_a_checker.deduction_criteria:
                            criteria = self.part_a_checker.deduction_criteria[issue]
                            student_points += abs(criteria['points'])
                            a_issue_counts[issue] += 1
                
                a_total_points_deducted[student_name] = student_points
            
            # Process Part B stats
            part_b_result = student_results['part_b']
            if 'error' in part_b_result:
                b_total_points_deducted[student_name] = 0
            else:
                total_deductions = part_b_result.get('total_deductions', 0)
                b_total_points_deducted[student_name] = total_deductions
                
                if total_deductions > 0:
                    b_students_with_issues += 1
                    
                    if 'deductions' in part_b_result:
                        for deduction_key, has_issue in part_b_result['deductions'].items():
                            if has_issue:
                                b_issue_counts[deduction_key] += 1
        
        # Create summary data
        summary_data = [
            ['Metric', 'Part A', 'Part B', 'Hebrew'],
            ['Total Students', total_students, total_students, 'סך סטודנטים'],
            ['Students with Issues', a_students_with_issues, b_students_with_issues, 'סטודנטים עם בעיות'],
            ['Students without Issues', total_students - a_students_with_issues, total_students - b_students_with_issues, 'סטודנטים ללא בעיות'],
            ['Average Points Deducted', 
             sum(a_total_points_deducted.values()) / total_students if total_students > 0 else 0,
             sum(b_total_points_deducted.values()) / total_students if total_students > 0 else 0,
             'ממוצע נקודות הפסד'],
            ['', '', '', ''],
            ['Top Issues Part A', 'Count', 'Percentage', ''],
        ]
        
        # Add top Part A issues
        sorted_a_issues = sorted(a_issue_counts.items(), key=lambda x: x[1], reverse=True)
        for issue, count in sorted_a_issues[:5]:
            if count > 0:
                criteria = self.part_a_checker.deduction_criteria[issue]
                percentage = (count / total_students) * 100
                summary_data.append([
                    criteria['hebrew_description'],
                    count,
                    f"{percentage:.1f}%",
                    f"{criteria['points']} points each"
                ])
        
        summary_data.append(['', '', '', ''])
        summary_data.append(['Top Issues Part B', 'Count', 'Percentage', ''])
        
        # Add top Part B issues
        sorted_b_issues = sorted(b_issue_counts.items(), key=lambda x: x[1], reverse=True)
        for issue, count in sorted_b_issues[:5]:
            if count > 0:
                criteria = self.part_b_checker.deduction_criteria[issue]
                percentage = (count / total_students) * 100
                summary_data.append([
                    criteria['hebrew_description'],
                    count,
                    f"{percentage:.1f}%",
                    f"{criteria['points']} points each"
                ])
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False, header=False)
    
    def _create_part_a_criteria_sheet(self, writer):
        """Create a sheet explaining Part A criteria"""
        criteria_data = []
        
        for issue, criteria in self.part_a_checker.deduction_criteria.items():
            criteria_data.append({
                'Issue Code': issue,
                'Hebrew Description': criteria['hebrew_description'],
                'English Description': criteria['description'],
                'Explanation': criteria['explanation'],
                'Severity': criteria['severity'],
                'Points Deducted': criteria['points']
            })
        
        criteria_df = pd.DataFrame(criteria_data)
        criteria_df.to_excel(writer, sheet_name='Part A Criteria', index=False)
    
    def _create_part_b_criteria_sheet(self, writer):
        """Create a sheet explaining Part B criteria"""
        criteria_data = []
        
        for issue, criteria in self.part_b_checker.deduction_criteria.items():
            criteria_data.append({
                'Issue Code': issue,
                'Hebrew Description': criteria['hebrew_description'],
                'English Description': criteria['description'],
                'Explanation': criteria['explanation'],
                'Severity': criteria['severity'],
                'Points Deducted': criteria['points'],
                'Max Score': criteria['max_score']
            })
        
        criteria_df = pd.DataFrame(criteria_data)
        criteria_df.to_excel(writer, sheet_name='Part B Criteria', index=False)


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build path to submissions folder
    submissions_folder = os.path.join(current_dir, "test")
    
    # Alternative: you can still use command line argument if provided
    if len(sys.argv) == 2:
        submissions_folder = sys.argv[1]
    
    print(f"Processing HW3 submissions (Part A + Part B) in: {submissions_folder}")
    
    checker = UnifiedHomeworkChecker()
    results = checker.process_all_submissions(submissions_folder)
    
    # Generate unified Excel report
    try:
        excel_path = checker.generate_unified_excel_report(results, current_dir)
        print(f"📁 Unified Excel file saved to: {excel_path}")
    except ImportError:
        print("❌ Error: pandas and openpyxl are required for Excel export.")
        print("Install them with: pip install pandas openpyxl")
    except Exception as e:
        print(f"❌ Error generating Excel file: {e}")


if __name__ == "__main__":
    main()
