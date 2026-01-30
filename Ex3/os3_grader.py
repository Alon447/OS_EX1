#!/usr/bin/env python3
"""
Simplified OS3 Grader - 2026
Grade: 50 (queue) + 40 (module) + 5 (script) + 5 (Makefile) = 100 points
"""

import os
import sys
import re
import tarfile
from pathlib import Path
import pandas as pd
from datetime import datetime

class OS3Grader:
    def __init__(self):
        # Part A: Queue (50 points total)
        self.queue_criteria = {
            'has_main': ('Has main() function', -10, 'major'),
            'missing_sum': ('Missing or broken sum() function', -8, 'major'),
            'wrong_type': ('Using int instead of long', -5, 'minor'),
            'malloc_in_lock': ('malloc() inside critical section', -5, 'minor'),
            'free_in_lock': ('free() inside critical section', -5, 'minor'),
            'lock_for_read': ('Lock used for simple value read', -3, 'minor'),
            'no_destroy_free': ('destroy() doesnt free all items', -5, 'minor'),
            'static_global': ('Uses static/global variables', -8, 'major'),
            'missing_cv': ('Missing or wrong condition variables', -10, 'major'),
        }
        
        # Part B: Kernel Module (40 points total)
        self.module_criteria = {
            'no_gpl': ('Missing GPL license', -4, 'major'),
            'wrong_sleep': ('Wrong sleep time (not 4 seconds)', -3, 'minor'),
            'no_array_param': ('Not using array parameter', -8, 'major'),
            'msg_before': ('Message printed BEFORE syscall', -8, 'major'),
            'wrong_buffer': ('Buffer size not 13 (12+null)', -3, 'minor'),
            'no_get_user': ('Missing get_user (copy from user memory)', -8, 'major'),
            'no_validation': ('Missing invalid syscall check', -8, 'major'),
            'no_error_restore': ('Missing restore on init error', -8, 'major'),
            'no_kern_info': ('Missing KERN_INFO in printk', -3, 'minor'),
            'no_restore': ('Missing proper cleanup/restore', -3, 'minor'),
        }
        
        # Part C: Script (5 points)
        self.script_criteria = {
            'wrong_args': ('Script doesnt handle 3 arguments', -3, 'major'),
            'no_copy': ('Missing file copy commands', -1, 'minor'),
            'no_make': ('Missing make/insmod commands', -2, 'major'),
        }
        
        # Part D: Makefile (5 points)
        self.makefile_criteria = {
            'no_obj_m': ('Missing obj-m target', -3, 'major'),
            'no_clean': ('Missing clean target', -2, 'minor'),
        }
    
    def extract_tar(self, tar_path, extract_to):
        """Extract tar.gz file"""
        try:
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(extract_to, filter='data')
            return True
        except:
            return False
    
    def find_file(self, directory, filename):
        """Find file recursively"""
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return os.path.join(root, filename)
        return None
    
    def read_file(self, filepath):
        """Read file content"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            return None
    
    # ========== PART A: QUEUE CHECKS ==========
    
    def check_queue(self, content):
        """Check os3q.c for common issues"""
        issues = {}
        
        # Auto-fail: has main
        issues['has_main'] = bool(re.search(r'int\s+main\s*\(', content))
        
        # Missing sum function - just check if function signature exists
        # Don't try to parse function body (nested braces are too complex for simple regex)
        # Accept both lowercase and capitalized versions (queueos_sum or QueueOS_sum)
        has_sum_signature = bool(re.search(r'long\s+[Qq]ueue[Oo][Ss]_sum\s*\([^)]*\)', content))
        issues['missing_sum'] = not has_sum_signature
        
        # Wrong data type (int instead of long)
        struct_match = re.search(r'struct\s+QItem\s*\{([^}]*)\}', content, re.DOTALL)
        if struct_match:
            issues['wrong_type'] = bool(re.search(r'int\s+val', struct_match.group(1)))
        else:
            issues['wrong_type'] = False
        
        # malloc in critical section (enqueue)
        enqueue = re.search(r'queueos_enqueue\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        if enqueue:
            func = enqueue.group(1)
            lock_pos = func.find('pthread_mutex_lock')
            malloc_pos = func.find('malloc')
            issues['malloc_in_lock'] = lock_pos != -1 and malloc_pos != -1 and malloc_pos > lock_pos
        else:
            issues['malloc_in_lock'] = False
        
        # free in critical section (dequeue)
        dequeue = re.search(r'queueos_dequeue\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        if dequeue:
            func = dequeue.group(1)
            unlock_pos = func.find('pthread_mutex_unlock')
            free_pos = func.find('free(')
            issues['free_in_lock'] = unlock_pos != -1 and free_pos != -1 and free_pos < unlock_pos
        else:
            issues['free_in_lock'] = False
        
        # Lock for simple read (size or sum)
        size_match = re.search(r'queueos_size\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        sum_match_check = re.search(r'queueos_sum\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        issues['lock_for_read'] = (
            (size_match and 'pthread_mutex_lock' in size_match.group(1)) or
            (sum_match_check and 'pthread_mutex_lock' in sum_match_check.group(1))
        )
        
        # destroy doesn't free items
        # Check if destroy function or any helper function frees items
        # Look for any function that frees queue nodes (loop + free pattern)
        has_cleanup = bool(re.search(r'(while|for).*?free\(', content, re.DOTALL))
        issues['no_destroy_free'] = not has_cleanup
        
        # Static/global variables (NOT static functions - those are OK!)
        temp = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        temp = re.sub(r'//.*', '', temp)
        temp = re.sub(r'struct\s+\w+\s*\{[^}]*\}', '', temp, flags=re.DOTALL)
        # Match static variables but NOT static functions (those have parentheses)
        issues['static_global'] = bool(re.search(r'^\s*static\s+(int|long|char|pthread_\w+)\s+\w+\s*[;=]', temp, re.MULTILINE))
        
        # Missing condition variables
        issues['missing_cv'] = not ('pthread_cond_wait' in content and 'pthread_cond_signal' in content)
        
        return issues
    
    # ========== PART B: KERNEL MODULE CHECKS ==========
    
    def check_module(self, content):
        """Check os3mod.c for 2026 requirements"""
        issues = {}
        
        # GPL license
        issues['no_gpl'] = 'MODULE_LICENSE("GPL")' not in content and "MODULE_LICENSE('GPL')" not in content
        
        # Sleep time (should be 4 seconds - ssleep(4) or msleep(4000) or schedule_timeout(4*HZ))
        has_valid_sleep = (
            'ssleep(4)' in content or 
            'msleep(4000)' in content or
            'schedule_timeout(4 * HZ)' in content or
            'schedule_timeout(4*HZ)' in content
        )
        issues['wrong_sleep'] = not has_valid_sleep
        
        # Array parameter (syscalls array)
        issues['no_array_param'] = 'module_param_array' not in content
        
        # Message printed AFTER syscall - check if printk comes AFTER the ref_xxx call
        # Look for pattern where syscall is called FIRST: ret = ref_xxx(...); then printk
        mkdir_match = re.search(r'new_mkdir[^{]*\{([^}]*)\}', content, re.DOTALL)
        if mkdir_match:
            func = mkdir_match.group(1)
            # Should have: ret = ref_mkdir(...) BEFORE printk
            # If printk appears before ref_mkdir, that's BEFORE (wrong)
            lines = func.split('\n')
            ref_line = -1
            printk_line = -1
            for i, line in enumerate(lines):
                if 'ref_mkdir' in line and '(' in line:
                    ref_line = i
                if 'printk' in line and ref_line == -1:  # printk before ref_mkdir
                    printk_line = i
                    break
            issues['msg_before'] = printk_line != -1 and printk_line < ref_line
        else:
            issues['msg_before'] = False
        
        # Buffer size check - should be 13 bytes (12 chars + null) for mkdir/chdir
        # Look for literal numbers or check for MAX_DIR_CHARS/similar defines set to 12
        buffer_matches = re.findall(r'char\s+\w+\[(\d+)\]', content)
        has_literal_buffer = '13' in buffer_matches or '16' in buffer_matches
        has_define_12 = bool(re.search(r'#define\s+\w*(?:MAX|DIR|CHAR|SIZE)\w*\s+12', content))
        issues['wrong_buffer'] = not (has_literal_buffer or has_define_12)
        
        # Copy from user memory - MANDATORY (must use get_user or strncpy_from_user)
        has_user_copy = 'get_user' in content or 'strncpy_from_user' in content or 'copy_from_user' in content
        issues['no_get_user'] = not has_user_copy
        
        # Invalid syscall validation - should check and return error
        # Look for checking against valid syscall numbers
        has_validation = (
            '__NR_mkdir' in content and '__NR_chdir' in content and 
            '__NR_close' in content and '__NR_dup' in content and
            ('return -' in content or 'EINVAL' in content)
        )
        issues['no_validation'] = not has_validation
        
        # Restore on error - MANDATORY: must restore already-changed syscalls if error in init
        # Look for restore logic in init_module when encountering invalid syscall
        # Only flag if validation happens INSIDE the replacement loop (not before)
        init_match = re.search(r'init_module[^{]*\{(.*)', content, re.DOTALL)
        has_error_restore = True  # Assume OK unless proven otherwise
        if init_match:
            init_content = init_match.group(1)
            # Check if there's a loop that modifies syscalls AND has validation inside it
            # Pattern: for loop with syscall table modification + invalid check
            loop_with_validation = re.search(
                r'for\s*\([^)]*\)\s*\{([^}]*sys_call_table[^}]*(?:__NR_|syscalls\[)[^}]*)\}',
                init_content, re.DOTALL
            )
            if loop_with_validation:
                loop_body = loop_with_validation.group(1)
                # Check if there's error handling (return -) without restore in the loop
                has_error_return = bool(re.search(r'return\s*-', loop_body))
                has_restore_before_error = bool(re.search(r'restore', loop_body, re.IGNORECASE))
                
                # Error if: returns error in loop but doesn't restore
                if has_error_return and not has_restore_before_error:
                    has_error_restore = False
        issues['no_error_restore'] = not has_error_restore
        
        # KERN_INFO in printk - should have at least a few
        kern_info_count = content.count('KERN_INFO')
        issues['no_kern_info'] = kern_info_count < 2
        
        # Restore functionality - check for cleanup_module/exit function with syscall table restore
        # Accept either direct sys_call_table usage or helper functions that restore
        # Also accept module_exit() macro with custom function name
        cleanup_exists = 'cleanup_module' in content or 'module_exit' in content
        if cleanup_exists:
            # Check if there's any restore logic (directly or via helper function)
            has_restore = (
                'sys_call_table' in content and  # Has syscall table
                ('restore' in content.lower() or  # Has some restore logic
                 re.search(r'sys_call_table\[', content))  # Any table access (not just __NR_)
            )
        else:
            has_restore = False
        issues['no_restore'] = not has_restore
        
        return issues
    
    # ========== PART C: SCRIPT CHECKS ==========
    
    def check_script(self, content):
        """Check os3mod.sh script"""
        issues = {}
        
        # Should handle 3 arguments ($1, $2, $3) - or at least 2 with optional 3rd
        # Accept either all 3 required, or 2 required + 1 optional
        # Also accept ${*:3} or ${@:3} which captures all args from 3rd onwards (valid for text with spaces)
        has_arg1 = '$1' in content or '${1' in content
        has_arg2 = '$2' in content or '${2' in content
        has_arg3 = '$3' in content or '${3' in content or '${*:3}' in content or '${@:3}' in content
        issues['wrong_args'] = not (has_arg1 and has_arg2 and has_arg3)
        
        # File copy (cp command)
        issues['no_copy'] = 'cp' not in content
        
        # Make and insmod
        issues['no_make'] = not ('make' in content and 'insmod' in content)
        
        return issues
    
    # ========== PART D: MAKEFILE CHECKS ==========
    
    def check_makefile(self, content):
        """Check Makefile"""
        issues = {}
        
        # obj-m target
        issues['no_obj_m'] = 'obj-m' not in content
        
        # clean target
        issues['no_clean'] = 'clean:' not in content
        
        return issues
    
    # ========== GRADING ==========
    
    def grade_student(self, student_folder):
        """Grade one student's submission"""
        student_name = os.path.basename(student_folder)
        result = {
            'name': student_name,
            'queue_points': 50,
            'module_points': 40,
            'script_points': 5,
            'makefile_points': 5,
            'errors': []
        }
        
        # Extract tar if needed
        tar_files = list(Path(student_folder).glob('*.tar.gz'))
        if tar_files:
            self.extract_tar(str(tar_files[0]), student_folder)
        
        # Part A: Queue
        queue_file = self.find_file(student_folder, 'os3q.c')
        if queue_file:
            content = self.read_file(queue_file)
            if content:
                issues = self.check_queue(content)
                for key, found in issues.items():
                    if found:
                        desc, points, severity = self.queue_criteria[key]
                        result['queue_points'] += points
                        result['errors'].append(f"[Queue] {desc} ({points} pts)")
            else:
                result['queue_points'] = 0
                result['errors'].append("[Queue] Could not read file")
        else:
            result['queue_points'] = 0
            result['errors'].append("[Queue] File not found")
        
        # Part B: Module
        mod_file = self.find_file(student_folder, 'os3mod.c')
        if mod_file:
            content = self.read_file(mod_file)
            if content:
                issues = self.check_module(content)
                for key, found in issues.items():
                    if found:
                        desc, points, severity = self.module_criteria[key]
                        result['module_points'] += points
                        result['errors'].append(f"[Module] {desc} ({points} pts)")
            else:
                result['module_points'] = 0
                result['errors'].append("[Module] Could not read file")
        else:
            result['module_points'] = 0
            result['errors'].append("[Module] File not found")
        
        # Part C: Script
        script_file = self.find_file(student_folder, 'os3mod.sh')
        if script_file:
            content = self.read_file(script_file)
            if content:
                issues = self.check_script(content)
                for key, found in issues.items():
                    if found:
                        desc, points, severity = self.script_criteria[key]
                        result['script_points'] += points
                        result['errors'].append(f"[Script] {desc} ({points} pts)")
            else:
                result['script_points'] = 0
                result['errors'].append("[Script] Could not read file")
        else:
            result['script_points'] = 0
            result['errors'].append("[Script] File not found")
        
        # Part D: Makefile
        make_file = self.find_file(student_folder, 'Makefile')
        if make_file:
            content = self.read_file(make_file)
            if content:
                issues = self.check_makefile(content)
                for key, found in issues.items():
                    if found:
                        desc, points, severity = self.makefile_criteria[key]
                        result['makefile_points'] += points
                        result['errors'].append(f"[Makefile] {desc} ({points} pts)")
            else:
                result['makefile_points'] = 0
                result['errors'].append("[Makefile] Could not read file")
        else:
            result['makefile_points'] = 0
            result['errors'].append("[Makefile] File not found")
        
        # Ensure no negative scores
        result['queue_points'] = max(0, result['queue_points'])
        result['module_points'] = max(0, result['module_points'])
        result['script_points'] = max(0, result['script_points'])
        result['makefile_points'] = max(0, result['makefile_points'])
        
        result['total'] = (result['queue_points'] + result['module_points'] + 
                          result['script_points'] + result['makefile_points'])
        
        return result
    
    def grade_all(self, submissions_folder):
        """Grade all submissions"""
        if not os.path.exists(submissions_folder):
            print(f"Error: {submissions_folder} not found")
            return
        
        student_dirs = [d for d in os.listdir(submissions_folder)
                       if os.path.isdir(os.path.join(submissions_folder, d))]
        
        print(f"Grading {len(student_dirs)} submissions...")
        print("=" * 70)
        
        results = []
        for student_dir in sorted(student_dirs):
            student_path = os.path.join(submissions_folder, student_dir)
            result = self.grade_student(student_path)
            results.append(result)
            
            # Calculate Part B total (module + script + makefile)
            part_b_total = result['module_points'] + result['script_points'] + result['makefile_points']
            
            # Print detailed results
            print(f"\n{'='*70}")
            print(f"Student: {result['name']}")
            print(f"  Part A (Queue):                    {result['queue_points']:2}/50")
            print(f"  Part B (Module+Script+Makefile):   {part_b_total:2}/50")
            print(f"    - Module (40):                   {result['module_points']:2}/40")
            print(f"    - Script (5):                    {result['script_points']:2}/5")
            print(f"    - Makefile (5):                  {result['makefile_points']:2}/5")
            print(f"  {'─'*40}")
            print(f"  TOTAL:                             {result['total']:3}/100")
            
            if result['errors']:
                print(f"\n  Errors:")
                for error in result['errors']:
                    print(f"    • {error}")
            else:
                print(f"\n  ✓ No errors found")
        
        print("=" * 70)
        
        # Generate Excel
        self.generate_excel(results)
        
        # Print statistics
        self.print_statistics(results)
        
        return results
    
    def generate_excel(self, results):
        """Generate CSV report"""
        df_data = []
        for r in results:
            # Separate errors by part
            queue_errors = [e for e in r['errors'] if e.startswith('[Queue]')]
            module_errors = [e for e in r['errors'] if e.startswith('[Module]')]
            script_errors = [e for e in r['errors'] if e.startswith('[Script]')]
            makefile_errors = [e for e in r['errors'] if e.startswith('[Makefile]')]
            
            # Remove point deductions from error messages
            queue_errors_clean = [re.sub(r'\s*\([^)]*pts?\)', '', e) for e in queue_errors]
            part_b_errors = module_errors + script_errors + makefile_errors
            part_b_errors_clean = [re.sub(r'\s*\([^)]*pts?\)', '', e) for e in part_b_errors]
            
            part_b_total = r['module_points'] + r['script_points'] + r['makefile_points']
            
            df_data.append({
                'Student': r['name'],
                'Part A: Queue (50)': r['queue_points'],
                'Part A Errors': '\n'.join(queue_errors_clean) if queue_errors_clean else '',
                'Part B: Module+Script+Makefile (50)': part_b_total,
                'Part B Errors': '\n'.join(part_b_errors_clean) if part_b_errors_clean else '',
                'Total': r['total']
            })
        
        df = pd.DataFrame(df_data)
        
        # Create grading_results folder if it doesn't exist
        output_dir = "grading_results"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"os3_grades_{timestamp}.csv")
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"\n✓ CSV report saved: {filename}")
    
    def print_statistics(self, results):
        """Print grading statistics"""
        if not results:
            return
        
        print(f"\n{'='*70}")
        print("GRADING STATISTICS")
        print(f"{'='*70}")
        
        # Calculate scores
        scores = [r['total'] for r in results]
        scores.sort()
        
        # Median
        n = len(scores)
        median = scores[n//2] if n % 2 == 1 else (scores[n//2-1] + scores[n//2]) / 2
        
        print(f"\nTotal Students: {n}")
        print(f"Median Score: {median:.1f}/100")
        print(f"Average Score: {sum(scores)/n:.1f}/100")
        print(f"Highest Score: {max(scores)}/100")
        print(f"Lowest Score: {min(scores)}/100")
        
        # Score distribution
        print(f"\n{'─'*70}")
        print("SCORE DISTRIBUTION")
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
        
        # Most common errors
        print(f"\n{'─'*70}")
        print("MOST COMMON ERRORS")
        print(f"{'─'*70}")
        
        error_counts = {}
        for r in results:
            for error in r['errors']:
                # Clean up error message (remove point info)
                clean_error = re.sub(r'\s*\([^)]*pts?\)', '', error)
                error_counts[clean_error] = error_counts.get(clean_error, 0) + 1
        
        # Sort by frequency
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        
        for i, (error, count) in enumerate(sorted_errors[:10], 1):
            percentage = (count / n * 100) if n > 0 else 0
            print(f"  {i:2}. {error:50} → {count:3}x ({percentage:5.1f}%)")
        
        # 10 lowest graded students
        print(f"\n{'─'*70}")
        print("10 LOWEST GRADED STUDENTS")
        print(f"{'─'*70}")
        
        sorted_results = sorted(results, key=lambda x: x['total'])
        for i, r in enumerate(sorted_results[:10], 1):
            part_b = r['module_points'] + r['script_points'] + r['makefile_points']
            print(f"  {i:2}. {r['name']:40} → {r['total']:3}/100 (A:{r['queue_points']:2} B:{part_b:2})")
        
        print(f"{'='*70}\n")

if __name__ == "__main__":
    submissions_folder = sys.argv[1] if len(sys.argv) > 1 else "submissions"
    
    grader = OS3Grader()
    grader.grade_all(submissions_folder)
