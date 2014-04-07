#!/usr/bin/python
import sys
import re


def die (s):
    "Give a string warning S to stderr and abort with exit code 1."
    sys.stderr.write (s + "\n")
    sys.exit (1)


def main():
    """The main function."""

    if (len (sys.argv) < 3):
        die ("""You need to specify the function name and the input file.""")

    sym = sys.argv[1]

#    gcc_start = re.compile (r"^" + sym + r"\..*:")
    gcc_start = re.compile (r"(^" + sym + r"\..*:)|(^" + sym + r":)")
    gcc_end = re.compile (r"\.cfi_endproc")
    icc_start = re.compile (r"-- Begin\s*" + sym + "$")
    icc_end = re.compile (r"-- End\s*" + sym + "$")

    in_func = False
    got_it = False

    for file_name in sys.argv[2:]:
        f = open (file_name, 'r')
        for line in f:
            if in_func:
                sys.stdout.write (line)
                if comp_is_gcc and gcc_end.search (line):
                    in_func = False
                    got_it = True
                    break
                elif (not comp_is_gcc) and icc_end.search (line):
                    in_func = False
                    got_it = True
                    break
                pass
            else:
                if gcc_start.search (line):
                    in_func = True
                    comp_is_gcc = True
                    sys.stdout.write (line)
                elif icc_start.search (line):
                    in_func = True
                    comp_is_gcc = False
                    sys.stdout.write (line)
                    pass
                pass
            pass
        f.close()
        if got_it:
            break

if __name__ == '__main__':
    main()
