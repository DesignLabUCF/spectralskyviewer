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
# @since: 11/02/2017
# @summary: A module that handles loading/checking sky data from the data directory.
# ====================================================================
import math
import os
import csv
import copy
from datetime import datetime
from enum import Enum
import numpy as np
from PIL import Image
import exifread
import spa


HDRRawExts = ['.cr2', '.raw', '.dng']
PixelRegionMin = 1
PixelRegionMax = 99
PixelWeighting = Enum('PixelWeighting', 'Mean Median Gaussian')
GaussianKernels = {}

# for row in range(0, kernel.shape[0]):
#     for col in range(0, kernel.shape[1]):
#         print("%.4f " % round(kernel[row, col, 0], 4), end='')
#     print()
# print(np.sum(kernel))
# for row in range(0, utility_data.KernelGauss5x5SD1.shape[0]):
#     for col in range(0, utility_data.KernelGauss5x5SD1.shape[1]):
#         print("%.4f " % round(utility_data.KernelGauss5x5SD1[row, col, 0], 4), end='')
#     print()
# print(np.sum(utility_data.KernelGauss5x5SD1)

'''
Function to extract the "DateTimeOriginal" EXIF value of an image.
:param filepath: Path to image
'''
def imageEXIFDateTime(filepath):
    strDateTime = imageEXIFTag(filepath, "EXIF DateTimeOriginal")
    if strDateTime is None or len(strDateTime) <= 0:
        return datetime.min
    return datetime.strptime(strDateTime, '%Y:%m:%d %H:%M:%S')

'''
Function to extract the EXIF value of a particular tag.
:param filepath: Path to image
:param tag: EXIF tagname (not code) provided by module exifread
'''
def imageEXIFTag(filepath, tag):
    result = None
    with open(filepath, 'rb') as f:
        tags = exifread.process_file(f, details=False, stop_tag=tag)
        if tag in tags.keys():
            result = tags[tag]
    return str(result) if result is not None else None

'''
Function to extract all important EXIF data from an image.
:param filepath: Path to image
:return: A dict of key,value pairs for each EXIF metadata tag
'''
def imageEXIF(filepath):
    data = {}
    with open(filepath, 'rb') as f:
        data = exifread.process_file(f, details=False)
    return data

'''
Function to retrieve the pixels of specific coordinates of an image.
:param coords: A list of (x, y) points to lookup in the image file.
:param file: Optional path to the image file.
:param pixels: Optional numpy array of pixels in format [[[R G B (A)]]].
:param region: n for (n x n) region of pixels considered in pixel weighting.
:param weighting: Pixel weighting convolution algorithm.
:return: A list of (R,G,B(,A)) tuples representing the pixel colors.
:note: Coordinates MUST be within image bounds or this function will throw an exception!
:note: Alpha component may or may not be included, depending on image format.
'''
def collectPixels(coords, file='', pixels=None, region=1, weighting=PixelWeighting.Mean):
    if pixels is None:
        if not os.path.exists(file) or not coords:
            return []
        image = Image.open(file)
        #imgPixels = img.load()
        pixels = np.array(image)
        image.close()

    result = []
    if pixels.any():
        if region <= 1:
            result = [pixels[int(c[1]), int(c[0])] for c in coords]
        else:
            if weighting == PixelWeighting.Mean:
                result = [pixelWeightedMean(pixels, c, region) for c in coords]
            elif weighting == PixelWeighting.Median:
                result = [pixelWeightedMedian(pixels, c, region) for c in coords]
            elif weighting == PixelWeighting.Gaussian:
                result = [pixelWeightedGaussian(pixels, c, GaussianKernels[region]) for c in coords]
    return result

def gaussianKernel(width):
    kernel = np.zeros(shape=(width,width,1), dtype=np.float32)
    radius = int(width/2)
    # sigma = 1.0
    sigma = radius/2.0 # for [-2*sigma, 2*sigma]
    total = 0.0
    # gaussian function
    #gaussian = lambda x: x + 1
    #kernel = gaussian(kernel)
    for row in range(0, width):
        for col in range(0, width):
            kernel[row,col,0] = math.exp(-0.5 * (pow((col - radius) / sigma, 2.0) + pow((row - radius) / sigma, 2.0))) / (2 * math.pi * sigma * sigma)
            total += kernel[row,col,0]
    # normalize
    kernel = kernel / total
    return kernel
GaussianKernels = {w:gaussianKernel(w) for w in range(PixelRegionMin+2, PixelRegionMax+1, 2)}

