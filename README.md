# mbzextract

Usage: `mbzextract.py [-h] [-o OUTPUT DIR] [-e] MOODLE BACKUP FILE`

A utility to extract files from a .mbz Moodle backup file

positional arguments:
  MOODLE BACKUP FILE  A .mbz moodle backup file

optional arguments:
    -h, --help          show this help message and exit
    -o OUTPUT DIR       Set output directory. If omitted, files will be
                          extracted to a folder in the current directory
    -e                  Skip the interactive prompt and extract.
