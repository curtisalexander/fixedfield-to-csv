#!/usr/bin/env python

import csv
from itertools import compress
from struct import Struct

def check_ctl(incsv):
    """Check the Length variable within the control file.
    
    Length = Start - End + 1
    """
    with open(incsv, 'rU') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            assert (int(row['End']) - int(row['Start']) + 1) == int(row['Length'])

def import_ctl(incsv):
    """Import the control file that contains the starting and ending values for
    the fixed width file.

    File is structured as:

    Field_Name      Start       End     Length      Format      Notes
    field1          1           12      12          A           field 1
    field2          13          14      2           A           field 2
    field3          15          19      5           N           field 3
    """
    # U = universal newline
    with open(incsv, 'rU') as f:
        csv_reader = csv.DictReader(f)
        field_widths = [], keep_fields = []
        for fw in csv_reader:
            field_widths.append(int(fw['Length']))
            keep_fields.append(int(fw['Keep']))

    return field_widths, keep_fields

def create_fmt(field_widths, keep_fields):
    """Given two lists: 1) the field widths 2) list with a 1 or 0 indicating whether or not to keep a field,
    create a fmt string

    Field Widths - https://docs.python.org/3.4/library/struct.html

    Format      C Type      Python Type         Standard Size
    x           pad byte    no value
    c           char        bytes of length 1   1
    s           char[]      bytes
    """
    keep_fields_pos_neg = [-1 if keep == 0 else keep for keep in keep_fields]
    field_widths_pos_neg = [fw*keep for fw, keep in zip(field_widths, keep_fields_pos_neg)]
    fmt_string = ''.join('{}{}'.format(abs(fw), 'x' if fw == 0 else 's')
                                              for fw in field_widths_pos_neg)

    return fmt_string

def read_records(record_struct, f):
    """Given a struct instance and a file handle, return a tuple containing 
    all fields (as strings) for a single record
    """
    while True:
        line = f.read(record_struct.size)
        if line == b'':
            break
        yield decode_record(record_struct, line)

def _decode_record(record_struct, line):
    return tuple(s.decode() for s in record_struct.unpack_from(line))

def decode_record(rec):
    return tuple(s.decode() for s in rec)

if __name__ == '__main__':
    # Will throw an AssertionError if the Length variable within the control file is wrong
    check_ctl('/some/dir/to/keep.csv')

    field_widths, keep_fields = import_ctl('/some/dir/to/keep.csv')
    fmt_string = create_fmt(field_widths, keep_fields)
    record_struct = Struct(fmt_string)

    with open('/some/dir/to/fixedfield/split1_sample', 'rb') as infile:
        with open('/some/dir/to/fixedfield/split1_sample.csv', 'w', newline='') as outfile:
            csv_writer = csv.writer(outfile, delimiter=',')
            for rec in record_struct.iter_unpack(infile.read(record_struct.size*10)):
            # for rec in read_records(record_struct, infile):
                csv_writer.writerow(decode_record(rec))
