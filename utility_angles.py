#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 11/02/2017
# @summary: A module with angle and coordinate transformations.
# @note: Parts of this file came from angle_utilities.py written by Dan Knowlton of PCG at Cornell.
# Redistributed with permission.
# ====================================================================
# Provides functionality to convert between UV coordinates and angles as well
#   as other useful angle utilities.
#
#  Copyright 2014-2015 Program of Computer Graphics, Cornell University
#     580 Rhodes Hall
#     Cornell University
#     Ithaca NY 14853
#  Web: http://www.graphics.cornell.edu/
#
#  Not for commercial use. Do not redistribute without permission.
# ====================================================================
import math
import numpy as np
import common


'''
Convert a sky coordinate (azimuth, altitude) to fisheye UV coordinate (0-1, 0-1).
Note that images in this application were taken with North facing downward, so we must account for this in UV.
Note sampling pattern coordinates in this application were measured in altitude, but calculation below requires zenith.
Note altering of zenith to account for warp of lens used:
http://paulbourke.net/dome/fisheyecorrect/
http://michel.thoby.free.fr/Fisheye_history_short/Projections/Models_of_classical_projections.html
'''
def SkyCoord2FisheyeUV(azimuth, altitude, lenswarp=True):
    # rotate azimuth so that position of North is pointing directly down
    azimuth = 360 - ((azimuth + 270) % 360)

    # convert altitude to zenith
    zenith = (90 - altitude)

    # convert from angles to radians
    azimuth = azimuth * math.pi / 180.0
    zenith = zenith * math.pi / 180.0

    # compute radius
    # account for non-linearity/warp of actual lens
    if lenswarp and len(common.LensWarp) > 0:
        radius = np.polyval(common.LensWarp, zenith)
    # use ideal lens
    else:
        radius = np.polyval(common.LensIdeal, zenith)

    # compute UVs
    u = radius * math.cos(azimuth)
    v = radius * math.sin(azimuth)

    # adjust to [0, 1] range
    u = 0.5 * u + 0.5
    v = 0.5 * v + 0.5

    return u, v

'''
Convert a fisheye UV coordinate (0-1, 0-1) to a sky coordinate (azimuth, altitude).
'''
def FisheyeUV2SkyCoord(u, v, lenswarp=True):
    # adjust to [-1, 1] range
    u = (u - 0.5) * 2
    v = (v - 0.5) * 2

    radius = math.sqrt((u * u) + (v * v))

    # compute azimuth
    azimuth = math.atan2(u, v)
    # rotate azimuth so that position of North is pointing directly down
    azimuth = (azimuth + 2*math.pi) % (2*math.pi)

    # compute zenith
    # account for non-linearity/warp of actual lens
    if lenswarp and len(common.LensWarpInv) > 0:
        zenith = np.polyval(common.LensWarpInv, radius)
    # use ideal lens
    else:
        zenith = np.polyval(common.LensIdealInv, radius)

    # convert zenith to altitude
    altitude = (math.pi / 2) - zenith

    # convert from radians to angles
    azimuth = azimuth * 180.0 / math.pi
    altitude = altitude * 180.0 / math.pi

    return azimuth, altitude

'''
Convert an image pixel coordinate to a fisheye UV coordinate (0-1, 0-1).
'''
def Pixel2FisheyeUV(x, y, width, height):
    u = (x - (int(width/2) - int(height/2))) / height
    v = y / height
    return u, v

'''
Take in a pair of (azimuth, altitude) sky coordintes and return the corresponding central angle between them.
https://en.wikipedia.org/wiki/Great-circle_distance#Formulas
'''
def CentralAngle(a, b, inRadians=False):
    if not inRadians:
        a = (math.radians(a[0]), math.radians(a[1]))
        b = (math.radians(b[0]), math.radians(b[1]))
    return math.acos( math.sin(a[1]) * math.sin(b[1]) + math.cos(a[1]) * math.cos(b[1]) * math.cos( abs(a[0]-b[0]) ) )
