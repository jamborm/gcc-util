#!/usr/bin/python

# Python module to represent symbol table, also implementing the
# ablitlity to load stuff from symbol table dumps (which is a running
# target, of course).

import sys
import re

class Symbol(object):
    """Symbol table symbol"""

    def __init__(self, table, name, order):
        self.name = name
        self.order = order
        self.symtable = table

        self.visibility = []
        self.availability = ""
        self.address_taken = False
        self.referring = []
        self.references = []

        self.referring_orders = []
        self.references_orders = []
        self.unhandled_attributes = []
#        print "New symbol %s/%u" % (name, order)
        return

    def __repr__(self):
        return repr((self.name, self.order))

    def __str__(self):
        return "%s/%i" % (self.name, self.order)

    def fixup (self):
        """Fixup data after the whole symtab is loaded."""

        self.referring = [self.symtable.order_to_sym[i]
                          for i in self.referring_orders]
        self.references = [self.symtable.order_to_sym[i]
                           for i in self.references_orders]
        return
    

class Function (Symbol):
    def __init__(self, table, name, order):
        Symbol.__init__ (self, table, name, order)
        self.is_clone = False
        self.is_inlined = False
        self.is_thunk = False
        self.attrs = ""

        self.callers_orders = []
        self.callees_orders = []

        self.callers = []
        self.callees = []
        self.clones = []
        self.inlinees = []
        return

    def fixup (self):
        """Fixup data after the whole symtab is loaded."""

        Symbol.fixup(self)

        if self.is_clone:
            clone_of = self.symtable.order_to_sym[self.clone_of_order]
            self.clone_of = clone_of
            clone_of.clones.append (self)
            pass

        if self.is_inlined:
            inlined_to = self.symtable.order_to_sym[self.inlined_to_order]
            self.inlined_to = inlined_to
            inlined_to.inlinees.append (self)
            pass
        else:
            self.symtable.uninlined_functions.append (self)

        self.callers = [self.symtable.order_to_sym[i]
                        for i in self.callers_orders]
        self.callees = [self.symtable.order_to_sym[i]
                        for i in self.callees_orders]

        return

    def get_origin (self):
        f = self
        while f.is_clone:
            f = f.clone_of
            pass
        return f
        

    pass

class Variable (Symbol):
    def __init__(self, table, name, order):
        Symbol.__init__ (self, table, name, order)
        self.attrs = ""
        return


class Symtab(object):
    """Symbol table of one gcc inliner run"""

    def __init__(self):
        self.order_to_sym = {}

        self.all_symbols = []
        self.all_functions = []
        self.all_variables = []
        self.uninlined_functions = []

        return

    def fixup(self):
        for f in self.all_symbols:
            f.fixup()
            pass
        return

    def dot_data(self, only_orders=False, clones=False, only_ref_to_f=False):
        """Produce output suitable as input for dot describing symtab"""

        r = ["digraph G {"]
        r.append("node [shape=ellipse, fontsize=9, height=0.1];")
        for f in self.all_functions:
            attrs = {}
            if only_orders:
                attrs["label"] = '"' + str(f.order) + '"'
            else:
                attrs["label"] = '"' + str(f) + '"'
                pass

            if f.is_inlined:
                attrs["style"] = "filled"
                attrs["fillcolor"] = "lightblue"
                pass
            elif f.is_clone:
                attrs["style"] = "filled"
                attrs["fillcolor"] = "yellowgreen"
                pass
                
            if f.is_thunk:
                attrs["shape"] = "octagon"
                attrs["style"] = "filled"
                attrs["fillcolor"] = "palevioletred"
                pass

            p = [k + "=" + attrs[k] for k in attrs.keys()]
            r.append("{0:d} [{1}]".format(f.order, ", ".join(p)))
            pass
#        del f
        r.append("")

        r.append("node [shape=box, fontsize=9, height=0.1];")
        for v in self.all_variables:
            attrs = {}
            if only_orders:
                attrs["label"] = '"' + str(v.order) + '"'
            else:
                attrs["label"] = '"' + str(v) + '"'
                pass

            p = [k + "=" + attrs[k] for k in attrs.keys()]
            r.append("{0:d} [{1}]".format(v.order, ", ".join(p)))
            pass
