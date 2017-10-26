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


# skydome sampling pattern: 81 samples (theta, phi)
SkydomeSamplingPattern = [
    [000.00, 12.1151],
    [011.25, 12.1151],
    [022.50, 12.1151],
    [033.75, 12.1151],
    [045.00, 12.1151],
    [056.25, 12.1151],
    [067.50, 12.1151],
    [078.75, 12.1151],
    [090.00, 12.1151],
    [101.25, 12.1151],
    [112.50, 12.1151],
    [123.75, 12.1151],
    [135.00, 12.1151],
    [146.25, 12.1151],
    [157.50, 12.1151],
    [168.75, 12.1151],
    [180.00, 12.1151],
    [191.25, 12.1151],
    [202.50, 12.1151],
    [213.75, 12.1151],
    [225.00, 12.1151],
    [236.25, 12.1151],
    [247.50, 12.1151],
    [258.75, 12.1151],
    [270.00, 12.1151],
    [281.25, 12.1151],
    [292.50, 12.1151],
    [303.75, 12.1151],
    [315.00, 12.1151],
    [326.25, 12.1151],
    [337.50, 12.1151],
    [348.75, 12.1151],
    [345.00, 33.7490],
    [330.00, 33.7490],
    [315.00, 33.7490],
    [300.00, 33.7490],
    [285.00, 33.7490],
    [270.00, 33.7490],
    [255.00, 33.7490],
    [240.00, 33.7490],
    [225.00, 33.7490],
    [210.00, 33.7490],
    [195.00, 33.7490],
    [180.00, 33.7490],
    [165.00, 33.7490],
    [150.00, 33.7490],
    [135.00, 33.7490],
    [120.00, 33.7490],
    [105.00, 33.7490],
    [090.00, 33.7490],
    [075.00, 33.7490],
    [060.00, 33.7490],
    [045.00, 33.7490],
    [030.00, 33.7490],
    [015.00, 33.7490],
    [000.00, 33.7490],
    [000.00, 53.3665],
    [022.50, 53.3665],
    [045.00, 53.3665],
    [067.50, 53.3665],
    [090.00, 53.3665],
    [112.50, 53.3665],
    [135.00, 53.3665],
    [157.50, 53.3665],
    [180.00, 53.3665],
    [202.50, 53.3665],
    [225.00, 53.3665],
    [247.50, 53.3665],
    [270.00, 53.3665],
    [292.50, 53.3665],
    [315.00, 53.3665],
    [337.50, 53.3665],
    [315.00, 71.9187],
    [270.00, 71.9187],
    [225.00, 71.9187],
    [180.00, 71.9187],
    [135.00, 71.9187],
    [090.00, 71.9187],
    [045.00, 71.9187],
    [000.00, 71.9187],
    [000.00, 90.0000],
]


def ListSubDirectories(args):
    print("Listing subdirectories of:\n" + args.directory)
    dirs = utility.findFiles(args.directory, mode=2)
    for dir in dirs:
        print(dir)

#-HDR-----------------------------------------------------------------

'''
Function that renames HDR capture timestamp dirs to 'HH.MM.SS'.
:param args: ArgumentParser arguments parsed at program startup
:note: Warning! This function assumes that folders are already in the format 'HH-MM-SS'.
'''
def HDRRenameDirs(args):
    print("Renaming directories in:\n" + args.directory)
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

'''
Function that renames HDR files to just 'IMG_####.ETX', and does so by stripping anything else out of the name.
:param args: ArgumentParser arguments parsed at program startup
:note: This function assumes that IMG_#### already exists in the filename.
'''
def HDRRenameFiles(args):
    print("Renaming files in:\n" + args.directory)
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

'''
Function that renames HDR files starting a specified counter.
This is useful when the camera's counter overflows during capture and thus the files start over.
:param args: ArgumentParser arguments parsed at program startup
'''
def HDRRenameFilesCounter(args):
    print("Renaming photos starting from counter " + str(args.counter) + " in:\n" + args.directory)
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

'''
Function that reorganizes HDR photos into capture directories (timestamps) based on a capture interval.
The interval between captures has a default (below), but can also be specified to this script.
:param args: ArgumentParser arguments parsed at program startup
'''
def HDROrganizePhotos(args):
    print("Organizing HDR photos into timestamp directories in:\n" + args.directory)
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # grab all photos
    photos = utility.findFiles(args.directory, mode=1, ext=["jpg", "cr2"])
    if (len(photos) <= 0):
        print("No photos found in this directory.")
        return

    # we want to separate photos into directories for each capture
    captures = []
    captureIntervals = [utility.imageEXIFDateTime(photos[0])] # start with first photo timestamp
    threshold = 4       # look for next timestamp after this amount of time (next capture interval)
    if (args.interval): # user can specify capture interval
        threshold = args.interval
    captureFolder = os.path.join(args.directory, str(captureIntervals[-1].time()).replace(':', '.'))
    print(captureFolder)
    if (not args.readonly):
        os.mkdir(captureFolder)

    # for each loose photo
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

