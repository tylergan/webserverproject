#!/bin/python

import sys

try:
    with open("file_does_not_exist", "r"):
        pass
except FileNotFoundError:
    sys.exit(1) #running a file that will send a "ran unsuccessfully" signal to runner.py

