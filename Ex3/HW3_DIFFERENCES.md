# HW3 2025 vs 2026 - Key Differences

## Part A Changes

### 2025: mylist.c - Linked List

- File name: `mylist.c`
- Data structure: **Doubly linked list** (MyList struct)
- Element type: `int`
- Operations:
   - Insert head/tail
   - Remove head/tail
   - Size
   - Init/Destroy

### 2026: os3q.c - Queue

- File name: `os3q.c`
- Data structure: **Queue** (QueueOS struct)
- Element type: `long`
- Operations:
   - enqueue (add to end)
   - dequeue (remove from head)
   - size
   - **sum** (NEW - sum all elements)
   - init/destroy
- Header file: `os3q.h` (provided, don't modify)
- Must use pointer-based implementation (not array)
- No global or static variables allowed
- Additional allowed functions: `printf`, `perror`, `exit`

## Part B Changes

### 2025: mymod.c - Single Syscall Replacement

- File name: `mymod.c`
- Parameters:
   - `sysnr` (int) - single syscall number
   - `msg` (string) - message
- Replaces ONE syscall: mkdir, chdir, close, or dup
- Message printed **BEFORE** syscall execution
- Wait **3 seconds** before cleanup
- Script: `mymod.sh` with 1 argument
- Message max length: 15 chars (mkdir/chdir), unlimited (close/dup)

### 2026: os3mod.c - Multiple Syscall Replacement

- File name: `os3mod.c`
- Parameters:
   - `syscalls` (int array) - **multiple** syscall numbers
   - `text` (string) - message text
- Replaces **ONE OR MORE** syscalls: mkdir, chdir, close, or dup
- Message printed **AFTER** syscall execution
- Wait **4 seconds** before cleanup
- Script: `os3mod.sh` with **3 arguments**:
   1. Target directory
   2. Syscall numbers (comma-separated, e.g., "83,32")
   3. Text message
- Message max length: 12 chars (mkdir/chdir), unlimited (close/dup)
- Example: `sudo ./os3mod.sh ~/kmod 83,32 "Hello"`

## Summary of Adaptation Needs

1. **Part A Checker**: Change from linked list checking to queue checking
   - Look for queue operations instead of list operations
   - Check for `sum()` function implementation
   - Verify `long` type usage instead of `int`
   - Check for `printf`, `perror`, `exit` usage

2. **Part B Checker**: Update for multiple syscall support
   - Check for array parameter instead of single int
   - Verify 4 second wait instead of 3
   - Check message appears AFTER syscall (not BEFORE)
   - Update script checking for 3 arguments
   - Verify comma-separated syscall numbers parsing

3. **File Names**: Update all references
   - mylist.c → os3q.c
   - mymod.c → os3mod.c
   - mymod.sh → os3mod.sh
