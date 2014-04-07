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
        die ("""You need to specify the function name and at least one 
assembly file.""")

    sym = sys.argv[1]

    func_start_re = re.compile (r"^([^.:/\s][^:\s]*):")
    call_re = re.compile (r"call\s*" + sym + r"\b")
    res = {}
    total = 0

    for file_name in sys.argv[2:]:
        in_func = False
        f = open (file_name, 'r')
        for line in f:
            match = func_start_re.search (line)
            if match:
                in_func = True
                func = match.group(1)
            match = call_re.search (line)
            if match:
                if not in_func:
                    sys.stderr.write ("Call outside function!\n")
                    continue
                total = total + 1
                if func in res:
                    res[func] = res[func] + 1
                else:
                    res[func] = 1

        f.close()

    k = res.keys()[:]
    k.sort()
    for c in k:
        print "| %s | %i |" % (c, res[c])
    print "| TOTAL | %i |" % total

if __name__ == '__main__':
    main()
