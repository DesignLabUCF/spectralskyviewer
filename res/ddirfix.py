#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# Copyright (c) 2017-2018 Joe Del Rocco
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
# @summary: Script to clean/organize a directory of sky data for use with SkyDataViewer.
# ====================================================================
import sys
import os
import shutil
import argparse
from datetime import datetime, timedelta
from PIL import Image
# we need our utilities
sys.path.insert(0, '../')
import utility
import utility_data


#-----------------------------
# Sampling pattern is hardcoded for now
# TODO: support loading different sampling patterns from this script
#-----------------------------
SamplingPattern = [
    (000.00, 12.1151),
    (011.25, 12.1151),
    (022.50, 12.1151),
    (033.75, 12.1151),
    (045.00, 12.1151),
    (056.25, 12.1151),
    (067.50, 12.1151),
    (078.75, 12.1151),
    (090.00, 12.1151),
    (101.25, 12.1151),
    (112.50, 12.1151),
    (123.75, 12.1151),
    (135.00, 12.1151),
    (146.25, 12.1151),
    (157.50, 12.1151),
    (168.75, 12.1151),
    (180.00, 12.1151),
    (191.25, 12.1151),
    (202.50, 12.1151),
    (213.75, 12.1151),
    (225.00, 12.1151),
    (236.25, 12.1151),
    (247.50, 12.1151),
    (258.75, 12.1151),
    (270.00, 12.1151),
    (281.25, 12.1151),
    (292.50, 12.1151),
    (303.75, 12.1151),
    (315.00, 12.1151),
    (326.25, 12.1151),
    (337.50, 12.1151),
    (348.75, 12.1151),
    (345.00, 33.7490),
    (330.00, 33.7490),
    (315.00, 33.7490),
    (300.00, 33.7490),
    (285.00, 33.7490),
    (270.00, 33.7490),
    (255.00, 33.7490),
    (240.00, 33.7490),
    (225.00, 33.7490),
    (210.00, 33.7490),
    (195.00, 33.7490),
    (180.00, 33.7490),
    (165.00, 33.7490),
    (150.00, 33.7490),
    (135.00, 33.7490),
    (120.00, 33.7490),
    (105.00, 33.7490),
    (090.00, 33.7490),
    (075.00, 33.7490),
    (060.00, 33.7490),
    (045.00, 33.7490),
    (030.00, 33.7490),
    (015.00, 33.7490),
    (000.00, 33.7490),
    (000.00, 53.3665),
    (022.50, 53.3665),
    (045.00, 53.3665),
    (067.50, 53.3665),
    (090.00, 53.3665),
    (112.50, 53.3665),
    (135.00, 53.3665),
    (157.50, 53.3665),
    (180.00, 53.3665),
    (202.50, 53.3665),
    (225.00, 53.3665),
    (247.50, 53.3665),
    (270.00, 53.3665),
    (292.50, 53.3665),
    (315.00, 53.3665),
    (337.50, 53.3665),
    (315.00, 71.9187),
    (270.00, 71.9187),
    (225.00, 71.9187),
    (180.00, 71.9187),
    (135.00, 71.9187),
    (090.00, 71.9187),
    (045.00, 71.9187),
    (000.00, 71.9187),
    (000.00, 90.0000),
]


'''
Simple function to list all subdirectories of a directory.
:param args: ArgumentParser arguments parsed at program startup
'''
def ListSubDirectories(args):
    print("Listing subdirectories of:\n" + args.directory)
    dirs = utility.findFiles(args.directory, mode=2)
    for dir in dirs:
        print(dir)

