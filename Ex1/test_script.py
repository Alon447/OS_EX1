#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import glob
import re
import shutil
import csv
import tempfile
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
    EXCEL_AVAILABLE = True
except ImportError:
    print("Note: pandas not found. Excel output will not be available.")
    print("To enable Excel output, install pandas with: pip install pandas openpyxl")
    EXCEL_AVAILABLE = False

# Configuration
TIMEOUT = 5  # seconds
OUTPUT_DIR = "grading_results"  # Directory for output files
SUBMISSION_DIR = "submissions"  # Directory for student submissions
# SUBMISSION_DIR = "subs"  # Directory for student submissions
COMPILER = "gcc"
COMPILER_FLAGS = "-Wall"

# List of commands to test
TEST_COMMANDS = [
    ("ls", "Test basic command execution"),
    ("ls -l", "Test command with arguments"),
    ("echo hello world", "Test command with multiple arguments"),
    ("sleep 1 %", "Test background processes"),
    ("pwd", "Test current directory command"),
    ("invalid_command", "Test handling of invalid commands"),
    ("cat os1.c", "Test file display")
]

def check_shell_prompt(student_dir, timeout=TIMEOUT):
    """Check if the shell uses the correct $$ prompt."""
    try:
        current_dir = os.getcwd()
        os.chdir(student_dir)
        
        shell_process = subprocess.Popen(
            ["./os1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Just send exit to get the prompt
        shell_process.stdin.write("exit\n")
        shell_process.stdin.flush()
        
        try:
            stdout, stderr = shell_process.communicate(timeout=timeout)
            os.chdir(current_dir)
            
            # Check if $$ prompt appears in output
            if "$$ " in stdout:
                return True, ""
            else:
                return False, "Shell prompt '$$ ' not found"
        except subprocess.TimeoutExpired:
            shell_process.kill()
            os.chdir(current_dir)
            return False, "Shell timed out"
    except Exception as e:
        os.chdir(current_dir)
        return False, f"Error checking prompt: {str(e)}"

def compile_submission(source_dir, source_file):
    """Compile the C source code in its own directory."""
    try:
        # Change to the student's directory
        current_dir = os.getcwd()
        os.chdir(source_dir)
        
        # Get just the filename without path
        source_filename = os.path.basename(source_file)
        output_file = "os1"
        
        # Compile in the student's directory
        result = subprocess.run(
            [COMPILER, source_filename, "-o", output_file, COMPILER_FLAGS], 
            capture_output=True, 
            text=True,
            timeout=TIMEOUT
        )
        
        success = result.returncode == 0
        message = "Compilation successful" if success else f"Compilation Error: {result.stderr}"
        
        # Return to original directory
        os.chdir(current_dir)
        
        return success, message
    except subprocess.TimeoutExpired:
        # Ensure we return to original directory even if timeout occurs
        os.chdir(current_dir)
        return False, "Compilation timed out"
    except Exception as e:
        # Ensure we return to original directory even if exception occurs
        os.chdir(current_dir)
        return False, f"Compilation error: {str(e)}"

def test_shell_script(student_dir, timeout=TIMEOUT):
    """
    Test the os1.sh shell script.
    
    The script should:
    1. Create a directory named by arg1
    2. Create greeting.txt with "Hey <USER>! My name is <NAME>"
    3. Copy file from arg2, compile it to os1exe with -Wall
    4. List files in directory from arg3 using ls -la
    
    Returns: (passed_tests, total_tests, results_list)
    """
    results = []
    current_dir = os.getcwd()
    
    # Convert to absolute path
    student_dir = os.path.abspath(student_dir)
    
    try:
        os.chdir(student_dir)
        
        # Check if os1.sh exists
        if not os.path.exists("os1.sh"):
            os.chdir(current_dir)
            return 0, 4, [{"test": "os1.sh exists", "passed": False, "reason": "os1.sh file not found"}]
        
        # Create a temporary test directory in /tmp to avoid path issues with Hebrew names
        test_base_dir = tempfile.mkdtemp(prefix="os1_test_")
        test_dir_name = "test_output_dir"
        test_dir_path = os.path.join(test_base_dir, test_dir_name)
        
        # Copy os1.sh to temp directory and fix line endings
        # Convert Windows (CRLF) to Unix (LF) line endings
        with open("os1.sh", 'r', newline='') as f:
            content = f.read()
        # Replace CRLF with LF
        content = content.replace('\r\n', '\n')
        with open(os.path.join(test_base_dir, "os1.sh"), 'w', newline='\n') as f:
            f.write(content)
        
        # Copy os1.c to the temp directory
        shutil.copy("os1.c", test_base_dir)
        
        # Use os1.c as the file to compile (arg2)
        source_file = os.path.join(test_base_dir, "os1.c")
        
        # Use /tmp as the directory to list (arg3)
        list_dir = "/tmp"
        
        try:
            # Run the shell script: bash os1.sh <dir_name> <source_file> <list_dir>
            # We run it from test_base_dir so the directory is created there
            result = subprocess.run(
                ["bash", "os1.sh", test_dir_name, source_file, list_dir],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=test_base_dir
            )
            
            script_ran = result.returncode == 0
            script_stderr = result.stderr
            script_stdout = result.stdout
            
            # Check if student used home directory (~/) instead of current directory
            # This is a common mistake that causes all tests to fail
            uses_home_dir = False
            with open(os.path.join(test_base_dir, "os1.sh"), 'r') as f:
                script_content = f.read()
                if "~/" in script_content or "~$" in script_content:
                    uses_home_dir = True
            
            # Check for hardcoded username in script (regardless of home dir usage)
            uses_hardcoded_user = False
            hardcoded_username = ""
            expected_user = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
            
            # Look for common patterns of hardcoded usernames in the script
            if '"Hey ' in script_content or "'Hey " in script_content:
                # Extract what comes after "Hey "
                import re
                match = re.search(r'["\']Hey\s+(\w+)[,!]', script_content)
                if match:
                    found_user = match.group(1)
                    if found_user != "$USER" and found_user != expected_user:
                        uses_hardcoded_user = True
                        hardcoded_username = found_user
            
            if uses_home_dir:
                # Single error for using home directory instead of current directory
                results.append({
                    "test": "Script path usage",
                    "passed": False,
                    "reason": "Script uses home directory (~/) instead of current directory - all paths should be relative (e.g., $1 not ~/$1)"
                })
            
            if uses_hardcoded_user:
                # Error for hardcoded username
                results.append({
                    "test": "Script uses $USER variable",
                    "passed": False,
                    "reason": f"greeting.txt uses hardcoded username '{hardcoded_username}' instead of $USER variable"
                })
            
            # Only run detailed tests if not using home directory
            if not uses_home_dir:
                # Test 1: Directory was created
                dir_created = os.path.isdir(test_dir_path)
                
                # Debug: if directory not created, check if script ran successfully
                if not dir_created:
                    dir_reason = "Directory was not created"
                    if script_stderr:
                        dir_reason = f"Directory was not created (script error: {script_stderr[:100]})"
                    elif result.returncode != 0:
                        dir_reason = f"Directory was not created (script exit code: {result.returncode})"
                else:
                    dir_reason = ""
                
                results.append({
                    "test": "Script creates directory (arg1)",
                    "passed": dir_created,
                    "reason": dir_reason
                })
                
                # Test 2: greeting.txt was created with correct format
                greeting_file = os.path.join(test_dir_path, "greeting.txt")
                greeting_correct = False
                greeting_reason = ""
                
                if os.path.exists(greeting_file):
                    with open(greeting_file, 'r') as f:
                        content = f.read().strip()
                    # Check format: "Hey <USER>! My name is <NAME>" or "Hey <USER> My name is <NAME>"
                    # The USER should match actual $USER env var, NAME can be anything
                    expected_user = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
                    
                    # Accept both "! My name is" and " My name is" (with or without !)
                    has_my_name = " My name is " in content or "! My name is " in content
                    
                    if content.startswith("Hey ") and has_my_name:
                        # Extract username - try with ! first, then without
                        if "!" in content:
                            username_in_greeting = content.split("!")[0].replace("Hey ", "").strip()
                        else:
                            # No !, split by "My name is"
                            username_in_greeting = content.split("My name is")[0].replace("Hey ", "").strip()
                        
                        if username_in_greeting == expected_user:
                            greeting_correct = True
                            # Minor note if missing ! (but still pass)
                            if "!" not in content:
                                greeting_reason = "Minor: missing '!' (1 point)"
                        else:
                            greeting_reason = f"greeting.txt uses hardcoded username '{username_in_greeting}' instead of $USER variable"
                    else:
                        greeting_reason = "greeting.txt has wrong format"
                else:
                    greeting_reason = "greeting.txt was not created"
                
                results.append({
                    "test": "Script creates greeting.txt with correct format",
                    "passed": greeting_correct,
                    "reason": greeting_reason
                })
                
                # Test 3: os1exe was created (compiled)
                exe_file = os.path.join(test_dir_path, "os1exe")
                exe_created = os.path.exists(exe_file)
                exe_reason = ""
                
                if not exe_created:
                    # Check if student created an executable with wrong name
                    wrong_exe_names = []
                    if os.path.isdir(test_dir_path):
                        for f in os.listdir(test_dir_path):
                            fpath = os.path.join(test_dir_path, f)
                            # Check if it's an executable file (not os1.c, not .txt, not .sh)
                            if os.path.isfile(fpath) and not f.endswith(('.c', '.txt', '.sh', '.h', '.o')):
                                # Check if it's executable or a compiled binary
                                if os.access(fpath, os.X_OK) or f in ['exe1os', 'os1', 'myexe', 'a.out']:
                                    wrong_exe_names.append(f)
                    
                    if wrong_exe_names:
                        exe_reason = f"Wrong executable name: '{', '.join(wrong_exe_names)}' (expected 'os1exe')"
                    else:
                        # Check if there was a compilation error in stderr
                        if "gcc" in script_stderr or "error" in script_stderr.lower():
                            exe_reason = "Compilation failed (check gcc command and file paths)"
                        elif "No such file" in script_stderr or "cannot find" in script_stderr:
                            exe_reason = "Source file not found (check cp command and paths)"
                        else:
                            exe_reason = "os1exe was not created (compilation have failed)"
                
                results.append({
                    "test": "Script compiles os1.c to os1exe",
                    "passed": exe_created,
                    "reason": exe_reason
                })
                
                # Test 4: ls -la output was produced (check stdout contains typical ls -la output)
                ls_output_correct = False
                ls_reason = ""
                
                # ls -la output should contain "total" and have file permission patterns like "drwx" or "-rw-"
                if script_stdout:
                    if "total " in script_stdout or re.search(r'[d\-][rwx\-]{9}', script_stdout):
                        ls_output_correct = True
                    else:
                        ls_reason = "ls -la output not detected"
                else:
                    ls_reason = "No ls -la output from script"
                
                results.append({
                    "test": "Script outputs ls -la of arg3 directory",
                    "passed": ls_output_correct,
                    "reason": ls_reason
                })
            
        finally:
            # Cleanup test directory
            if os.path.exists(test_base_dir):
                shutil.rmtree(test_base_dir, ignore_errors=True)
                
    except subprocess.TimeoutExpired:
        results.append({
            "test": "os1.sh execution",
            "passed": False,
            "reason": "Script execution timed out"
        })
    except Exception as e:
        results.append({
            "test": "os1.sh execution",
            "passed": False,
            "reason": f"Error running script: {str(e)}"
        })
    finally:
        os.chdir(current_dir)
    
    passed = sum(1 for r in results if r["passed"])
    return passed, len(results), results

def run_test_command(student_dir, command, timeout=TIMEOUT):
    """Run a test command through the shell in the student's directory."""
    try:
        # Change to the student's directory
        current_dir = os.getcwd()
        os.chdir(student_dir)
        
        # Start the shell process
        shell_process = subprocess.Popen(
            ["./os1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send the command + exit to the shell
        shell_process.stdin.write(f"{command}\nexit\n")
        shell_process.stdin.flush()
        
        # Wait for completion with timeout
        try:
            stdout, stderr = shell_process.communicate(timeout=timeout)
            print(f"Command: {command} executed with output:\n{stdout}")
            
            # Return to original directory
            os.chdir(current_dir)
            return True, stdout, stderr
        except subprocess.TimeoutExpired:
            shell_process.kill()
            os.chdir(current_dir)
            return False, "", "Command timed out"
            
    except Exception as e:
        # Return to original directory in case of error
        os.chdir(current_dir)
        return False, "", f"Error executing command: {str(e)}"

def format_results(results, student_id):
    """Format the results into a readable report."""
    report = []
    report.append("=" * 50)
    report.append(f"OS1 SHELL GRADING REPORT - STUDENT: {student_id}")
    report.append("=" * 50)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    score = (passed / total) * 100
    
    report.append(f"Score: {score:.1f}% ({passed}/{total} tests passed)")
    report.append("-" * 50)
    
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        report.append(f"[{status}] Test: {result['description']}")
        report.append(f"  Command: {result['command']}")
        if not result["passed"]:
            report.append(f"  Failure reason: {result['reason']}")
        report.append("")
    
    return "\n".join(report), score, passed, total

def save_clean_output(student_id, command, stdout, output_dir):
    """Save the clean output (stdout only) to a file for comparison."""
    # Create directory for clean outputs if not exists
    clean_output_dir = os.path.join(output_dir, "clean_outputs")
    os.makedirs(clean_output_dir, exist_ok=True)
    
    # Create the output file path - one file per student
    output_file = os.path.join(clean_output_dir, f"{student_id}_outputs.txt")
    
    # Extract only the shell output without prompt lines
    # This pattern looks for lines that are not shell prompts or input commands
    clean_output = ""
    
    # Split the output into lines
    lines = stdout.splitlines()
    
    # Filter out prompt lines and input echoes
    # We're only keeping the actual output generated by the command
    for line in lines:
        # Skip lines that might be prompts or command echoes
        # Adjust these patterns based on your shell's actual prompt format
        # HW1-2026 uses '$$ ' as the prompt
        if not re.match(r'^(os1|>|\$\$|\$|.*\$\$ )', line.strip()) and line.strip() != command:
            clean_output += line + "\n"
    
    # Append the clean output to the student's output file
    # Add a header for this command's output
    with open(output_file, "a") as f:
        f.write(f"=== Output for command: {command} ===\n")
        f.write(clean_output)
        f.write("\n\n")

def grade_submission(student_info, output_dir=OUTPUT_DIR):
    """Grade a single submission."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract student ID and file path
    student_id, submission_path = student_info
    
    # Define paths
    student_dir = os.path.dirname(submission_path)
    report_file = os.path.join(output_dir, f"report_{student_id}.txt")
    
    # Create clean outputs directory
    clean_output_dir = os.path.join(output_dir, "clean_outputs")
    os.makedirs(clean_output_dir, exist_ok=True)
    
    # Initialize the student's clean output file
    student_clean_output = os.path.join(clean_output_dir, f"{student_id}_outputs.txt")

    
    # Print starting information with clear formatting
    print("\n" + "=" * 50)
    print(f"GRADING: {student_id}")
    print("-" * 50)
    print(f"Source file: {submission_path}")
    print(f"Student directory: {student_dir}")
    
    # Compile the submission
    print("Compiling submission...", end="", flush=True)
    compile_success, compile_msg = compile_submission(student_dir, submission_path)
    if compile_success:
        print(" SUCCESS")
    else:
        print(" FAILED")
        print(f"  Reason: {compile_msg}")
    
    results = []
    
    # ========== TEST PART A: os1.sh shell script ==========
    print("\nTesting os1.sh script:")
    script_passed, script_total, script_results = test_shell_script(student_dir)
    
    for sr in script_results:
        print(f"  {sr['test']:<45}", end="", flush=True)
        if sr['passed']:
            print(" PASSED")
        else:
            print(" FAILED")
            if sr['reason']:
                print(f"    Reason: {sr['reason'][:100]}")
        
        results.append({
            "command": sr['test'],
            "description": f"os1.sh: {sr['test']}",
            "passed": sr['passed'],
            "reason": sr.get('reason', ''),
            "actual_output": sr.get('actual_output', sr.get('reason', ''))
        })
    
    print(f"  Script tests: {script_passed}/{script_total} passed")
    
    # ========== TEST PART B: os1.c shell implementation ==========
    if not compile_success:
        results.append({
            "command": "COMPILATION",
            "description": "Compile the submission",
            "passed": False,
            "reason": compile_msg,
            "actual_output": compile_msg
        })
    else:
        # Create directory for test outputs
        test_output_dir = os.path.join(output_dir, "test")
        os.makedirs(test_output_dir, exist_ok=True)
        
        # Student log file for all test outputs
        student_output_log = os.path.join(test_output_dir, f"{student_id}_test_outputs.txt")
        with open(student_output_log, "w") as f:
            f.write(f"TEST OUTPUTS FOR {student_id}\n")
            f.write("=" * 50 + "\n\n")
        
        # Test 1: Check for correct $$ prompt
        print("\nChecking shell prompt:")
        prompt_ok, prompt_reason = check_shell_prompt(student_dir)
        print(f"  Shell uses '$$ ' prompt: ", end="", flush=True)
        if prompt_ok:
            print("PASSED")
        else:
            print("FAILED")
            if prompt_reason:
                print(f"    Reason: {prompt_reason[:100]}")
        
        results.append({
            "command": "Shell prompt check",
            "description": "Shell uses correct '$$ ' prompt",
            "passed": prompt_ok,
            "reason": prompt_reason,
            "actual_output": prompt_reason if not prompt_ok else ""
        })
        
        # Run each test command
        print("\nRunning tests:")
        for command, description in TEST_COMMANDS:
            print(f"  Testing: {command:<20}", end="", flush=True)
            success, stdout, stderr = run_test_command(student_dir, command)

            passed = success
            reason = ""
            actual_output = ""

            if not passed:
                reason = "Command failed or timed out"
                actual_output = ""

            results.append({
                "command": command,
                "description": description,
                "passed": passed,
                "reason": reason,
                "actual_output": actual_output
            })

            # Save clean output for comparison
            if passed:
                save_clean_output(student_id, command, stdout, output_dir)

            # Save command output to student file
            with open(student_output_log, "a") as f:
                f.write("=" * 40 + "\n")
                f.write(f"Test: {description}\n")
                f.write(f"Command: {command}\n")
                f.write(f"Status: {'PASS' if passed else 'FAIL'}\n")
                f.write("STDOUT:\n")
                f.write(stdout + "\n")
                f.write("STDERR:\n")
                f.write(stderr + "\n")

            if passed:
                print(" PASSED")
            else:
                print(" FAILED")
                if reason:
                    print(f"    Reason: {reason}")
    
    # Generate report
    report, score, passed, total = format_results(results, student_id)
    
    # Save report to file
    with open(report_file, "w") as f:
        f.write(report)
    
    # Print a brief summary to the console
    print("\nSUMMARY:")
    print(f"  Score: {score:.1f}% ({passed}/{total} tests passed)")
    print(f"  Detailed report saved to {report_file}")
    
    print("=" * 50)
    
    # Return results and grade information
    return {
        "student_id": student_id,
        "score": score,
        "passed": passed,
        "total": total,
        "details": results
    }

def main():
    """Main function to run the grading script."""
    print("\n" + "=" * 60)
    print("OS1 SHELL ASSIGNMENT GRADER".center(60))
    print("=" * 60)
    
    print(f"\nLooking for student submissions in '{SUBMISSION_DIR}'...")
    
    # Check if the directory exists
    if not os.path.exists(SUBMISSION_DIR):
        print(f"Directory '{SUBMISSION_DIR}' not found.")
        print(f"Creating '{SUBMISSION_DIR}' directory. Please place student submissions there.")
        os.makedirs(SUBMISSION_DIR, exist_ok=True)
        sys.exit(1)
    
    # Find all student directories
    student_dirs = [d for d in os.listdir(SUBMISSION_DIR) 
                   if os.path.isdir(os.path.join(SUBMISSION_DIR, d))]
    
    if not student_dirs:
        print(f"No student directories found in '{SUBMISSION_DIR}'.")
        print("Make sure each student has their own directory containing os1.c")
        sys.exit(1)
    
    # Create list of submissions (student ID and file path)
    submissions = []
    missing_files = []
    
    for student_dir in student_dirs:
        os1_path = os.path.join(SUBMISSION_DIR, student_dir, "os1.c")
        if os.path.exists(os1_path):
            submissions.append((student_dir, os1_path))
        else:
            missing_files.append(student_dir)
    
    if missing_files:
        print(f"\nWARNING: {len(missing_files)} directories without os1.c file:")
        for student_dir in missing_files:
            print(f"  - {student_dir}")
    
    if not submissions:
        print(f"No os1.c files found in any student directory.")
        print("Make sure each student directory contains a os1.c file.")
        sys.exit(1)
    
    print(f"\nFound {len(submissions)} submission(s) to grade.")
    
    # Make sure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Copy lecturer's solution to the output directory for reference
    lecturer_solution = "p_solution/os1.c"
    if os.path.exists(lecturer_solution):
        shutil.copy(lecturer_solution, os.path.join(OUTPUT_DIR, "lecturer_solution.c"))
        print(f"Copied lecturer's solution to {OUTPUT_DIR} for reference.")
    
    # Grade each submission and collect results
    all_results = []
    for student_info in submissions:
        result = grade_submission(student_info)
        all_results.append(result)
    
    # Generate a summary report
    summary_file = os.path.join(OUTPUT_DIR, "grading_summary.txt")
    with open(summary_file, "w") as f:
        f.write("OS1 SHELL GRADING SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total submissions: {len(submissions)}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Student ID".ljust(30) + "Score\n")
        f.write("-" * 50 + "\n")
        
        # Sort by score (highest first)
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        for result in all_results:
            student_id = result['student_id']
            score = result['score']
            f.write(f"{student_id.ljust(30)}{score:.1f}%\n")
    
    # Create CSV reports
    export_to_csv(all_results)
    
    # Print sorted summary to console
    print("\n" + "=" * 60)
    print("FINAL GRADING RESULTS".center(60))
    print("=" * 60)
    print("\nRanked by score (highest first):\n")
    print("Rank".ljust(6) + "Student ID".ljust(30) + "Score".ljust(10) + "Tests Passed")
    print("-" * 60)
    
    for i, result in enumerate(all_results, 1):
        print(f"{i:3}   {result['student_id'].ljust(30)}" + 
              f"{result['score']:.1f}%".ljust(10) + 
              f"{result['passed']}/{result['total']}")
    
    print("\n" + "=" * 60)
    print(f"Grading completed. All results saved to '{OUTPUT_DIR}' directory.")
    print(f"Summary report: {summary_file}")
    print(f"Clean outputs saved to '{OUTPUT_DIR}/clean_outputs' for comparison")
    print("=" * 60)

def export_to_csv(results, filename="grading_results/grading_summary.csv"):
    """Export grading results to CSV and Excel files."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Point deduction scheme
    POINT_DEDUCTIONS = {
        # Part A (os1.sh) errors
        "Script uses home directory": 6,  # Single major conceptual error
        "Directory was not created": 5,        
        "hardcoded username": 1,  # Should use $USER variable        
        "greeting.txt has wrong format": 2,
        "greeting.txt was not created": 5,
        "Missing '!' at greeting": 1,  # Very minor formatting issue
        "Wrong executable name": 3,
        "os1exe was not created": 4,
        "Compilation failed": 4,
        "Source file not found": 4,
        "ls -la output not detected": 3,
        "No ls -la output from script": 3,
        "Script execution timed out": 5,
        
        # Part B (os1.c) errors
        "Compilation Error": 20,
        "Shell prompt '$$ ' not found": 5,
        "Command failed or timed out": 3,
        "Command timed out": 3,
        "Failed to execute command": 3,
    }
    
    # Prepare data for export
    detailed_data = []
    
    for result in results:
        student_id = result["student_id"]
        score = result["score"]
        
        # Separate Part A (os1.sh) and Part B (os1.c) errors and calculate stats
        part_a_errors = []
        part_b_errors = []
        part_a_passed = 0
        part_a_total = 0
        part_b_passed = 0
        part_b_total = 0
        part_a_deductions = 0
        part_b_deductions = 0
        
        for detail in result.get("details", []):
            is_part_a = detail.get('description', '').startswith('os1.sh:')
            
            if is_part_a:
                part_a_total += 1
                if detail.get("passed", False):
                    part_a_passed += 1
            else:
                part_b_total += 1
                if detail.get("passed", False):
                    part_b_passed += 1
            
            if not detail.get("passed", False):
                error_msg = detail.get('reason', '')
                
                # Calculate point deduction
                deduction = 0
                for error_pattern, points in POINT_DEDUCTIONS.items():
                    if error_pattern in error_msg:
                        deduction = points
                        break
                
                # Add to appropriate list
                if is_part_a:
                    part_a_errors.append(error_msg)
                    part_a_deductions += deduction
                else:
                    part_b_errors.append(error_msg)
                    part_b_deductions += deduction
        
        detailed_data.append({
            "Student ID": student_id,
            "Score": f"{score:.1f}%",
            "Part A Tests Passed": f"{part_a_passed}/{part_a_total}",
            "Part B Tests Passed": f"{part_b_passed}/{part_b_total}",
            "Part A Points Deducted": part_a_deductions,
            "Part B Points Deducted": part_b_deductions,
            "Part A (os1.sh) Errors": " | ".join(part_a_errors) if part_a_errors else "",
            "Part B (os1.c) Errors": " | ".join(part_b_errors) if part_b_errors else ""
        })
    
    # Sort by student ID (filename)
    detailed_data.sort(key=lambda x: x["Student ID"])
    
    # Create detailed CSV with Part A and Part B errors
    detailed_csv = filename.replace(".csv", "_detailed.csv")
    with open(detailed_csv, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Student ID", "Score", "Part A Tests Passed", "Part B Tests Passed", 
                     "Part A Points Deducted", "Part B Points Deducted",
                     "Part A (os1.sh) Errors", "Part B (os1.c) Errors"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in detailed_data:
            writer.writerow(row)
    
    print(f"\nDetailed CSV created: {detailed_csv}")
    print(f"  - Sorted by student ID")
    print(f"  - Separate columns for Part A and Part B tests passed")
    print(f"  - Point deductions calculated for each part")
    print(f"  - Part A errors in column 7, Part B errors in column 8")
    
    # Also create a simple summary CSV
    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["student_id", "score", "passed", "total"])
        writer.writeheader()
        for result in results:
            writer.writerow({
                "student_id": result["student_id"],
                "score": result["score"],
                "passed": result["passed"],
                "total": result["total"]
            })
    
    print(f"Summary CSV created: {filename}")

if __name__ == "__main__":
    main()