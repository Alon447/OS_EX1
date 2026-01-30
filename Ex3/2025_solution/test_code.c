// Test file to verify string termination detection improvements
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/syscalls.h>

MODULE_LICENSE("GPL");

static int sysnr = -1;
static char *msg = "default message";

module_param(sysnr, int, 0644);
module_param(msg, charp, 0644);

asmlinkage long (*ref_mkdir)(const char __user *pathname, umode_t mode);
asmlinkage long (*ref_chdir)(const char __user *filename);
asmlinkage long (*ref_close)(unsigned int fd);
asmlinkage long (*ref_dup)(unsigned int fildes);

asmlinkage long new_mkdir(const char __user *pathname, umode_t mode) {
    char buffer[16];
    get_user(buffer[0], pathname);
    
    // Various string termination methods that should be detected:
    buffer[15] = 0;           // Index assignment
    // Alternative: buffer[size-1] = '\0';
    // Alternative: memset(buffer, 0, 16);
    
    printk(KERN_INFO "mkdir called with path: %s\n", buffer);
    msleep(3000);
    return ref_mkdir(pathname, mode);
}

int init_module(void) {
    if (sysnr == 39) {  // mkdir
        printk(KERN_INFO "Replacing mkdir\n");
    } else if (sysnr == 80) {  // chdir  
        printk(KERN_INFO "Replacing chdir\n");
    } else if (sysnr == 3) {   // close
        printk(KERN_INFO "Replacing close\n");
    } else if (sysnr == 41) {  // dup
        printk(KERN_INFO "Replacing dup\n");
    } else {
        return -1;
    }
    
    write_cr0(read_cr0() & ~0x10000);
    sys_call_table[sysnr] = (unsigned long *)new_mkdir;
    write_cr0(read_cr0() | 0x10000);
    
    return 0;
}

void cleanup_module(void) {
    printk(KERN_INFO "Cleaning up module\n");
}