'''
'''
def CorrelateCaptures(args):
    print("Finding HDR/ASD capture times w/in " + str(args.correlatecaptures) + "s in:\n" + args.directory)
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # grab all capture DATE directories
    dateDirs = utility.findFiles(args.directory, mode=2)
    if (len(dateDirs) <= 0):
        print("No directories found at all.")
        return
    dateDirs[:] = [dir for dir in dateDirs if utility.verifyDateTime(os.path.basename(dir), "%Y-%m-%d")]
    if (len(dateDirs) <= 0):
        print("No capture date directories found.")
        return

    # iterate through all capture dates and find all HDR and ASD captures
    hdrCaptures = []
    asdCaptures = []
    correlatedCaptures = []
    for datedir in dateDirs:
        #print(datedir)

        # grab all capture HDR captures
        hdrDir = os.path.join(datedir, "HDR")
        hdrCaptures = utility.findFiles(hdrDir, mode=2)
        if (len(hdrCaptures) <= 0):
            print("No HDR directories found at all.")
            return
        hdrCaptures = [(datetime.strptime(os.path.basename(datedir) + " " + os.path.basename(dir), '%Y-%m-%d %H.%M.%S'), dir) for dir in hdrCaptures if utility.verifyDateTime(os.path.basename(dir), "%H.%M.%S")]
        if (len(hdrCaptures) <= 0):
            print("No HDR captures found.")
            return
        #for capture in hdrCaptures:
        #    print(capture[0], capture[1])

        # grab all capture ASD captures
        asdDir = os.path.join(datedir, "ASD")
        asdCaptures = utility.findFiles(asdDir, mode=2)
        if (len(asdCaptures) <= 0):
            print("No ASD directories found at all.")
            return
        asdCaptures = [(datetime.strptime(os.path.basename(datedir) + " " + os.path.basename(dir), '%Y-%m-%d %H.%M.%S'), dir) for dir in asdCaptures if utility.verifyDateTime(os.path.basename(dir), "%H.%M.%S")]
        if (len(asdCaptures) <= 0):
            print("No ASD captures found.")
            return
        #for capture in asdCaptures:
        #    print(capture[0], capture[1])

        # correlate HDR to ASD captures
        for i in range(0, len(hdrCaptures)):
            for j in range(0, len(asdCaptures)):
                diff = abs((hdrCaptures[i][0] - asdCaptures[j][0]).total_seconds())
                #print(hdrCaptures[i][0], asdCaptures[j][0], diff)
                if (diff <= args.correlatecaptures):
                    correlatedCaptures.append((hdrCaptures[i][0], hdrCaptures[i][1], asdCaptures[j][0], asdCaptures[j][1]))

    print("Found " + str(len(correlatedCaptures)) + " captures w/in " + str(args.correlatecaptures) + "s")
    prev = None
    for capture in correlatedCaptures:
        if prev != capture[0].date():
            print(capture[1])
            print(capture[3])
            prev = capture[0].date()
        print("HDR:", capture[0], "ASD:", capture[2])
    print("Found " + str(len(correlatedCaptures)) + " captures w/in " + str(args.correlatecaptures) + "s")

