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
            'missing_memory_cleanup': {
                'description': 'Missing kfree() calls for allocated memory',
                'hebrew_description': 'חסרה קריאה ל-kfree() לזיכרון שהוקצה',
                'explanation': 'כל קריאה ל-kmalloc() חייבת להיות מלווה בקריאה מתאימה ל-kfree() כדי למנוע זליגת זיכרון',
                'severity': 'major',
                'points': -5,
                'pattern': None  # Will be checked with custom logic
            },
            'missing_unregister': {
                'description': 'Missing unregister_chrdev() in cleanup_module',
                'hebrew_description': 'חסרה קריאה ל-unregister_chrdev() ב-cleanup_module',
                'explanation': 'המודול חייב לבטל את הרישום שלו בעת ההתנתקות כדי למנוע בעיות במערכת',
                'severity': 'major',
                'points': -5,
                'pattern': None  # Will be checked with custom logic
            },
            'shared_encryption_key': {
                'description': 'Encryption key shared between file instances',
                'hebrew_description': 'מפתח הצפנה משותף בין instance-ים של קבצים',
                'explanation': 'כל פתיחה של קובץ צריכה להיות עם מפתח הצפנה נפרד, לא משותף עם פתיחות אחרות של אותו device',
                'severity': 'major',
                'points': -8,
                'pattern': None  # Will be checked with custom logic
            },
            'no_parameter_validation': {
                'description': 'Missing validation for size/count parameters',
                'hebrew_description': 'חסרת בדיקת תקינות לפרמטרים size/count',
                'explanation': 'פרמטרי המודול size ו-count חייבים להיבדק שהם חיוביים לפני השימוש בהם',
                'severity': 'minor',
                'points': -2,
                'pattern': None  # Will be checked with custom logic
            },
            'no_minor_validation': {
                'description': 'Missing minor number validation in device_open',
                'hebrew_description': 'חסרת בדיקת תקינות למספר minor ב-device_open',
                'explanation': 'צריך לוודא שמספר ה-minor נמצא בטווח החוקי (0 עד count-1)',
                'severity': 'minor',
                'points': -2,
                'pattern': None  # Will be checked with custom logic
            },
            'no_register_error_check': {
                'description': 'Missing error checking for register_chrdev return value',
                'hebrew_description': 'חסרת בדיקת שגיאה לערך החזרה של register_chrdev',
                'explanation': 'צריך לבדוק את ערך ההחזרה של register_chrdev ולטפל בכישלון',
                'severity': 'minor',
                'points': -2,
                'pattern': None  # Will be checked with custom logic
            },
            'missing_required_functions': {
                'description': 'Missing required file operations or module functions',
                'hebrew_description': 'חסרות פונקציות נדרשות של file operations או module',
                'explanation': 'המודול חייב לכלול את כל הפונקציות הנדרשות: open, release, read, write, ioctl, llseek',
                'severity': 'major',
                'points': -9,
                'pattern': None  # Will be checked with custom logic
            },
            'different_function_names': {
                'description': 'Different function names used in init_module or cleanup_module',
                'hebrew_description': 'שמות פונקציות שונים בשימוש בפעולות קובץ',
                'explanation': 'יש להשתמש בשמות הפונקציות הנכונים: init_module, cleanup_module',
                'severity': 'minor',
                'points': -1,
                'pattern': None  # Will be checked with custom logic
            },
            'no_allocation_error_handling': {
                'description': 'Missing error handling for memory allocation failures',
                'hebrew_description': 'חסר טיפול בשגיאות הקצאת זיכרון',
                'explanation': 'צריך לבדוק את ערך ההחזרה של kmalloc ולשחרר זיכרון שכבר הוקצה במקרה של כישלון',
                'severity': 'minor',
                'points': -3,
                'pattern': None  # Will be checked with custom logic
            },
            'wrong_ioctl_command': {
                'description': 'Using wrong IOCTL command name or validation',
                'hebrew_description': 'שימוש שגוי בשם פקודת IOCTL או בדיקת תקינות',
                'explanation': 'צריך להשתמש ב-IOCTL_SET_KEY (לא IOCTL_SET_VAL) ולבדוק טווח ערכים 0-255',
                'severity': 'minor',
                'points': -2,
                'pattern': None  # Will be checked with custom logic
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
    
    def find_encdev_c(self, directory):
        """Find encdev.c file in the extracted directory"""
        for root, dirs, files in os.walk(directory):
            if 'encdev.c' in files:
                return os.path.join(root, 'encdev.c')
        return None
    
    def read_file_content(self, file_path):
        """Read and return file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def check_missing_memory_cleanup(self, content):
        """Check if kmalloc calls have corresponding kfree calls"""
        # Count kmalloc and kfree calls - improved to catch kmalloc_array
        kmalloc_patterns = [r'kmalloc\s*\(', r'kmalloc_array\s*\(']
        kmalloc_count = 0
        for pattern in kmalloc_patterns:
            kmalloc_count += len(re.findall(pattern, content))
        
        kfree_count = len(re.findall(r'kfree\s*\(', content))
        
        # More sophisticated: check in cleanup_module and device_release
        cleanup_func = re.search(r'void\s+cleanup_module\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        release_func = re.search(r'int\s+device_release\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        has_cleanup_kfree = False
        has_release_kfree = False
        
        if cleanup_func and 'kfree(' in cleanup_func.group(1):
            has_cleanup_kfree = True
            
        if release_func and 'kfree(' in release_func.group(1):
            has_release_kfree = True
        
        # Check if kmalloc is used in device_open (needs kfree in device_release)
        device_open_func = re.search(r'static\s+int\s+device_open\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        has_open_kmalloc = False
        if device_open_func and re.search(r'kmalloc\s*\(', device_open_func.group(1)):
            has_open_kmalloc = True
        
        # Check if kmalloc is used in init_module (needs kfree in cleanup_module)
        init_func = re.search(r'int\s+init_module\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        has_init_kmalloc = False
        if init_func and re.search(r'kmalloc[_\w]*\s*\(', init_func.group(1)):
            has_init_kmalloc = True
        
        # If we have kmalloc in device_open but no kfree in device_release
        if has_open_kmalloc and not has_release_kfree:
            return True
            
        # If we have kmalloc in init_module but no kfree in cleanup_module
        if has_init_kmalloc and not has_cleanup_kfree:
            return True
            
        # Basic sanity check: should have roughly equal kmalloc and kfree counts
        if kmalloc_count > 0 and kfree_count == 0:
            return True
            
        return False
    
    def check_missing_unregister(self, content):
        """Check if cleanup_module calls unregister_chrdev"""

        if 'unregister_chrdev' in content:
            return False  # Found unregister_chrdev, no issue
        return True

    
    def check_shared_encryption_key(self, content):
        """Check if encryption key is shared (global/static) instead of per-file"""
        # Look for global/static key variables
        # global_key_patterns = [
        #     r'static\s+.*key',
        #     r'char\s+key\s*[=;]',  # Global key variable
        #     r'unsigned\s+char\s+key\s*[=;]',
        #     r'int\s+key\s*[=;]'
        # ]
        
        # for pattern in global_key_patterns:
        #     if re.search(pattern, content, re.IGNORECASE):
        #         return True
        
        # # Check if key is stored in file_data/file_val struct (good practice)
        # # Look for struct with key field - can be named file_data, file_val, etc.
        # has_file_struct_with_key = re.search(r'struct\s+\w+\s*\{[^}]*key[^}]*\}', content, re.DOTALL)
        # device_open_func = re.search(r'static\s+int\s+device_open\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        # if device_open_func:
        #     func_content = device_open_func.group(1)
        #     # Check if key is allocated and set per file opening
        #     has_per_file_key = bool(re.search(r'->key\s*=|\.key\s*=', func_content))
            
        #     # If no file struct with key or key not set per file
        #     if not has_file_struct_with_key or not has_per_file_key:
        #         return True
                
        return False
    
    def check_no_parameter_validation(self, content):
        """Check if size and count parameters are validated"""
        init_func = re.search(r'int\s+init_module\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        if init_func:
            func_content = init_func.group(1)
            # Look for validation of size and count - improved patterns
            has_size_check = bool(re.search(r'size\s*[<>]=?\s*0|if\s*\([^)]*size[^)]*[<>]|size.*<=|size.*<\s*1', func_content))
            has_count_check = bool(re.search(r'count\s*[<>]=?\s*0|if\s*\([^)]*count[^)]*[<>]|count.*<=|count.*<\s*1', func_content))
            
            if not (has_size_check and has_count_check):
                return True
                
        return False
    
    def check_no_minor_validation(self, content):
        """Check if minor number is validated in device_open"""
        device_open_func = re.search(r'static\s+int\s+device_open\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        if device_open_func:
            func_content = device_open_func.group(1)
            # Look for minor validation
            has_minor_check = bool(re.search(r'minor\s*[<>]=?\s*count|if\s*\([^)]*minor[^)]*\)', func_content))
            
            if not has_minor_check:
                return True
                
        return False
    
    def check_no_register_error_check(self, content):
        """Check if register_chrdev return value is checked"""
        # Look for register_chrdev call and error checking
        text = "register_chrdev"
        if text in content:
            return False
        return True
    
    def check_missing_required_functions(self, content):
        """Check if all required functions are present"""
        required_functions = [
            r'_open',
            r'_release',
            r'_read',
            r'_write',
            r'_ioctl',
            r'seek',
            # r'init_module',
            # r'cleanup_module'
        ]
        
        missing_functions = []
        for func in required_functions:
            if not re.search(f'{func}', content):
                missing_functions.append(func)
        
        if missing_functions:
            return True
            
        return False
    
    def check_different_function_names(self, content):
        """Check if init_module or cleanup_module have different names like "encdev_exit" or "encdev_init" """
        init_func = re.search(r'init_module', content, re.DOTALL)
        cleanup_func = re.search(r'cleanup_module', content, re.DOTALL)
        init_functions = [
            r'encdev_init',
            r'mychardev_init',
            r'mynetdev_init',
            r'myfs_init'
        ]
        exit_functions = [
            r'encdev_exit',
            r'mychardev_exit',
            r'mynetdev_exit',
            r'myfs_exit'
        ]
        # Check if init_module or cleanup_module are named differently
        if init_func and cleanup_func:
            return False  # Both functions are correctly named
        if not init_func and any(re.search(pattern, content) for pattern in init_functions):
            return True
        if not cleanup_func and any(re.search(pattern, content) for pattern in exit_functions):
            return True
        # If both functions are missing or have different names
        
        if not init_func or not cleanup_func:
            return True
        return False
    
    def check_wrong_ioctl_command(self, content):
        """Check if using wrong IOCTL command name or missing validation"""
        # Check device_ioctl function
        ioctl_func = re.search(r'static\s+long\s+device_ioctl\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        if ioctl_func:
            func_content = ioctl_func.group(1)
            
            # Check if using wrong command name (should be IOCTL_SET_KEY, not IOCTL_SET_VAL)
            if 'IOCTL_SET_VAL' in func_content:
                return True
                
            # Check if missing proper range validation for the argument
            has_range_check = bool(re.search(r'arg\s*[<>]=?\s*255|arg\s*[<>]=?\s*0|\(arg\s*[<>]|255.*arg|0.*arg', func_content))
            
            if not has_range_check:
                return True
                
        return False
    
    def check_no_allocation_error_handling(self, content):
        """Check if kmalloc return values are checked for errors"""
        # Find all kmalloc calls - improved pattern to catch more variations
        kmalloc_calls = re.findall(r'(\w+)\s*=\s*kmalloc[_\w]*\s*\([^)]*\)', content)
        
        if not kmalloc_calls:
            return False  # No kmalloc calls found
        
        for var_name in kmalloc_calls:
            # Check if there's error checking for this variable - improved patterns
            error_check_patterns = [
                f'if\\s*\\(\\s*!{var_name}\\s*\\)',
                f'if\\s*\\(\\s*{var_name}\\s*==\\s*NULL\\s*\\)',
                f'if\\s*\\(\\s*{var_name}\\s*==\\s*0\\s*\\)',
                f'if\\s*\\(!{var_name}\\)',
                f'if\\s*\\({var_name}\\s*==\\s*-1\\)',
                f'return\\s+-1',  # Check for basic error handling
                f'return\\s+-ENOMEM'
            ]
            
            has_error_check = any(re.search(pattern, content) for pattern in error_check_patterns)
            
            if not has_error_check:
                return True
                
        return False
    
    def analyze_submission(self, content):
        """Analyze a single submission for all deduction criteria"""
        results = {}
        
        # Check each criterion
        results['missing_memory_cleanup'] = self.check_missing_memory_cleanup(content)
        results['missing_unregister'] = self.check_missing_unregister(content)
        results['shared_encryption_key'] = self.check_shared_encryption_key(content)
        results['no_parameter_validation'] = self.check_no_parameter_validation(content)
        results['no_minor_validation'] = self.check_no_minor_validation(content)
        results['no_register_error_check'] = self.check_no_register_error_check(content)
        results['missing_required_functions'] = self.check_missing_required_functions(content)
        results['different_function_names'] = self.check_different_function_names(content)
        results['no_allocation_error_handling'] = self.check_no_allocation_error_handling(content)
        results['wrong_ioctl_command'] = self.check_wrong_ioctl_command(content)
        
        return results
    
    def process_student_folder(self, student_folder):
        """Process a single student's folder"""
        student_name = os.path.basename(student_folder)
        
        # First, check if encdev.c already exists in the student folder
        encdev_path = self.find_encdev_c(student_folder)
        
        if encdev_path:
            # encdev.c found directly in student folder
            content = self.read_file_content(encdev_path)
            if content is None:
                return student_name, None, "Failed to read encdev.c"
            
            # Analyze content
            results = self.analyze_submission(content)
            return student_name, results, None
        
        # encdev.c not found, look for tar.gz file to extract
        tar_files = [f for f in os.listdir(student_folder) if f.endswith('.tar.gz')]
        
        if not tar_files:
            return student_name, None, "No encdev.c or tar.gz file found"
        
        if len(tar_files) > 1:
            return student_name, None, "Multiple tar.gz files found"
        
        tar_path = os.path.join(student_folder, tar_files[0])
        
        # Extract tar file directly into student folder
        if not self.extract_tar_file(tar_path, student_folder):
            return student_name, None, "Failed to extract tar file"
        
        # Now look for encdev.c in the student folder (including newly extracted files)
        encdev_path = self.find_encdev_c(student_folder)
        if not encdev_path:
            return student_name, None, "encdev.c not found even after extraction"
        
        # Read content
        content = self.read_file_content(encdev_path)
        if content is None:
            return student_name, None, "Failed to read encdev.c"
        
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
        print("DETAILED ANALYSIS REPORT (HW4 - Linux Kernel Module)")
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
                        
                        print(f"  {severity_icon} {criteria['description']} ({points} points)")
                        print(f"      Explanation: {criteria['explanation']}")
                        # print(f"      {criteria['description']}")
                        issue_counts[issue] += 1
                
                total_points_deducted[student_name] = student_points
            else:
                total_points_deducted[student_name] = 0
        
        print(f"\n📊 SUMMARY:")
        print(f"Total students processed: {total_students}")
        print(f"Students with issues: {students_with_issues}")
        print(f"Students without issues: {total_students - students_with_issues}")
        
        # Calculate average points deducted
        if total_students > 0:
            avg_deduction = sum(total_points_deducted.values()) / total_students
            print(f"Average points deducted: {avg_deduction:.1f}")
        
        print(f"\n📈 ISSUE BREAKDOWN:")
        for issue, count in issue_counts.items():
            criteria = self.deduction_criteria[issue]
            severity_icon = "🔴" if criteria['severity'] == 'major' else "🟡"
            percentage = (count / total_students) * 100 if total_students > 0 else 0
            total_points_for_issue = abs(criteria['points']) * count
            print(f"  {severity_icon} {criteria['description']}")
            print(f"      {count} students ({percentage:.1f}%) - {criteria['points']} points each")
            # print(f"      Total points deducted for this issue: {total_points_for_issue}")
            print(f"      {criteria['explanation']}")
            print()
        
        
        # Show final grades for all students
        print(f"\n📋 FINAL GRADES - ALL STUDENTS:")
        print("="*60)
        
        # Assume starting grade is 100 (you can adjust this)
        base_grade = 100
        
        # Sort students alphabetically for easier reading
        sorted_students = sorted(total_points_deducted.items(), key=lambda x: x[0])
        
        for student_name, points_deducted in sorted_students:
            final_grade = base_grade - points_deducted
            
            # Add status indicator
            if points_deducted == 0:
                status = "✅"
            elif points_deducted <= 5:
                status = "🟡"
            else:
                status = "🔴"
            
            print(f"{status} {student_name}: {final_grade}")
        
        print("="*60)
        print(f"Legend: ✅ Perfect (0 deductions), 🟡 Minor issues (1-5 points), 🔴 Major issues (6+ points)")
    
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
                    'Errors Found': f"Processing Error: {student_results['error']}",
                    'Total Points Deducted': 0
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
        excel_filename = f"hw4_kernel_module_analysis_{timestamp}.xlsx"
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

def main(folder_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build path to submissions folder
    general_folder = os.path.join(current_dir, folder_name)
    
    # Alternative: you can still use command line argument if provided
    if len(sys.argv) == 2:
        general_folder = sys.argv[1]
    
    print(f"Processing HW4 (Linux Kernel Module) submissions in: {general_folder}")
    
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
    
    main("submissions")
    # main("test")
