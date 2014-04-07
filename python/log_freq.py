#!/usr/bin/python

# Figure out how many times a line was printed in input, which can be
# a series of file names on the command line or standard input.

import fileinput

def process_line (line, freq_dict):
    """Either add LINE to FREQ_DICT or increment is frequency"""
    
    if line in freq_dict:
        freq_dict[line] = freq_dict[line] + 1
    else:
        freq_dict[line] = 1
        pass
    return


def main():
    """The main function."""

    freq_dict = {}
    for line in fileinput.input():
        process_line (line, freq_dict)
        pass

    if len(freq_dict.keys()) == 0:
        return 0

    numlen = 0
    for s in sorted(freq_dict.keys(),
                    cmp = lambda x,y: cmp(freq_dict[x], freq_dict[y]),
                    reverse=True):
        if numlen == 0:
            numlen = len(str(freq_dict[s]))
            pass
        print (("{0:" + str(numlen) + "d} {1}").format(freq_dict[s],
                                                        s.strip()))

    return 0

if __name__ == '__main__':
    main()
