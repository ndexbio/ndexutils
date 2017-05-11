#!/usr/bin/python

import sys


def main():

    lines = set()
    firstLine = True

    for line in sys.stdin:
        if firstLine:
            sys.stdout.write(line)
            firstLine = False
            continue
        if line not in lines:
            lines.add(line)
            sys.stdout.write(line)

    sys.stdout.flush()

if __name__ == '__main__':
    main()
