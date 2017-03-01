#!/usr/bin/python

import sys

lines = set()
firstLine = True

for line in sys.stdin:
    if firstLine:
        sys.stdout.write(line)
        fistLine = False
        continue
    if line not in lines:
        lines.add(line)
        sys.stdout.write(line)
