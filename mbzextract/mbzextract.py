#!/usr/bin/env python3
import argparse
import sys
import os
from mbzextract import mbz

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='''A utility to extract files
        from a .mbz Moodle backup file''')
    parser.add_argument("input",
                        metavar="MOODLE BACKUP FILE",
                        help="A .mbz moodle backup file")
    parser.add_argument("-o",
                        metavar="OUTPUT DIR",
                        help='''Set output directory. If omitted, files will be extracted to a
            folder in the current directory''')
    parser.add_argument("-e",
                        help="Skip the interactive prompt and extract.",
                        action='store_true')

    args = parser.parse_args()
    m = mbz.MBZ(args.o)
    if args.o == None:
        cwd = os.getcwd()
    else:
        cwd = args.o
    try:
        m.parse_backup(os.path.abspath(args.input))
        if args.e is not True:
            while True:
                prompt = input(
                    "Extract files to '\033[32;1m" + cwd + "\033[0m' (y)es, (n)o? ")
                if prompt == 'y' or prompt == 'yes':
                    m.extract()
                    m.clean()
                    break
                elif prompt == 'n' or prompt == 'no' or prompt == '':
                    sys.exit('Not extracting files. Exiting.')
                else:
                    print("Please answer yes or no.")
        else:
            m.extract()
            m.clean()

    except (KeyboardInterrupt):
        m.clean()
        sys.exit()