'''
Function that offsets capture directories (times of day) by a specific amount.
This is used to correct/account for time shift errors in the photo EXIF data (like daylight savings).
:param args: ArgumentParser arguments parsed at program startup
:note: This can be used on both HDR or ASD data because it is simply offsetting the capture time directory.
'''
def OffsetCaptureTimes(args):
    print("Offsetting all capture time directories in:\n" + args.directory)
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
        print("No capture time directories found.")
        return

    # prevent collisions between directories with the same name
    # sort directories ascending when timeoffset is negative
    if args.timeoffset < 0:
        timeDirs.sort()
    # sort directories descending when timeoffset is positive
    elif args.timeoffset > 0:
        timeDirs.sort(reverse=True)

    # for each timestamp directory
    for dir in timeDirs:
        oldname = os.path.basename(dir)
        oldtime = datetime.strptime(oldname, "%H.%M.%S")
        newtime = oldtime + timedelta(hours=args.timeoffset)
        newname = str(newtime.time()).replace(':', '.') # folder names can't have colons
        print("Rename: " + oldname + " to " + newname)
        if (not args.readonly):
            os.rename(dir, os.path.join(os.path.dirname(dir), newname))

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
        print("No capture time directories found.")
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
Function that rotate HDR photos by some specified degrees (+/-).
This is useful an HDR image (or set of images in a capture) are offset by some rotation.
:param args: ArgumentParser arguments parsed at program startup
'''
def HDRRotatePhotos(args):
    print("Rotating photos in:\n" + args.directory)
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # grab all photos
    photos = utility.findFiles(args.directory, mode=1, recursive=True, ext=["jpg"]) # NOTE: .cr2 ignored atm!!
    if (len(photos) <= 0):
        print("No photos found in this directory.")
        return
    for p in photos:
        # pName, pExt = os.path.basename(p).split(".")
        # pNameNew = pName + "_new." + pExt
        # pNew = os.path.join(os.path.dirname(p), pNameNew)
        print("Rotate (" + str(args.hdrrotate) + "°): " + p)
        if (not args.readonly):
            img = Image.open(p)
            dpi = img.info.get('dpi')
            exif = img.info['exif']
            img2 = img.rotate(args.hdrrotate)
            img2.save(p, dpi=dpi, subsampling=-1, quality=100, exif=exif)

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
    captureIntervals = [utility_data.imageEXIFDateTime(photos[0])] # start with first photo timestamp
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
        next = utility_data.imageEXIFDateTime(p)

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
:note: Warning! This function assumes each asd file in a capture directory is from a different capture pattern location,
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
        print("No capture time directories found.")
        return

    # for each timestamp directory
    for dir in timeDirs:
        print(dir)
        # grab all asd files
        asdFiles = utility.findFiles(dir, mode=1, ext=["asd"])
        if (len(asdFiles) <= 0):
            print("No asd files found in this directory.")
            return

        # THIS ASSUMES EACH FILE IN THIS DIRECTORY IS FROM A DIFFERENT SAMPLING PATTERN LOCATION,
        # AND THE ORDERING IS THE SAME AS THE CAPTURE PATTERN DEFINED ABOVE!
        # THIS IS A MAJOR ASSUMPTION! IT IS BELIEVED TO BE CORRECT IN THE DATA I HAVE AT THE TIME OF WRITING THIS CODE,
        # BUT PLEASE CONFIRM THIS BEFORE RUNNING THIS CODE ON YOUR OWN DATA!

        # First, make sure the list is NATURAL sorted (for humans, like in Windows Explorer)
        # We have to do this because someone may not have padded the filename digits.
        # If the files are not natural sorted, THEY WILL BE RENAMED TO THE WRONG CAPTURE PATTERN LOCATIONS!
        asdFiles.sort(key=utility.naturalSortKey)

        # for the number of files in the sampling pattern
        for idx in range(0, len(SamplingPattern)):
            if (idx >= len(asdFiles)):
                print("ASD file #" + str(idx+1) + " is beyond the capture pattern location count (" + str(len(SamplingPattern)) + ")")
                break

            # rename to format: ##_TTT.TT_PP.PPPP_.asd
            oldName = os.path.basename(asdFiles[idx])
            newName = '{0:02d}_{1:06.02f}_{2:07.04f}_.asd'.format(idx, SamplingPattern[idx][0], SamplingPattern[idx][1])
            print("Rename: " + oldName + " to " + newName)
            if (not args.readonly):
                os.rename(asdFiles[idx], os.path.join(dir, newName))
            if (os.path.exists(os.path.join(dir, oldName) + ".rad")):
                old = oldName + ".rad"
                new = newName + ".rad"
                print("Rename: " + old + " to " + new)
                if (not args.readonly):
                    os.rename(os.path.join(dir, old), os.path.join(dir, new))
            if (os.path.exists(os.path.join(dir, oldName) + ".rad.txt")):
                old = oldName + ".rad.txt"
                new = newName + ".rad.txt"
                print("Rename: " + old + " to " + new)
                if (not args.readonly):
                    os.rename(os.path.join(dir, old), os.path.join(dir, new))

'''
Function that reorganizes ASD files into capture directories (timestamps) based on a capture interval.
:note: Warning! This function assumes each asd file is from a different capture pattern location,
and that the ordering is the same as the capture pattern. There is no way to confirm this in the file itself by looking
at the data, so we have to make this assumption.
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

    # THIS ASSUMES EACH FILE IN THIS DIRECTORY IS FROM A DIFFERENT SAMPLING PATTERN LOCATION,
    # AND THE ORDERING IS THE SAME AS THE CAPTURE PATTERN DEFINED ABOVE!
    # THIS IS A MAJOR ASSUMPTION! IT IS BELIEVED TO BE CORRECT IN THE DATA I HAVE AT THE TIME OF WRITING THIS CODE,
    # BUT PLEASE CONFIRM THIS BEFORE RUNNING THIS CODE ON YOUR OWN DATA!

    # we want to organize all asd files into folders - one folder for each capture interval
    captures = []
    captureIntervals = [datetime.fromtimestamp(os.path.getmtime(asdFiles[0]))]  # start with first timestamp
    threshold = 4  # look for next timestamp after this amount of time (next capture interval)
    if (args.interval):  # user can specify capture interval
        threshold = args.interval
    captureFolder = os.path.join(args.directory, str(captureIntervals[-1].time()).replace(':', '.'))
    print(captureFolder)
    if (not args.readonly):
        os.mkdir(captureFolder)

    # this stuff is for error checking - to make sure we are on track
    filesPerCapture = 0
    dirsToMake = []
    filesToMove = []

    # for each asd file
    for asdfile in asdFiles:
        last = captureIntervals[-1]
        next = datetime.fromtimestamp(os.path.getmtime(asdfile))

        # we've encountered next capture interval
        if ((next - last).total_seconds() / 60.0 >= threshold):
            if (filesPerCapture < len(SamplingPattern)): # warning, last folder was not complete
                print("ASD file count (" + str(filesPerCapture) + ") for last capture folder was less than capture pattern location count (" + str(len(SamplingPattern)) + ")")
            captureIntervals.append(next)
            captureFolder = os.path.join(args.directory, str(next.time()).replace(':', '.'))
            print(captureFolder)
            dirsToMake.append(captureFolder)
            filesPerCapture = 0  # reset file count as we are considering a new capture folder

        # check to see if we've tried to move more files than there are in a capture pattern
        filesPerCapture += 1
        if (filesPerCapture > len(SamplingPattern)):
            print("ASD file #" + str(filesPerCapture) + " is beyond the capture pattern location count (" + str(len(SamplingPattern)) + ")")
            return

        # put file into folder
        destPath = os.path.join(captureFolder, os.path.basename(asdfile))
        print("Move " + os.path.basename(asdfile) + " to " + destPath)
        filesToMove.append([asdfile, destPath])
        if (os.path.exists(asdfile + ".rad")):
            old = asdfile + ".rad"
            new = destPath + ".rad"
            print("Move " + os.path.basename(old) + " to " + new)
            filesToMove.append([old, new])
        if (os.path.exists(asdfile + ".rad.txt")):
            old = asdfile + ".rad.txt"
            new = destPath + ".rad.txt"
            print("Move " + os.path.basename(old) + " to " + new)
            filesToMove.append([old, new])

    # if we've gotten this far, then we haven't errored out, and it's safe to actually do this work
    if (not args.readonly):
        for dir in dirsToMake:
            os.mkdir(dir)
        for f in filesToMove:
            shutil.move(f[0], f[1])

