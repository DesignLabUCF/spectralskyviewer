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
from PyQt5.QtCore import Qt, QRect, QPointF
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QImage, QPainterPath
from PyQt5.QtWidgets import QWidget, QStyle
import utility
import utility_angles
import utility_data


class ViewFisheye(QWidget):
    def __init__(self):
        super().__init__()

        # members - skydome sampling pattern: 81 samples (theta, phi)
        self.samplingPattern = [
            [000.00, 12.1151],
            [011.25, 12.1151],
            [022.50, 12.1151],
            [033.75, 12.1151],
            [045.00, 12.1151],
            [056.25, 12.1151],
            [067.50, 12.1151],
            [078.75, 12.1151],
            [090.00, 12.1151],
            [101.25, 12.1151],
            [112.50, 12.1151],
            [123.75, 12.1151],
            [135.00, 12.1151],
            [146.25, 12.1151],
            [157.50, 12.1151],
            [168.75, 12.1151],
            [180.00, 12.1151],
            [191.25, 12.1151],
            [202.50, 12.1151],
            [213.75, 12.1151],
            [225.00, 12.1151],
            [236.25, 12.1151],
            [247.50, 12.1151],
            [258.75, 12.1151],
            [270.00, 12.1151],
            [281.25, 12.1151],
            [292.50, 12.1151],
            [303.75, 12.1151],
            [315.00, 12.1151],
            [326.25, 12.1151],
            [337.50, 12.1151],
            [348.75, 12.1151],
            [345.00, 33.7490],
            [330.00, 33.7490],
            [315.00, 33.7490],
            [300.00, 33.7490],
            [285.00, 33.7490],
            [270.00, 33.7490],
            [255.00, 33.7490],
            [240.00, 33.7490],
            [225.00, 33.7490],
            [210.00, 33.7490],
            [195.00, 33.7490],
            [180.00, 33.7490],
            [165.00, 33.7490],
            [150.00, 33.7490],
            [135.00, 33.7490],
            [120.00, 33.7490],
            [105.00, 33.7490],
            [090.00, 33.7490],
            [075.00, 33.7490],
            [060.00, 33.7490],
            [045.00, 33.7490],
            [030.00, 33.7490],
            [015.00, 33.7490],
            [000.00, 33.7490],
            [000.00, 53.3665],
            [022.50, 53.3665],
            [045.00, 53.3665],
            [067.50, 53.3665],
            [090.00, 53.3665],
            [112.50, 53.3665],
            [135.00, 53.3665],
            [157.50, 53.3665],
            [180.00, 53.3665],
            [202.50, 53.3665],
            [225.00, 53.3665],
            [247.50, 53.3665],
            [270.00, 53.3665],
            [292.50, 53.3665],
            [315.00, 53.3665],
            [337.50, 53.3665],
            [315.00, 71.9187],
            [270.00, 71.9187],
            [225.00, 71.9187],
            [180.00, 71.9187],
            [135.00, 71.9187],
            [090.00, 71.9187],
            [045.00, 71.9187],
            [000.00, 71.9187],
            [000.00, 90.0000],
        ]
        # convert to radians
        #self.samplingPattern[:] = [[math.radians(s[0]), math.radians(s[1])] for s in self.samplingPattern]

        # members
        self.myPhoto = QImage()
        self.myPhotoPath = ""
        self.myPhotoTime = datetime(1,1,1)
        self.myPhotoSrcRect = QRect()
        self.myPhotoDestRect = QRect()
        self.enableHUD = True
        self.enableGrid = False
        self.enableSunPath = False
        self.rawAvailable = False
        self.coordsMouse = [0, 0]
        self.sunPathPoints = []  # theta (azimuth), phi (90-zenith), datetime
        self.gridCenter = [0, 0]
        self.gridRadius = 0
        self.gridSamples = []
        for i in range(0, len(self.samplingPattern)):
            self.gridSamples.append(QRect(0,0,0,0)) # these need to be recomputed after valid photo dest rect

        # members - preloaded graphics
        self.painter = QPainter()
        self.pathSun = QPainterPath()
        self.brushBG = QBrush(Qt.black, Qt.SolidPattern)
        self.penText = QPen(Qt.white, 1, Qt.SolidLine)
        self.penSun = QPen(Qt.yellow, 1, Qt.SolidLine)
        self.font = QFont('Courier New', 8)
        self.iconWarning = self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(16)

        # init
        self.setMouseTracking(True)

    def setPhoto(self, path, exif=None):
        # if photo is valid
        if (path is not None and os.path.exists(path)):
            self.myPhotoPath = path
            self.myPhoto = QImage(path)
            self.myPhotoSrcRect = QRect(0, 0, self.myPhoto.width(), self.myPhoto.height())
            self.myPhotoDestRect = QRect(0, 0, self.width(), self.height())
            self.rawAvailable = utility_data.isHDRRawAvailable(path)
            if (exif is not None):
                self.myPhotoTime = datetime.strptime(str(exif["EXIF DateTimeOriginal"]), '%Y:%m:%d %H:%M:%S')
            else:
                self.myPhotoTime = utility_data.imageEXIFDateTime(path)
        # photo is null or missing
        else:
            self.myPhoto = QImage()
            self.myPhotoPath = ""
            self.myPhotoTime = datetime(1, 1, 1)
            self.myPhotoSrcRect = QRect()
            self.myPhotoDestRect = QRect()
            self.rawAvailable = False
        self.computeBounds()

    def setSunPath(self, sunpath):
        self.sunPathPoints = sunpath

    def computeBounds(self):
        if (self.myPhoto.isNull()):
            self.myPhotoDestRect = QRect(0, 0, self.width(), self.height())
            self.gridCenter = [self.width()/2, self.height()/2]
            self.gridRadius = 0
            for i in range(0, len(self.samplingPattern)):
                self.gridSamples[i].setRect(self.gridCenter[0], self.gridCenter[1], 0, 0)
            return

        # scale the photo dest rect
        # scale by the scaling factor that requires the most scaling ( - 2 to fit in border )
        wRatio = self.width() / self.myPhoto.width()
        hRatio = self.height() / self.myPhoto.height()
        if (wRatio <= hRatio):
            self.myPhotoDestRect.setWidth(self.myPhotoSrcRect.width() * wRatio - 2)
            self.myPhotoDestRect.setHeight(self.myPhotoSrcRect.height() * wRatio - 2)
        else:
            self.myPhotoDestRect.setWidth(self.myPhotoSrcRect.width() * hRatio - 2)
            self.myPhotoDestRect.setHeight(self.myPhotoSrcRect.height() * hRatio - 2)

        # center the photo dest rect
        self.myPhotoDestRect.moveTo(self.width() / 2 - self.myPhotoDestRect.width() / 2,
                                    self.height() / 2 - self.myPhotoDestRect.height() / 2)

        # compute grid center
        self.gridCenter[0] = self.myPhotoDestRect.x() + self.myPhotoDestRect.width() / 2
        self.gridCenter[1] = self.myPhotoDestRect.y() + self.myPhotoDestRect.height() / 2
        self.gridRadius = self.myPhotoDestRect.height() / 2

        # computer sampling pattern locations
        diameter = self.gridRadius * 2
        radiusSample = self.gridRadius / 50
        radiusSample2 = radiusSample * 2
        u, v = 0, 0
        for i in range(0, len(self.samplingPattern)):
            u, v = utility_angles.FisheyeAngleWarp(self.samplingPattern[i][0], self.samplingPattern[i][1], inRadians=False)
            u, v = utility_angles.GetUVFromAngle(u, v, inRadians=False)
            u = (self.gridCenter[0] - self.gridRadius) + (u * diameter)
            v = (self.gridCenter[1] - self.gridRadius) + (v * diameter)
            self.gridSamples[i].setRect(u - radiusSample, v - radiusSample, radiusSample2, radiusSample2)

        # compute sun path
        self.pathSun = QPainterPath()
        if (len(self.sunPathPoints) > 0):
            t, p, dt = self.sunPathPoints[0]
            t, p = utility_angles.FisheyeAngleWarp(t, p, inRadians=False)
            u, v = utility_angles.GetUVFromAngle(t, p, inRadians=False)
            x = (self.gridCenter[0] - self.gridRadius) + (u * diameter)
            y = (self.gridCenter[1] - self.gridRadius) + (v * diameter)
            self.pathSun.moveTo(x, y)
            for i in range(1, len(self.sunPathPoints)):
                t, p, dt = self.sunPathPoints[i]
                t, p = utility_angles.FisheyeAngleWarp(t, p, inRadians=False)
                u, v = utility_angles.GetUVFromAngle(t, p, inRadians=False)
                x = (self.gridCenter[0] - self.gridRadius) + (u * diameter)
                y = (self.gridCenter[1] - self.gridRadius) + (v * diameter)
                self.pathSun.lineTo(x, y)

    def showHUD(self, b):
        self.enableHUD = b

    def showGrid(self, b):
        self.enableGrid = b

    def showSunPath(self, b):
        self.enableSunPath = b

    def mouseMoveEvent(self, event):
        self.coordsMouse = [event.x(), event.y()]
        self.repaint()

    def leaveEvent(self, event):
        self.coordsMouse = [-1, -1]
        self.repaint()

    def resizeEvent(self, event):
        self.computeBounds()

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
            painter.drawImage(self.myPhotoDestRect, self.myPhoto, self.myPhotoSrcRect)

            # HUD
            if (self.enableHUD):
                painter.setBackgroundMode(Qt.TransparentMode)
                #painter.setBackground(Qt.black)
                painter.setBrush(Qt.NoBrush)
                painter.setFont(self.font)
                destRect = QRect()
                diameter = self.gridRadius * 2

                # draw sun path
                if (self.enableSunPath):
                    painter.setPen(self.penSun)
                    painter.drawPath(self.pathSun)
                    for i in range(0, self.pathSun.elementCount()):
                        e = self.pathSun.elementAt(i)
                        destRect.setCoords(e.x, e.y + 5, self.width() - 1, self.height() - 1)
                        painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.sunPathPoints[i][2].hour))

                # draw grid
                if (self.enableGrid):
                    painter.setPen(self.penText)
                    # radius
                    painter.drawEllipse(self.gridCenter[0] - self.gridRadius, self.gridCenter[1] - self.gridRadius, diameter, diameter)
                    # crosshairs
                    painter.drawLine(self.gridCenter[0] - self.gridRadius, self.gridCenter[1], self.gridCenter[0] + self.gridRadius, self.gridCenter[1])
                    painter.drawLine(self.gridCenter[0], self.gridCenter[1] - self.gridRadius, self.gridCenter[0], self.gridCenter[1] + self.gridRadius)
                    # labels
                    destRect.setCoords(self.gridCenter[0] - self.gridRadius + 5, self.gridCenter[1] + 5, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "0")
                    destRect.setCoords(self.gridCenter[0] + self.gridRadius - 15, self.gridCenter[1] + 5, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    destRect.setCoords(self.gridCenter[0] + 5, self.gridCenter[1] - self.gridRadius + 5, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "0")
                    destRect.setCoords(self.gridCenter[0] + 5, self.gridCenter[1] + self.gridRadius - 20, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    # sampling pattern
                    for r in self.gridSamples:
                        painter.drawEllipse(r)

                # draw filename
                painter.setPen(self.penText)
                destRect.setCoords(10, 10, self.width() / 2, 50)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, os.path.basename(self.myPhotoPath))
                # draw timestamp
                destRect.moveTo(10, 25)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.myPhotoTime))
                # draw dimensions
                destRect.moveTo(10, 40)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft,
                                 str(self.myPhotoSrcRect.width()) + " x " + str(self.myPhotoSrcRect.height()))

                # coordinates we are interested in
                #self.coordsMouse   # x,y of this widget
                coordsxy = [-1, -1] # x,y over photo as scaled/rendered on this widget
                coordsXY = [-1, -1] # x,y over actual original photo on disk
                coordsUC = [-1, -1] # unit circle coords [0-1] from center of photo to edge of fisheye radius
                coordsUV = [-1, -1] # u,v coords of fisheye portion of photo w/ 0,0 top left and 1,1 bottom right
                coordsTP = [-1, -1] # theta,phi polar coordinates
                distance = math.inf # distance from center of fisheye to mouse in unit circle

                # compute all relevant coordinates only when mouse is over fisheye portion of photo
                if (self.coordsMouse[0] >= self.myPhotoDestRect.x() and
                    self.coordsMouse[1] >= self.myPhotoDestRect.y() and
                    self.coordsMouse[0] < self.myPhotoDestRect.x() + self.myPhotoDestRect.width() and
                    self.coordsMouse[1] < self.myPhotoDestRect.y() + self.myPhotoDestRect.height()):
                    coordsxy[0] = self.coordsMouse[0] - self.myPhotoDestRect.x()
                    coordsxy[1] = self.coordsMouse[1] - self.myPhotoDestRect.y()
                    coordsUC[0] = (coordsxy[0] - self.myPhotoDestRect.width()/2) / self.gridRadius
                    coordsUC[1] = (coordsxy[1] - self.myPhotoDestRect.height()/2) / self.gridRadius
                    coordsXY[0] = int(coordsxy[0] / self.myPhotoDestRect.width() * self.myPhoto.width())
                    coordsXY[1] = int(coordsxy[1] / self.myPhotoDestRect.height() * self.myPhoto.height())
                    coordsUV[0] = (coordsUC[0] + 1) / 2
                    coordsUV[1] = (coordsUC[1] + 1) / 2
                    coordsTP = utility_angles.GetAngleFromUV(coordsUV[0], coordsUV[1])
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
