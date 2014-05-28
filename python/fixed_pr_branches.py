#!/usr/bin/python

# List git branches which apparently refer to closed bugs in bugzilla
# (i.e. they have pr12345 in their name and pr 12345 is closed).

import sys
import re
import urllib2
from subprocess import Popen, PIPE, call
import xml.etree.ElementTree as ET

def die (s):
    "Give a string warning S to stderr and abort with exit code 1."
    sys.stderr.write (s + "\n")
    sys.exit (1)
    pass

def list_fixed_branches_main():

    p1 = Popen (["git", "branch"], stdout=PIPE)
    o1 = p1.communicate()
    if p1.returncode != 0:
        die ("Git did not list local branches successfully");
        return
    local_branches = o1[0].split ("\n")

    for branch in local_branches:
        branch = branch.strip().lstrip("*").strip()

        match = re.search (r"pr([0-9]{4,})", branch)
        if not match:
            continue

#        print match.group(1)
#        print branch

        url = ("https://gcc.gnu.org/bugzilla/show_bug.cgi?ctype=xml&id="
               + str(match.group(1)))
#        print url
        try:
            stream = urllib2.urlopen(url)
            tree = ET.parse(stream)
            root = tree.getroot()
            status = root.find("./bug/bug_status")
            resolution = root.find("./bug/resolution")
            stream.close()
            
            if status.text == "RESOLVED":
                print branch

        except:
            sys.stderr.write ("Failed examining branch {}\n".format(branch))
            continue
        pass
    pass

if __name__ == '__main__':
    list_fixed_branches_main()
