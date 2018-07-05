#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# Copyright (c) 2018 University of Central Florida
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ====================================================================
# @author: Joe Del Rocco
# @since: 06/25/2018
# @summary: Script to search/tweak SkyDataViewer exported datasets.
# ====================================================================
import sys
import os
import csv
import argparse


def CountSamples(args):
    n = 0
    with open(args.file, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        next(reader, None)
        n = sum(1 for row in reader)
    print("Samples: " + str(n))

def FindDuplicates(args):
    samples = {}
    with open(args.file, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        header = next(reader, None)
        args.wavesidx = header.index("350")
        isi = header.index("SamplePatternIndex")
        idt = header.index("Date")
        itm = header.index("Time")
        PrintRow(args, header)
        for row in reader:
            key = str(row[idt]) + " " + str(row[itm]) + " " + str(row[isi])
            if key in samples:
                #Log(args, samples[key])
                PrintRow(args, row)
            else:
                samples[key] = row

def FindBySky(args):
    with open(args.file, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        header = next(reader, None)
        args.wavesidx = header.index("350")
        isc = header.index("SkyCover")
        PrintRow(args, header)
        for row in reader:
            if int(row[isc]) == args.skycover:
                PrintRow(args, row)

def PrintRow(args, row):
    if args.hidewaves:
        print(*row[0:args.wavesidx], sep=',')
    else:
        print(*row, sep=',')

#---------------------------------------------------------------------

def main():
    # handle command line args
    parser = argparse.ArgumentParser(description='Script to search/tweak SkyDataViewer exported datasets. This script does not make any changes to the original file. All results are written to standard out.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_help = True
    parser.add_argument('file', help='a sky data export file')
    parser.add_argument('-w', '--hidewaves', dest='hidewaves', action='store_true', help='hide wavelength data (easier to read)')
    parser.add_argument('-n', '--count', dest='count', action='store_true', help='count number of samples')
    parser.add_argument('-d', '--dups', dest='dups', action='store_true', help='find duplicates')
    parser.add_argument('-s', '--skycover', dest='skycover', type=int, help='find data by skycover')
    args = parser.parse_args()

    # file required as parameter
    if not args.file:
        print("Error: no data file specified.")
        sys.exit(2)
    # file not found
    elif not os.path.exists(args.file):
        print("Error: data file not found: '" + args.file + "'")
        sys.exit(2)

    # do it
    if args.count:
        CountSamples(args)
    elif args.dups:
        FindDuplicates(args)
    elif args.skycover:
        FindBySky(args)


if __name__ == "__main__":
    main()
