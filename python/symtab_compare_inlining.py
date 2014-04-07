#!/usr/bin/python

# This scripts takes two filenames of inline dumps as parameters,
# extracts their symbol table and compares inlining decisions in them.

import sys
import re
from symtab import *

def die (s):
    "Give a string warning S to stderr and abort with exit code 1."
    sys.stderr.write (s + "\n")
    sys.exit (1)
    pass

#by_order = True
by_order = False

def compare_functions (f1, f2):
    global by_order

    if by_order:
        if f1.order == f2.order:
            return 0
        elif f1.order < f2.order:
            return -1
        else:
            return 1
        pass
    else:
        if f1.name == f2.name:
            return 0
        elif f1.name < f2.name:
            return -1
        else:
            return 1
        pass
    pass

def report_extra_function (num, st, f):
    """Extra top-level function F in dump number NUM, symtab ST"""

    print "In file %i: extra un-inlined function %s/%i" % (num, f.name, f.order)
    if f.is_clone:
        o = f.get_origin ()
        print "  Originally a clone of %s/%i" % (o.name, o.order)
        pass
    print "  Callers: %i, Callees: %i, Inlinees: %i" % (len(f.callers),
                                                        len(f.callees),
                                                        len(f.inlinees))
    if len(f.inlinees) > 0:
        print "  Inlinees:"
        for i in f.inlinees:
            o = i.get_origin ()
            print "    %s/%i" % (o.name, o.order)
            pass
        pass
    print ""
    return

def report_extra_inlining_in_func (num, st, f, ex):
    """Extra inlinee in dump NUM in func F

EX is a tuple consisting of, in this order: inlinee object, number
of call sites inlined into F in dump NUM and number of call sites
inlined into the function in the other dump."""

    print ("In file %i: extra inlining into function %s/%i"
           % (num, f.name, f.order))

    for z in ex:
        c = z[0]
        print ("  Function %s/%i inlined %i times (as opposed to %i times)"
               % (c.name, c.order, z[1], z[2]))
        pass

    print ""
    return

def compare_same_functions (st1, st2, f1, f2):
    global by_order

    ils1 = map (lambda f: f.get_origin().order, f1.inlinees)
    ils2 = map (lambda f: f.get_origin().order, f2.inlinees)
    ils1.sort ()
    ils2.sort ()

    u1 = map (lambda u: (st1.order_to_sym[u], ils1.count(u)),
              sorted (set (ils1)))
    u2 = map (lambda u: (st2.order_to_sym[u], ils2.count(u)),
              sorted (set (ils2)))

    if not by_order:
        u1.sort (key=lambda u: u[0].name)
        u2.sort (key=lambda u: u[0].name)
        pass

    i1 = 0;
    i2 = 0;

    ex1 = []
    ex2 = []

    while True:
        if i1 >= len (u1):
            ex2.extend (map (lambda x: (x[0], x[1], 0), u2[i2:]))
            break
        if i2 >= len (u2):
            ex1.extend (map (lambda x: (x[0], x[1], 0), u1[i1:]))
            break

        z1 = u1[i1]
        z2 = u2[i2]
        
        if compare_functions (z1[0], z2[0]) == 0:
            i1 = i1 + 1
            i2 = i2 + 1

            if z1[1] == z2[1]:
                continue
            if z1[1] > z2[1]:
                ex1.append ((z1[0], z1[1], z2[1]))
                pass
            else:
                ex2.append ((z1[0], z2[1], z1[1]))
                pass
            pass
        elif compare_functions (z1[0], z2[0]) < 0:
            ex1.append((z1[0], z1[1], 0))
            i1 = i1 + 1
            pass
        else:
            ex2.append((z2[0], z2[1], 0))
            i2 = i2 + 1
            pass
        pass

    if len (ex1) > 0:
        report_extra_inlining_in_func (1, st1, f1, ex1)
        pass
    if len (ex2) > 0:
        report_extra_inlining_in_func (2, st2, f2, ex2)
        pass

    return

def list_all_remaining (num, st, it):
    try:
        while True:
            f = it.next()
            report_extra_function (num, st, f)
            pass
    except StopIteration:
        pass
    return

def main():
    """The main function."""
    global by_order

    if (len (sys.argv) < 3):
        die ("""You need to specify the two file names of inline dumps.""")
        pass

    st1 = DumpSymtab()
    st1.load_from_dump (sys.argv[1])

    st2 = DumpSymtab()
    st2.load_from_dump (sys.argv[2])

    l1 = filter (lambda sym: len(sym.callers)>0, st1.uninlined_functions)
    l2 = filter (lambda sym: len(sym.callers)>0, st2.uninlined_functions)
    
    if not by_order:
        l1.sort (key=lambda sym: sym.name)
        l2.sort (key=lambda sym: sym.name)
        pass

    i1 = iter(l1)
    i2 = iter(l2)

    fetch1 = True
    fetch2 = True

    while True:
        if fetch1:
            try:
                f1 = i1.next()
                fetch1 = False
            except StopIteration:
                list_all_remaining (2, st2, i2)
                break;
            pass

        if fetch2:
            try:
                f2 = i2.next()
                fetch2 = False
            except StopIteration:
                list_all_remaining (1, st1, i1)
                break;
            pass

        if compare_functions (f1, f2) == 0:
            compare_same_functions (st1, st2, f1, f2)
            fetch1 = True
            fetch2 = True
            pass
        elif compare_functions (f1, f2) < 0:
            report_extra_function (1, st1, f1)
            fetch1 = True
            pass
        else:
            report_extra_function (2, st2, f2)
            fetch2 = True
            pass
        pass
            
#    for f in l1:
#        print ("%s/%i callers: %i, callees: %i, inlinees: %i, clones: %i"
#               % (f.name, f.order, len(f.callers), len(f.callees), len(f.inlinees),
#                  len(f.clones)))
#        pass
#    print "----------------------------------------"
#    for f in l2:
#        print ("%s/%i callers: %i, callees: %i, inlinees: %i, clones: %i"
#               % (f.name, f.order, len(f.callers), len(f.callees), len(f.inlinees),
#                  len(f.clones)))
#        pass
    return

if __name__ == '__main__':
    main()
