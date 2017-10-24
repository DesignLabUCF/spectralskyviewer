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
# @since: 10/13/2017
# @summary: A widget for displaying the original fisheye view of the HDR data
# ====================================================================
import os
import math
from datetime import datetime
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QImage
from PyQt5.QtWidgets import QWidget, QStyle
import utility
import angle_utilities


class ViewFisheye(QWidget):
    def __init__(self):
        super().__init__()

        # skydome sampling pattern: 81 samples (theta, phi)
        self.samplingPattern = [
            [0.0, 12.1151],
            [11.25, 12.1151],
            [22.5, 12.1151],
            [33.75, 12.1151],
            [45.0, 12.1151],
            [56.25, 12.1151],
            [67.5, 12.1151],
            [78.75, 12.1151],
            [90.0, 12.1151],
            [101.25, 12.1151],
            [112.5, 12.1151],
            [123.75, 12.1151],
            [135.0, 12.1151],
            [146.25, 12.1151],
            [157.5, 12.1151],
            [168.75, 12.1151],
            [180.0, 12.1151],
            [191.25, 12.1151],
            [202.5, 12.1151],
            [213.75, 12.1151],
            [225.0, 12.1151],
            [236.25, 12.1151],
            [247.5, 12.1151],
            [258.75, 12.1151],
            [270.0, 12.1151],
            [281.25, 12.1151],
            [292.5, 12.1151],
            [303.75, 12.1151],
            [315.0, 12.1151],
            [326.25, 12.1151],
            [337.5, 12.1151],
            [348.75, 12.1151],
            [345.0, 33.749],
            [330.0, 33.749],
            [315.0, 33.749],
            [300.0, 33.749],
            [285.0, 33.749],
            [270.0, 33.749],
            [255.0, 33.749],
            [240.0, 33.749],
            [225.0, 33.749],
            [210.0, 33.749],
            [195.0, 33.749],
            [180.0, 33.749],
            [165.0, 33.749],
            [150.0, 33.749],
            [135.0, 33.749],
            [120.0, 33.749],
            [105.0, 33.749],
            [90.0, 33.749],
            [75.0, 33.749],
            [60.0, 33.749],
            [45.0, 33.749],
            [30.0, 33.749],
            [15.0, 33.749],
            [0.0, 33.749],
            [0.0, 53.3665],
            [22.5, 53.3665],
            [45.0, 53.3665],
            [67.5, 53.3665],
            [90.0, 53.3665],
            [112.5, 53.3665],
            [135.0, 53.3665],
            [157.5, 53.3665],
            [180.0, 53.3665],
            [202.5, 53.3665],
            [225.0, 53.3665],
            [247.5, 53.3665],
            [270.0, 53.3665],
            [292.5, 53.3665],
            [315.0, 53.3665],
            [337.5, 53.3665],
            [315.0, 71.9187],
            [270.0, 71.9187],
            [225.0, 71.9187],
            [180.0, 71.9187],
            [135.0, 71.9187],
            [90.0, 71.9187],
            [45.0, 71.9187],
            [0.0, 71.9187],
            [0.0, 90.0],
        ]
        self.samplingPattern[:] = [[math.radians(s[0]), math.radians(s[1])] for s in self.samplingPattern]

        # members
        self.myPhoto = QImage()
        self.myPhotoPath = ""
        self.myPhotoTime = datetime(1,1,1)
        self.srcRect = QRect()
        self.enableHUD = True
        self.enableGrid = False
        self.rawAvailable = False
        self.coordsMouse = [0, 0]

        # preloaded graphics
        self.painter = QPainter()
        self.brushBG = QBrush(Qt.black, Qt.SolidPattern)
        self.penText = QPen(Qt.white, 1, Qt.SolidLine)
        self.font = QFont('Courier New', 8)
        self.iconWarning = self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(16)

        # init
        self.setMouseTracking(True)

    def setPhoto(self, path, exif=None):
        if (path is not None and os.path.exists(path)):
            self.myPhotoPath = path
            self.myPhoto = QImage(path)
            self.srcRect = QRect(0, 0, self.myPhoto.width(), self.myPhoto.height())
            if (exif is not None):
                self.myPhotoTime = datetime.strptime(str(exif["EXIF DateTimeOriginal"]), '%Y:%m:%d %H:%M:%S')
            else:
                self.myPhotoTime = utility.imageEXIFDateTime(path)
        else:
            self.myPhoto = QImage()
            self.myPhotoPath = ""
            self.myPhotoTime = datetime(1, 1, 1)
            self.srcRect = QRect()
            self.rawAvailable = False

    def showHUD(self, b):
        self.enableHUD = b

    def showGrid(self, b):
        self.enableGrid = b

    def setRAWAvailable(self, b):
        self.rawAvailable = b

    def mouseMoveEvent(self, event):
        self.coordsMouse = [event.x(), event.y()]
        self.repaint()

    def leaveEvent(self, event):
        self.coordsMouse = [-1, -1]
        self.repaint()

    #def resizeEvent(self, event):


    def paintEvent(self, event):
        super().paintEvent(event)

        # start draw
        painter = QPainter()
        painter.begin(self)

        # background
        # painter.setBackground(Qt.gray)
        # self.brush.setColor(Qt.darkGray)
        # self.brush.setStyle(Qt.Dense1Pattern)
        painter.setBackgroundMode(Qt.OpaqueMode)
        painter.setBackground(Qt.black)
        painter.setBrush(self.brushBG)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width()-1, self.height()-1)

        # draw photo
        if (not self.myPhoto.isNull()):
            destRectPhoto = QRect()

            # use the appropriate scaling factor that requires the most scaling ( - 2 to fit in border )
            wRatio = self.width()/self.myPhoto.width()
            hRatio = self.height()/self.myPhoto.height()
            if (wRatio <= hRatio):
                destRectPhoto.setWidth(self.srcRect.width() * wRatio - 2)
                destRectPhoto.setHeight(self.srcRect.height() * wRatio - 2)
            else:
                destRectPhoto.setWidth(self.srcRect.width() * hRatio - 2)
                destRectPhoto.setHeight(self.srcRect.height() * hRatio - 2)

            # center and draw it
            destRectPhoto.moveTo(self.width()/2-destRectPhoto.width()/2, self.height()/2-destRectPhoto.height()/2)
            painter.drawImage(destRectPhoto, self.myPhoto, self.srcRect)

            # HUD
            if (self.enableHUD):
                painter.setBackgroundMode(Qt.TransparentMode)
                #painter.setBackground(Qt.black)
                painter.setBrush(Qt.NoBrush)
                painter.setPen(self.penText)
                painter.setFont(self.font)
                destRect = QRect()
                radius = destRectPhoto.height() / 2

                # draw filename
                destRect.setCoords(10, 10, self.width()/2, 50)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, os.path.basename(self.myPhotoPath))
                # draw timestamp
                destRect.moveTo(10, 25)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.myPhotoTime))
                # draw dimensions
                destRect.moveTo(10, 40)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.srcRect.width()) + " x " + str(self.srcRect.height()))

                # draw grid
                if (self.enableGrid):
                    cx = destRectPhoto.x() + destRectPhoto.width() / 2
                    cy = destRectPhoto.y() + destRectPhoto.height() / 2
                    # radius
                    painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
                    # crosshairs
                    painter.drawLine(cx - radius, cy, cx + radius, cy)
                    painter.drawLine(cx, cy - radius, cx, cy + radius)
                    # labels
                    destRect.setCoords(cx - radius + 5, cy + 5, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "0")
                    destRect.setCoords(cx + radius - 15, cy + 5, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    destRect.setCoords(cx + 5, cy - radius + 5, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "0")
                    destRect.setCoords(cx + 5, cy + radius - 20, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    # sampling pattern
                    diameter = radius * 2
                    radiusSample = radius / 50
                    radiusSample2 = radiusSample * 2
                    u,v = 0,0
                    for s in self.samplingPattern:
                        u,v = angle_utilities.FisheyeAngleWarp(s[0], s[1])
                        u,v = angle_utilities.GetUVFromAngle(u, v)
                        u = (cx - radius) + (u * diameter)
                        v = (cy - radius) + (v * diameter)
                        painter.drawEllipse(u - radiusSample, v - radiusSample, radiusSample2, radiusSample2)

                # coordinates we are interested in
                #self.coordsMouse   # x,y of this widget
                coordsxy = [-1, -1] # x,y over photo as scaled/rendered on this widget
                coordsXY = [-1, -1] # x,y over actual original photo on disk
                coordsUC = [-1, -1] # unit circle coords [0-1] from center of photo to edge of fisheye radius
                coordsUV = [-1, -1] # u,v coords of fisheye portion of photo w/ 0,0 top left and 1,1 bottom right
                coordsTP = [-1, -1] # theta,phi polar coordinates
                distance = math.inf # distance from center of fisheye to mouse in unit circle

                # compute all relevant coordinates only when mouse is over fisheye portion of photo
                if (self.coordsMouse[0] >= destRectPhoto.x() and
                    self.coordsMouse[1] >= destRectPhoto.y() and
                    self.coordsMouse[0] < destRectPhoto.x() + destRectPhoto.width() and
                    self.coordsMouse[1] < destRectPhoto.y() + destRectPhoto.height()):
                    coordsxy[0] = self.coordsMouse[0] - destRectPhoto.x()
                    coordsxy[1] = self.coordsMouse[1] - destRectPhoto.y()
                    coordsUC[0] = (coordsxy[0] - destRectPhoto.width()/2) / radius
                    coordsUC[1] = (coordsxy[1] - destRectPhoto.height()/2) / radius
                    coordsXY[0] = int(coordsxy[0] / destRectPhoto.width() * self.myPhoto.width())
                    coordsXY[1] = int(coordsxy[1] / destRectPhoto.height() * self.myPhoto.height())
                    coordsUV[0] = (coordsUC[0] + 1) / 2
                    coordsUV[1] = (coordsUC[1] + 1) / 2
                    coordsTP = angle_utilities.GetAngleFromUV(coordsUV[0], coordsUV[1])
                    distance = math.sqrt((coordsUC[0] * coordsUC[0]) + (coordsUC[1] * coordsUC[1]))

                # formatted text strings for coordinates
                textxy = "-1, -1 xy"
                textXY = "-1, -1 uv"
                textUC = "-1, -1 uc"
                textUV = "-1, -1 fr"
                textTP = "-1, -1 θφ"
                if (distance <= 1.0):
                    textxy = str(coordsxy[0]) + ", " + str(coordsxy[1]) + " xy"
                    textXY = str(coordsXY[0]) + ", " + str(coordsXY[1]) + " xy"
                    textUC = "{:.2f}".format(coordsUC[0]) + ", " + "{:.2f}".format(coordsUC[1]) + " uc"
                    textUV = "{:.2f}".format(coordsUV[0]) + ", " + "{:.2f}".format(coordsUV[1]) + " uv"
                    textTP = "{:.2f}".format(coordsTP[0]) + ", " + "{:.2f}".format(coordsTP[1]) + " θφ"

                # draw x,y coords
                destRect.setCoords(10, 10, self.width()-10, self.height()- 124)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textxy)
                # draw u,v coords
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 114)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textXY)
                # draw unit circle coords
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 104)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textUC)
                # draw fractional coords
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 94)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textUV)
                # draw t,p coords
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 84)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textTP)

                # draw cursor visual indicators (outlines)
                circleX = self.width() - 10 - 64 - 10 - 64
                circleY = self.height() - 10 - 64
                pixelX = self.width() - 64 - 10
                pixelY = self.height() - 64 - 10
                painter.drawEllipse(circleX, circleY, 64, 64)
                painter.drawRect(pixelX, pixelY, 64, 64)

                # draw cursor visual indicators (filled if cursor is within fisheye radius)
                if (distance <= 1.0):
                    color = self.myPhoto.pixelColor(coordsXY[0], coordsXY[1])
                    painter.setBackgroundMode(Qt.OpaqueMode)
                    painter.setBackground(color)
                    painter.setBrush(QBrush(color, Qt.SolidPattern))
                    cx = circleX + (coordsUV[0] * 64)
                    cy = circleY + (coordsUV[1] * 64)
                    painter.drawEllipse(cx - 5, cy - 5, 10, 10)
                    painter.drawRect(pixelX, pixelY, 64, 64)

                # raw notice
                if (not self.rawAvailable):
                    painter.drawPixmap(self.width()-16-16, 16, self.iconWarning)

        # end draw
        painter.end()