def pixelWeightedMean(pixels, coord, dim):
    radius = int(dim / 2)
    scale = 1.0 / (dim * dim)
    pixelset = pixels[coord[1]-radius:coord[1]+radius+1, coord[0]-radius:coord[0]+radius+1]
    pixelset = pixelset * scale
    pixelset = np.sum(pixelset, axis=0)
    pxl = np.sum(pixelset, axis=0)
    # pxl = np.zeros(pixels.shape[2], np.float32)
    # for j in dim:
    #     for i in dim:
    #         pxl += scale * pixels[coord[1]+j-radius, coord[0]+i-radius]
    pxl = np.around(pxl, decimals=1, out=pxl)
    pxl = pxl.astype(np.uint8, copy=False)
    return pxl

def pixelWeightedMedian(pixels, coord, dim):
    return None

def pixelWeightedGaussian(pixels, coord, kernel):
    radius = int(kernel.shape[1] / 2)
    pixelset = pixels[coord[1]-radius:coord[1]+radius+1, coord[0]-radius:coord[0]+radius+1]
    pixelset = pixelset * kernel
    pixelset = np.sum(pixelset, axis=0)
    pxl = np.sum(pixelset, axis=0)
    # pxl = np.zeros(pixels.shape[2], np.float32)
    # for j in range(0, kernel.shape[0]):
    #     for i in range(0, kernel.shape[1]):
    #         pxl += kernel[j][i] * pixels[coord[1]+j-radius, coord[0]+i-radius]
    pxl = np.around(pxl, decimals=1, out=pxl)
    pxl = pxl.astype(np.uint8, copy=False)
    return pxl

'''
Function to check if a raw data photo is available, given a path to an existing photo.
:param hdrImgpath: Path to a photo in the HDR folder of a capture date in the data directory.
:note: This assumes the raw data file is the same name (but different extension) of given file.
'''
def isHDRRawAvailable(hdrImgPath):
    if (not os.path.exists(hdrImgPath)):
        return False
    pathSplit = os.path.splitext(hdrImgPath.lower())
    for ext in HDRRawExts:
        if (pathSplit[1] == ext):
            return True
        elif (os.path.exists(pathSplit[0] + ext)):
            return True
    return False

