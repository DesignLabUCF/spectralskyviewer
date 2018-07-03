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


# sky sampling pattern (azimuth, altitude)
SamplingPattern = []
SamplingPatternRads = []

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
    "AvoidSunAngle": 0,
    "GraphResolution": 5,
}
DefAppSettings.update({"ExportOptions": dict(DefExportOptions)})

# application settings
AppSettings = dict(DefAppSettings)