#        del v
        r.append("")

        for f in self.all_functions:
            for cs in f.callees:
                attrs = {}
            
                if cs.is_inlined:
                    attrs["color"] = "blue"
                else:
                    attrs["color"] = "black"
                    pass

                p = [k + "=" + attrs[k] for k in attrs.keys()]
                r.append("{0:d} -> {1:d} [{2}]".format(f.order, cs.order,
                                                           ", ".join(p)))
                pass

            if clones and f.is_clone:
                attrs = {}
                attrs["color"] = "yellowgreen"
                attrs["style"] = "dotted"
                p = [k + "=" + attrs[k] for k in attrs.keys()]
                r.append("{0:d} -> {1:d} [{2}]".format(f.clone_of.order,
                                                       f.order,
                                                       ", ".join(p)))
                pass

            pass
        r.append("")
#        del cs
#        del f

        for s in self.all_symbols:
            for ref in s.references:
                if not only_ref_to_f or isinstance (ref, Function):
                    attrs = {}
                    attrs["color"] = "black"
                    attrs["style"] = "dashed"
                    p = [k + "=" + attrs[k] for k in attrs.keys()]
                    r.append("{0:d} -> {1:d} [{2}]".format(s.order, ref.order,
                                                           ", ".join(p)))
                pass
            pass
        r.append("")
#        del s
#        del ref

        r.append("}")
        return r


# Functionality required to read symbol table from a dump file

class CommonSymbolDumpCapabilities (object):
    """Comon capabilities of symbols read from a dump file"""

    def simple_attr (self, name, line):
        """Process an attr that is a name, comma and value(s)"""

        idx = line.find(name + ":")
        if (idx != 0):
            return False
        val = line[len(name)+2:].strip()
        if val == "":
            return False
        if val.find(" ") == -1:
            return val;
        return val.split()


    def symlist_attr (self, name, line):
        """Process an attr that is a list of other symbols"""

        idx = line.find(name + ":")
        if (idx != 0):
            return False
        val = line[len(name)+2:].strip()
        if val == "":
            return False
        str_orders = re.findall (r"/[0-9]+", val)
        return [int(i[1:]) for i in str_orders]


    def common_attr (self, line):
        """Proces common attrs of functions and variables.

           Return True iff successful"""

        visibility = self.simple_attr ("Visibility", line)
        if visibility:
            self.visibility = visibility
            return True
        availability = self.simple_attr ("Availability", line)
        if availability:
            self.availability = availability
            return True
        referring = self.symlist_attr ("Referring", line)
        if referring:
            self.referring_orders = referring
            return True;
        references = self.symlist_attr ("References", line)
        if references:
            self.references_orders = references
            return True
        if line.find("Address is taken") >= 0:
            self.address_taken = True
            return True

        return False

    def unhandled_attribute (self, line):
        """Process an otherwise unhandled attribute line"""
        self.unhandled_attributes.append (line)
        return


class DumpFunction (Function, CommonSymbolDumpCapabilities):
    """Representation of call graph nodes that are read from a dump"""

    def process_clone_of (self, line):
        """Process Clone of attr, return true if done so"""

        match = re.match(r"Clone of ([^/]+)/([0-9]+)", line)
        if match:
            self.is_clone = True
            self.clone_of_order = int(match.group(2))
            return True
        return False

    def process_inlined_into (self, line):
        """Process Inlined into attr, return true if done so"""
        
        ito_re = re.compile (r"Function [^/]+/%i is inline copy in " % self.order
                             + r"([^/]+)/([0-9]+)")

        match = ito_re.match(line)
        if match:
            self.is_inlined = True
            self.inlined_to_order = int(match.group(2))
            return True
        return False

    def process_attribute (self, line):
        """Process a line that describes the function"""
        if self.common_attr (line):
            return
        attrs = self.simple_attr ("Function flags", line)
        if attrs:
            self.attrs = attrs
            return
        if self.process_clone_of (line) or self.process_inlined_into (line):
            return
        callers = self.symlist_attr ("Called by", line)
        if callers:
            self.callers_orders = callers
            return
        callees = self.symlist_attr ("Calls", line)
        if callees:
            self.callees_orders = callees
            return
        if line.strip().startswith("Thunk"):
            self.is_thunk = True

        self.unhandled_attribute (line)
        return

