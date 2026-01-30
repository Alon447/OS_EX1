#!/usr/bin/env python3
"""
Kernel Module Homework Checker
Automatically checks student submissions for the second part of the OS homework.
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
from datetime import datetime
from openpyxl.styles import Alignment

class KernelModuleChecker:
    def __init__(self):
        self.required_files = ['mymod.c', 'Makefile', 'mymod.sh']
        self.syscall_numbers = {
            '__NR_mkdir': 'mkdir',
            '__NR_chdir': 'chdir', 
            '__NR_close': 'close',
            '__NR_dup': 'dup'
        }
        self.results = {}
        
        # Define deduction criteria with the same structure as hw_checker
        self.deduction_criteria = {
            'missing_files': {
                'description': 'Missing required files (mymod.c, Makefile, mymod.sh)',
                'hebrew_description': 'קבצים חסרים (mymod.c, Makefile, mymod.sh)',
                'explanation': 'כל הקבצים הנדרשים חייבים להיות קיימים',
                'severity': 'major',
                'points': -4,
                'max_score': 4
            },
            'missing_includes': {
                'description': 'Missing required kernel includes',
                'hebrew_description': 'חסרים include-ים נדרשים לקרנל',
                'explanation': 'חובה לכלול את הכותרות הנדרשות למודול קרנל',
                'severity': 'major',
                'points': -3,
                'max_score': 3
            },
            'missing_gpl_license': {
                'description': 'Missing GPL license declaration',
                'hebrew_description': 'חסר הגדרת רישיון GPL',
                'explanation': 'מודולי קרנל חייבים להכיל הגדרת רישיון GPL',
                'severity': 'major',
                'points': -3,
                'max_score': 3
            },
            'missing_init_cleanup': {
                'description': 'Missing init and cleanup functions',
                'hebrew_description': 'חסרות פונקציות init ו-cleanup',
                'explanation': 'כל מודול קרנל חייב להכיל פונקציות אתחול וניקוי',
                'severity': 'major',
                'points': -2,
                'max_score': 2
            },
            'missing_sysnr_param': {
                'description': 'Missing sysnr parameter',
                'hebrew_description': 'חסר פרמטר sysnr',
                'explanation': 'חובה להגדיר פרמטר sysnr למספר קריאת המערכת',
                'severity': 'major',
                'points': -2,
                'max_score': 2
            },
            'missing_msg_param': {
                'description': 'Missing msg parameter',
                'hebrew_description': 'חסר פרמטר msg',
                'explanation': 'חובה להגדיר פרמטר msg להודעה',
                'severity': 'major',
                'points': -2,
                'max_score': 2
            },
            'missing_function_pointers': {
                'description': 'Missing function pointer declarations',
                'hebrew_description': 'חסרות הגדרות מצביעי פונקציות',
                'explanation': 'חובה להגדיר מצביעי פונקציות לשמירת קריאות המערכת המקוריות',
                'severity': 'major',
                'points': -3,
                'max_score': 3
            },
            'missing_syscall_checks': {
                'description': 'Missing syscall number validation',
                'hebrew_description': 'חסרת בדיקת מספרי קריאות מערכת',
                'explanation': 'חובה לבדוק את מספר קריאת המערכת ולוודא שהוא תקין',
                'severity': 'major',
                'points': -4,
                'max_score': 4
            },
            'missing_error_handling': {
                'description': 'Missing invalid syscall error handling',
                'hebrew_description': 'חסרת טיפול במספר קריאת מערכת לא תקין',
                'explanation': 'יש לטפל במקרה של מספר קריאת מערכת לא תקין',
                'severity': 'major',
                'points': -3,
                'max_score': 3
            },
            'missing_syscall_table': {
                'description': 'Missing syscall table manipulation',
                'hebrew_description': 'חסרת מניפולציה של טבלת קריאות המערכת',
                'explanation': 'חובה לבצע מניפולציה של טבלת קריאות המערכת',
                'severity': 'major',
                'points': -4,
                'max_score': 4
            },
            'missing_user_copy': {
                'description': 'Missing user memory copying',
                'hebrew_description': 'חסרת העתקת זיכרון ממשתמש',
                'explanation': 'חובה להעתיק נתונים מזיכרון המשתמש לזיכרון הקרנל',
                'severity': 'major',
                'points': -3,
                'max_score': 3
            },
            'missing_kern_info': {
                'description': 'Missing KERN_INFO in printk calls',
                'hebrew_description': 'חסר KERN_INFO בקריאות printk',
                'explanation': 'יש להשתמש ב-KERN_INFO בקריאות printk',
                'severity': 'minor',
                'points': -1,
                'max_score': 1
            },
            'wrong_buffer_size': {
                'description': 'Incorrect buffer size',
                'hebrew_description': 'גודל באפר שגוי',
                'explanation': 'גודל הבאפר צריך להיות 16',
                'severity': 'minor',
                'points': -1,
                'max_score': 1
            },
            'missing_string_termination': {
                'description': 'Missing string null termination',
                'hebrew_description': 'חסרת סיום מחרוזת עם null',
                'explanation': 'חובה לסיים מחרוזות עם תו null',
                'severity': 'minor',
                'points': -1,
                'max_score': 1
            },
            'missing_3sec_sleep': {
                'description': 'Missing 3 second sleep',
                'hebrew_description': 'חסרת המתנה של 3 שניות',
                'explanation': 'חובה להמתין 3 שניות כפי שנדרש',
                'severity': 'major',
                'points': -2,
                'max_score': 2
            },
            'makefile_missing_obj': {
                'description': 'Makefile missing obj-m target',
                'hebrew_description': 'חסר obj-m ב-Makefile',
                'explanation': 'ה-Makefile חייב להכיל obj-m למודול קרנל',
                'severity': 'major',
                'points': -3,
                'max_score': 3
            },
            'makefile_missing_module_ref': {
                'description': 'Makefile missing module reference',
                'hebrew_description': 'חסרת התייחסות למודול ב-Makefile',
                'explanation': 'ה-Makefile חייב להתייחס למודול mymod',
                'severity': 'major',
                'points': -3,
                'max_score': 3
            },
            'makefile_missing_clean': {
                'description': 'Makefile missing clean target',
                'hebrew_description': 'חסר clean target ב-Makefile',
                'explanation': 'ה-Makefile חייב להכיל clean target',
                'severity': 'minor',
                'points': -2,
                'max_score': 2
            },
            'script_missing_shebang': {
                'description': 'Script missing proper shebang',
                'hebrew_description': 'חסר shebang תקין בסקריפט',
                'explanation': 'הסקריפט חייב להתחיל עם #!/bin/bash',
                'severity': 'minor',
                'points': -1,
                'max_score': 1
            },
            'script_missing_file_copy': {
                'description': 'Script missing file copying commands',
                'hebrew_description': 'חסרות פקודות העתקת קבצים בסקריפט',
                'explanation': 'הסקריפט חייב להעתיק את הקבצים הנדרשים',
                'severity': 'major',
                'points': -3,
                'max_score': 3
            },
            'script_missing_compilation': {
                'description': 'Script missing compilation or module loading',
                'hebrew_description': 'חסרת קומפילציה או טעינת מודול בסקריפט',
                'explanation': 'הסקריפט חייב לקמפל ולטעון את המודול',
                'severity': 'major',
                'points': -3,
                'max_score': 3
            },
            'script_missing_cleanup': {
                'description': 'Script missing cleanup commands',
                'hebrew_description': 'חסרות פקודות ניקוי בסקריפט',
                'explanation': 'הסקריפט חייב לכלול פקודות ניקוי',
                'severity': 'major',
                'points': -2,
                'max_score': 2
            },
            'script_missing_file_removal': {
                'description': 'Script missing file removal commands',
                'hebrew_description': 'חסרות פקודות מחיקת קבצים בסקריפט',
                'explanation': 'הסקריפט חייב למחוק קבצים זמניים',
                'severity': 'major',
                'points': -2,
                'max_score': 2
            }
        }
        
    def check_submission(self, submission_path: str) -> Dict:
        """Main function to check a single submission"""
        student_id = os.path.basename(submission_path)        
        result = {
            'student_id': student_id,
            'total_score': 0,
            'max_score': 100,
            'deductions': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check if submission directory exists
            if not os.path.isdir(submission_path):
                result['errors'].append(f"❌ Submission directory not found: {submission_path}")
                return result
                
            # Analyze submission for all deduction criteria
            self._analyze_submission(submission_path, result)
                    
        except Exception as e:
            print(f"💥 Critical error: {str(e)}")
            result['errors'].append(f"Critical error: {str(e)}")
            
        # Calculate final score
        self._calculate_score(result)
        self.results[student_id] = result
        
        return result
    
    def _analyze_submission(self, submission_path: str, result: Dict):
        """Analyze submission for all deduction criteria"""
        # Check file existence
        self._check_files_exist(submission_path, result)
        
        # Check mymod.c if it exists
        mymod_path = os.path.join(submission_path, 'mymod.c')
        if os.path.exists(mymod_path):
            self._check_mymod_c(submission_path, result)
        
        # Check Makefile if it exists
        makefile_path = os.path.join(submission_path, 'Makefile')
        if os.path.exists(makefile_path):
            self._check_makefile(submission_path, result)
        
        # Check script if it exists
        script_path = os.path.join(submission_path, 'mymod.sh')
        if os.path.exists(script_path):
            self._check_script(submission_path, result)
    
    def _check_files_exist(self, submission_dir: str, result: Dict):
        """Check if all required files exist"""
        existing_files = os.listdir(submission_dir)
        missing_files = [f for f in self.required_files if f not in existing_files]
        
        if missing_files:
            result['deductions']['missing_files'] = True
            result['errors'].append(f"Missing required files: {missing_files}")
        else:
            result['deductions']['missing_files'] = False
    
    def _check_mymod_c(self, submission_dir: str, result: Dict):
        """Comprehensive check of mymod.c file"""
        mymod_path = os.path.join(submission_dir, 'mymod.c')
        
        try:
            with open(mymod_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            result['errors'].append(f"Error reading mymod.c: {str(e)}")
            return
            
        # Check all mymod.c related criteria
        self._check_includes(content, result)
        self._check_gpl_license(content, result)
        self._check_init_cleanup(content, result)
        self._check_sysnr_param(content, result)
        self._check_msg_param(content, result)
        self._check_function_pointers(content, result)
        self._check_syscall_validation(content, result)
        self._check_error_handling(content, result)
        self._check_syscall_table_manipulation(content, result)
        self._check_user_memory_copying(content, result)
        self._check_kern_info_usage(content, result)
        self._check_buffer_size(content, result)
        self._check_string_termination(content, result)
        self._check_sleep_functionality(content, result)
    
    def _check_includes(self, content: str, result: Dict):
        """Check required includes"""
        required_includes = ['linux/module.h', 'linux/kernel.h', 'linux/syscalls.h']
        found_includes = [inc for inc in required_includes if f'#include <{inc}>' in content]
        
        if len(found_includes) < 3:
            result['deductions']['missing_includes'] = True
        else:
            result['deductions']['missing_includes'] = False
    
    def _check_gpl_license(self, content: str, result: Dict):
        """Check GPL license"""
        if 'MODULE_LICENSE("GPL")' not in content:
            result['deductions']['missing_gpl_license'] = True
        else:
            result['deductions']['missing_gpl_license'] = False
    
    def _check_init_cleanup(self, content: str, result: Dict):
        """Check init and cleanup functions"""
        has_init = 'init_module' in content or 'module_init' in content
        has_cleanup = 'cleanup_module' in content or 'module_exit' in content
        
        if not (has_init and has_cleanup):
            result['deductions']['missing_init_cleanup'] = True
        else:
            result['deductions']['missing_init_cleanup'] = False
    
    def _check_sysnr_param(self, content: str, result: Dict):
        """Check sysnr parameter"""
        if 'module_param(sysnr, int' not in content and 'int sysnr' not in content:
            result['deductions']['missing_sysnr_param'] = True
        else:
            result['deductions']['missing_sysnr_param'] = False
    
    def _check_msg_param(self, content: str, result: Dict):
        """Check msg parameter"""
        msg_patterns = ['module_param(msg, charp', 'char *msg', 'char* msg']
        has_msg = any(pattern in content for pattern in msg_patterns)
        
        if not has_msg:
            result['deductions']['missing_msg_param'] = True
        else:
            result['deductions']['missing_msg_param'] = False
    
    def _check_function_pointers(self, content: str, result: Dict):
        """Check function pointer declarations"""
        syscall_functions = ['mkdir', 'chdir', 'close', 'dup']
        found_pointers = []
        
        for func in syscall_functions:
            patterns = [
                f'asmlinkage long (*ref_{func})',
                f'asmlinkage long (*orig_{func})',
                f'asmlinkage long (*original_{func})',
                f'asmlinkage long (*saved_{func})',
                f'asmlinkage long (*old_{func})',
                f'asmlinkage long (*{func}_orig)',
                f'asmlinkage long (*{func}_ref)',
                f'asmlinkage long (*{func}_original)',
            ]
            
            if any(pattern in content for pattern in patterns):
                found_pointers.append(func)
        
        # if len(found_pointers) < 3:
        # result['deductions']['missing_function_pointers'] = True
        # else:
        result['deductions']['missing_function_pointers'] = False
    
    def _check_syscall_validation(self, content: str, result: Dict):
        """Check syscall number validation"""
        syscall_checks = []
        for nr, name in self.syscall_numbers.items():
            if nr in content:
                syscall_checks.append(name)
        
        if len(syscall_checks) < 2:
            result['deductions']['missing_syscall_checks'] = True
        else:
            result['deductions']['missing_syscall_checks'] = False
    
    def _check_error_handling(self, content: str, result: Dict):
        """Check invalid syscall number handling"""
        error_patterns = ['return -1', 'return -EINVAL', 'default:', 'else {']
        found_error_handling = any(pattern in content for pattern in error_patterns)
        
        if not found_error_handling:
            result['deductions']['missing_error_handling'] = True
        else:
            result['deductions']['missing_error_handling'] = False
    
    def _check_syscall_table_manipulation(self, content: str, result: Dict):
        """Check syscall table manipulation"""
        table_manipulation = ('sys_call_table' in content and 'write_cr0' in content) or 'kallsyms_lookup_name' in content
        
        if not table_manipulation:
            result['deductions']['missing_syscall_table'] = True
        else:
            result['deductions']['missing_syscall_table'] = False
    
    def _check_user_memory_copying(self, content: str, result: Dict):
        """Check user memory copying"""
        user_copy_methods = ['get_user', 'copy_from_user', 'strncpy_from_user', '__get_user', 'access_ok']
        found_methods = [method for method in user_copy_methods if method in content]
        
        if not found_methods:
            result['deductions']['missing_user_copy'] = True
        else:
            result['deductions']['missing_user_copy'] = False
    
    def _check_kern_info_usage(self, content: str, result: Dict):
        """Check KERN_INFO usage"""
        kern_info_count = content.count('KERN_INFO')
        pr_info_count = content.count('pr_info')
        total_log_count = kern_info_count + pr_info_count
        
        if total_log_count < 2:
            result['deductions']['missing_kern_info'] = True
        else:
            result['deductions']['missing_kern_info'] = False
    
    def _check_buffer_size(self, content: str, result: Dict):
        """Check proper buffer size"""
        if '16' not in content:
            result['deductions']['wrong_buffer_size'] = True
        else:
            result['deductions']['wrong_buffer_size'] = False
    
    def _check_string_termination(self, content: str, result: Dict):
        """Check string null termination"""
        termination_patterns = [
            r"\[15\]\s*=\s*0\s*;",
            r"\[15\]\s*=\s*'\\0'\s*;",
            r"memset\s*\(",
            r"bzero\s*\(",
            r"=\s*\{\s*0\s*\}",
            r"'\\0'",
        ]
        
        termination_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in termination_patterns)
        
        if not termination_found:
            result['deductions']['missing_string_termination'] = True
        else:
            result['deductions']['missing_string_termination'] = False
    
    def _check_sleep_functionality(self, content: str, result: Dict):
        """Check 3 second sleep"""
        sleep_variations = [
            'msleep(3000)',
            'ssleep(3)',
            'mdelay(3000)',
            'udelay(3000000)',
            'usleep_range(3000000',
            'schedule_timeout_interruptible(3*HZ)',
            'schedule_timeout(3*HZ)',
            'msleep_interruptible(3000)',
        ]
        
        found_sleep = any(sleep_var in content for sleep_var in sleep_variations)
        
        if not found_sleep:
            result['deductions']['missing_3sec_sleep'] = True
        else:
            result['deductions']['missing_3sec_sleep'] = False
    
    def _check_basic_requirements(self, content: str, check: Dict):
        """Check basic kernel module structure, includes, license, and parameters"""
        # First check if this is actually a kernel module
        kernel_indicators = [
            '#include <linux/module.h>',
            'MODULE_LICENSE',
            ('init_module' in content or 'module_init' in content),
            ('cleanup_module' in content or 'module_exit' in content)
        ]
        
        kernel_score = sum(1 for indicator in kernel_indicators if 
                          (isinstance(indicator, str) and indicator in content) or 
                          (isinstance(indicator, bool) and indicator))
        
        if kernel_score < 3:
            check['details'].append("❌ This doesn't appear to be a valid kernel module")
            return  # Early exit - this is not a kernel module
        
        # Check required includes
        required_includes = ['linux/module.h', 'linux/kernel.h', 'linux/syscalls.h']
        found_includes = [inc for inc in required_includes if f'#include <{inc}>' in content]
        
        if len(found_includes) >= 3:
            check['score'] += 4
            check['details'].append("✅ Required includes present")
        else:
            missing = set(required_includes) - set(found_includes)
            check['details'].append(f"❌ Missing includes: {missing}")
            
        # Check GPL license
        if 'MODULE_LICENSE("GPL")' in content:
            check['score'] += 3
            check['details'].append("✅ GPL license found")
        else:
            check['details'].append("❌ Missing GPL license")
            
        # Check init and cleanup functions
        # if 'init_module' in content and 'cleanup_module' in content:
        check['score'] += 3
        check['details'].append("✅ Init and cleanup functions found")
        # else:
        #     check['details'].append("❌ Missing init_module or cleanup_module")
            
        # Check module parameters (flexible for different approaches)
        # Check for sysnr parameter or variable
        if 'module_param(sysnr, int' in content:
            check['score'] += 3
            check['details'].append("✅ sysnr parameter defined")
        elif 'int sysnr' in content:
            check['score'] += 2
            check['details'].append("⚠️ sysnr variable found (parameter preferred)")
        else:
            check['details'].append("❌ Missing sysnr parameter/variable")
            
        # Check for msg parameter or variable
        if 'module_param(msg, charp' in content:
            check['score'] += 3
            check['details'].append("✅ msg parameter defined")
        elif 'char *msg' in content or 'char* msg' in content:
            check['score'] += 2
            check['details'].append("⚠️ msg variable found (parameter preferred)")
        else:
            check['details'].append("❌ Missing msg parameter/variable")
            
        # Check parameter initialization
        if 'sysnr = -1' in content or 'sysnr = 0' in content:
            check['score'] += 2
            check['details'].append("✅ sysnr properly initialized")
        else:
            check['details'].append("⚠️ sysnr should be initialized to non-zero")
            
        # Check for msg variable declaration (handle various formats)
        msg_variations = [
            'static char *msg',     # Professor's format
            'static char* msg',     # Alternative pointer syntax
            'char *msg',            # Without static
            'char* msg',            # Alternative without static
        ]
        
        found_msg_declaration = any(var in content for var in msg_variations)
        
        if found_msg_declaration:
            check['score'] += 2
            check['details'].append("✅ msg variable declared")
        else:
            check['details'].append("❌ msg variable not found")
            
        # Check for syscall pointer declarations (handle various naming conventions)
        syscall_functions = ['mkdir', 'chdir', 'close', 'dup']
        found_pointers = []
        
        for func in syscall_functions:
            # Check for various naming patterns students use
            patterns = [
                f'asmlinkage long (*ref_{func})',     # ref_ prefix (professor's style)
                f'asmlinkage long (*orig_{func})',    # orig_ prefix
                f'asmlinkage long (*original_{func})', # original_ prefix  
                f'asmlinkage long (*saved_{func})',   # saved_ prefix
                f'asmlinkage long (*old_{func})',     # old_ prefix
                f'asmlinkage long (*{func}_orig)',    # _orig suffix
                f'asmlinkage long (*{func}_ref)',     # _ref suffix
                f'asmlinkage long (*{func}_original)', # _original suffix
            ]
            
            if any(pattern in content for pattern in patterns):
                found_pointers.append(func)
        
        if len(found_pointers) >= 3:
            check['score'] += 5
            check['details'].append(f"✅ Function pointers found ({', '.join(found_pointers)})")
        elif len(found_pointers) >= 1:
            check['score'] += 2
            check['details'].append(f"⚠️ Some function pointers found ({', '.join(found_pointers)})")
        else:
            check['details'].append("❌ Missing function pointer declarations")
    
    def _check_syscall_implementation(self, content: str, check: Dict):
        """Check syscall replacement logic and validation"""
        # Check for syscall number validation
        syscall_checks = []
        for nr, name in self.syscall_numbers.items():
            if nr in content:
                syscall_checks.append(name)
                
        if len(syscall_checks) == 4:
            check['score'] += 8
            check['details'].append("✅ All syscall numbers checked")
        elif len(syscall_checks) >= 2:
            check['score'] += 5
            check['details'].append(f"⚠️ Some syscall checks found: {syscall_checks}")
        else:
            missing = set(self.syscall_numbers.values()) - set(syscall_checks)
            check['details'].append(f"❌ Missing syscall checks: {missing}")
            
        # Check for invalid syscall number handling
        error_patterns = ['return -1', 'return -EINVAL', 'default:', 'else {']
        found_error_handling = any(pattern in content for pattern in error_patterns)
        
        if found_error_handling:
            check['score'] += 5
            check['details'].append("✅ Invalid syscall number handling found")
        else:
            check['details'].append("❌ Missing invalid syscall number handling")
            
        # Check for syscall table manipulation
        if ('sys_call_table' in content and 'write_cr0' in content) or 'kallsyms_lookup_name' in content:
            check['score'] += 7
            check['details'].append("✅ Syscall table manipulation found")
        else:
            check['details'].append("❌ Missing syscall table manipulation")
            
        # Check for user memory copying (critical for mkdir/chdir)
        user_copy_methods = [
            'get_user',           # Professor's preferred method
            'copy_from_user',     # Alternative method
            'strncpy_from_user',  # String copy from user
            '__get_user',         # Lower level variant
            'access_ok'           # Memory access validation
        ]
        
        found_methods = [method for method in user_copy_methods if method in content]
        
        if found_methods:
            check['score'] += 5
            methods_str = ', '.join(found_methods)
            check['details'].append(f"✅ User memory copying found ({methods_str})")
        else:
            check['details'].append("❌ Missing user memory copying (major deduction)")
    
    def _check_message_and_cleanup(self, content: str, check: Dict):
        """Check message printing, cleanup and sleep functionality"""
        # Check for KERN_INFO usage
        kern_info_count = content.count('KERN_INFO')
        pr_info_count = content.count('pr_info')
        total_log_count = kern_info_count + pr_info_count
        
        if total_log_count >= 4:
            check['score'] += 3
            check['details'].append("✅ KERN_INFO/pr_info used in printk calls")
        elif total_log_count >= 2:
            check['score'] += 2
            check['details'].append("⚠️ Some KERN_INFO/pr_info usage found")
        else:
            check['details'].append("❌ Missing KERN_INFO/pr_info in printk calls")
            
        # Check for proper buffer size (16 chars as mentioned in professor's code)
        if '16' in content:
            check['score'] += 2
            check['details'].append("✅ Proper buffer size (16)")
        else:
            check['details'].append("❌ Incorrect buffer size (should be 16)")
            
        # Check for proper string termination - multiple valid patterns
        string_termination_patterns = [
            # Direct null character assignment patterns
            r"\[15\]\s*=\s*0\s*;",                    # buffer[15] = 0;
            r"\[15\]\s*=\s*'\\0'\s*;",                # buffer[15] = '\0';
            r"\[\s*\d+\s*-\s*1\s*\]\s*=\s*0\s*;",    # buffer[size-1] = 0;
            r"\[\s*\d+\s*-\s*1\s*\]\s*=\s*'\\0'\s*;", # buffer[size-1] = '\0';
            r"\[\s*SIZE\s*-\s*1\s*\]\s*=\s*0\s*;",   # buffer[SIZE-1] = 0;
            r"\[\s*copied\s*\]\s*=\s*'\\0'\s*;",     # buffer[copied] = '\0';
            
            # Memory clearing patterns
            r"memset\s*\(",                          # memset() calls
            r"bzero\s*\(",                           # bzero() calls
            
            # Array initialization patterns
            r"=\s*\{\s*0\s*\}",                      # = {0} initialization
            r"=\s*\{\s*\}",                          # = {} initialization
            
            # Explicit null termination
            r"'\\0'",                                # Simple '\0' anywhere
            r"\\0",                                  # \0 in string literals
        ]
        
        import re
        termination_found = False
        termination_method = ""
        
        for i, pattern in enumerate(string_termination_patterns):
            if re.search(pattern, content, re.IGNORECASE):
                termination_found = True
                if i < 6:
                    termination_method = "index assignment"
                elif i < 8:
                    termination_method = "memory clearing function"
                elif i < 10:
                    termination_method = "array initialization"
                else:
                    termination_method = "null character"
                break
        
        if termination_found:
            check['score'] += 2
            check['details'].append(f"✅ Proper string termination ({termination_method})")
        else:
            check['details'].append("❌ Missing string termination")
            
        # Check for 3 second sleep (critical requirement)
        sleep_variations = [
            'msleep(3000)',     # milliseconds - most common
            'ssleep(3)',        # seconds
            'mdelay(3000)',     # milliseconds - busy wait
            'udelay(3000000)',  # microseconds
            'usleep_range(3000000', # microseconds range
            'schedule_timeout_interruptible(3*HZ)', # jiffies
            'schedule_timeout(3*HZ)', # jiffies
            'msleep_interruptible(3000)', # interruptible version
        ]
        
        found_sleep = None
        for sleep_var in sleep_variations:
            if sleep_var in content:
                found_sleep = sleep_var
                break
        
        if found_sleep:
            check['score'] += 3
            check['details'].append(f"✅ 3 second sleep found ({found_sleep.split('(')[0]})")
        elif 'msleep(2000)' in content:
            check['details'].append("⚠️ Incorrect sleep time (should be 3000ms, not 2000ms)")
            check['score'] += 1
        elif any(sleep in content for sleep in ['msleep', 'ssleep', 'mdelay', 'udelay', 'schedule_timeout']):
            check['details'].append("⚠️ Sleep function found but incorrect duration")
            check['score'] += 1
        else:
            check['details'].append("❌ Missing 3 second sleep")
    
    def _check_makefile(self, submission_dir: str, result: Dict):
        """Check Makefile"""
        makefile_path = os.path.join(submission_dir, 'Makefile')
        
        try:
            with open(makefile_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check for kernel module compilation target
            if 'obj-m' not in content:
                result['deductions']['makefile_missing_obj'] = True
            else:
                result['deductions']['makefile_missing_obj'] = False
                
            # Check for mymod.ko reference
            if 'mymod.ko' not in content and 'mymod.o' not in content:
                result['deductions']['makefile_missing_module_ref'] = True
            else:
                result['deductions']['makefile_missing_module_ref'] = False
                
            # Check for clean target
            if 'clean:' not in content:
                result['deductions']['makefile_missing_clean'] = True
            else:
                result['deductions']['makefile_missing_clean'] = False
                
        except Exception as e:
            result['errors'].append(f"Error reading Makefile: {str(e)}")
    
    def _check_script(self, submission_dir: str, result: Dict):
        """Check mymod.sh script"""
        script_path = os.path.join(submission_dir, 'mymod.sh')
        
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check for shebang
            if not content.startswith('#!/bin/bash'):
                result['deductions']['script_missing_shebang'] = True
            else:
                result['deductions']['script_missing_shebang'] = False
                
            # Check for file copying
            cp_patterns = [
                'cp mymod.c Makefile',
                'cp mymod.c Makefile "$1"',
                'cp mymod.c Makefile $1',
            ]
            
            separate_commands = ('cp mymod.c' in content and 'cp Makefile' in content)
            combined_commands = any(pattern in content for pattern in cp_patterns)
            has_copying = separate_commands or combined_commands
                
            if not has_copying:
                result['deductions']['script_missing_file_copy'] = True
            else:
                result['deductions']['script_missing_file_copy'] = False
                
            # Check for compilation and module loading
            has_make = 'make' in content
            has_insmod = 'insmod' in content or 'modprobe' in content
            
            if not (has_make and has_insmod):
                result['deductions']['script_missing_compilation'] = True
            else:
                result['deductions']['script_missing_compilation'] = False
                
            # Check for cleanup
            has_clean = 'make clean' in content or 'sudo make clean' in content
            
            if not has_clean:
                result['deductions']['script_missing_cleanup'] = True
            else:
                result['deductions']['script_missing_cleanup'] = False
                
            # Check for file removal commands
            if "rm" not in content:
                result['deductions']['script_missing_file_removal'] = True
            else:
                result['deductions']['script_missing_file_removal'] = False
                
        except Exception as e:
            result['errors'].append(f"Error reading script: {str(e)}")
    
    def _calculate_score(self, result: Dict):
        """Calculate final score based on deductions"""
        total_deductions = 0
        max_possible_score = sum(criteria['max_score'] for criteria in self.deduction_criteria.values())
        
        for deduction_key, has_issue in result['deductions'].items():
            if has_issue and deduction_key in self.deduction_criteria:
                criteria = self.deduction_criteria[deduction_key]
                total_deductions += abs(criteria['points'])
        
        result['total_score'] = max(0, max_possible_score - total_deductions)
        result['max_score'] = max_possible_score
        result['total_deductions'] = total_deductions
    
    def process_all_submissions(self, submissions_folder: str) -> Dict:
        """Process all submissions in the folder"""
        results = {}
        
        if not os.path.exists(submissions_folder):
            print(f"Error: Submissions folder '{submissions_folder}' does not exist")
            return results
        
        # Get all student directories
        student_dirs = [d for d in os.listdir(submissions_folder) 
                       if os.path.isdir(os.path.join(submissions_folder, d))]
        
        print(f"Found {len(student_dirs)} student folders")
        
        for student_dir in student_dirs:
            student_path = os.path.join(submissions_folder, student_dir)
            try:
                result = self.check_submission(student_path)
                results[student_dir] = result
                
                # Quick feedback
                issues = [k for k, v in result['deductions'].items() if v]
                if issues:
                    print(f"✓ {student_dir}: {len(issues)} issues found")
                else:
                    print(f"✓ {student_dir}: No issues found")
                    
            except Exception as e:
                print(f"✗ {student_dir}: Error - {str(e)}")
                results[student_dir] = {'error': str(e)}
        
        return results
    
    def generate_excel_report(self, results: Dict, output_dir: str = None) -> str:
        """Generate an Excel report with detailed results"""
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Prepare data for Excel
        excel_data = []
        
        for student_name, result in results.items():
            if 'error' in result:
                # Handle error cases
                row = {
                    'Student Name': student_name,
                    'Errors Found In Part B': f"Processing Error: {result['error']}",
                    'Total Points Deducted Part B': 0,
                    'Final Score Part B': 0
                }
                excel_data.append(row)
                continue
            
            # Calculate total points deducted and build error description
            total_deductions = result.get('total_deductions', 0)
            errors_list = []
            
            for deduction_key, has_issue in result['deductions'].items():
                if has_issue and deduction_key in self.deduction_criteria:
                    criteria = self.deduction_criteria[deduction_key]
                    
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
                'Errors Found In Part B': all_errors,
                'Total Points Deducted Part B': total_deductions,
                'Final Score Part B': result['total_score']
            }
            excel_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"kernel_module_analysis_{timestamp}.xlsx"
        excel_path = os.path.join(output_dir, excel_filename)
        
        # Create Excel writer with multiple sheets
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Main results sheet
            df.to_excel(writer, sheet_name='Kernel Module Results', index=False)
            
            # Format the Excel file for better readability
            workbook = writer.book
            worksheet = writer.sheets['Kernel Module Results']
            
            # Set column widths
            worksheet.column_dimensions['A'].width = 30  # Student Name
            worksheet.column_dimensions['B'].width = 80  # Errors Found
            worksheet.column_dimensions['C'].width = 25  # Total Points Deducted
            worksheet.column_dimensions['D'].width = 20  # Final Score
            
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
    
    def _create_summary_sheet(self, writer, results: Dict):
        """Create a summary sheet with statistics"""
        total_students = len(results)
        students_with_issues = 0
        issue_counts = {criteria: 0 for criteria in self.deduction_criteria.keys()}
        total_points_deducted = {}
        
        for student_name, result in results.items():
            if 'error' in result:
                total_points_deducted[student_name] = 0
                continue
                
            total_deductions = result.get('total_deductions', 0)
            total_points_deducted[student_name] = total_deductions
            
            if total_deductions > 0:
                students_with_issues += 1
                
                for deduction_key, has_issue in result['deductions'].items():
                    if has_issue:
                        issue_counts[deduction_key] += 1
        
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
                'Points Deducted': criteria['points'],
                'Max Score': criteria['max_score']
            })
        
        criteria_df = pd.DataFrame(criteria_data)
        criteria_df.to_excel(writer, sheet_name='Criteria', index=False)

def main(folder="submissions"):
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build path to submissions folder
    submissions_folder = os.path.join(current_dir, folder)
    
    print(f"Processing submissions in: {submissions_folder}")
    
    checker = KernelModuleChecker()
    results = checker.process_all_submissions(submissions_folder)
    
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
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main("submissions")