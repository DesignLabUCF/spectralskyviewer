#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 11/02/2017
# @summary: A module with angle and coordinate transformations.
# @note: Parts of this file came from angle_utilities.py written by Dan Knowlton - redistributed with permission.
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

    # convert to radians
    zenith = zenith * math.pi / 180.0
    azimuth = azimuth * math.pi / 180.0

    # use actual lens - account for non-linearity/warp
    if lenswarp and len(common.LensWarp) == 4:
        radius = (common.LensWarp[0] * zenith) + \
                 (common.LensWarp[1] * zenith * zenith) - \
                 (common.LensWarp[2] * zenith * zenith * zenith) - \
                 (common.LensWarp[3] * zenith * zenith * zenith * zenith)
    # use ideal lens
    else:
        radius = zenith / (math.pi / 2.0)

    # compute UVs
    u = 0.5 * (radius * math.cos(azimuth) + 1)
    v = 0.5 * (radius * math.sin(azimuth) + 1)

    return u, v

'''
Convert a fisheye UV coordinate (0-1, 0-1) to a sky coordinate (azimuth, altitude).
'''
def FisheyeUV2SkyCoord(u, v, lenswarp=True):
    radius = math.sqrt((u - 0.5) * (u - 0.5) + (v - 0.5) * (v - 0.5))

    # account for lens warp
    #if lenswarp:
    #    radius = (0.7189 * radius) + (0.00079342 * radius * radius) - (0.0289 * radius * radius * radius) - (0.001 * radius * radius * radius * radius)

    u = u - 0.5
    v = v - 0.5

    azimuth = math.atan2(u, v)
    zenith = radius * math.pi / 2.0

    # convert radians to angles
    # convert zenith back to altitude
    return (int((azimuth * 180.0 / math.pi + 360) % 360), int(90 - 2 * zenith * 180.0 / math.pi))

'''
Take in a pair of (azimuth, altitude) sky coordintes and return the corresponding central angle between them.
https://en.wikipedia.org/wiki/Great-circle_distance#Formulas
'''
def CentralAngle(a, b, inRadians=False):
    if not inRadians:
        a = (math.radians(a[0]), math.radians(a[1]))
        b = (math.radians(b[0]), math.radians(b[1]))
    return math.acos( math.sin(a[1]) * math.sin(b[1]) + math.cos(a[1]) * math.cos(b[1]) * math.cos( abs(a[0]-b[0]) ) )
