#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 03/14/2018
# @summary: Common constants and variables used across the program.
# ====================================================================
from enum import Enum


# constants -------------------------------------------------------------------
# constants -------------------------------------------------------------------
# constants -------------------------------------------------------------------

ColorModel = Enum('ColorModel', 'RGB HSV LAB')  # used to store pixel color components
PixelWeighting = Enum('PixelWeighting', 'Mean Median Gaussian')  # used during pixel convolution
SkyCover = Enum('SkyCover', 'UNK CLR SCT OVC')
SkyCoverDesc = {SkyCover.UNK: "Unknown", SkyCover.CLR: "Clear", SkyCover.SCT: "Scattered", SkyCover.OVC: "Overcast"}
HDRRawExts = ['.cr2', '.raw', '.dng']  # types of RAW data
PixelRegionMin = 1
PixelRegionMax = 51
RadianceFOV = 1
CaptureEpsilon = 60
HUDTextScaleMin = 20
HUDTextScaleMax = 80

# sample export features
SampleFeatures = [
    # column name           description
    # required ----------------------------------------------------------
    ("Date",                "Date of Capture"),
    ("Time",                "Time of Capture"),
    # optional ----------------------------------------------------------
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

# default settings ------------------------------------------------------------
# default settings ------------------------------------------------------------
# default settings ------------------------------------------------------------

# default data directory configuration
DefDataConfig = {
    "Filename": "config.json",
    "RadianceFOV": 1,             # (degrees) field of view used when measuring radiance with spectroradiometer
    "CaptureEpsilon": 60,         # (seconds) max acceptable time delta between measurements of same capture
    "Exposures": [1],             # (seconds) exposures of photos found in data directory
    "Lens": {                     # lens used during data capture
        "Name": "Cannon 8mm",     # for identification
        "Linearity": [            # read more here -> http://paulbourke.net/dome/fisheyecorrect/
            -0.001,               # x^4 coefficient
            -0.0289,              # x^3 coefficient
            0.00079342,           # x^2 coefficient
            0.7189,               # x^1 coefficient
            0                     # x^0 coefficient
        ]
    },
    "SPA": {                      # site data used for NREL SPA -> https://midcdmz.nrel.gov/solpos/spa.html
        "time_zone": -5,          # (hours) (-18 to 18)
        "delta_ut1": 0.153,       # (seconds) (-1 to 1)
        "delta_t": 66.9069,       # (seconds) (-8000 to 8000)
        "longitude": -76.481638,  # (degrees) (-180 to 180)
        "latitude": 42.443441,    # (degrees) (-90 to 90)
        "elevation": 325,         # (meters) (-6.5e6 to 6.5e6)
        "pressure": 1032.844454,  # (millibars) (0 to 5000)
        "temperature": -2.9,      # (degrees) (-273 to 6000)
        "slope": 0,               # (degrees) (-360 to 360)
        "azm_rotation": 0,        # (degrees) (-360 to 360)
        "atmos_refract": 0.5667   # (degrees) (-5 to 5)
    },
    "SamplingPattern": [          # (degrees) sky sampling pattern used for spectral radiance measurements
        [0, 90]
    ],
    "SkyCover": [                 # periods of known sky cover
        ["11/6/2012", "12:26", "16:21", "SCT"]
    ]
}

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
    "PixelRegionMin": 1,
    "PixelRegionMax": 51,
    "PixelWeighting": PixelWeighting.Mean.value,
    "AvoidSunAngle": 0,
    "GraphResolution": 5,
    "GraphLineThickness": 1,
    "HUDTextScale": 60,
    "HUDTextScaleMin": 20,
    "HUDTextScaleMax": 80
}
DefAppSettings.update({"ExportOptions": dict(DefExportOptions)})

# globals ---------------------------------------------------------------------
# globals ---------------------------------------------------------------------
# globals ---------------------------------------------------------------------

# main program data configuration!
DataConfig = dict(DefDataConfig)

# main program application settings!
AppSettings = dict(DefAppSettings)

Exposures = []            # photo capture exposure times (in seconds)
ExposureIdxMap = {}       # for convenience
LensWarp = ()             # camera lens warp/linearity constants used to correct sky coordinates when transforming to fisheye uv
SPASiteData = None        # SPA (sun positioning algorithm) site data
SamplingPattern = []      # sky sampling pattern coordinates (azimuth, altitude)
SamplingPatternRads = []  # for convenience
SamplingPatternAlts = []  # a sorted unique set of just the altitudes
SkyCoverData = []         # sky cover ranges
