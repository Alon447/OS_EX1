#include <linux/module.h>
#include <linux/kernel.h>
MODULE_LICENSE("GPL");

#include <linux/syscalls.h>
#include <linux/delay.h>

// make sure all output is with printk
// all printk calls begin with KERN_INFO (minor deduction if not)

static int syscalls[4];
static int arr_argc;
static char *text;

module_param(text, charp, 0000);
MODULE_PARM_DESC(text, "String message"); // not mandatory

module_param_array(syscalls, int, &arr_argc, 0000);
MODULE_PARM_DESC(syscalls, "Array of syscall numbers (max 4)");

unsigned long **sys_call_table;
unsigned long original_cr0;

asmlinkage long (*ref_mkdir)(const char __user *pathname, umode_t mode);
asmlinkage long new_mkdir(const char __user *pathname, umode_t mode)
{
	int i;
	long ret;
	char kpath_name[13]; // ENSURE THIS IS 13 (not 12)

	// syscall is BEFORE text
	ret = ref_mkdir(pathname, mode);

	// MUST COPY FROM USER MEMORY, otherwise major deduction
	// ensure loop of 12 -- array size -1
	for (i = 0; i < 12; i++)
		get_user(kpath_name[i], pathname + i);
	
	kpath_name[12] = '\0'; // also ensure 12 (last cell)

	// ok if message is different, as long as it contains 'text' and pathname
	// must use KERN_INFO before print - minor deduction if not
	printk(KERN_INFO "<mkdir> %s: %s\n", text, kpath_name);

	return ret;
}

asmlinkage long (*ref_chdir)(const char __user *pathname);
asmlinkage long new_chdir(const char __user *pathname)
{
	// (same comments as mkdir)
	int i;
	long ret;
	char kpath_name[16];

	ret = ref_chdir(pathname);

	for (i = 0; i < 15; i++)
		get_user(kpath_name[i], pathname + i);
	kpath_name[15] = '\0';

	printk(KERN_INFO "<chdir> %s: %s\n", text, kpath_name);

	return ret;
}

asmlinkage long (*ref_close)(unsigned int fd);
asmlinkage long new_close(unsigned int fd)
{
	// syscall is BEFORE text
	long ret = ref_close(fd);
	printk(KERN_INFO "<close> %s: %d\n", text, fd);
	return ret;
}

asmlinkage long (*ref_dup)(unsigned int fildes);
asmlinkage long new_dup(unsigned int fildes)
{
	// syscall is BEFORE text
	long ret = ref_dup(fildes);
	printk(KERN_INFO "<dup> %s: %d\n", text, fildes);
	return ret;
}

static unsigned long **acquire_sys_call_table(void)
{
	unsigned long int offset = PAGE_OFFSET;
	unsigned long **sct;

	while (offset < ULLONG_MAX) {
		sct = (unsigned long **)offset;

		if (sct[__NR_close] == (unsigned long *) sys_close)
			return sct;

		offset += sizeof(void *);
	}
	return NULL;
}

void* replace_syscall(int sysnum, void* newcall)
{
	void* oldcall;

	original_cr0 = read_cr0();
	write_cr0(original_cr0 & ~0x00010000);
	oldcall = (void *)sys_call_table[sysnum];
	sys_call_table[sysnum] = (unsigned long *)newcall;
	write_cr0(original_cr0);

	return oldcall;
}

void restore_syscalls(void)
{
	int i;
	for (i = 0; i < arr_argc; ++i) {
		if (syscalls[i] == __NR_mkdir) {
			printk(KERN_INFO "Restoring mkdir\n");
			replace_syscall(__NR_mkdir, ref_mkdir);
		}
		else if (syscalls[i] == __NR_chdir) {
			printk(KERN_INFO "Restoring chdir\n");
			replace_syscall(__NR_chdir, ref_chdir);
		}
		else if (syscalls[i] == __NR_close) {
			printk(KERN_INFO "Restoring close\n");
			replace_syscall(__NR_close, ref_close);
		}
		else if (syscalls[i] == __NR_dup) {
			printk(KERN_INFO "Restoring dup\n");
			replace_syscall(__NR_dup, ref_dup);
		}
	}
}

int init_module(void) 
{
	int i;
	// ON ERROR - doesn't matter which negative value is returned (-1 is ok)

	// non-mandatory check - may assume text is not empty
	if (text == NULL) {
		printk(KERN_INFO "Empty 'text' parameter\n");
		return -EINVAL;
	}
	// MANDATORY check - no syscall numbers
	if (arr_argc == 0) {
		printk(KERN_INFO "No syscall numbers provided\n"); // not mandatory
		return -EINVAL;
	}
	// MANDATORY check - can't find syscall table
	if(!(sys_call_table = acquire_sys_call_table())) {
		printk(KERN_INFO "Failed to find syscall table\n"); // not mandatory
		return -EIO;
	}

	// ok to use switch or any other method
	// also ok if it's not modular
	for (i = 0; i < arr_argc; ++i) {
		if (syscalls[i] == __NR_mkdir) {
			printk(KERN_INFO "Intercepting mkdir\n");
			ref_mkdir = replace_syscall(__NR_mkdir, new_mkdir);
		}
		else if (syscalls[i] == __NR_chdir) {
			printk(KERN_INFO "Intercepting chdir\n");
			ref_chdir = replace_syscall(__NR_chdir, new_chdir);
		}
		else if (syscalls[i] == __NR_close) {
			printk(KERN_INFO "Intercepting close\n");
			ref_close = replace_syscall(__NR_close, new_close);
		}
		else if (syscalls[i] == __NR_dup) {
			printk(KERN_INFO "Intercepting dup\n");
			ref_dup = replace_syscall(__NR_dup, new_dup);
		}
		else {
			// MUST CHECK INVALID SYSCALL NUMBER
			printk(KERN_INFO "Invalid syscall number: %d\n", syscalls[i]); // printk not mandatory

			// MUST RESTORE syscalls if already changed
			arr_argc = i;
			restore_syscalls();

			return -EINVAL; // MANDATORY
		}
	}
	return 0;
}

void cleanup_module(void) 
{
	if(!sys_call_table) {
		return;
	}
	restore_syscalls();
	
	// make sure it's 4000 and not 2000/3000 (copied solution without following instructions)
	// minor deduction otherwise
	msleep(4000);
}
