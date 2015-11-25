#! /usr/bin/env python3
import moodle2extract.mbz as mbz
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("input",metavar="MOODLE BACKUP FILE",help="A .mbz moodle backup file.")
    parser.add_argument("-o",metavar="OUTPUT DIR",help="Output directory. If omitted, files will be extracted to a folder in the current directory")

    args = parser.parse_args()
    m = mbz.MBZ(args.o)

    m.parse_backup(args.input)
    m.extract()
    m.clean()
