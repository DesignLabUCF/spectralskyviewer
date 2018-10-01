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
# @since: 10/01/2018
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


'''
Convert a sky coordinate (azimuth, altitude) to fisheye UV coordinate (0-1, 0-1).
Note that images in this application were taken with North facing downward, so we must account for this in UV.
Note sampling pattern coordinates in this application were measured in altitude, but calculation below requires zenith.
'''
def SkyCoord2FisheyeUV(azimuth, altitude):
    # rotate azimuth so that position of North is pointing directly down
    azimuth = 360 - ((azimuth + 270) % 360)

    # convert altitude to zenith
    zenith = (90 - altitude)

    # convert to radians
    zenith = zenith * math.pi / 180.0
    azimuth = azimuth * math.pi / 180.0

    # compute radius
    radius = zenith / (math.pi / 2.0)

    # compute UV
    return (0.5 * (radius * math.cos(azimuth) + 1), 0.5 * (radius * math.sin(azimuth) + 1))

'''
Convert a fisheye UV coordinate (0-1, 0-1) to a sky coordinate (azimuth, altitude).
'''
def FisheyeUV2SkyCoord(u, v):
    radius = math.sqrt((u - 0.5) * (u - 0.5) + (v - 0.5) * (v - 0.5))
    u = u - 0.5
    v = v - 0.5
    theta = math.atan2(u, v)
    phi = radius * math.pi / 2.0

    # convert radians to angles
    # convert zenith back to altitude
    return (int((theta * 180.0 / math.pi + 360) % 360), int(90 - 2 * phi * 180.0 / math.pi))

# '''
# Compute cartesian UV (0-1, 0-1) coordinate given an (azimuth, altitude) sky coordinate.
# Note sampling pattern coordinates in this application were measured in altitude, but calculation below requires zenith.
# '''
# def GetUVFromAngle(azimuth, altitude):
#     # convert altitude to zenith
#     zenith = (90 - altitude)
#     # convert to radians
#     zenith = zenith * math.pi / 180.0
#     azimuth = azimuth * math.pi / 180.0
#     # compute UV
#     radius = zenith / (math.pi / 2.0)
#     return (0.5 * (radius * math.cos(azimuth) + 1), 0.5 * (radius * math.sin(azimuth) + 1))
#
# '''
# Compute (azimuth, altitude) sky coordinate given a cartesian UV (0-1, 0-1) coordinate.
# '''
# def GetAngleFromUV(u, v):
#     radius = math.sqrt((u - 0.5) * (u - 0.5) + (v - 0.5) * (v - 0.5))
#     u = u - 0.5
#     v = v - 0.5
#     theta = math.atan2(u, v)
#     phi = radius * math.pi / 2.0
#     return (int((theta * 180.0 / math.pi + 360) % 360), int(90 - 2 * phi * 180.0 / math.pi))

'''
Take in a pair of (azimuth, altitude) sky coordintes and return the corresponding central angle between them.
https://en.wikipedia.org/wiki/Great-circle_distance#Formulas
'''
def CentralAngle(a, b, inRadians=False):
    if not inRadians:
        a = (math.radians(a[0]), math.radians(a[1]))
        b = (math.radians(b[0]), math.radians(b[1]))
    return math.acos( math.sin(a[1]) * math.sin(b[1]) + math.cos(a[1]) * math.cos(b[1]) * math.cos( abs(a[0]-b[0]) ) )
