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
# @since: 03/14/2018
# @summary: Common constants and variables used across the program.
# ====================================================================
from enum import Enum


# default sampling pattern: 81 samples (azimuth, altitude)
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
# convert to radians
# SamplingPattern = [(math.radians(s[0]), math.radians(s[1])) for s in SamplingPattern]

# exposure times of the HDR data (in seconds)
Exposures = [
    0.000125,
    0.001000,
    0.008000,
    0.066000,
    0.033000,
    0.250000,
    1.000000,
    2.000000,
    4.000000,
]

# sky cover categories
SkyCover = Enum('SkyCover', 'UNK CLR SCT OVC')
SkyCoverDesc = {SkyCover.UNK: "Unknown", SkyCover.CLR: "Clear", SkyCover.SCT: "Scattered", SkyCover.OVC: "Overcast"}
SkyCoverFromStr = {"UNK": SkyCover.UNK, "CLR": SkyCover.CLR, "SCT": SkyCover.SCT, "OVC": SkyCover.OVC}

# pixel region and weighting settings
PixelRegionMin = 1
PixelRegionMax = 99
PixelWeighting = Enum('PixelWeighting', 'Mean Median Gaussian')

# types of RAW data
HDRRawExts = ['.cr2', '.raw', '.dng']

# export attributes
ExportAttributes = [
    # column name           description
    ("Header",              "Header Row"),
    ("Date",                "Date of Capture"),
    ("Time",                "Time of Capture"),
    ("SunAzimuth",          "Sun Azimuth (East from North)"),
    ("SunAltitude",         "Sun Altitude (90 - Zenith)"),
    ("SkyCover",            "Sky Cover Assessment"),
    ("SamplePatternIndex",  "Sample Pattern Index"),
    ("SampleAzimuth",       "Sample Azimuth (East from North)"),
    ("SampleAltitude",      "Sample Altitude (90 - Zenith)"),
    ("Exposure",            "Photo Exposure Time (s)"),
    ("PixelRegion",         "Sample Pixel Kernel Size (n x n)"),
    ("PixelWeighting",      "Sample Pixel Weighting Algorithm"),
    ("PixelRGB",            "Sample Pixel RGB Channels"),
    ("Radiance",            "Sample Radiance (W/m²/sr) per Wavelength (350-2500nm)"),
]

# default export options
DefExportOptions = {
    "Filename": "",
    "Delimiter": ",",
    "PixelRegion": PixelRegionMin,
    "PixelWeighting": PixelWeighting.Mean.value,
    "Attributes": [0, 1, 2, 3, 4, 6, 7, 8, 12, 13]
}

# default application settings
DefAppSettings = {
    "Filename": "res\\settings.json",
    "DataDirectory": "",
    "WindowWidth": 1024,
    "WindowHeight": 768,
    "HorizSplitLeft": -1,
    "HorizSplitRight": -1,
    "VertSplitTop": -1,
    "VertSplitBottom": -1,
    "ShowMask": True,
    "ShowHUD": True,
    "ShowCompass": False,
    "ShowSunPath": False,
    "ShowSamples": False,
    "ShowUVGrid": False,
    "ShowEXIF": True,
    "ShowStatusBar": True,
    "PixelRegion": 1,
    "PixelWeighting": PixelWeighting.Mean.value,
}
DefAppSettings.update({"ExportOptions": dict(DefExportOptions)})

# application settings
AppSettings = dict(DefAppSettings)
