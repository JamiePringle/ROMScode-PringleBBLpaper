#!/bin/bash

#duplicate run, don't copy *.nc files

rsync -a --exclude='ocean*.nc' $1 $2
