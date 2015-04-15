#!/usr/bin/python

import glob
import fileinput
import os
import sys
import subprocess
import re

import pickle

def die (s):
    "Give a string warning S to stderr and abort with exit code 1."
    sys.stderr.write(s + "\n")
    sys.exit(1)
    pass

# list of includes which are not necessary, indexed by the file containing them
unnecessary_includes = {}

# indexed by dependent, contains set of required providers on which it depends
depending_on = {}
# indexed by provider, contains set of files depending on the provider
providing_for = {}
# indexed by tuple (provider, debendent), contains set of actual error messages
# which are generated if the dependence is not met
reasons = {}

def add_dep (err_file, include, message):
    global depending_on, providing_for, reasons

#    print ("   add_dep({}, {}, ...)".format (err_file, include))


    if "/" in err_file:
        err_file = err_file[err_file.rindex("/")+1:]

    if err_file in depending_on:
        depending_on[err_file].add(include)
    else:
        depending_on[err_file] = set([include])
        
    if include in providing_for:
        providing_for[include].add(err_file)
    else:
        providing_for[include] = set([err_file])

    mkey = (include, err_file)
    if mkey in reasons:
        if not message in reasons[mkey]:
            reasons[mkey].append(message)
    else:
        reasons[mkey] = [message]

    return
    
def parse_errors (changed_file, include, errors):

    err_re = re.compile("([^:]+):(\d+):\d+: error: (.*)")
    i = 0
    j = 0
    while True:
        while i < len(errors):
            if ("error:" in errors[i]):
                break
            if ("warning:" in errors[i]):
                j = i + 1
            i = i + 1
            continue
        
        if i >= len(errors):
            return

        mo = err_re.match(errors[i])
        if not mo:
            die (("Somehow the error regular expression did not match "
                  + "on line {}").format(errors[i]))
            return

        err_file = mo.group(1)
        err_message = mo.group(3)
        
        interesting_include = ""
        while (j < i):
            if errors[j].startswith("In file included from "):
                interesting_include = ""
                assert ":" in errors[j]
                prev_include = errors[j][22:errors[j].index(':')]
                j = j + 1
                while ((j < i)
                       and errors[j].startswith("                 from ")):
                    interesting_include = prev_include
                    assert ":" in errors[j]
                    prev_include = errors[j][22:errors[j].index(':')]
                    j = j + 1
                    continue
                pass
            else:
                # errors happening during macro expansion have the above
                # explaining where the expansion happens, not where the problem
                # is
                interesting_include = ""
                j = j + 1
                pass
            continue
                    
        if interesting_include != "":
            err_file = interesting_include
            pass

        if not err_file.endswith(changed_file):
            add_dep (err_file, include, err_message) 
        i = i + 1
        j = i
        continue



def try_compiling (changed_file, include):
    global unnecessary_includes

    os.chdir("../../obj");
    cmd = subprocess.Popen("make > /dev/null", shell=True,
                           stderr=subprocess.PIPE)
    errors = []
    for line in cmd.stderr:
        if not line.startswith("make"):
            errors.append (line.rstrip("\n"))
        pass
        
    if cmd.wait() == 0:
        print ("Compilation succeeded")
        ret = False
        if changed_file in unnecessary_includes:
            unnecessary_includes[changed_file].append(include)
        else:
            unnecessary_includes[changed_file] = [include]
            pass
    else:
        parse_errors (changed_file, include, errors)
        ret = True
    return ret
        


def process_file (filename):
    i = 1
    includes = []

    if os.system ("git reset --hard &> /dev/null") != 0:
        die("git reset --hard failed")
        return
    for line in fileinput.input(filename):
        if (line.startswith ('#include "') and line.rstrip().endswith('.h"')
            and (not line.startswith ('#include "config.h"'))
            and (not line.startswith ('#include "system.h"'))
            and (not line.startswith ('#include "coretypes.h"'))):
            includes.append (i)
            pass
        i = i + 1
        pass

    srcpath = os.getcwd()
    for omit in includes:
        if os.system ("git reset --hard &> /dev/null") != 0:
            die("git reset --hard failed")
            return
        i = 1
        include = ""
        for line in fileinput.input(filename, inplace=True):
            if i == omit:
                print("")
                include = line[line.index('"') + 1:]
                include = include[:include.index('"')]
            else:
                print(line.rstrip("\n"))
                pass
            i = i + 1
            pass

        print ("Compiling {}, omitting include {} at line {}".format (filename,
                                                                      include,
                                                                      omit))
        try_compiling (filename, include)
        os.chdir (srcpath)
        pass

def output_report (depending_on, providing_for, reasons, unnecessary_includes):
    print("Generating textual report")
    f = open('dependencies_report.txt', 'w')

    f.write("---- Dependencies sorted by dependent files ----\n");
    for dependant in sorted(depending_on.keys()):
        f.write("\n{} requires the following files:\n".format(dependant))
        for prov in depending_on[dependant]:
            f.write("  - {} in order to supress the following errors:\n".format(
                prov))
            for r in reasons[(prov, dependant)]:
                f.write("      + {}\n".format(r))

    f.write ("\n---- Dependencies sorted by files providing stuff ----\n");
    for prov in sorted(providing_for.keys()):
        f.write ("\n{} provides stuff for the following files:\n".format(prov))
        for dep in providing_for[prov]:
            f.write("  - {} so that it avoids the following errors:\n".format(
                dep))
            for r in reasons[(prov, dep)]:
                f.write("      + {}\n".format(r))

    f.write ("\n---- Superfluous includes: ----\n")
    for unn in sorted(unnecessary_includes.keys()):
        f.write("\nFile {} unnecessarily includes the following files:\n".format(
            unn))
        f.write("  {}".format(", ".join(unnecessary_includes[unn])))


    f.close()
    return



def output_dot (nodes, deps):
    print("Generating dot file")
    f = open("dependencies_graph.dot", "w")
    
    f.write("digraph G {\n")

#    for n in nodes:
#        f.write('\t"{}"[label="{}"];\n'.format(

    for d in deps.keys():
        for p in deps[d]:
            f.write('\t"{}" -> "{}";\n'.format(d, p))
    f.write("}\n")

    f.close()
    return


def process_results (depending_on, providing_for, reasons, unnecessary_includes):

    output_report(depending_on, providing_for, reasons, unnecessary_includes)
    output_dot(set(depending_on.keys()) | set(providing_for.keys()),
               depending_on)

    return            

def main():
    global pickle_file_name
    global depending_on, providing_for, reasons, unnecessary_includes

    pickle_file_name = 'pickled_dependencies.pkl'

    if os.path.isfile(pickle_file_name):
        print ("Unpickling results");

        pkl_file = open(pickle_file_name, 'rb')
        depending_on = pickle.load(pkl_file)
        providing_for = pickle.load(pkl_file)
        reasons = pickle.load(pkl_file)
        unnecessary_includes = pickle.load(pkl_file)
        pkl_file.close()
    else:
        process_file ("tree-sra.c")               # !!!

#        for filename in glob.glob("*.c"):
#            process_file (filename)
#            pass

        print ("Pickling results");
        output = open(pickle_file_name, 'wb')
        pickle.dump(depending_on, output, -1)
        pickle.dump(providing_for, output, -1)
        pickle.dump(reasons, output, -1)
        pickle.dump(unnecessary_includes, output, -1)
        output.close()

    process_results (depending_on, providing_for, reasons, unnecessary_includes)
    return

if __name__ == '__main__':
    main()

