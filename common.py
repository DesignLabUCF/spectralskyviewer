#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 03/14/2018
# @summary: Common constants and variables used across the program.
# ====================================================================
from enum import Enum


# sky sampling pattern coordinates (azimuth, altitude)
SamplingPattern = []
SamplingPatternRads = []
SamplingPatternAlts = []  # a unique set of all the altitudes
SamplingPatternFile = "sampling.csv"

# photo capture exposure times (in seconds)
Exposures = []
ExposureIdxMap = {}
ExposuresFile = "exposure.csv"

# SPA (sun positioning algorithm) site data
SPASiteData = None
SPASiteFile = "spa.csv"

# sky cover mappings
SkyCoverData = []
SkyCover = Enum('SkyCover', 'UNK CLR SCT OVC')
SkyCoverDesc = {SkyCover.UNK: "Unknown", SkyCover.CLR: "Clear", SkyCover.SCT: "Scattered", SkyCover.OVC: "Overcast"}
SkyCoverFile = "skycover.csv"

# pixel region/kernel, convolution weighting, and color model settings
PixelRegionMin = 1
PixelRegionMax = 51
PixelWeighting = Enum('PixelWeighting', 'Mean Median Gaussian')  # used during pixel convolution
ColorModel = Enum('ColorModel', 'RGB HSV LAB')  # used to store pixel color components

# other constants
RadianceFOV = 1  # (degrees) field of view used when measuring radiance with spectroradiometer
CaptureEpsilon = 60  # (seconds) max acceptable time delta between measurements of the same capture timestamp
HDRRawExts = ['.cr2', '.raw', '.dng']  # types of RAW data

# sample export features
SampleFeatures = [
    # column name           description
    # required ----------------------------------------------------------------------
    ("Date",                "Date of Capture"),
    ("Time",                "Time of Capture"),
    # optional ----------------------------------------------------------------------
    ("SunAzimuth",          "Sun Azimuth (East from North)"),
    ("SunAltitude",         "Sun Altitude (90 - Zenith)"),
    ("SkyCover",            "Sky Cover Assessment"),
    ("SamplePatternIndex",  "Sample Pattern Index"),
    ("SampleAzimuth",       "Sample Azimuth (East from North)"),
    ("SampleAltitude",      "Sample Altitude (90 - Zenith)"),
    ("SunPointAngle",       "Sun Point Angle (SPA)"),
    ("PixelRegion",         "Sample Pixel Region/Kernel (n x n)"),
    ("PixelWeighting",      "Sample Pixel Weighting Algorithm"),
    ("ColorModel",          "Sample Pixel Color Model"),
    ("Exposure",            "Photo Exposure Time (s)"),
    ("PixelColor",          "Sample Pixel Color Components"),
    ("Radiance",            "Sample Radiance (W/m²/sr/nm) (350-2500nm)"),
]
SampleFeatureIdxMap = {SampleFeatures[i][0]: i for i in range(0, len(SampleFeatures))}

# default export options
DefExportOptions = {
    "Filename": "",
    "Delimiter": ",",
    "IsHDR": False,
    "ComputePixelRegion": True,
    "PixelRegion": PixelRegionMin,
    "PixelWeighting": PixelWeighting.Mean.value,
    "ColorModel": ColorModel.RGB.value,
    "SpectrumResolution": 1,
    "Features": [i for i in range(0, len(SampleFeatures))]
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
    "ShowCompass": True,
    "ShowLensWarp": False,
    "ShowSunPath": False,
    "ShowSamples": False,
    "ShowShadows": True,
    "ShowUVGrid": False,
    "ShowEXIF": True,
    "ShowStatusBar": True,
    "PixelRegion": 1,
    "PixelWeighting": PixelWeighting.Mean.value,
    "AvoidSunAngle": 0,
    "GraphResolution": 5,
    "GraphLineThickness": 1,
}
DefAppSettings.update({"ExportOptions": dict(DefExportOptions)})

# main program application settings variable!
AppSettings = dict(DefAppSettings)
