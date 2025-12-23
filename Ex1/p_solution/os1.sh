#!/bin/bash

mkdir $1; cd $1
echo Hey $USER! My name is BBB > greeting.txt
cp $2 .; gcc $(basename $2) -Wall -o os1exe
ls -la $3
