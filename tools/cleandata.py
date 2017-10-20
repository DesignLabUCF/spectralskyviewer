#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# Copyright (c) 2017 University of Central Florida
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
# @since: 10/18/2017
# @summary: Script with tools to help reorganize a directory of sky data.
# ====================================================================
import sys
import os
import shutil
import argparse
from datetime import datetime
# we need utility
sys.path.insert(0, '../')
import utility


def ListSubDirectories(args):
    dirs = utility.findFiles(args.directory, mode=2)
    for dir in dirs:
        print(dir)

def HDRFixTimeDirNames(args):
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # grab all capture timestamp directories
    timeDirs = utility.findFiles(args.directory, mode=2)
    if (len(timeDirs) <= 0):
        print("No directories found at all.")
        return
    timeDirs[:] = [dir for dir in timeDirs if utility.verifyDateTime(os.path.basename(dir), "%H-%M-%S")]
    if (len(timeDirs) <= 0):
        print("No capture timestamp directories found.")
        return

    # for each timestamp directory
    for dir in timeDirs:
        dirBaseOld = os.path.basename(dir)
        dirBaseNew = str(datetime.strptime(dirBaseOld, "%H-%M-%S").time()) # we want 24h format
        dirBaseNew = dirBaseNew.replace(':', '.') # folder names can't have colons
        print("Rename: " + dirBaseOld + " to " + dirBaseNew)
        dirNew = os.path.join(os.path.dirname(dir), dirBaseNew)
        if (not args.readonly):
            os.rename(dir, dirNew)

def HDRStripTimestamps(args):
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # grab all photos
    photos = utility.findFiles(args.directory, mode=1, ext=["jpg", "cr2"])
    if (len(photos) <= 0):
        print("No photos found in this directory.")
        return
    for p in photos:
        oldName = os.path.basename(p)
        idx = oldName.find("IMG")
        if (idx < 0):
            print("Cound not find substring 'IMG' in photo.")
            continue
        newName = oldName[idx:len(oldName)]
        if (newName != oldName):
            print("Rename: " + oldName + " to " + newName)
            if (not args.readonly):
                os.rename(p, os.path.join(os.path.dirname(p), newName))

def HDRRenamePhotos(args):
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # grab all photos
    photos = utility.findFiles(args.directory, mode=1, ext=["jpg", "cr2"])
    if (len(photos) <= 0):
        print("No photos found in this directory.")
        return

    renameMap = {}
    counter = args.counter

    # for all photos
    for p in photos:
        pName, pExt = os.path.basename(p).split(".")
        newName = "IMG_"
        if pName not in renameMap.keys():
            renameMap[pName] = str(counter).zfill(4)
            newName += renameMap[pName]
            counter += 1
        else:
            newName += renameMap[pName]
        newName += "." + pExt
        print("Rename: " + pName + "." + pExt + " to " + newName)
        if (not args.readonly):
            os.rename(p, os.path.join(os.path.dirname(p), newName))

def HDROrganizePhotos(args):
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # grab all photos
    photos = utility.findFiles(args.directory, mode=1, ext=["jpg", "cr2"])
    if (len(photos) <= 0):
        print("No photos found in this directory.")
        return

    # we want to separate each photo into directories for each exposure capture
    captures = []
    captureIntervals = [utility.imageEXIFDateTime(photos[0])] # start with first photo timestamp
    threshold = 4       # look for next timestamp after this amount of time (next capture interval)
    if (args.interval): # user can specify it
        threshold = args.interval
    captureFolder = os.path.join(args.directory, str(captureIntervals[-1].time()).replace(':', '.'))
    print(captureFolder)
    if (not args.readonly):
        os.mkdir(captureFolder)

    # for any loose photos
    for p in photos:
        last = captureIntervals[-1]
        next = utility.imageEXIFDateTime(p)
        # we've encountered next capture interval
        if ((next - last).total_seconds() / 60.0 >= threshold):
            captureIntervals.append(next)
            captureFolder = os.path.join(args.directory, str(next.time()).replace(':', '.'))
            print(captureFolder)
            if (not args.readonly):
                os.mkdir(captureFolder)
        # put photo in folder
        destPath = os.path.join(captureFolder, os.path.basename(p))
        print("Move " + os.path.basename(p) + " to " + destPath)
        if (not args.readonly):
            shutil.move(p, destPath)

def ASDDecode(args):
    print("")

'''
@summary: Main module entry point.  Handles command line args and starts program.
'''
def main():
    # handle command line args
    parser = argparse.ArgumentParser(description='Script with tools to help reorganize a directory of sky data.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_help = True
    parser.add_argument('directory', help='a directory to operate on')
    parser.add_argument('-r', '--readonly', dest='readonly', action='store_true', help='read only mode (no writes)', default=False)
    parser.add_argument('-l', '--listdirs', dest='listdirs', action='store_true', help='list subdirs of directory', default=False)
    parser.add_argument('-t', '--timedir', dest='timedir', action='store_true', help='time dir name cleanup', default=False)
    parser.add_argument('-s', '--striptime', dest='striptime', action='store_true', help='strip timestamps from filenames', default=False)
    parser.add_argument('-o', '--orgphotos', dest='orgphotos', action='store_true', help='organize photos into time dirs', default=False)
    parser.add_argument('-n', '--interval', dest='interval', type=int, help='time interval between captures')
    parser.add_argument('-c', '--counter', dest='counter', type=int, help='rename photos starting from counter')
    parser.add_argument('-a', '--asd2txt', dest='asd2txt', action='store_true', help='create .txt from .asd', default=False)
    args = parser.parse_args()

    # file required as parameter
    if (not args.directory):
        print("Error: no directory specified!")
        sys.exit(2)

    # do it
    if (args.listdirs):
        print("Listing subdirectories of:\n" + args.directory)
        ListSubDirectories(args)
    elif (args.timedir):
        print("Renaming timestamp directories in:\n" + args.directory)
        HDRFixTimeDirNames(args)
    elif (args.striptime):
        print("Stripping timestamps from photo filenames in:\n" + args.directory)
        HDRStripTimestamps(args)
    elif (args.counter):
        print("Renaming photos starting from counter " + str(args.counter) + " in:\n" + args.directory)
        HDRRenamePhotos(args)
    elif (args.orgphotos):
        print("Organizing photos into timestamp directories in:\n" + args.directory)
        HDROrganizePhotos(args)
    elif (args.asd2txt):
        print("Decoding ASD files to TXT in:\n" + args.directory)
        ASDDecode(args)


if __name__ == "__main__":
    main()