#-ASD-----------------------------------------------------------------

'''
Function that renames ASD capture dirs to just the time of capture.
:param args: ArgumentParser arguments parsed at program startup
'''
def ASDRenameDirs(args):
    print("Renaming directories in:\n" + args.directory)
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # grab all capture timestamp directories
    timeDirs = utility.findFiles(args.directory, mode=2)
    if (len(timeDirs) <= 0):
        print("No directories found at all.")
        return
    timeDirs[:] = [dir for dir in timeDirs if utility.verifyDateTime(os.path.basename(dir), "%Y-%m-%d___%H.%M.%S")]
    if (len(timeDirs) <= 0):
        print("No capture timestamp directories found.")
        return

    # for each timestamp directory
    for dir in timeDirs:
        dirBaseOld = os.path.basename(dir)
        dirBaseNew = str(datetime.strptime(dirBaseOld, "%Y-%m-%d___%H.%M.%S").time()) # we want 24h format
        dirBaseNew = dirBaseNew.replace(':', '.') # folder names can't have colons
        print("Rename: " + dirBaseOld + " to " + dirBaseNew)
        dirNew = os.path.join(os.path.dirname(dir), dirBaseNew)
        if (not args.readonly):
            os.rename(dir, dirNew)

'''
Function that renames ASD files to capture pattern index and polar coordinates.
:param args: ArgumentParser arguments parsed at program startup
:note: Warning! This function assumes each asd file in a capture directory is a different capture pattern location,
and that the ordering is the same as the capture pattern. There is no way to confirm this in the file itself by looking
at the data, so we have to make this assumption.
'''
def ASDRenameFiles(args):
    print("Renaming files in:\n" + args.directory)
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # grab all capture timestamp directories
    timeDirs = utility.findFiles(args.directory, mode=2)
    if (len(timeDirs) <= 0):
        print("No directories found at all.")
        return
    timeDirs[:] = [dir for dir in timeDirs if utility.verifyDateTime(os.path.basename(dir), "%H.%M.%S")]
    if (len(timeDirs) <= 0):
        print("No capture timestamp directories found.")
        return

    # for each timestamp directory
    for dir in timeDirs:
        print(dir)
        # grab all asd files
        asdFiles = utility.findFiles(dir, mode=1, ext=["asd"])
        if (len(asdFiles) <= 0):
            print("No asd files found in this directory.")
            return

        # THIS ASSUMES THE FILES IN THIS DIRECTORY ARE THE CAPTURE PATTERN LOCATIONS!

        # FIRST, make sure the list is NATURAL sorted (for humans, like in Windows Explorer)
        # We have to do this because someone may not have padded the filename digits.
        # If the files are not natural sorted, THEY WILL BE RENAMED TO THE WRONG CAPTURE PATTERN LOCATIONS!
        asdFiles.sort(key=utility.naturalSortKey)

        # for the number of files in the sampling pattern
        for idx in range(0, len(SkydomeSamplingPattern)):
            if (idx >= len(asdFiles)):
                print("ASD file count (" + str(idx) + ") doesn't match sample pattern locations (" + str(len(SkydomeSamplingPattern)))
                break

            # rename to format: ##_TTT.TT_PP.PPPP_.asd
            oldName = os.path.basename(asdFiles[idx])
            newName = '{0:02d}_{1:06.02f}_{2:07.04f}_.asd'.format(idx, SkydomeSamplingPattern[idx][0], SkydomeSamplingPattern[idx][1])
            print("Rename: " + oldName + " to " + newName)
            if (not args.readonly):
                os.rename(asdFiles[idx], os.path.join(dir, newName))
            if (os.path.exists(os.path.join(dir, oldName) + ".rad")):
                oldName = oldName + ".rad"
                newName = newName + ".rad"
                print("Rename: " + oldName + " to " + newName)
                if (not args.readonly):
                    os.rename(os.path.join(dir, oldName), os.path.join(dir, newName))
            if (os.path.exists(os.path.join(dir, oldName) + ".txt")):
                oldName = oldName + ".txt"
                newName = newName + ".txt"
                print("Rename: " + oldName + " to " + newName)
                if (not args.readonly):
                    os.rename(os.path.join(dir, oldName), os.path.join(dir, newName))

