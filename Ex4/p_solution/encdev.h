#ifndef _ENCDEV_H
#define _ENCDEV_H

#include <linux/ioctl.h>

// specific number doesn't matter
#define MAJOR_NUM 244

// should be _IOW only! (not _IO / _IOR / _IOWR)
// const name is IOCTL_SET_KEY exactly
//		2nd param is 0
//		3rd is any number type (char/short/int/long)
#define IOCTL_SET_KEY _IOW(MAJOR_NUM, 0, unsigned long)

#endif
