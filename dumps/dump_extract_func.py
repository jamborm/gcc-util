#!/usr/bin/python

# This script extracts a function from an rtl or tree dump.

import sys
import re


def die (s):
    "Give a string warning S to stderr and abort with exit code 1."
    sys.stderr.write (s + "\n")
    sys.exit (1)


def main():
    """The main function."""

    if (len (sys.argv) < 3):
        die ("""You need to specify the function name and the input file.
Hint: function identifications like "funcdef_no=12", decl_uid=2336"
      or symbol_order=14" should also work.""")

    sym = sys.argv[1]

    if "=" in sym:
        start = re.compile (r"^;; Function.*" + sym)
    else:
        start = re.compile (r"^;; Function[^(]*" + sym)
    end = re.compile (r"^;; Function")
    in_func = False

    for file_name in sys.argv[2:]:
        f = open (file_name, 'r')
        for line in f:
            if in_func:
                if end.search (line):
                    in_func = False
                else:
                    sys.stdout.write (line)
                    pass
                pass

            if not in_func and start.search (line):
                in_func = True
                sys.stdout.write (line)
                pass
            pass
        f.close()
        pass


if __name__ == '__main__':
    main()