'''
Function that reorganizes ASD files into capture directories (timestamps) based on a capture interval.
The interval between captures has a default (below), but can also be specified to this script.
:param args: ArgumentParser arguments parsed at program startup
'''
def ASDOrganizeFiles(args):
    print("Organizing ASD files into timestamp directories in:\n" + args.directory)
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # grab all asd files
    asdFiles = utility.findFiles(args.directory, mode=1, ext=["asd"])
    if (len(asdFiles) <= 0):
        print("No asd files found in this directory.")
        return

    # # we want to separate files into directories for each capture
    # # for the number of files in the sampling pattern
    # for idx in range(0, len(SkydomeSamplingPattern)):
    #     if (idx >= len(asdFiles)):
    #         print("ASD file count (" + str(idx) + ") doesn't match sample pattern locations (" + str(len(SkydomeSamplingPattern)))
    #         break
    #
    #     fileModDate = ...
    #     captureFolder = os.path.join(args.directory, str(fileModDate.time()).replace(':', '.'))
    #     print(captureFolder)
    #     if (not args.readonly):
    #         os.mkdir(captureFolder)

    # # we want to separate files into directories for each capture
    # captures = []
    # captureIntervals = [utility.imageEXIFDateTime(photos[0])] # start with first photo timestamp
    # threshold = 4       # look for next timestamp after this amount of time (next capture interval)
    # if (args.interval): # user can specify it
    #     threshold = args.interval
    # captureFolder = os.path.join(args.directory, str(captureIntervals[-1].time()).replace(':', '.'))
    # print(captureFolder)
    # if (not args.readonly):
    #     os.mkdir(captureFolder)
    #
    # # for each file
    # for p in photos:
    #     last = captureIntervals[-1]
    #     next = utility.imageEXIFDateTime(p)
    #     # we've encountered next capture interval
    #     if ((next - last).total_seconds() / 60.0 >= threshold):
    #         captureIntervals.append(next)
    #         captureFolder = os.path.join(args.directory, str(next.time()).replace(':', '.'))
    #         print(captureFolder)
    #         if (not args.readonly):
    #             os.mkdir(captureFolder)
    #     # put photo in folder
    #     destPath = os.path.join(captureFolder, os.path.basename(p))
    #     print("Move " + os.path.basename(p) + " to " + destPath)
    #     if (not args.readonly):
    #         shutil.move(p, destPath)

#---------------------------------------------------------------------

def main():
    # handle command line args
    parser = argparse.ArgumentParser(description='Script with tools to help reorganize a directory of sky data.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_help = True
    parser.add_argument('directory', help='a directory to operate on')
    parser.add_argument('-r', '--readonly', dest='readonly', action='store_true', help='read only mode (no writes)', default=False)
    parser.add_argument('-l', '--listdirs', dest='listdirs', action='store_true', help='list sub dirs of directory', default=False)
    parser.add_argument('-hdr', '--hdr', dest='hdr', action='store_true', help='HDR mode - working w/ HDR photos')
    parser.add_argument('-asd', '--asd', dest='asd', action='store_true', help='ASD mode - working w/ ASD files')
    parser.add_argument('-d', '--renamedirs', dest='renamedirs', action='store_true', help='cleanup dir names', default=False)
    parser.add_argument('-f', '--renamefiles', dest='renamefiles', action='store_true', help='cleanup file names', default=False)
    parser.add_argument('-o', '--organize', dest='organize', action='store_true', help='organize files into dirs by capture interval', default=False)
    parser.add_argument('-n', '--interval', dest='interval', type=int, help='time interval between captures')
    # HDR specific
    parser.add_argument('-hc', '--hdrcounter', dest='hdrcounter', type=int, help='rename HDR photos starting from counter')
    args = parser.parse_args()

    # file required as parameter
    if (not args.directory):
        print("Error: no directory specified.")
        sys.exit(2)

    # do it
    if (args.listdirs):
        ListSubDirectories(args)
    elif (args.hdr):
        if (args.renamedirs):
            HDRRenameDirs(args)
        elif (args.renamefiles):
            HDRRenameFiles(args)
        elif (args.hdrcounter):
            HDRRenameFilesCounter(args)
        elif (args.organize):
            HDROrganizePhotos(args)
    elif (args.asd):
        if (args.renamedirs):
            ASDRenameDirs(args)
        elif (args.renamefiles):
            ASDRenameFiles(args)
        elif (args.organize):
            ASDOrganizeFiles(args)


if __name__ == "__main__":
    main()
