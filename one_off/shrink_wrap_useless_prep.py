#!/usr/bin/python

# This script takes as input the log of IRA shrink-wrapping
# preparation function and comapres it to a log of actual performed
# shrink wrappings to figure out when the preparation did not result
# in shrink wrapping.

import sys

def die (s):
    "Give a string warning S to stderr and abort with exit code 1."
    sys.stderr.write (s + "\n")
    sys.exit (1)
    pass

if (len (sys.argv) < 3):
    die ("You need to specify the ira preparation "
         + "log file and the shrink wrap log file.")
    pass

processed = set ()

added = 0;

f1 = open (sys.argv[1])
for line in f1:
    i = line.find (": Modifying a function")
    if (i >= 0):
        s = line[0:i];
        if s in processed:
            sys.stderr.write (("Warning: adding {} for "
                               + "the second time\n").format(s));
            pass
        else:
            processed.add (s);
            added = added + 1
            pass
        pass
    pass

f1.close ()

f2 = open (sys.argv[2])
for line in f2:
    i = line.find (": Performing shrink wrapping")
    if (i >= 0):
        s = line[0:i];
        if s in processed:
            processed.remove (s)
        pass
    else:
        sys.stderr.write ("Warning: Unrecognized line in {}\n"
                          .format(sys.argv[2]))
        pass
    pass

f2.close ()

print ("{:d} were changed".format (added))
print ("{:d} functions were prepared but no shrink-wrapping occured."
       .format (len(processed)))



