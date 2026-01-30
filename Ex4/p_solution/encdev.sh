#!/bin/bash

# ok if commands are differnt as long as result is the same
# may use sudo or not (since script is said to run using sudo)
cp encdev.c $1
cp encdev.h $1
cp Makefile $1
cd $1

# should use Makefile and not build manually (make -C ...)
make
insmod encdev.ko count=10 size=1024

# again should use makefile
make clean

# ok if same command, -f, etc.
rm encdev.c
rm encdev.h
rm Makefile
