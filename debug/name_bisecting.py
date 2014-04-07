#!/usr/bin/python

# This script together with the function in name_bisecting.c is a last
# resort and crude tool for bootstrap problem hunting.  If you face a
# hard to track bootstrap comparison failure with your patch and it is
# possible to selectively compile some files the old way and dome the
# new way, use the function in name_bisecting.c and only use the new
# way if it returns true.  Then run this script.

# The C function uses the file name of the current compiled source to
# decide whether to use the new method and does that consistently
# during each bootstrap in a series.  Together with this script they
# bisect the space of source names until they find one that is
# compiled wrong.  Of course, this only works if it is enough to
# miscompile one file to reproduce the error.

# Remember that usually there are much faster ways to debug
# miscomparisons.  On te other one, this one can do a bit of
# analysisis at night by itself.

import sys
import os
import tempfile
import subprocess

def die (s):
    "Give a string warning S to stderr and abort with exit code 1."
    sys.stderr.write (s + "\n")
    sys.exit (1)

debug_mode = True
run_num = 0;

def configure():
    """Run the configuration passed in parameters"""

    r = os.system(' '.join(sys.argv[1:]))
    return (r == 0)


def test_run(build_dir, low_s, high_s, log_msg):
    """One test run of bootstrap"""

    global debug_mode, run_num

    os.mkdir(build_dir)
    os.chdir(build_dir)
    os.system("echo %s >> %s" % (log_msg, "aaa-name-bisecting-status"))

    os.environ["NAME_BISECT_MODE"] = "BISECT"
    os.environ["NAME_BISECT_LOW"] = low_s
    os.environ["NAME_BISECT_HIGH"] = high_s

    if debug_mode:
        log_filename = (tempfile.gettempdir() + "/name_bisecting-run-"
                        + str(os.getpid()) + "-" + str(run_num))
        os.environ["NAME_BISECT_NAMELOG"] = log_filename
        pass
    elif "NAME_BISECT_NAMELOG" in os.environ:
        del os.environ["NAME_BISECT_NAMELOG"]
        pass

    configure()
    r = os.system("make -j24")
    os.chdir("..")
    os.system("rm -r " + build_dir)
    
    return (r == 0)

def main():
    """The main function"""
    global debug_mode, run_num

    if (len (sys.argv) < 2):
        die ("Please provide the configuration command (with absolute path) "
             + "as the first parameter.")
        pass

    namelog_file = tempfile.gettempdir() + "/namelog-" + str(os.getpid())
    build_dir = "name_bisect-" + str(os.getpid()) 
    os.mkdir(build_dir)
    os.chdir(build_dir)

    os.environ["NAME_BISECT_MODE"] = "GEN_ALL"
    os.environ["NAME_BISECT_NAMELOG"] = namelog_file

    if not configure():
        os.chdir("..")
        die ("Configuration command exited with non zero exit status")
        pass

    r = os.system("make -j24")
    os.chdir("..")
    os.system("rm -r " + build_dir)
    del os.environ["NAME_BISECT_NAMELOG"]

    if (r == 0):
        if not debug_mode:
            os.remove(namelog_file)
            pass
        die ("Initial run succeeded, nothing to bisect");
        pass

    if (not os.path.exists(namelog_file)):
        die ("Name log not generated, have you modified the sources?");
        pass

    proc = subprocess.Popen(["sort", "-u", namelog_file], stdout=subprocess.PIPE)
    sort_output = proc.communicate()[0]
    if not debug_mode:
        os.remove(namelog_file)
        pass
    if len(sort_output) <= 1:
        die ("Namelog empty?")
        pass

    filelist = sort_output[:-1].splitlines()
    low = 0
    high = len(filelist)-1

    while (low <> high):
        run_num = run_num + 1
        mid = low + ((high - low) / 2)

        log_msg = (("Pid %i, run %i: low=%i, high=%i, mid=%i, low_s=%s, "
                    + "mid_s=%s") %
                   (os.getpid(), run_num, low, high, mid, filelist[low],
                    filelist[mid]))
        if (debug_mode):
            log_filename = tempfile.gettempdir() + "/name_bisecting_log"
            os.system("echo %s >> %s" % (log_msg, log_filename))
            pass

        r = test_run (build_dir, filelist[low], filelist[mid], log_msg)
        if r:
            low = mid + 1
            pass
        else:
            high = mid;
            pass
        pass

    print "The following file (possibly among others) is miscompiled:"
    print filelist[low]

    return

if __name__ == '__main__':
    main()
