#include <linux/kernel.h>  
#include <linux/module.h>  
#include <linux/fs.h>  
#include <linux/slab.h>  
#include <linux/uaccess.h>
MODULE_LICENSE("GPL");

#include "encdev.h"

#define NAME "encdev"

// MAJOR number of module
static int major;

// buffer for each device
static char** devices;

// PARAMETERS
static int size;
static int count;
module_param(size, int, 0000);
module_param(count, int, 0000);

// FILE_DATA struct for each open file
struct file_data {
	int		minor;
	char	key;
};

static int device_open(struct inode *inode, struct file *filp)
{
	struct file_data* fd;
    int minor = MINOR(inode->i_rdev);

	// MUST check minor is within 'count' range
    if (minor >= count) {
        printk(KERN_ERR "%s: invalid minor %d\n", NAME, minor);
        return -ENODEV;
    }

	fd = kmalloc(count * sizeof(char*), GFP_KERNEL);
	if (!fd) {
		printk(KERN_ALERT "%s: memory allocation failed\n", NAME);
		return -ENOMEM;
	}
	fd->minor = minor;
	// KEY is set per open file, not per device
	// should not be shared for same device!
	fd->key = 0;
	filp->private_data = fd;

    printk(KERN_INFO "%s: device_open minor=%d\n", NAME, minor);
    return 0;
}

int device_release(struct inode *inode, struct file *filp)
{
	// MUST free allocated memory
	kfree(filp->private_data);
    printk(KERN_INFO "%s: device_release\n", NAME);
    return 0;
}

static ssize_t device_read(struct file *file, char __user *buf, size_t len, loff_t *offset)
{
	struct file_data *fd;
	size_t i;
	ssize_t ret = 0;

	printk(KERN_INFO "%s: device_read %zu bytes\n", NAME, len);

	// MUST handle offset (parameter or own method to track offset)
    fd = (struct file_data*) file->private_data;

	// MUST return EOF if at or beyond end-of-file
    if (*offset >= size)
        return 0;	// 0 == EOF

    for (i = 0; (i < len) && (*offset+i < size); ++i) {
		// equals: buf[i] = devices[...]
		put_user(devices[fd->minor][*offset+i], buf+i);
		++ret;
		// no need to check put_user, but ok if they do
    }

	*offset += ret;
    return ret;
}

static ssize_t device_write(struct file *file, const char __user *buf, size_t len, loff_t *offset)
{
	struct file_data *fd;
	size_t i;
	ssize_t ret = 0;

    printk(KERN_INFO "%s: device_read %zu bytes\n", NAME, len);

	// MUST handle offset (parameter or own method to track offset)
    fd = (struct file_data*) file->private_data;

	// MUST return error if at or beyond end-of-file
    if (*offset >= size)
        return -ENOSPC; // specific error code doesn't matter

    for (i = 0; (i < len) && (*offset+i < size); ++i) {
		// equals: buf[i] = devices[...]
		get_user(devices[fd->minor][*offset+i], buf+i);
		++ret;
		// no need to check get_user, but ok if they do
    }

	*offset += ret;
    return ret;
}

static long device_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	// MUST check for cmd
    if (cmd == IOCTL_SET_KEY) {
		struct file_data* fd;

		// MUST check arg is in correct range
		if ((arg < 0) || (arg > 255))
            return -EINVAL;

		fd = (struct file_data*) file->private_data;
		fd->key = (unsigned char)arg;

        printk(KERN_INFO "%s: ioctl set key=%lu\n", NAME, arg);
        return 0;
    }

	// MUST return error on invalid cmd
    return -EINVAL;
}

static loff_t device_llseek(struct file *file, loff_t off, int whence)
{
	// OK if using their own way to track offset instead of built-in f_pos
    loff_t newpos;

	// MUST check whence and update offset accordingly
    switch (whence) {
        case SEEK_SET:
            newpos = off;
            break;
        case SEEK_CUR:
            newpos = file->f_pos + off;
            break;
        case SEEK_END:
            newpos = size + off;
            break;
        default:
            return -EINVAL;
    }

	// OK if checking max of (size-1) as well
    if (newpos < 0)
        return -EINVAL;
	// MUST return new offset
    return newpos;
}

// MUST have exactly all of these fields (no more no less)
struct file_operations fops = {
    .owner = THIS_MODULE,
    .open = device_open,
    .release = device_release,
    .read = device_read,
    .write = device_write,
    .unlocked_ioctl = device_ioctl,
    .llseek = device_llseek,
};

// -1 if different function name (with marco at the end)
int init_module(void)
{
    int i;

	// MUST check parameters
    if (size <= 0 || count <= 0) {
        printk(KERN_ALERT "%s: invalid parameters size=%d count=%d\n", NAME, size, count);
        return -EINVAL;
    }

	// correct way to allocate (MUST check for success)
    devices = kmalloc(count * sizeof(char*), GFP_KERNEL);
    if (!devices) {
        return -ENOMEM;
    }

	// initialize all cells of the dynamioc array
    for (i = 0; i < count; i++) {
        devices[i] = kmalloc(size * sizeof(char), GFP_KERNEL);
		// MUST free memory if failed
        if (!devices[i]) {
			for (; i>=0; --i)
				kfree(devices[i]);
			kfree(devices);

			// specific error code doesn't matter
            return -ENOMEM;
		}
		devices[i] = 0;
	}

	// MUST check return values
    major = register_chrdev(0, NAME, &fops);
    if (major < 0) {
        printk(KERN_ALERT "Module %s registration failed: %d\n", NAME, major);
        return major;
    }

    printk(KERN_INFO "Module %s registered, major number is: %d\n", NAME, major);
    return 0;
}

// -1 if different function name (with marco at the end)
void cleanup_module(void)
{
	// MUST free all memory and unregister
    int i;
    for (i = 0; i < count; i++) {
        kfree(devices[i]);
    }
    kfree(devices);
    unregister_chrdev(major, NAME);
    printk(KERN_INFO "Module %s unregistered\n", NAME);
}
