#!/usr/bin/env python3
import argparse
import sys
from moodle2extract import mbz

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

    args = parser.parse_args()
    m = mbz.MBZ(args.o)
    try:
        m.parse_backup(args.input)
        m.extract()
    except (KeyboardInterrupt,SystemExit):
        m.clean()
        sys.exit('Interrputed. Cleaning up and exiting.')

    m.clean()
