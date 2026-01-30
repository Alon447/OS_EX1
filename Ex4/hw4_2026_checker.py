#!/usr/bin/env python3
"""
HW4 2026 Submission Checker
Adapted from 2025 checker for the new requirements:
- File names: os4mod.c, os4mod.h, os4mod.sh (instead of encdev.*)
- Encryption: XOR cipher (instead of Caesar cipher)
- Initial key: 0xFF (instead of 0)
- IOCTL command: IOCTL_XOR_KEY (instead of IOCTL_SET_KEY)
- Script: 3 arguments (folder, size, count) instead of 1 with hardcoded values
- PDF answer file: os4.pdf (instead of myanswers.pdf)
- Part B: Theoretical questions about disk storage and transfer times
"""
import os
import sys
import tarfile
import tempfile
import shutil
import re
from pathlib import Path
import pandas as pd
from datetime import datetime

try:
    import fitz  # PyMuPDF for PDF extraction
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: PyMuPDF (fitz) not installed. Part B PDF checking disabled.")
    print("Install with: pip install PyMuPDF")


class PartBChecker:
    """
    Checker for Part B theoretical questions about disk storage and transfer times.
    
    Correct answers (from solution):
    Q1: 225,000 blocks (or 1,800,000 sectors)
    Q2: 5ms for the last transfer stage (or 3.33ms depending on interpretation)
    """
    
    def __init__(self):
        # Q1: Correct answer is 225,000 blocks (1,800,000 sectors / 8 sectors per block)
        self.q1_correct_blocks = 225000
        self.q1_correct_sectors = 1800000
        
        # Q2: Maximum time for last data transfer
        # Solution says 5ms (transferring in zone B at 800 sectors/track)
        # Some interpret as 3.33ms (continuing in zone A)
        self.q2_correct_ms = 5
        self.q2_alternative_ms = 3.33  # Also acceptable
        
        self.part_b_criteria = {
            'q1_wrong_answer': {
                'description': 'Question 1: Wrong disk storage calculation',
                'hebrew_description': 'שאלה 1: חישוב שגוי של שטח האחסון בדיסק',
                'explanation': 'התשובה הנכונה היא 225,000 בלוקים (או 1,800,000 סקטורים)',
                'points': -10,
            },
            'q1_no_calculation': {
                'description': 'Question 1: Missing calculation/explanation',
                'hebrew_description': 'שאלה 1: חסר חישוב/הסבר',
                'explanation': 'יש להציג את החישוב המלא',
                'points': -5,
            },
            'q2_wrong_answer': {
                'description': 'Question 2: Wrong transfer time calculation',
                'hebrew_description': 'שאלה 2: חישוב שגוי של זמן ההעברה',
                'explanation': 'התשובה הנכונה היא 5ms (או 3.33ms)',
                'points': -10,
            },
            'q2_no_calculation': {
                'description': 'Question 2: Missing calculation/explanation',
                'hebrew_description': 'שאלה 2: חסר חישוב/הסבר',
                'explanation': 'יש להציג את החישוב המלא לכל שלב',
                'points': -5,
            },
            'pdf_not_found': {
                'description': 'PDF file (os4.pdf) not found',
                'hebrew_description': 'קובץ PDF (os4.pdf) לא נמצא',
                'explanation': 'יש להגיש קובץ os4.pdf עם התשובות לחלק ב',
                'points': -20,
            },
            'pdf_read_error': {
                'description': 'Could not read PDF file',
                'hebrew_description': 'לא ניתן לקרוא את קובץ ה-PDF',
                'explanation': 'בעיה בקריאת הקובץ',
                'points': -20,
            },
        }
    
    def extract_pdf_text(self, pdf_path):
        """Extract text from PDF file"""
        if not PDF_SUPPORT:
            return None
        
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return None
    
    def find_pdf_file(self, student_folder):
        """Find os4.pdf in student folder (including extracted tar contents)"""
        # Look for os4.pdf directly
        for root, dirs, files in os.walk(student_folder):
            for f in files:
                if f.lower() == 'os4.pdf':
                    return os.path.join(root, f)
        return None
    
    def extract_numbers_from_text(self, text):
        """Extract all numbers from text"""
        # Find integers and decimals
        numbers = re.findall(r'[\d,]+\.?\d*', text)
        result = []
        for num in numbers:
            try:
                # Remove commas
                clean_num = num.replace(',', '')
                if '.' in clean_num:
                    result.append(float(clean_num))
                else:
                    result.append(int(clean_num))
            except ValueError:
                pass
        return result
    
    def check_q1_answer(self, text):
        """
        Check Question 1: Total disk storage in blocks
        Correct: 225,000 blocks (or 1,800,000 sectors)
        """
        numbers = self.extract_numbers_from_text(text)
        
        # Check if correct answer appears
        has_correct_blocks = self.q1_correct_blocks in numbers or 225000 in numbers
        has_correct_sectors = self.q1_correct_sectors in numbers or 1800000 in numbers
        
        # Also check for variations like 300000 (per surface)
        has_per_surface = 300000 in numbers
        
        # Check for key calculation elements
        text_lower = text.lower()
        has_calculation = any(x in text for x in [
            '(1200+800+600+400)',
            '1200+800+600+400',
            '3000',  # sum of sectors per track
            '300,000', '300000',  # sectors per surface
        ])
        
        results = {
            'correct_answer': has_correct_blocks or has_correct_sectors,
            'has_calculation': has_calculation or has_per_surface,
            'found_values': {
                'blocks': has_correct_blocks,
                'sectors': has_correct_sectors,
            }
        }
        
        return results
    
    def check_q2_answer(self, text):
        """
        Check Question 2: Maximum transfer time for last stage
        Correct: 5ms (transferring 200 sectors in zone B at 800 sectors/track)
        Alternative: 3.33ms (continuing in zone A)
        """
        numbers = self.extract_numbers_from_text(text)
        
        # Check for correct answers (5ms or ~3.33ms)
        has_5ms = 5 in numbers or 5.0 in numbers
        has_3_33ms = any(abs(n - 3.33) < 0.1 for n in numbers if isinstance(n, (int, float)))
        
        # Check for key calculation elements
        has_calculation = any(x in text for x in [
            '20ms', '20 ms',  # rotation time
            '10ms', '10 ms',  # half rotation for 300KB
            '600',  # sectors for 300KB
            '200',  # sectors for 100KB
            '800',  # sectors per track in zone B
            '1200', # sectors per track in zone A
        ])
        
        # Check for zone identification
        has_zone_analysis = any(x in text.lower() for x in [
            'zone a', 'zona', 'אזור a', 'אזור b',
            'שטח a', 'שטח b', 'איזור',
        ])
        
        results = {
            'correct_answer': has_5ms or has_3_33ms,
            'has_5ms': has_5ms,
            'has_3_33ms': has_3_33ms,
            'has_calculation': has_calculation,
            'has_zone_analysis': has_zone_analysis,
        }
        
        return results
    
    def analyze_pdf(self, student_folder):
        """Analyze a student's PDF submission for Part B"""
        results = {
            'pdf_found': False,
            'pdf_readable': False,
            'q1_results': None,
            'q2_results': None,
            'errors': [],
            'pdf_text': None,
        }
        
        # Find PDF
        pdf_path = self.find_pdf_file(student_folder)
        if not pdf_path:
            results['errors'].append('pdf_not_found')
            return results
        
        results['pdf_found'] = True
        
        # Extract text
        text = self.extract_pdf_text(pdf_path)
        if text is None:
            results['errors'].append('pdf_read_error')
            return results
        
        results['pdf_readable'] = True
        results['pdf_text'] = text
        
        # Check answers
        results['q1_results'] = self.check_q1_answer(text)
        results['q2_results'] = self.check_q2_answer(text)
        
        # Determine errors
        if not results['q1_results']['correct_answer']:
            results['errors'].append('q1_wrong_answer')
        elif not results['q1_results']['has_calculation']:
            results['errors'].append('q1_no_calculation')
        
        if not results['q2_results']['correct_answer']:
            results['errors'].append('q2_wrong_answer')
        elif not results['q2_results']['has_calculation']:
            results['errors'].append('q2_no_calculation')
        
        return results
    
    def calculate_deductions(self, analysis_results):
        """Calculate point deductions based on analysis results"""
        deductions = []
        total_deduction = 0
        
        for error in analysis_results.get('errors', []):
            if error in self.part_b_criteria:
                criteria = self.part_b_criteria[error]
                deductions.append({
                    'error': error,
                    'description': criteria['description'],
                    'hebrew_description': criteria['hebrew_description'],
                    'points': criteria['points'],
                })
                total_deduction += abs(criteria['points'])
        
        return deductions, total_deduction


