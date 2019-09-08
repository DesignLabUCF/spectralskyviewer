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

CoordSystem = Enum('CoordSystem', 'Polar PolarNorm UV')          # used for sky coordinates
SourceExt = Enum('SourceExt', 'JPG TIFF')                        # used for pixel extraction
ColorModel = Enum('ColorModel', 'RGB HSV HSL LAB')               # used for pixel color components
PixelWeighting = Enum('PixelWeighting', 'Mean Median Gaussian')  # used during pixel convolution
SkyCover = Enum('SkyCover', 'UNK CLR SCT OVC')
SkyCoverDesc = {SkyCover.UNK: "Unknown", SkyCover.CLR: "Clear", SkyCover.SCT: "Scattered", SkyCover.OVC: "Overcast"}
HDRRawExts = ['.cr2', '.raw', '.dng']  # types of RAW data
PixelRegionMin = 1     # used for pixel convolution
PixelRegionMax = 63    # used for pixel convolution
HUDTextScaleMin = 10   # used for font resizing
HUDTextScaleMax = 100  # used for font resizing
# TODO: this is hardcoded to our sampling pattern. compute it properly by projecting area and taking width and height!!
AltitudeRegionMap = {90:9, 71.9187:7, 53.3665:7, 33.749:7, 12.1151:5}  # pixel regions per altitude

# sample export features
SampleFeatures = [
    # column name           description
    # required ----------------------------------------------------------
    ("Date",                "Date of Capture"),
    ("Time",                "Time of Capture"),
    ("Space",               "Coordinate System"),
    # optional ----------------------------------------------------------
    ("SunAzimuth",          "Sun Azimuth"),
    ("SunAltitude",         "Sun Altitude"),
    ("SkyCover",            "Sky Cover Assessment"),
    ("SamplePatternIndex",  "Sample Pattern Index"),
    ("SampleAzimuth",       "Sample Azimuth"),
    ("SampleAltitude",      "Sample Altitude"),
    ("SunPointAngle",       "Sun Point Angle (SPA)"),
    ("PixelRegion",         "Sample Pixel Region/Kernel (n x n)"),
    ("PixelWeighting",      "Sample Pixel Weighting Algorithm"),
    ("ColorModel",          "Sample Pixel Color Model"),
    ("Exposure",            "Photo Exposure Time (s)"),
    ("PixelColor",          "Sample Pixel Color Components"),
    ("Radiance",            "Sample Radiance (W/m²/sr/nm)"),
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
    "SpectrumStart": 350,         # (nm) inclusive start of spectral range
	"SpectrumEnd": 2500,          # (nm) inclusive end of spectral range
    "Exposures": [1],             # (seconds) exposures of photos found in data directory
    "Lens": {                     # lens used during data capture
        "Name": "Sigma 8mm f/3.5",# for identification
        "Linearity": [            # fisheye lens linearity polynomial (see http://paulbourke.net/dome/fisheyecorrect)
            -0.0004325,           # x^4 coefficient
            -0.0499,              # x^3 coefficient
            0.0252,               # x^2 coefficient
            0.7230,               # x^1 coefficient
            0                     # x^0 coefficient
        ],
        "Inverse": [              # inverse polynomial of one above
            0.4171,
            -0.3803,
            0.1755,
            1.3525,
            0
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
    "CoordSystem": CoordSystem.Polar.value,
    "IsHDR": False,
    "SourceExt": SourceExt.JPG.value,
    "ComputePixelRegion": True,
    "PixelRegion": PixelRegionMin,
    "PixelWeighting": PixelWeighting.Mean.value,
    "ColorModel": ColorModel.RGB.value,
    "SpectrumStart": 350,
    "SpectrumEnd": 2500,
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
    "HUDTextScale": 60,
}
DefAppSettings.update({"ExportOptions": dict(DefExportOptions)})

# globals ---------------------------------------------------------------------
# globals ---------------------------------------------------------------------
# globals ---------------------------------------------------------------------

# main program data directory configuration!
DataConfig = dict(DefDataConfig)

# main program application settings!
AppSettings = dict(DefAppSettings)

# pre-computed/loaded globals exposed to rest of program
Exposures = []            # photo capture exposure times (in seconds)
ExposureIdxMap = {}       # for convenience
LensWarp = ()             # camera lens warp/linearity 4^th degree poly coefficients (used for sky to fisheye coords)
LensWarpInv = ()          # inverse of polynomial above (used for fisheye to sky coords)
SPASiteData = None        # SPA (sun positioning algorithm) site data
SamplingPattern = []      # sky sampling pattern coordinates (azimuth, altitude)
SamplingPatternRads = []  # for convenience
SamplingPatternAlts = []  # a sorted unique set of just the altitudes
SkyCoverData = []         # sky cover ranges
SpectrumRange = ()        # inclusive range of wavelengths of radiance data
CaptureEpsilon = 0        # max acceptable time delta between measurements of same capture
