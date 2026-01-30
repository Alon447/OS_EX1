#!/usr/bin/env python3
"""
Test script to verify function pointer detection improvements
"""
import re

# Sample student code patterns from the provided examples
test_cases = [
    # Student 1 - orig_ prefix
    """
    asmlinkage long (*orig_mkdir)(const char __user *pathname, umode_t mode);
    asmlinkage long (*orig_chdir)(const char __user *pathname);
    asmlinkage long (*orig_close)(unsigned int fd);
    asmlinkage long (*orig_dup)(unsigned int fildes);
    """,
    
    # Student 2 - ref_ prefix
    """
    asmlinkage long (*ref_close)(unsigned int);
    asmlinkage long (*ref_dup)(unsigned int);
    asmlinkage long (*ref_chdir)(const char __user*);
    asmlinkage long (*ref_mkdir)(const char __user*, umode_t);
    """,
    
    # Student 3 - original_ prefix
    """
    asmlinkage long (*original_chdir)(const char __user*);
    asmlinkage long (*original_mkdir)(const char __user*, umode_t);
    asmlinkage long (*original_close)(unsigned int);
    asmlinkage long (*original_dup)(unsigned int);
    """,
]

def test_function_pointer_detection(content):
    """Test the improved function pointer detection logic"""
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
    
    return found_pointers

def test_string_termination_detection(content):
    """Test the improved string termination detection logic"""
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
    
    for i, pattern in enumerate(string_termination_patterns):
        if re.search(pattern, content, re.IGNORECASE):
            if i < 6:
                method = "index assignment"
            elif i < 8:
                method = "memory clearing function"
            elif i < 10:
                method = "array initialization"
            else:
                method = "null character"
            return True, method
    
    return False, ""

# Test function pointer detection
print("Testing Function Pointer Detection:")
print("=" * 50)

for i, test_case in enumerate(test_cases, 1):
    found = test_function_pointer_detection(test_case)
    print(f"Test Case {i}: Found {len(found)} function pointers: {found}")

# Test string termination detection
print("\nTesting String Termination Detection:")
print("=" * 50)

string_test_cases = [
    "char buffer[16] = {0};",           # Array initialization
    "buffer[15] = '\\0';",              # Index assignment
    "buffer[copied] = '\\0';",          # Dynamic index assignment
    "memset(buffer, 0, 16);",           # Memory clearing
    "kpath[copied > 15 ? 15 : copied] = '\\0';",  # Complex assignment
]

for i, test_case in enumerate(string_test_cases, 1):
    found, method = test_string_termination_detection(test_case)
    print(f"Test Case {i}: {test_case}")
    print(f"  Result: {'✅' if found else '❌'} {method if found else 'Not detected'}")