class SubmissionChecker:
    def __init__(self):
        # Initialize Part B checker
        self.part_b_checker = PartBChecker() if PDF_SUPPORT else None
        
        self.deduction_criteria = {
            'missing_memory_cleanup': {
                'description': 'Missing kfree() calls for allocated memory',
                'hebrew_description': 'חסרה קריאה ל-kfree() לזיכרון שהוקצה',
                'explanation': 'כל קריאה ל-kmalloc() חייבת להיות מלווה בקריאה מתאימה ל-kfree() כדי למנוע זליגת זיכרון',
                'severity': 'major',
                'points': -5,
                'pattern': None
            },
            'missing_unregister': {
                'description': 'Missing unregister_chrdev() in cleanup_module',
                'hebrew_description': 'חסרה קריאה ל-unregister_chrdev() ב-cleanup_module',
                'explanation': 'המודול חייב לבטל את הרישום שלו בעת ההתנתקות כדי למנוע בעיות במערכת',
                'severity': 'major',
                'points': -5,
                'pattern': None
            },
            'shared_encryption_key': {
                'description': 'Encryption key shared between file instances',
                'hebrew_description': 'מפתח הצפנה משותף בין instance-ים של קבצים',
                'explanation': 'כל פתיחה של קובץ צריכה להיות עם מפתח הצפנה נפרד, לא משותף עם פתיחות אחרות של אותו device',
                'severity': 'major',
                'points': -8,
                'pattern': None
            },
            'no_parameter_validation': {
                'description': 'Missing validation for size/count parameters',
                'hebrew_description': 'חסרת בדיקת תקינות לפרמטרים size/count',
                'explanation': 'פרמטרי המודול size ו-count חייבים להיבדק שהם חיוביים לפני השימוש בהם',
                'severity': 'minor',
                'points': -2,
                'pattern': None
            },
            'no_minor_validation': {
                'description': 'Missing minor number validation in device_open',
                'hebrew_description': 'חסרת בדיקת תקינות למספר minor ב-device_open',
                'explanation': 'צריך לוודא שמספר ה-minor נמצא בטווח החוקי (0 עד count-1)',
                'severity': 'minor',
                'points': -2,
                'pattern': None
            },
            'no_register_error_check': {
                'description': 'Missing error checking for register_chrdev return value',
                'hebrew_description': 'חסרת בדיקת שגיאה לערך החזרה של register_chrdev',
                'explanation': 'צריך לבדוק את ערך ההחזרה של register_chrdev ולטפל בכישלון',
                'severity': 'minor',
                'points': -2,
                'pattern': None
            },
            'missing_required_functions': {
                'description': 'Missing required file operations or module functions',
                'hebrew_description': 'חסרות פונקציות נדרשות של file operations או module',
                'explanation': 'המודול חייב לכלול את כל הפונקציות הנדרשות: open, release, read, write, ioctl, llseek',
                'severity': 'major',
                'points': -9,
                'pattern': None
            },
            'different_function_names': {
                'description': 'Different function names used in init_module or cleanup_module',
                'hebrew_description': 'שמות פונקציות שונים בשימוש בפעולות קובץ',
                'explanation': 'יש להשתמש בשמות הפונקציות הנכונים: init_module, cleanup_module',
                'severity': 'minor',
                'points': -1,
                'pattern': None
            },
            'no_allocation_error_handling': {
                'description': 'Missing error handling for memory allocation failures',
                'hebrew_description': 'חסר טיפול בשגיאות הקצאת זיכרון',
                'explanation': 'צריך לבדוק את ערך ההחזרה של kmalloc ולשחרר זיכרון שכבר הוקצה במקרה של כישלון',
                'severity': 'minor',
                'points': -3,
                'pattern': None
            },
            'wrong_ioctl_command': {
                'description': 'Using wrong IOCTL command name (should be IOCTL_XOR_KEY)',
                'hebrew_description': 'שימוש שגוי בשם פקודת IOCTL (צריך להיות IOCTL_XOR_KEY)',
                'explanation': 'צריך להשתמש ב-IOCTL_XOR_KEY ולבדוק טווח ערכים 0-255',
                'severity': 'minor',
                'points': -2,
                'pattern': None
            },
            'wrong_initial_key': {
                'description': 'Initial encryption key should be 0xFF (not 0)',
                'hebrew_description': 'מפתח הצפנה התחלתי צריך להיות 0xFF (לא 0)',
                'explanation': 'בכל פתיחה של קובץ התקן יאותחל מפתח הצפנה עם ערך 0xFF',
                'severity': 'minor',
                'points': -3,
                'pattern': None
            },
            'wrong_encryption_method': {
                'description': 'Should use XOR encryption (not Caesar cipher)',
                'hebrew_description': 'צריך להשתמש בהצפנת XOR (לא צופן קיסר)',
                'explanation': 'ההצפנה היא צופן XOR, כך שלכל בית שנכתב לרכיב או נקרא ממנו מתבצע XOR עם מפתח ההצפנה',
                'severity': 'major',
                'points': -5,
                'pattern': None
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
    
    def find_os4mod_c(self, directory):
        """Find os4mod.c file in the extracted directory"""
        for root, dirs, files in os.walk(directory):
            if 'os4mod.c' in files:
                return os.path.join(root, 'os4mod.c')
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
        kmalloc_patterns = [r'kmalloc\s*\(', r'kmalloc_array\s*\(']
        kmalloc_count = 0
        for pattern in kmalloc_patterns:
            kmalloc_count += len(re.findall(pattern, content))
        
        kfree_count = len(re.findall(r'kfree\s*\(', content))
        
        cleanup_func = re.search(r'void\s+cleanup_module\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        release_func = re.search(r'int\s+device_release\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        has_cleanup_kfree = False
        has_release_kfree = False
        
        if cleanup_func and 'kfree(' in cleanup_func.group(1):
            has_cleanup_kfree = True
            
        if release_func and 'kfree(' in release_func.group(1):
            has_release_kfree = True
        
        device_open_func = re.search(r'static\s+int\s+device_open\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        has_open_kmalloc = False
        if device_open_func and re.search(r'kmalloc\s*\(', device_open_func.group(1)):
            has_open_kmalloc = True
        
        init_func = re.search(r'int\s+init_module\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        has_init_kmalloc = False
        if init_func and re.search(r'kmalloc[_\w]*\s*\(', init_func.group(1)):
            has_init_kmalloc = True
        
        if has_open_kmalloc and not has_release_kfree:
            return True
            
        if has_init_kmalloc and not has_cleanup_kfree:
            return True
            
        if kmalloc_count > 0 and kfree_count == 0:
            return True
            
        return False
    
    def check_missing_unregister(self, content):
        """Check if cleanup_module calls unregister_chrdev"""
        if 'unregister_chrdev' in content:
            return False
        return True

    def check_shared_encryption_key(self, content):
        """Check if encryption key is shared (global/static) instead of per-file"""
        return False  # Complex check - keeping disabled as in 2025
    
    def check_no_parameter_validation(self, content):
        """Check if size and count parameters are validated"""
        init_func = re.search(r'int\s+init_module\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        if init_func:
            func_content = init_func.group(1)
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
            has_minor_check = bool(re.search(r'minor\s*[<>]=?\s*count|if\s*\([^)]*minor[^)]*\)', func_content))
            
            if not has_minor_check:
                return True
                
        return False
    
    def check_no_register_error_check(self, content):
        """Check if register_chrdev return value is checked"""
        if 'register_chrdev' in content:
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
        ]
        
        missing_functions = []
        for func in required_functions:
            if not re.search(f'{func}', content):
                missing_functions.append(func)
        
        if missing_functions:
            return True
            
        return False
    
    def check_different_function_names(self, content):
        """Check if init_module or cleanup_module have different names"""
        # Check for direct init_module and cleanup_module
        has_init_module = bool(re.search(r'\bint\s+init_module\s*\(', content))
        has_cleanup_module = bool(re.search(r'\bvoid\s+cleanup_module\s*\(', content))
        
        # Check for modern module_init/module_exit macros (also valid)
        has_module_init_macro = bool(re.search(r'module_init\s*\(', content))
        has_module_exit_macro = bool(re.search(r'module_exit\s*\(', content))
        
        # Accept either approach: direct functions OR macros
        has_valid_init = has_init_module or has_module_init_macro
        has_valid_cleanup = has_cleanup_module or has_module_exit_macro
        
        # Only flag as error if neither valid pattern is found
        if not has_valid_init or not has_valid_cleanup:
            return True
        
        return False
    
    def check_wrong_ioctl_command(self, content):
        """Check if using wrong IOCTL command name (should be IOCTL_XOR_KEY)"""
        # For 2026: should use IOCTL_XOR_KEY
        # Extract device_ioctl function with proper handling of nested braces
        match = re.search(r'static\s+long\s+device_ioctl\s*\([^)]*\)\s*\{', content, re.DOTALL)
        if match:
            start = match.end() - 1  # Include the opening brace
            brace_count = 0
            pos = start
            while pos < len(content):
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        func_content = content[start+1:pos]  # Get content between braces
                        break
                pos += 1
        else:
            func_content = None
        
        # Check if IOCTL_XOR_KEY is defined
        has_xor_key = bool(re.search(r'IOCTL_XOR_KEY|IOCTL_SET_XOR|XOR_KEY', content, re.IGNORECASE))
        
        # Check if using old Caesar cipher command name
        if 'IOCTL_SET_KEY' in content and not has_xor_key:
            return True  # Using old command from 2025
            
        if 'IOCTL_SET_VAL' in content:
            return True  # Wrong generic command
        
        if func_content:
            has_range_check = bool(re.search(r'arg\s*[<>]=?\s*255|arg\s*[<>]=?\s*0|\(arg\s*[<>]|255.*arg|0.*arg', func_content))
            
            if not has_range_check:
                return True
                
        return False
    
    def check_no_allocation_error_handling(self, content):
        """Check if kmalloc return values are checked for errors"""
        kmalloc_calls = re.findall(r'(\w+)\s*=\s*kmalloc[_\w]*\s*\([^)]*\)', content)
        
        if not kmalloc_calls:
            return False
        
        for var_name in kmalloc_calls:
            error_check_patterns = [
                f'if\\s*\\(\\s*!{var_name}\\s*\\)',
                f'if\\s*\\(\\s*{var_name}\\s*==\\s*NULL\\s*\\)',
                f'if\\s*\\(\\s*{var_name}\\s*==\\s*0\\s*\\)',
                f'if\\s*\\(!{var_name}\\)',
                f'if\\s*\\({var_name}\\s*==\\s*-1\\)',
                f'return\\s+-1',
                f'return\\s+-ENOMEM'
            ]
            
            has_error_check = any(re.search(pattern, content) for pattern in error_check_patterns)
            
            if not has_error_check:
                return True
                
        return False
    
    def check_wrong_initial_key(self, content):
        """Check if initial key is 0xFF (required for 2026)"""
        # Look for key initialization in device_open
        device_open_func = re.search(r'static\s+int\s+device_open\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        if device_open_func:
            func_content = device_open_func.group(1)
            # Check for 0xFF initialization
            has_correct_init = bool(re.search(r'key\s*=\s*(0[xX][fF]{2}|255|0xFF)', func_content))
            has_zero_init = bool(re.search(r'key\s*=\s*0\s*[;\)]', func_content))
            
            if has_zero_init and not has_correct_init:
                return True  # Using 0 instead of 0xFF
        
        # Also check struct initialization
        struct_init = re.search(r'\.key\s*=\s*(0[xX][fF]{2}|255|0xFF)', content)
        struct_zero = re.search(r'\.key\s*=\s*0\s*[,}]', content)
        
        if struct_zero and not struct_init:
            return True
                
        return False
    
    def check_wrong_encryption_method(self, content):
        """Check if XOR encryption is used (not Caesar cipher)"""
        # Look for XOR operations in read/write functions
        # Match patterns like: val ^ key, val ^= key, val ^ session->key, etc.
        has_xor = bool(re.search(r'\^=|\^[\s\w>.-]*key|XOR|xor', content, re.IGNORECASE))
        
        # Look for Caesar cipher operations (add/subtract)
        # This is a heuristic - looking for data[i] + key or data[i] - key patterns
        has_caesar_add = bool(re.search(r'\[\s*\w+\s*\]\s*\+\s*key|\[\s*\w+\s*\]\s*\+=\s*key', content))
        has_caesar_sub = bool(re.search(r'\[\s*\w+\s*\]\s*-\s*key|\[\s*\w+\s*\]\s*-=\s*key', content))
        
        # If using Caesar but not XOR
        if (has_caesar_add or has_caesar_sub) and not has_xor:
            return True
        
        # If no encryption at all - check read/write functions specifically
        if not has_xor and not has_caesar_add and not has_caesar_sub:
            # Only flag as error if we have read/write functions but no encryption
            has_read_write = bool(re.search(r'device_read|device_write', content))
            if has_read_write:
                return True  # Has read/write but no clear encryption
        
        return False
    
    def analyze_submission(self, content):
        """Analyze a single submission for all deduction criteria"""
        results = {}
        
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
        results['wrong_initial_key'] = self.check_wrong_initial_key(content)
        results['wrong_encryption_method'] = self.check_wrong_encryption_method(content)
        
        return results
    
    def process_student_folder(self, student_folder):
        """Process a single student's folder (Part A: code, Part B: PDF)"""
        student_name = os.path.basename(student_folder)
        
        # Initialize results structure
        combined_results = {
            'part_a': None,
            'part_b': None,
            'part_a_error': None,
            'part_b_error': None,
        }
        
        # ============ PART A: Code Analysis ============
        # First, check if os4mod.c already exists in the student folder
        os4mod_path = self.find_os4mod_c(student_folder)
        
        if not os4mod_path:
            # os4mod.c not found, look for tar.gz file to extract
            tar_files = [f for f in os.listdir(student_folder) if f.endswith('.tar.gz')]
            
            if not tar_files:
                combined_results['part_a_error'] = "No os4mod.c or tar.gz file found"
            elif len(tar_files) > 1:
                combined_results['part_a_error'] = "Multiple tar.gz files found"
            else:
                tar_path = os.path.join(student_folder, tar_files[0])
                
                # Extract tar file directly into student folder
                if not self.extract_tar_file(tar_path, student_folder):
                    combined_results['part_a_error'] = "Failed to extract tar file"
                else:
                    # Now look for os4mod.c in the student folder (including newly extracted files)
                    os4mod_path = self.find_os4mod_c(student_folder)
                    if not os4mod_path:
                        combined_results['part_a_error'] = "os4mod.c not found even after extraction"
        
        if os4mod_path and combined_results['part_a_error'] is None:
            content = self.read_file_content(os4mod_path)
            if content is None:
                combined_results['part_a_error'] = "Failed to read os4mod.c"
            else:
                combined_results['part_a'] = self.analyze_submission(content)
        
        # ============ PART B: PDF Analysis ============
        if self.part_b_checker:
            part_b_analysis = self.part_b_checker.analyze_pdf(student_folder)
            combined_results['part_b'] = part_b_analysis
            if part_b_analysis.get('errors'):
                combined_results['part_b_error'] = part_b_analysis['errors']
        else:
            combined_results['part_b_error'] = "PDF support not available"
        
        return student_name, combined_results, None
    
    def process_all_submissions(self, general_folder):
        """Process all submissions in the general folder"""
        results = {}
        
        if not os.path.exists(general_folder):
            print(f"Error: General folder '{general_folder}' does not exist")
            return results
        
        student_folders = [f for f in os.listdir(general_folder) 
                          if os.path.isdir(os.path.join(general_folder, f))]
        
        print(f"Found {len(student_folders)} student folders")
        
        for student_folder in student_folders:
            student_path = os.path.join(general_folder, student_folder)
            student_name, analysis_results, error = self.process_student_folder(student_path)
            
            results[student_name] = analysis_results
        
        return results
    
    def generate_report(self, results):
        """Generate a detailed report of all findings (Part A + Part B)"""
        print(f"\n{'='*70}")
        print("GRADING RESULTS (Part A: Code + Part B: PDF)")
        print(f"{'='*70}")
        
        total_students = len(results)
        
        # Issue counts for Part A
        part_a_issue_counts = {criteria: 0 for criteria in self.deduction_criteria.keys()}
        
        # Issue counts for Part B
        part_b_issue_counts = {}
        if self.part_b_checker:
            part_b_issue_counts = {criteria: 0 for criteria in self.part_b_checker.part_b_criteria.keys()}
        
        student_grades = {}
        student_errors = {}
        
        part_a_max = 50  # Part A is worth 50 points
        part_b_max = 50  # Part B is worth 50 points
        
        for student_name, student_results in results.items():
            part_a_points = 0
            part_b_points = 0
            errors = []
            
            # ============ Process Part A ============
            if student_results.get('part_a_error'):
                errors.append(f"[Part A] Processing Error: {student_results['part_a_error']}")
                part_a_points += 50  # Major penalty for no code
            elif student_results.get('part_a'):
                for issue, found in student_results['part_a'].items():
                    if found and issue in self.deduction_criteria:
                        criteria = self.deduction_criteria[issue]
                        part_a_points += abs(criteria['points'])
                        errors.append(f"[Part A] {criteria['description']} ({criteria['points']})")
                        part_a_issue_counts[issue] += 1
            
            # ============ Process Part B ============
            if student_results.get('part_b_error') == "PDF support not available":
                pass  # Skip if no PDF support
            elif student_results.get('part_b'):
                part_b = student_results['part_b']
                for error_code in part_b.get('errors', []):
                    if self.part_b_checker and error_code in self.part_b_checker.part_b_criteria:
                        criteria = self.part_b_checker.part_b_criteria[error_code]
                        part_b_points += abs(criteria['points'])
                        errors.append(f"[Part B] {criteria['description']} ({criteria['points']})")
                        part_b_issue_counts[error_code] = part_b_issue_counts.get(error_code, 0) + 1
            
            # Calculate grades out of 50 each
            part_a_grade = max(0, part_a_max - part_a_points)
            part_b_grade = max(0, part_b_max - part_b_points)
            total_grade = part_a_grade + part_b_grade
            
            student_grades[student_name] = total_grade
            student_errors[student_name] = errors
            
            # Store separate Part A and Part B grades (out of 50 each)
            student_results['_part_a_grade'] = part_a_grade
            student_results['_part_b_grade'] = part_b_grade
        
        # Print per-student results
        for student_name in sorted(student_grades.keys()):
            grade = student_grades[student_name]
            errors = student_errors[student_name]
            
            print(f"\n{'─'*70}")
            print(f"Student: {student_name}")
            print(f"  Grade: {grade}/100")
            
            if errors:
                print(f"  Errors:")
                for error in errors:
                    print(f"    • {error}")
            else:
                print(f"  ✓ No errors found")
        
        # Collect Part A and Part B grades for distribution
        part_a_grades = {name: results[name].get('_part_a_grade', 100) for name in student_grades.keys()}
        part_b_grades = {name: results[name].get('_part_b_grade', 100) for name in student_grades.keys()}
        
        # Statistics - combine Part A and Part B issue counts
        all_issue_counts = {**part_a_issue_counts, **part_b_issue_counts}
        self.print_statistics(student_grades, all_issue_counts, total_students, part_a_grades, part_b_grades)
    
    def print_statistics(self, student_grades, issue_counts, total_students, part_a_grades=None, part_b_grades=None):
        """Print grading statistics like os3_grader"""
        scores = list(student_grades.values())
        scores.sort()
        n = len(scores)
        
        if n == 0:
            return
        
        median = scores[n//2] if n % 2 == 1 else (scores[n//2-1] + scores[n//2]) / 2
        
        print(f"\n{'='*70}")
        print("GRADING STATISTICS")
        print(f"{'='*70}")
        
        print(f"\nTotal Students: {n}")
        print(f"Median Score: {median:.1f}/100")
        print(f"Average Score: {sum(scores)/n:.1f}/100")
        print(f"Highest Score: {max(scores)}/100")
        print(f"Lowest Score: {min(scores)}/100")
        
        # Overall Score distribution
        print(f"\n{'─'*70}")
        print("OVERALL SCORE DISTRIBUTION")
        print(f"{'─'*70}")
        ranges = [
            (90, 100, "90-100"),
            (80, 89, "80-89"),
            (70, 79, "70-79"),
            (60, 69, "60-69"),
            (50, 59, "50-59"),
            (0, 49, "0-49")
        ]
        for low, high, label in ranges:
            count = sum(1 for s in scores if low <= s <= high)
            percentage = (count / n * 100) if n > 0 else 0
            bar = '█' * int(percentage / 2)
            print(f"  {label:>8}: {count:3} students ({percentage:5.1f}%) {bar}")
        
        # Part A Score distribution (out of 50)
        if part_a_grades:
            part_a_scores = list(part_a_grades.values())
            part_a_scores.sort()
            part_a_median = part_a_scores[n//2] if n % 2 == 1 else (part_a_scores[n//2-1] + part_a_scores[n//2]) / 2
            
            print(f"\n{'─'*70}")
            print("PART A (Code) SCORE DISTRIBUTION (Out of 50)")
            print(f"{'─'*70}")
            print(f"  Median: {part_a_median:.1f}/50 | Average: {sum(part_a_scores)/n:.1f}/50")
            part_a_ranges = [
                (45, 50, "45-50"),
                (40, 44, "40-44"),
                (35, 39, "35-39"),
                (30, 34, "30-34"),
                (25, 29, "25-29"),
                (0, 24, "0-24")
            ]
            for low, high, label in part_a_ranges:
                count = sum(1 for s in part_a_scores if low <= s <= high)
                percentage = (count / n * 100) if n > 0 else 0
                bar = '█' * int(percentage / 2)
                print(f"  {label:>8}: {count:3} students ({percentage:5.1f}%) {bar}")
        
        # Part B Score distribution (out of 50)
        if part_b_grades:
            part_b_scores = list(part_b_grades.values())
            part_b_scores.sort()
            part_b_median = part_b_scores[n//2] if n % 2 == 1 else (part_b_scores[n//2-1] + part_b_scores[n//2]) / 2
            
            print(f"\n{'─'*70}")
            print("PART B (PDF) SCORE DISTRIBUTION (Out of 50)")
            print(f"{'─'*70}")
            print(f"  Median: {part_b_median:.1f}/50 | Average: {sum(part_b_scores)/n:.1f}/50")
            part_b_ranges = [
                (45, 50, "45-50"),
                (40, 44, "40-44"),
                (35, 39, "35-39"),
                (30, 34, "30-34"),
                (25, 29, "25-29"),
                (0, 24, "0-24")
            ]
            for low, high, label in part_b_ranges:
                count = sum(1 for s in part_b_scores if low <= s <= high)
                percentage = (count / n * 100) if n > 0 else 0
                bar = '█' * int(percentage / 2)
                print(f"  {label:>8}: {count:3} students ({percentage:5.1f}%) {bar}")
        
        # Most common errors - Part A
        print(f"\n{'─'*70}")
        print("MOST COMMON ERRORS - PART A (Code)")
        print(f"{'─'*70}")
        
        part_a_issues = {k: v for k, v in issue_counts.items() if k in self.deduction_criteria}
        sorted_issues = sorted(part_a_issues.items(), key=lambda x: x[1], reverse=True)
        for i, (issue, count) in enumerate(sorted_issues, 1):
            if count > 0:
                criteria = self.deduction_criteria[issue]
                percentage = (count / n * 100) if n > 0 else 0
                print(f"  {i:2}. {criteria['description']:50} → {count:3}x ({percentage:5.1f}%)")
        
        # Most common errors - Part B
        if self.part_b_checker:
            print(f"\n{'─'*70}")
            print("MOST COMMON ERRORS - PART B (PDF)")
            print(f"{'─'*70}")
            
            part_b_issues = {k: v for k, v in issue_counts.items() if k in self.part_b_checker.part_b_criteria}
            sorted_issues = sorted(part_b_issues.items(), key=lambda x: x[1], reverse=True)
            for i, (issue, count) in enumerate(sorted_issues, 1):
                if count > 0:
                    criteria = self.part_b_checker.part_b_criteria[issue]
                    percentage = (count / n * 100) if n > 0 else 0
                    print(f"  {i:2}. {criteria['description']:50} → {count:3}x ({percentage:5.1f}%)")
        
        # 10 lowest graded students
        print(f"\n{'─'*70}")
        print("10 LOWEST GRADED STUDENTS")
        print(f"{'─'*70}")
        
        sorted_students = sorted(student_grades.items(), key=lambda x: x[1])
        for i, (name, grade) in enumerate(sorted_students[:10], 1):
            print(f"  {i:2}. {name:40} → {grade:3}/100")
        
        print(f"{'='*70}\n")
    
    def generate_csv_report(self, results, output_dir=None):
        """Generate a CSV report with detailed results (Part A + Part B)"""
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create grading_results folder
        output_dir = os.path.join(output_dir, 'grading_results')
        os.makedirs(output_dir, exist_ok=True)
        
        csv_data = []
        
        for student_name, student_results in results.items():
            total_points = 0
            part_a_errors = []
            part_b_errors = []
            
            # Process Part A
            if student_results.get('part_a_error'):
                part_a_errors.append(f"Error: {student_results['part_a_error']}")
                total_points += 50
            elif student_results.get('part_a'):
                for issue, found in student_results['part_a'].items():
                    if found and issue in self.deduction_criteria:
                        criteria = self.deduction_criteria[issue]
                        points_deducted = abs(criteria['points'])
                        total_points += points_deducted
                        part_a_errors.append(f"{criteria['description']} ({criteria['points']})")
            
            # Process Part B
            part_b_q1_correct = False
            part_b_q2_correct = False
            
            if student_results.get('part_b'):
                part_b = student_results['part_b']
                
                if part_b.get('q1_results'):
                    part_b_q1_correct = part_b['q1_results'].get('correct_answer', False)
                if part_b.get('q2_results'):
                    part_b_q2_correct = part_b['q2_results'].get('correct_answer', False)
                
                for error_code in part_b.get('errors', []):
                    if self.part_b_checker and error_code in self.part_b_checker.part_b_criteria:
                        criteria = self.part_b_checker.part_b_criteria[error_code]
                        points_deducted = abs(criteria['points'])
                        total_points += points_deducted
                        part_b_errors.append(f"{criteria['description']} ({criteria['points']})")
            
            # Get grades from stored values (out of 50 each)
            part_a_grade = student_results.get('_part_a_grade', 50)
            part_b_grade = student_results.get('_part_b_grade', 50)
            total_grade = part_a_grade + part_b_grade
            
            row = {
                'Student': student_name,
                'Grade': total_grade,
                'Part_A_Grade': part_a_grade,
                'Part_B_Grade': part_b_grade,
                'Part_B_Q1_Correct': 'Yes' if part_b_q1_correct else 'No',
                'Part_B_Q2_Correct': 'Yes' if part_b_q2_correct else 'No',
                'Part_A_Errors': '; '.join(part_a_errors) if part_a_errors else '',
                'Part_B_Errors': '; '.join(part_b_errors) if part_b_errors else '',
            }
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"hw4_grades_{timestamp}.csv"
        csv_path = os.path.join(output_dir, csv_filename)
        
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        return csv_path
    


def main(folder_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    general_folder = os.path.join(current_dir, folder_name)
    
    if len(sys.argv) == 2:
        general_folder = sys.argv[1]
    
    print(f"Grading HW4 submissions in: {general_folder}")
    
    checker = SubmissionChecker()
    results = checker.process_all_submissions(general_folder)
    checker.generate_report(results)
    
    try:
        csv_path = checker.generate_csv_report(results, current_dir)
        print(f"✓ CSV report saved: {csv_path}")
    except ImportError:
        print("Error: pandas required. Install with: pip install pandas")
    except Exception as e:
        print(f"Error generating CSV: {e}")


if __name__ == "__main__":
    main("submissions")
    # main("subs")
