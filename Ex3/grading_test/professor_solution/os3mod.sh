#!/bin/bash

# Script to load kernel module with 3 arguments
# $1 = text message
# $2 = syscall 1
# $3 = syscall 2

cp os3mod.c /tmp/
cd /tmp
make
insmod os3mod.ko text="$1" syscalls=$2,$3