'''
Function to create an .asd.rad.txt file filled with a specified literal value. 
:note: This is only useful if the .asd.rad.txt file couldn't be generated properly (e.g. .asd file is corrupt, etc.)   
'''
def ASDFillFile(args):
    #print("Creating new ASD file in:\n" + args.directory)
    # ensure directory exists
    if (not os.path.exists(args.directory)):
        return

    # generate filename for new file
    root, ext = "fake", ".asd.rad.txt"
    filename = os.path.join(args.directory, root + ext)
    counter = 1
    while (os.path.exists(filename)):
        filename = os.path.join(args.directory, root + str(counter) + ext)
        counter += 1

    print("Creating new ASD file:\n" + filename)
    if (not args.readonly):
        with open(filename, "w") as file:
            file.write("Wavelength\t0000-00-00___00.00.00_-_00_000.00_00.0000_.asd.rad\n")
            for wavelength in range(350, 2501):
                file.write(str(wavelength) + "\t " + str(args.asdfill) + " \n")
            file.close()

#---------------------------------------------------------------------

def main():
    # handle command line args
    parser = argparse.ArgumentParser(description='Script to clean / reorganize a sky data directory. WARNING! Use -r (--readonly) flag first to preview changes to your data!', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_help = True
    parser.add_argument('directory', help='a directory to operate on')
    # general arguments
    parser.add_argument('-r', '--readonly', dest='readonly', action='store_true', help='read only mode (no writes)', default=False)
    parser.add_argument('-l', '--listdirs', dest='listdirs', action='store_true', help='list sub dirs of directory', default=False)
    parser.add_argument('-t', '--timeoffset', dest='timeoffset', type=int, help='offset capture dirs by this number of hours +/-')
    parser.add_argument('-cc', '--correlate', dest='correlatecaptures', type=int, help='find HDR captures w/in #s of ASD captures')
    # specifies HDR or ASD specific operations
    parser.add_argument('-hdr', '--hdr', dest='hdr', action='store_true', help='HDR mode - working w/ HDR photos')
    parser.add_argument('-asd', '--asd', dest='asd', action='store_true', help='ASD mode - working w/ ASD files')
    # arguments used by both HDR and ASD files/folders
    parser.add_argument('-d', '--renamedirs', dest='renamedirs', action='store_true', help='cleanup dir names', default=False)
    parser.add_argument('-f', '--renamefiles', dest='renamefiles', action='store_true', help='cleanup file names', default=False)
    parser.add_argument('-o', '--organize', dest='organize', action='store_true', help='organize files into dirs by capture interval', default=False)
    parser.add_argument('-n', '--interval', dest='interval', type=int, help='time interval (in minutes) between captures')
    # arguments specific to HDR
    parser.add_argument('-hc', '--hdrcounter', dest='hdrcounter', type=int, help='rename HDR photos starting from counter')
    parser.add_argument('-hr', '--hdrrotate', dest='hdrrotate', type=int, help='rotate HDR photos by some +/- degrees')
    # arguments specific to ASD
    parser.add_argument('-af', '--asdfill', dest='asdfill', type=float, help='fill a new .asd.rad.txt file w/ literal')
    args = parser.parse_args()

    # file required as parameter
    if (not args.directory):
        print("Error: no directory specified.")
        sys.exit(2)

    # do it
    if (args.listdirs):
        ListSubDirectories(args)
    elif (args.timeoffset):
        OffsetCaptureTimes(args)
    elif (args.correlatecaptures):
        CorrelateCaptures(args)
    elif (args.hdr):
        if (args.renamedirs):
            HDRRenameDirs(args)
        elif (args.renamefiles):
            HDRRenameFiles(args)
        elif (args.hdrcounter):
            HDRRenameFilesCounter(args)
        elif (args.hdrrotate):
            HDRRotatePhotos(args)
        elif (args.organize):
            HDROrganizePhotos(args)
    elif (args.asd):
        if (args.renamedirs):
            ASDRenameDirs(args)
        elif (args.renamefiles):
            ASDRenameFiles(args)
        elif (args.organize):
            ASDOrganizeFiles(args)
        elif (args.asdfill):
            ASDFillFile(args)


if __name__ == "__main__":
    main()
