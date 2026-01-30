# OS3 Grader Verification Against Professor's Requirements

## Part A: Queue (os3q.c) - 50 Points

### Professor's Requirements (from p_solution/os3q.c comments):

| Requirement                           | Severity   | Grader Check      | Points | Status |
| ------------------------------------- | ---------- | ----------------- | ------ | ------ |
| malloc() after lock()                 | Minor      | `malloc_in_lock`  | -5     | ✅     |
| Lock for single value read (size/sum) | Minor      | `lock_for_read`   | -3     | ✅     |
| free() before unlock                  | Minor      | `free_in_lock`    | -5     | ✅     |
| destroy() doesn't free items          | Minor      | `no_destroy_free` | -5     | ✅     |
| Static/global variables               | Major      | `static_global`   | -8     | ✅     |
| Missing/wrong condition variables     | Major      | `missing_cv`      | -10    | ✅     |
| Has main() function                   | Major/Skip | `has_main`        | -50    | ✅     |
| Missing/broken sum() function         | Major      | `missing_sum`     | -8     | ✅     |
| Using int instead of long             | Minor      | `wrong_type`      | -5     | ✅     |

**Total Possible Deductions: 104 points (capped at 50)**
**All 9 checks implemented ✅**

---

## Part B: Kernel Module (os3mod.c) - 40 Points

### Professor's Requirements (from p_solution/os3mod.c comments):

| Requirement                          | Severity      | Grader Check       | Points | Status |
| ------------------------------------ | ------------- | ------------------ | ------ | ------ |
| MODULE_LICENSE("GPL")                | Major         | `no_gpl`           | -4     | ✅     |
| All printk with KERN_INFO            | Minor         | `no_kern_info`     | -3     | ✅     |
| Buffer size 13 (12+null), not 12     | Minor         | `wrong_buffer`     | -3     | ✅     |
| Syscall BEFORE message               | Major         | `msg_before`       | -8     | ✅     |
| **MUST copy from user (get_user)**   | **MAJOR**     | `no_get_user`      | -8     | ✅     |
| Array parameter (module_param_array) | Major         | `no_array_param`   | -8     | ✅     |
| **MUST check invalid syscall**       | **MANDATORY** | `no_validation`    | -8     | ✅     |
| **MUST restore on init error**       | **MANDATORY** | `no_error_restore` | -8     | ✅     |
| Sleep 4000ms (not 2000/3000)         | Minor         | `wrong_sleep`      | -3     | ✅     |
| Restore in cleanup_module            | Minor         | `no_restore`       | -3     | ✅     |

**Total Possible Deductions: 56 points (capped at 40)**
**All 10 checks implemented ✅**

### Critical Requirements (MANDATORY):

1. ✅ **get_user()**: Students MUST use get_user loop to copy pathname from user memory
   - Professor's comment: "MUST COPY FROM USER MEMORY, otherwise major deduction"
   - Check: `'get_user' not in content`

2. ✅ **Invalid syscall check**: Students MUST validate syscall numbers
   - Professor's comment: "MUST CHECK INVALID SYSCALL NUMBER"
   - Check: Looks for \_\_NR_xxx constants and error return

3. ✅ **Restore on error**: Students MUST restore already-changed syscalls before returning error
   - Professor's comment: "MUST RESTORE syscalls if already changed"
   - Pattern: `arr_argc = i; restore_syscalls(); return -EINVAL;`
   - Check: Regex looks for restore function call before error return

---

## Part C: Script (os3mod.sh) - 5 Points

| Requirement          | Severity | Grader Check | Points | Status |
| -------------------- | -------- | ------------ | ------ | ------ |
| Handle 3 arguments   | Major    | `wrong_args` | -3     | ✅     |
| File copy commands   | Minor    | `no_copy`    | -1     | ✅     |
| make/insmod commands | Major    | `no_make`    | -2     | ✅     |

**Total Possible Deductions: 6 points (capped at 5)**
**All 3 checks implemented ✅**

---

## Part D: Makefile - 5 Points

| Requirement  | Severity | Grader Check | Points | Status |
| ------------ | -------- | ------------ | ------ | ------ |
| obj-m target | Major    | `no_obj_m`   | -3     | ✅     |
| clean target | Minor    | `no_clean`   | -2     | ✅     |

**Total Possible Deductions: 5 points**
**All 2 checks implemented ✅**

---

## Summary

### Total Checks: 24

- Part A (Queue): 9 checks
- Part B (Module): 10 checks
- Part C (Script): 3 checks
- Part D (Makefile): 2 checks

### Verification Status: ✅ COMPLETE

All requirements from professor's solution comments are implemented in the grader.

### Testing

- Tested on professor's reference solution: **PASSES** (no false positives)
- Tested on 5 student submissions: Correctly identifies real issues
- Sample scores: 70-89/100 (realistic distribution)

### Key Improvements Made:

1. Added `no_get_user` check (MANDATORY requirement)
2. Added `no_error_restore` check (MANDATORY requirement)
3. Fixed buffer size check to accept 13 or 16
4. Fixed message timing check (AFTER syscall, not before)
5. Fixed static detection to ignore helper functions
6. All regex patterns verified against professor's solution

### Notes:

- Point deductions are cumulative but capped per section
- Major issues: -8 to -10 points each
- Minor issues: -3 to -5 points each
- Auto-fail: -50 points (has main() in queue)
