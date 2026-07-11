#!/usr/bin/env python3
"""
Simple OS2 Shell Grading Script
Tests basic requirements from HW2-2026
"""
import os
import sys
import subprocess
import csv
from pathlib import Path

try:
    import pandas as pd
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# Configuration
TIMEOUT = 5
# SUBMISSIONS_DIR = "submissions"
# SUBMISSIONS_DIR = "subs"
SUBMISSIONS_DIR = "subs-26b"
RESULTS_DIR = "grading_results"

# Points for each test
POINTS = {
    "prompt": 5,
    "ls": 5,
    "pwd": 5,
    "echo": 5,
    "input_redirect": 20,
    "output_redirect": 20,
    "pipe_single": 20,
    "pipe_double": 20
}

def run_command(student_dir, command, timeout=TIMEOUT):
    """Run a command in student's shell and return output."""
    try:
        current_dir = os.getcwd()
        os.chdir(student_dir)
        
        process = subprocess.Popen(
            ["./os2"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        process.stdin.write(f"{command}\nexit\n")
        process.stdin.flush()
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            os.chdir(current_dir)
            return True, stdout, stderr
        except subprocess.TimeoutExpired:
            process.kill()
            os.chdir(current_dir)
            return False, "", "Timeout"
    except Exception as e:
        os.chdir(current_dir)
        return False, "", str(e)

def compile_student(student_dir):
    """Compile student's os2.c"""
    try:
        result = subprocess.run(
            ["gcc", "os2.c", "-o", "os2", "-Wall"],
            cwd=student_dir,
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)

def test_student(student_dir):
    """Run all tests on a student submission."""
    results = {}
    total_points = 0
    max_points = sum(POINTS.values())
    
    # Test 1: Shell Prompt
    success, stdout, stderr = run_command(student_dir, "pwd")
    if success and "$$" in stdout:
        results["prompt"] = {"passed": True, "points": POINTS["prompt"], "error": ""}
        total_points += POINTS["prompt"]
    else:
        results["prompt"] = {"passed": False, "points": 0, "error": "Shell prompt not found"}
    
    # Test 2: ls command
    success, stdout, stderr = run_command(student_dir, "ls")
    if success and "os2.c" in stdout:
        results["ls"] = {"passed": True, "points": POINTS["ls"], "error": ""}
        total_points += POINTS["ls"]
    else:
        results["ls"] = {"passed": False, "points": 0, "error": "ls failed"}
    
    # Test 3: pwd command
    success, stdout, stderr = run_command(student_dir, "pwd")
    if success and "/" in stdout:
        results["pwd"] = {"passed": True, "points": POINTS["pwd"], "error": ""}
        total_points += POINTS["pwd"]
    else:
        results["pwd"] = {"passed": False, "points": 0, "error": "pwd failed"}
    
    # Test 4: echo command
    success, stdout, stderr = run_command(student_dir, "echo hello_world")
    if success and "hello_world" in stdout:
        results["echo"] = {"passed": True, "points": POINTS["echo"], "error": ""}
        total_points += POINTS["echo"]
    else:
        results["echo"] = {"passed": False, "points": 0, "error": "echo failed"}
    
    # Test 5: Input redirection
    current_dir = os.getcwd()
    try:
        os.chdir(student_dir)
        
        with open("test_input.txt", "w") as f:
            f.write("test_content\n")
        
        # Try correct syntax: {filename (attached, no space)
        process = subprocess.Popen(
            ["./os2"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        process.stdin.write("cat {test_input.txt\nexit\n")
        process.stdin.flush()
        try:
            stdout, stderr = process.communicate(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = "", "Timeout"
        
        passed = "test_content" in stdout
        error_msg = ""
        partial = False  # logic works but wrong operator (reversed symbol or wrong position)
        
        # If correct syntax failed, diagnose the issue
        if not passed:
            # Check if they used reversed symbols: } for input
            process = subprocess.Popen(
                ["./os2"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            process.stdin.write("cat }test_input.txt\nexit\n")
            process.stdin.flush()
            try:
                stdout2, stderr2 = process.communicate(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout2 = ""
            
            if "test_content" in stdout2:
                error_msg = "PARTIAL: Used '}' (reversed) for input redirection (should be '{' per assignment)"
                partial = True
            else:
                # Check if they used the suffix form: file{ instead of prefix {file
                process = subprocess.Popen(
                    ["./os2"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                process.stdin.write("cat test_input.txt{\nexit\n")
                process.stdin.flush()
                try:
                    stdout3, stderr3 = process.communicate(timeout=TIMEOUT)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout3 = ""

                if "test_content" in stdout3:
                    error_msg = "PARTIAL: Used suffix 'file{' for input redirection (should be prefix '{file')"
                    partial = True
                elif "$$" in stdout and stdout.count("$$") > 2:
                    error_msg = "ERROR: Redirection not recognized - command not executed"
                else:
                    error_msg = f"ERROR: Input redirection failed - got: {stdout.strip()[:50]}"
        
        if passed:
            results["input_redirect"] = {"passed": True, "points": POINTS["input_redirect"], "error": ""}
            total_points += POINTS["input_redirect"]
        elif partial:
            partial_pts = POINTS["input_redirect"] // 2
            results["input_redirect"] = {"passed": False, "points": partial_pts, "error": error_msg}
            total_points += partial_pts
        else:
            results["input_redirect"] = {"passed": False, "points": 0, "error": error_msg}
        
        os.remove("test_input.txt") if os.path.exists("test_input.txt") else None
        os.chdir(current_dir)
    except Exception as e:
        os.chdir(current_dir)
        results["input_redirect"] = {"passed": False, "points": 0, "error": f"CRASH: {str(e)[:100]}"}
    
    # Test 6: Output redirection
    try:
        os.chdir(student_dir)
        
        # Try correct syntax: }filename (attached, no space)
        process = subprocess.Popen(
            ["./os2"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        process.stdin.write("echo test_output }test_output.txt\nexit\n")
        process.stdin.flush()
        try:
            stdout, stderr = process.communicate(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout = ""
        
        passed = False
        error_msg = ""
        if os.path.exists("test_output.txt"):
            with open("test_output.txt", "r") as f:
                content = f.read()
            passed = "test_output" in content
            os.remove("test_output.txt")
        
        # If correct syntax failed, diagnose the issue
        if not passed:
            partial = False  # logic works but wrong operator (reversed symbol or wrong position)
            # Check if they used reversed symbols: { for output
            process = subprocess.Popen(
                ["./os2"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            process.stdin.write("echo test_output {test_output.txt\nexit\n")
            process.stdin.flush()
            try:
                stdout2, stderr2 = process.communicate(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
            
            if os.path.exists("test_output.txt"):
                with open("test_output.txt", "r") as f:
                    content = f.read()
                if "test_output" in content:
                    error_msg = "PARTIAL: Used '{' (reversed) for output redirection (should be '}' per assignment)"
                    partial = True
                os.remove("test_output.txt")
            if not partial:
                # Check if they used the suffix form: file} instead of prefix }file
                process = subprocess.Popen(
                    ["./os2"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                process.stdin.write("echo test_output test_output.txt}\nexit\n")
                process.stdin.flush()
                try:
                    stdout3, stderr3 = process.communicate(timeout=TIMEOUT)
                except subprocess.TimeoutExpired:
                    process.kill()

                if os.path.exists("test_output.txt"):
                    with open("test_output.txt", "r") as f:
                        content = f.read()
                    if "test_output" in content:
                        error_msg = "PARTIAL: Used suffix 'file}' for output redirection (should be prefix '}file')"
                        partial = True
                    os.remove("test_output.txt")
                if not partial:
                    error_msg = "ERROR: Output file not created"
        
        if passed:
            results["output_redirect"] = {"passed": True, "points": POINTS["output_redirect"], "error": ""}
            total_points += POINTS["output_redirect"]
        elif partial:
            partial_pts = POINTS["output_redirect"] // 2
            results["output_redirect"] = {"passed": False, "points": partial_pts, "error": error_msg}
            total_points += partial_pts
        else:
            results["output_redirect"] = {"passed": False, "points": 0, "error": error_msg}
        
        os.chdir(current_dir)
    except Exception as e:
        os.chdir(current_dir)
        results["output_redirect"] = {"passed": False, "points": 0, "error": f"CRASH: {str(e)[:100]}"}
    
    # Test 7: Single Pipe
    # A broken shell echoes the command line literally ("hello ! grep hello"),
    # which would also contain "hello". Require the pipe output to contain "hello"
    # AND not contain the un-executed pipe operator/command tokens.
    success, stdout, stderr = run_command(student_dir, "echo hello ! grep hello")
    pipe_executed = "!" not in stdout and "grep" not in stdout
    if success and "hello" in stdout and pipe_executed:
        results["pipe_single"] = {"passed": True, "points": POINTS["pipe_single"], "error": ""}
        total_points += POINTS["pipe_single"]
    else:
        results["pipe_single"] = {"passed": False, "points": 0, "error": f"Pipe failed, got: {stdout.strip()[:50]}"}
    
    # Test 8: Double Pipe
    success, stdout, stderr = run_command(student_dir, "echo hello_world ! grep hello ! wc -w")
    if success and "1" in stdout.strip():
        results["pipe_double"] = {"passed": True, "points": POINTS["pipe_double"], "error": ""}
        total_points += POINTS["pipe_double"]
    else:
        results["pipe_double"] = {"passed": False, "points": 0, "error": f"Expected '1', got: {stdout.strip()[:50]}"}
    
    return results, total_points, max_points

def process_submission(student_folder):
    """Process a single student submission."""
    student_path = os.path.join(SUBMISSIONS_DIR, student_folder)
    
    # Check if os2.c exists
    if not os.path.exists(os.path.join(student_path, "os2.c")):
        return {
            "name": student_folder,
            "compiled": False,
            "compile_error": "os2.c not found",
            "results": {},
            "points": 0,
            "max_points": sum(POINTS.values()),
            "percentage": 0
        }
    
    # Compile
    compiled, compile_error = compile_student(student_path)
    if not compiled:
        return {
            "name": student_folder,
            "compiled": False,
            "compile_error": compile_error[:200],
            "results": {},
            "points": 0,
            "max_points": sum(POINTS.values()),
            "percentage": 0
        }
    
    # Run tests
    results, points, max_points = test_student(student_path)
    percentage = (points / max_points * 100) if max_points > 0 else 0
    
    return {
        "name": student_folder,
        "compiled": True,
        "compile_error": "",
        "results": results,
        "points": points,
        "max_points": max_points,
        "percentage": percentage
    }

def print_results(all_results):
    """Print results to console in a nice format."""
    print("\n" + "="*80)
    print("OS2 SHELL GRADING RESULTS")
    print("="*80)
    
    for result in all_results:
        name = result["name"]
        if not result["compiled"]:
            print(f"\n{name}: COMPILATION FAILED")
            print(f"  Error: {result['compile_error']}")
            continue
        
        percentage = result["percentage"]
        points = result["points"]
        max_points = result["max_points"]
        
        print(f"\n{name}: {percentage:.1f}% ({points}/{max_points} points)")
        
        for test_name, test_result in result["results"].items():
            status = "✓" if test_result["passed"] else "✗"
            pts = test_result["points"]
            max_pts = POINTS[test_name]
            print(f"  {status} {test_name}: {pts}/{max_pts} pts", end="")
            if test_result["error"]:
                print(f" - {test_result['error'][:60]}")
            else:
                print()
    
    # Summary
    print("\n" + "="*80)
    total_students = len(all_results)
    compiled = sum(1 for r in all_results if r["compiled"])
    avg_score = sum(r["percentage"] for r in all_results if r["compiled"]) / compiled if compiled > 0 else 0
    
    print(f"Total Students: {total_students}")
    print(f"Successfully Compiled: {compiled}")
    print(f"Average Score: {avg_score:.1f}%")
    print("="*80)

def save_to_csv(all_results):
    """Save results to CSV."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    csv_file = os.path.join(RESULTS_DIR, "grades.csv")
    
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "Student", "Compiled", "Total Points", "Max Points", "Percentage",
            "Prompt", "ls", "pwd", "echo", "Input Redirect", "Output Redirect", 
            "Single Pipe", "Double Pipe", "Errors"
        ])
        
        # Data
        for result in all_results:
            if not result["compiled"]:
                writer.writerow([
                    result["name"], "NO", 0, result["max_points"], 0,
                    "", "", "", "", "", "", "", "",
                    result["compile_error"]
                ])
            else:
                errors = []
                row = [
                    result["name"],
                    "YES",
                    result["points"],
                    result["max_points"],
                    f"{result['percentage']:.1f}%"
                ]
                
                for test_name in ["prompt", "ls", "pwd", "echo", "input_redirect", "output_redirect", "pipe_single", "pipe_double"]:
                    test_result = result["results"][test_name]
                    row.append(test_result["points"])
                    if not test_result["passed"]:
                        errors.append(f"{test_name}: {test_result['error']}")
                
                row.append(" | ".join(errors))
                writer.writerow(row)
    
    print(f"\nCSV saved to: {csv_file}")
    return csv_file

def save_to_excel(all_results, csv_file):
    """Save results to Excel with formatting."""
    if not EXCEL_AVAILABLE:
        print("Pandas not available. Skipping Excel export.")
        return
    
    try:
        excel_file = os.path.join(RESULTS_DIR, "grades.xlsx")
        
        # Read CSV
        df = pd.read_csv(csv_file)
        
        # Create Excel writer
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Grades', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Grades']
            
            # Adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"Excel saved to: {excel_file}")
    except Exception as e:
        print(f"Could not create Excel file: {e}")

def main():
    """Main function."""
    # Parse arguments
    test_limit = None
    if "--test" in sys.argv:
        test_limit = 10
        print(f"TEST MODE: Will process first {test_limit} students\n")
    elif "--student" in sys.argv:
        # Test specific students
        idx = sys.argv.index("--student")
        if idx + 1 < len(sys.argv):
            specific_students = sys.argv[idx + 1].split(",")
            print(f"Testing specific students: {', '.join(specific_students)}\n")
    
    # Get all submissions
    if not os.path.exists(SUBMISSIONS_DIR):
        print(f"Error: {SUBMISSIONS_DIR} directory not found!")
        return
    
    submissions = [d for d in os.listdir(SUBMISSIONS_DIR) 
                   if os.path.isdir(os.path.join(SUBMISSIONS_DIR, d))]
    
    if not submissions:
        print(f"No submissions found in {SUBMISSIONS_DIR}")
        return
    
    # Filter if testing
    if test_limit:
        submissions = submissions[:test_limit]
    elif "--student" in sys.argv:
        idx = sys.argv.index("--student")
        if idx + 1 < len(sys.argv):
            specific_students = sys.argv[idx + 1].split(",")
            submissions = [s for s in submissions if any(spec in s for spec in specific_students)]
    
    print(f"Grading {len(submissions)} students...\n")
    
    # Process all submissions
    all_results = []
    for i, student_folder in enumerate(submissions, 1):
        print(f"[{i}/{len(submissions)}] {student_folder}...", end=" ")
        result = process_submission(student_folder)
        all_results.append(result)
        
        if result["compiled"]:
            print(f"{result['percentage']:.1f}%")
        else:
            print("COMPILATION FAILED")
    
    # Sort by percentage
    all_results.sort(key=lambda x: x["percentage"], reverse=True)
    
    # Print results
    print_results(all_results)
    
    # Save to CSV
    csv_file = save_to_csv(all_results)
    
    # Save to Excel
    save_to_excel(all_results, csv_file)

if __name__ == "__main__":
    main()