class DumpVariable (Variable, CommonSymbolDumpCapabilities):
    """Representation of varpool nodes that are read from a dump"""

    def process_attribute (self, line):
        """Process a line that describes the function"""
        if self.common_attr (line):
            return
        attrs = self.simple_attr ("Varpool flags", line)
        if attrs:
            self.attrs = attrs
            return

        self.unhandled_attribute (line)
        return
 

class DumpSymtab(Symtab):
    """Symbol table read from a dump file"""

    def read_dump(self, filename):
        """Read and process the symtab lines in the dump file."""

        symtab_start_re = re.compile (r"Symbol table:")
        item_start_re = re.compile (r"^([^/]+)/([0-9]+)")
        self.line_num = 0
        in_table = False
        new_symbol = False

        f = open (filename, "r")
        for line in f:
            self.line_num = self.line_num + 1
            if not in_table:
                if symtab_start_re.match (line):
                    in_table = True
                    pass
                continue
            stripped = line.strip()
            if stripped == "":
                continue

            if new_symbol:
                # complete the new symbol
                new_symbol = False
                if stripped.startswith("Type: function"):
                    current_symbol = DumpFunction(self, sym_name, sym_order)
                    self.all_functions.append (current_symbol)
                    pass
                elif stripped.startswith("Type: variable"):
                    current_symbol = DumpVariable(self, sym_name, sym_order)
                    self.all_variables.append (current_symbol)
                    pass
                else:
                    die (("Symbol %s on line %i is neither a function nor "
                         "variable.") % (sym_name, self.line_num - 1))
                    return
                self.order_to_sym[sym_order] = current_symbol
                self.all_symbols.append (current_symbol)
                pass
            elif line[0] != " ":
                # start new symbol
                match = item_start_re.match(line)
                if match:
                    new_symbol = True
                    sym_name = match.group(1)
                    sym_order = int(match.group(2))
                    pass
                else:
#                    sys.stderr.write (("Symtab seems to end in the middle of "
#                                       + "the file at line %i with string: %s")
#                                      % (self.line_num, line))
                    break
                pass
            else: 
                current_symbol.process_attribute (stripped)
                pass
            pass
        f.close()
        return

    def load_from_dump(self, filename):
        """Read the symtab info from the dump file."""

        self.read_dump (filename)
        self.fixup()
        
        self.all_symbols.sort (key=lambda sym: sym.order)
        self.all_functions.sort (key=lambda sym: sym.order)
        self.all_variables.sort (key=lambda sym: sym.order)
        self.uninlined_functions.sort (key=lambda sym: sym.order)

        return


# Functionality to show dot data in feh etc


def produce_dot (lines, filename = "symtab.png"):
    from subprocess import Popen, PIPE

    p = Popen(['dot', '-Tpng', '-o', filename], stdin=PIPE)
    p.communicate("\n".join(lines))
    return

def display_dot (lines, wait = True, filename = "symtab.png"):
    from subprocess import Popen, PIPE

    produce_dot (lines, filename = filename)
    p = Popen(['feh', filename])
    if wait:
        p.communicate()
    return


# Test main that reads a symtab from a dump file and then prints some nodes

def die (s):
    "Give a string warning S to stderr and abort with exit code 1."
    sys.stderr.write (s + "\n")
    sys.exit (1)
    pass

def symtab_main():
    """The main function."""

    if (len (sys.argv) < 2):
        die ("""You need to specify the file name.""")
        pass

    tab = DumpSymtab()
    tab.load_from_dump (sys.argv[1])

#    f = tab.order_to_sym[240]
#    print f
#    for i in f.inlinees:
#        print "  %s/%i from %i" % (i.name, i.order, i.get_origin().order)

    for s in tab.dot_data():
        print s
        pass
    display_dot (tab.dot_data ())
    return

    for f in tab.uninlined_functions:
        print ("%s/%i callers: %i, callees: %i, inlinees: %i, clones: %i"
               % (f.name, f.order, len(f.callers), len(f.callees),
                  len(f.inlinees), len(f.clones)))
    return


if __name__ == '__main__':
    symtab_main()