'''
Function to load a file with data used for NREL SPA's algorithm.
:param filepath: Path to file with SPA data
:param isDir: If filepath specified is a directory, then filename is assumed to be 'spa.csv'
:note: NREL SPA can be found at https://midcdmz.nrel.gov/spa/
:note: File format should be a CSV with the following columns: key, value, min, max, units, description.
       Each key is a field needed to compute SPA.
:return: A filled in spa.spa_data object.
'''
def loadSPASiteData(filepath, isDir=True):
    if (isDir):
        filepath = os.path.join(filepath, 'spa.csv') # assumes this filename if dir specified
    if (not os.path.exists(filepath)):
        return None

    # create spa data and fill with default values from their example
    data = spa.spa_data()
    data.year = 2003
    data.month = 10
    data.day = 17
    data.hour = 12
    data.minute = 30
    data.second = 30
    data.time_zone = -7.0
    data.delta_ut1 = 0
    data.delta_t = 67
    data.longitude = -105.1786
    data.latitude = 39.742476
    data.elevation = 1830.14
    data.pressure = 820
    data.temperature = 11
    data.slope = 30
    data.azm_rotation = -10
    data.atmos_refract = 0.5667
    data.function = spa.SPA_ZA

    # overwrite with values read from spa site info
    with open(filepath, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        next(reader, None) # ignore header
        for row in reader:
            if row[0].lower() == "time_zone":
                data.time_zone = float(row[1])
            elif row[0].lower() == "delta_ut1":
                data.delta_ut1 = float(row[1])
            elif row[0].lower() == "delta_t":
                data.delta_t = float(row[1])
            elif row[0].lower() == "longitude":
                data.longitude = float(row[1])
            elif row[0].lower() == "latitude":
                data.latitude = float(row[1])
            elif row[0].lower() == "elevation":
                data.elevation = float(row[1])
            elif row[0].lower() == "pressure":
                data.pressure = float(row[1])
            elif row[0].lower() == "temperature":
                data.temperature = float(row[1])
            elif row[0].lower() == "slope":
                data.slope = float(row[1])
            elif row[0].lower() == "azm_rotation":
                data.azm_rotation = float(row[1])
            elif row[0].lower() == "atmos_refract":
                data.atmos_refract = float(row[1])

    return data

'''
Function to deep copy a spa_data object. This function is useful because SWIG didn't create pickling code for deep copy.
:param src: source spa_data object
:note: NREL SPA can be found at https://midcdmz.nrel.gov/spa/
:return: A destination spa_data object
'''
def deepcopySPAData(src):
    dest = spa.spa_data()
    # input values
    dest.year = src.year
    dest.month = src.month
    dest.day = src.day
    dest.hour = src.hour
    dest.minute = src.minute
    dest.second = src.second
    dest.time_zone = src.time_zone
    dest.delta_ut1 = src.delta_ut1
    dest.delta_t = src.delta_t
    dest.longitude = src.longitude
    dest.latitude = src.latitude
    dest.elevation = src.elevation
    dest.pressure = src.pressure
    dest.temperature = src.temperature
    dest.slope = src.slope
    dest.azm_rotation = src.azm_rotation
    dest.atmos_refract = src.atmos_refract
    dest.function = src.function
    # intermediate values not important
    # output values
    dest.zenith = src.zenith
    dest.azimuth_astro = src.azimuth_astro
    dest.azimuth = src.azimuth
    dest.incidence = src.incidence
    dest.suntransit = src.suntransit
    dest.sunrise = src.sunrise
    dest.sunset = src.sunset
    return dest

'''
Function to fill a spa_data object from NREL SPA with specified date and time.
:param spadata: spa_data object
:param dt: datetime object
:note: NREL SPA can be found at https://midcdmz.nrel.gov/spa/
'''
def fillSPADateTime(spadata, dt):
    if (spadata == None or dt == None):
        return
    spadata.year = dt.year
    spadata.month = dt.month
    spadata.day = dt.day
    spadata.hour = dt.hour
    spadata.minute = dt.minute
    spadata.second = dt.second

'''
Function to compute the (azimuth, altitude) position of the sun using NREL SPA.
:param spadata: spa_data object with site info and date
:note: NREL SPA can be found at https://midcdmz.nrel.gov/spa/
:return: A single (azimuth, altitude) tuple of solar position.
'''
def computeSunPosition(spadata):
    spa.spa_calculate(spadata)
    altitude = 90 - spadata.zenith # this application uses altitude (90 - zenith)
    return (spadata.azimuth, altitude)

'''
Function to compute the (azimuth, altitude) points above horizon for each hour of the day using NREL SPA.
:param spadata: spa_data object with site info and date
:note: NREL SPA can be found at https://midcdmz.nrel.gov/spa/
:return: A list of (azimuth, altitude, datetime) tuples with solar position and timestamp
'''
def computeSunPath(spadata):
    sunpath = []
    spadata2 = deepcopySPAData(spadata)
    spadata2.function = spa.SPA_ZA
    spadata2.minute = 0
    spadata2.second = 0
    # for each hour of the day, compute a sunpath point
    for i in range(0, 24):
        spadata2.hour = i
        spa.spa_calculate(spadata2)
        altitude = 90 - spadata2.zenith # this application uses altitude (90 - zenith)
        # we only care about altitude when sun is visible (not on other side of Earth)
        if (altitude >= 0 and altitude <= 90):
            dt = datetime(spadata2.year, spadata2.month, spadata2.day, spadata2.hour, spadata2.minute, int(spadata2.second))
            sunpath.append((spadata2.azimuth, altitude, dt))
    return sunpath

'''
Function to load a solar position (sunpath) file exported from NREL's SPA calculator online.
:param filepath: Path to file with SPA data
:param isDir: If filepath specified is a directory, then filename is assumed to be 'spa.csv'
:note: NREL SPA can be found at https://midcdmz.nrel.gov/spa/
:note: File format should be a CSV with the following columns:
       Date, Time, Topocentric zenith angle, Topocentric azimuth angle (eastward from N)
:return: A list of (azimuth, altitude, datetime) tuples with solar position and timestamp
'''
def loadSunPath(filepath, isDir=True):
    if (isDir):
        filepath = os.path.join(filepath, 'spa.csv') # assumes this filename if dir specified
    if (not os.path.exists(filepath)):
        return []
    sunpath = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        next(reader, None)
        for row in reader:
            # we only care about rows with a valid timestamp
            dt = datetime.min
            try:
                dts = row[0] + " " + row[1]
                dt = datetime.strptime(dts, "%m/%d/%Y %H:%M:%S")
            except ValueError:
                continue
            # swap the order of (zenith, azimuth) to (azimuth, zenith) for consistency throughout application
            # this application uses altitude (90 - zenith)
            point = (float(row[3]), 90-float(row[2]), dt)
            # we only care about altitude when sun is visible (not on other side of Earth)
            if (point[1] >=0 and point[1] <= 90):
                sunpath.append(point)
    return sunpath

'''
Function to load a ViewSpecPro spectroradiometer ASD file.
:param filepath: Path to TXT file with ASD data
:note: File format should be a TXT with the following data per line: Wavelength, Reading
:note: The TXT files were converted from ViewSpecPro's software in the order .asd to .asd.rad to .asd.rad.txt .
       That may not be a requirement for ASD data of future projects.
:return: 2 lists, Xs (wavelengths) and Ys (irradiance)        
'''
def loadASDFile(filepath):
    if (not os.path.exists(filepath)):
        return [], []
    xdata, ydata = np.loadtxt(filepath, skiprows=1, unpack=True)
    return xdata, ydata
