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
from PyQt5.QtCore import Qt, QRect, QPoint, QPointF
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QImage, QPainterPath, QTransform
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
        self.myPhotoRadius = 0
        self.myPhotoRotation = 0
        self.enableHUD = True
        self.enableUVGrid = False
        self.enableCompass = False
        self.enableSunPath = False
        self.enableSamples = False
        self.rawAvailable = False
        self.coordsMouse = [0, 0]
        self.viewCenter = [0, 0]
        self.sunPathPoints = []    # [theta (azimuth), phi (90-zenith), datetime]
        self.compassTicks = []     # [x1, y1, x2, y2, x1lbl, y1lbl, angle]
        self.samplesLocations = [] # all sample locations in the sampling pattern
        for i in range(0, len(self.samplingPattern)):
            self.samplesLocations.append(QRect(0, 0, 0, 0))

        # members - preloaded graphics
        self.painter = QPainter()
        self.pathSun = QPainterPath()
        self.brushBG = QBrush(Qt.black, Qt.SolidPattern)
        self.penText = QPen(Qt.white, 1, Qt.SolidLine)
        self.penSun = QPen(Qt.yellow, 1, Qt.SolidLine)
        self.fontFixed = QFont('Courier New', 8)
        self.fontScaled = QFont('Courier New', 8)
        self.fontBounds = 50
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

        # precompute as much as we can before drawing
        self.computeBounds()

    def setSunPath(self, sunpath):
        self.sunPathPoints = sunpath

    def resetRotation(self, angles=0):
        self.myPhotoRotation = angles

    def showHUD(self, b):
        self.enableHUD = b

    def showUVGrid(self, b):
        self.enableUVGrid = b

    def showCompass(self, b):
        self.enableCompass = b

    def showSunPath(self, b):
        self.enableSunPath = b

    def showSamples(self, b):
        self.enableSamples = b

    def mouseMoveEvent(self, event):
        # detect middle mouse button drag for image rotation
        if (event.buttons() == Qt.MidButton):
            old = [self.coordsMouse[0] - self.viewCenter[0], self.coordsMouse[1] - self.viewCenter[1]]
            new = [event.x() - self.viewCenter[0], event.y() - self.viewCenter[1]]
            # clockwise drag increases rotation
            if (old[1]*new[0] < old[0]*new[1]):
                self.myPhotoRotation += 1
            # counter-clockwise drag decreases rotation
            else:
                self.myPhotoRotation -= 1
            # rotation
            if (self.myPhotoRotation >= 0):
                self.myPhotoRotation %= 360
            else:
                self.myPhotoRotation %= -360

        self.coordsMouse = [event.x(), event.y()]
        self.repaint()

    def leaveEvent(self, event):
        self.coordsMouse = [-1, -1]
        self.repaint()

    def resizeEvent(self, event):
        self.computeBounds()

    # def contextMenuEvent(self, event):
    #     menuCtx = QMenu(self)
    #     actExit = QAction(QIcon(), '&Exit', self)
    #     menuCtx.addAction(actExit)
    #     action = menuCtx.exec_(self.mapToGlobal(event.pos()))
    #     if action == actExit:
    #         self.close()

    def computeBounds(self):
        if (self.myPhoto.isNull()):
            self.myPhotoDestRect = QRect(0, 0, self.width(), self.height())
            self.viewCenter = [self.width() / 2, self.height() / 2]
            self.myPhotoRadius = 0
            for i in range(0, len(self.samplingPattern)):
                self.samplesLocations[i].setRect(self.viewCenter[0], self.viewCenter[1], 0, 0)
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
        self.viewCenter[0] = self.myPhotoDestRect.x() + self.myPhotoDestRect.width() / 2
        self.viewCenter[1] = self.myPhotoDestRect.y() + self.myPhotoDestRect.height() / 2
        self.myPhotoRadius = self.myPhotoDestRect.height() / 2

        # compute new scaled font size
        self.fontScaled = QFont('Courier New', self.myPhotoRadius / 40)

        # compute sampling pattern locations
        diameter = self.myPhotoRadius * 2
        radiusSample = self.myPhotoRadius / 50
        radiusSample2 = radiusSample * 2
        u, v = 0, 0
        for i in range(0, len(self.samplingPattern)):
            u, v = utility_angles.FisheyeAngleWarp(self.samplingPattern[i][0], self.samplingPattern[i][1], inRadians=False)
            u, v = utility_angles.GetUVFromAngle(u, v, inRadians=False)
            u = (self.viewCenter[0] - self.myPhotoRadius) + (u * diameter)
            v = (self.viewCenter[1] - self.myPhotoRadius) + (v * diameter)
            self.samplesLocations[i].setRect(u - radiusSample, v - radiusSample, radiusSample2, radiusSample2)

        # compute compass lines
        self.compassTicks.clear()
        tickLength = self.myPhotoRadius / 90
        fontSize = self.fontScaled.pointSizeF()
        labelOffset = self.myPhotoRadius / 15
        for angle in range(0, 360, 10):
            theta = 360 - ((angle + 270) % 360)  # angles eastward from North, North facing down
            rads = theta * math.pi / 180.0
            cx1 = math.cos(rads) * (self.myPhotoRadius - tickLength) + self.viewCenter[0]
            cy1 = math.sin(rads) * (self.myPhotoRadius - tickLength) + self.viewCenter[1]
            cx2 = math.cos(rads) * self.myPhotoRadius + self.viewCenter[0]
            cy2 = math.sin(rads) * self.myPhotoRadius + self.viewCenter[1]
            lx1 = math.cos(rads) * (self.myPhotoRadius - labelOffset) + self.viewCenter[0] - (len(str(angle)) / 2.0 * fontSize)
            ly1 = math.sin(rads) * (self.myPhotoRadius - labelOffset) + self.viewCenter[1] - fontSize
            self.compassTicks.append([cx1, cy1, cx2, cy2, lx1, ly1, angle]) # x1, y1, x2, y2, x1lbl, y1lbl, angle

        # compute sun path
        self.pathSun = QPainterPath()
        if (len(self.sunPathPoints) > 0):
            t, p, dt = self.sunPathPoints[0]
            t, p = utility_angles.FisheyeAngleWarp(t, p, inRadians=False)
            u, v = utility_angles.GetUVFromAngle(t, p, inRadians=False)
            x = (self.viewCenter[0] - self.myPhotoRadius) + (u * diameter)
            y = (self.viewCenter[1] - self.myPhotoRadius) + (v * diameter)
            self.pathSun.moveTo(x, y)
            for i in range(1, len(self.sunPathPoints)):
                t, p, dt = self.sunPathPoints[i]
                t, p = utility_angles.FisheyeAngleWarp(t, p, inRadians=False)
                u, v = utility_angles.GetUVFromAngle(t, p, inRadians=False)
                x = (self.viewCenter[0] - self.myPhotoRadius) + (u * diameter)
                y = (self.viewCenter[1] - self.myPhotoRadius) + (v * diameter)
                self.pathSun.lineTo(x, y)

    def paintEvent(self, event):
        super().paintEvent(event)

        # start draw
        painter = QPainter()
        painter.begin(self)

        # background
        #self.brushBG.setColor(Qt.darkGray)
        #self.brushBG.setStyle(Qt.Dense1Pattern)
        #painter.setBackground(Qt.gray)
        painter.setBackgroundMode(Qt.OpaqueMode)
        painter.setBackground(Qt.black)
        painter.setBrush(self.brushBG)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width(), self.height())

        # draw photo
        if (not self.myPhoto.isNull()):
            transform = QTransform()
            transform.translate(self.myPhotoDestRect.center().x(), self.myPhotoDestRect.center().y())
            transform.rotate(self.myPhotoRotation)
            transform.translate(-self.myPhotoDestRect.center().x(), -self.myPhotoDestRect.center().y())
            painter.setTransform(transform)
            painter.drawImage(self.myPhotoDestRect, self.myPhoto, self.myPhotoSrcRect)
            painter.resetTransform()

            # HUD
            if (self.enableHUD):
                painter.setBackgroundMode(Qt.TransparentMode)
                #painter.setBackground(Qt.black)
                painter.setBrush(Qt.NoBrush)
                painter.setFont(self.fontScaled)
                destRect = QRect(0, 0, self.fontBounds, self.fontBounds)
                diameter = self.myPhotoRadius * 2

                # draw UV grid
                if (self.enableUVGrid):
                    painter.setPen(self.penText)
                    # box
                    painter.drawLine(self.viewCenter[0] - self.myPhotoRadius, self.viewCenter[1] - self.myPhotoRadius,
                                     self.viewCenter[0] + self.myPhotoRadius, self.viewCenter[1] - self.myPhotoRadius)
                    painter.drawLine(self.viewCenter[0] - self.myPhotoRadius, self.viewCenter[1] + self.myPhotoRadius,
                                     self.viewCenter[0] + self.myPhotoRadius, self.viewCenter[1] + self.myPhotoRadius)
                    painter.drawLine(self.viewCenter[0] - self.myPhotoRadius, self.viewCenter[1] - self.myPhotoRadius,
                                     self.viewCenter[0] - self.myPhotoRadius, self.viewCenter[1] + self.myPhotoRadius)
                    painter.drawLine(self.viewCenter[0] + self.myPhotoRadius, self.viewCenter[1] - self.myPhotoRadius,
                                     self.viewCenter[0] + self.myPhotoRadius, self.viewCenter[1] + self.myPhotoRadius)
                    # crosshairs
                    painter.drawLine(self.viewCenter[0] - self.myPhotoRadius, self.viewCenter[1], self.viewCenter[0] + self.myPhotoRadius, self.viewCenter[1])
                    painter.drawLine(self.viewCenter[0], self.viewCenter[1] - self.myPhotoRadius, self.viewCenter[0], self.viewCenter[1] + self.myPhotoRadius)
                    # labels
                    destRect.moveTo(self.viewCenter[0] - self.myPhotoRadius + 5, self.viewCenter[1] - self.myPhotoRadius + 5)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "0")
                    destRect.moveTo(self.viewCenter[0] + self.myPhotoRadius - 10, self.viewCenter[1] - self.myPhotoRadius + 5)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    destRect.moveTo(self.viewCenter[0] - self.myPhotoRadius + 5, self.viewCenter[1] + self.myPhotoRadius - 15)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    destRect.moveTo(self.viewCenter[0] + self.myPhotoRadius - 10, self.viewCenter[1] + self.myPhotoRadius - 15)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")

                # draw sun path
                if (self.enableSunPath):
                    painter.setPen(self.penSun)
                    painter.drawPath(self.pathSun)
                    for i in range(0, self.pathSun.elementCount()):
                        e = self.pathSun.elementAt(i)
                        destRect.moveTo(e.x, e.y + 5)
                        painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.sunPathPoints[i][2].hour))

                # draw compass
                if (self.enableCompass):
                    painter.setPen(self.penText)
                    # ticks
                    for tick in self.compassTicks:
                        painter.drawLine(tick[0], tick[1], tick[2], tick[3])
                        destRect.moveTo(tick[4], tick[5])
                        painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(tick[6])) # + "°"
                    # radius
                    painter.drawEllipse(self.viewCenter[0] - self.myPhotoRadius, self.viewCenter[1] - self.myPhotoRadius, diameter, diameter)
                    # cardinal directions
                    destRect.moveTo(self.viewCenter[0] - self.myPhotoRadius - self.fontScaled.pointSizeF() * 3, self.viewCenter[1] - self.fontScaled.pointSizeF() / 2 * 2)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "W")
                    destRect.moveTo(self.viewCenter[0] + self.myPhotoRadius + self.fontScaled.pointSizeF(), self.viewCenter[1] - self.fontScaled.pointSizeF() / 2 * 2)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "E")
                    destRect.moveTo(self.viewCenter[0] - self.fontScaled.pointSizeF() / 2, self.viewCenter[1] - self.myPhotoRadius - self.fontScaled.pointSizeF() * 3)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "S")
                    destRect.moveTo(self.viewCenter[0] - self.fontScaled.pointSizeF() / 2, self.viewCenter[1] + self.myPhotoRadius + self.fontScaled.pointSizeF())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "N")

                # draw sampling pattern
                if (self.enableSamples):
                    painter.setPen(self.penText)
                    for r in self.samplesLocations:
                        painter.drawEllipse(r)

                # draw filename
                painter.setPen(self.penText)
                painter.setFont(self.fontFixed)
                destRect.setCoords(10, 10, self.width() / 2, 50)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, os.path.basename(self.myPhotoPath))
                # draw timestamp
                destRect.moveTo(10, 25)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.myPhotoTime))
                # draw dimensions
                destRect.moveTo(10, 40)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.myPhotoSrcRect.width()) + " x " + str(self.myPhotoSrcRect.height()))
                # draw photo rotation
                if (self.myPhotoRotation != 0):
                    destRect.moveTo(10, self.height()-25)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "Rotation: " + str(self.myPhotoRotation) + "°")

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
                    coordsUC[0] = (coordsxy[0] - self.myPhotoDestRect.width()/2) / self.myPhotoRadius
                    coordsUC[1] = (coordsxy[1] - self.myPhotoDestRect.height()/2) / self.myPhotoRadius
                    coordsXY[0] = int(coordsxy[0] / self.myPhotoDestRect.width() * self.myPhoto.width())
                    coordsXY[1] = int(coordsxy[1] / self.myPhotoDestRect.height() * self.myPhoto.height())
                    # rads = self.myPhotoRotation * math.pi / 180.0
                    # preRotX = coordsxy[0] - self.myPhotoDestRect.width()/2
                    # preRotY = coordsxy[1] - self.myPhotoDestRect.height()/2
                    # if (self.myPhotoRotation > 0):
                    #     preRotX = preRotX * math.cos(rads) + preRotY * math.sin(rads)
                    #     preRotY = -preRotX * math.sin(rads) + preRotY * math.cos(rads)
                    # else:
                    #     preRotX = preRotX * math.cos(rads) - preRotY * math.sin(rads)
                    #     preRotY = preRotX * math.sin(rads) + preRotY * math.cos(rads)
                    # preRotX = preRotX + self.myPhotoDestRect.width()/2
                    # preRotY = preRotY + self.myPhotoDestRect.height()/2
                    # coordsXY[0] = int(preRotX / self.myPhotoDestRect.width() * self.myPhoto.width())
                    # coordsXY[1] = int(preRotY / self.myPhotoDestRect.height() * self.myPhoto.height())
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
