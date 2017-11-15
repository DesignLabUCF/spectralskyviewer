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
from enum import Enum
from datetime import datetime
from PyQt5.QtCore import Qt, QRect, QPoint, QPointF
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QImage, QPixmap, QPainterPath, QTransform, QIcon
from PyQt5.QtWidgets import QWidget, QStyle, QAction, QMenu
import utility
import utility_angles
import utility_data


class ViewFisheye(QWidget):
    # selection types and modes
    SelectionType = Enum('SelectType', 'Exact Closest Rect')
    SelectionMode = Enum('SelectMode', 'Select Add Remove')
    SelectionRectMin = 10 # pixels, width and height

    # skydome sampling pattern: 81 samples (theta, phi)
    SamplingPattern = [
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
    # ViewFisheye.SamplingPattern[:] = [[math.radians(s[0]), math.radians(s[1])] for s in ViewFisheye.SamplingPattern]

    def __init__(self, parent):
        super().__init__()

        # members
        self.parent = parent
        self.myPhoto = QImage()
        self.myPhotoPath = ""
        self.myPhotoTime = datetime(1,1,1)
        self.myPhotoSrcRect = QRect()
        self.myPhotoDestRect = QRect()
        self.myPhotoRadius = 0
        self.myPhotoRotation = 0
        self.enableMask = True
        self.enableHUD = True
        self.enableUVGrid = False
        self.enableCompass = False
        self.enableSunPath = False
        self.enableSamples = False
        self.rawAvailable = False
        self.coordsMouse = [0, 0]
        self.viewCenter = [0, 0]
        self.dragSelectRect = QRect(0, 0, 0, 0)
        self.sunPathPoints = []    # [theta (azimuth), phi (90-zenith), datetime]
        self.compassTicks = []     # [x1, y1, x2, y2, x1lbl, y1lbl, angle]
        self.samplesLocations = [] # all sample locations in the sampling pattern
        self.samplesSelected = []  # indices of sample locations selected
        for i in range(0, len(ViewFisheye.SamplingPattern)):
            self.samplesLocations.append(QRect(0, 0, 0, 0))

        # members - preloaded graphics
        self.painter = QPainter()
        self.mask = QImage()
        self.pathSun = QPainterPath()
        self.brushBG = QBrush(Qt.black, Qt.SolidPattern)
        self.penText = QPen(Qt.white, 1, Qt.SolidLine)
        self.penSelected = QPen(Qt.magenta, 3, Qt.SolidLine)
        self.penSelectRect = QPen(Qt.white, 1, Qt.DashLine)
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

    def showMask(self, b):
        self.enableMask = b

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

    def selectSamples(self, message="none"):
        # nothing to do if no photo loaded
        if (self.myPhoto.isNull()):
            return

        # first clear selection
        self.samplesSelected.clear()

        # if (message == "none"):
        if (message == "all"):
            self.samplesSelected.clear()
            for i in range(0, len(self.samplesLocations)):
                self.samplesSelected.append(i)

        # update
        self.repaint()
        self.parent.graphSamples(self.samplesSelected)

    def mousePressEvent(self, event):
        # nothing to do if no photo loaded
        if (self.myPhoto.isNull()):
            return

        # we only care about a left click for point and drag selection
        # right click is for context menu - handled elsewhere
        # middle click is for rotation - handled elsewhere
        if (event.buttons() != Qt.LeftButton):
            return

        # start logging drag selection (whether user drags or not)
        self.dragSelectRect.setX(event.x())
        self.dragSelectRect.setY(event.y())
        self.dragSelectRect.setWidth(0)
        self.dragSelectRect.setHeight(0)

    def mouseMoveEvent(self, event):
        # nothing to do if no photo loaded
        if (self.myPhoto.isNull()):
            return

        # detect primary mouse button drag for sample selection
        if (event.buttons() == Qt.LeftButton):
            # update drag selection bounds
            self.dragSelectRect.setWidth(event.x() - self.dragSelectRect.x())
            self.dragSelectRect.setHeight(event.y() - self.dragSelectRect.y())

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

        # lastly, cache mouse coordinates and update
        self.coordsMouse = [event.x(), event.y()]
        self.repaint()

    def mouseReleaseEvent(self, event):
        # nothing to do if no photo loaded
        if (self.myPhoto.isNull()):
            return

        # detect primary mouse button release for stopping sample selection
        if (event.button() == Qt.LeftButton):
            # read modifier keys for user desired selection mode
            mode = ViewFisheye.SelectionMode.Select
            if (event.modifiers() == Qt.ControlModifier):
                mode = ViewFisheye.SelectionMode.Add
            elif (event.modifiers() == Qt.ShiftModifier):
                mode = ViewFisheye.SelectionMode.Remove

            # unflip coordinates of rect so that width and height are always positive
            r = self.dragSelectRect
            r = utility.rectForwardFacing([r.x(), r.y(), r.right(), r.bottom()])
            self.dragSelectRect.setCoords(r[0], r[1], r[2], r[3])

            # select samples
            prevCount = len(self.samplesSelected)
            if (self.dragSelectRect.width() < ViewFisheye.SelectionRectMin and
                self.dragSelectRect.height() < ViewFisheye.SelectionRectMin):
                self.computeSelectedSamples(ViewFisheye.SelectionType.Closest, mode)
            else:
                self.computeSelectedSamples(ViewFisheye.SelectionType.Rect, mode)
            diff = abs(len(self.samplesSelected) - prevCount)

            # reset drag selection
            self.dragSelectRect.setX(event.x())
            self.dragSelectRect.setY(event.y())
            self.dragSelectRect.setWidth(0)
            self.dragSelectRect.setHeight(0)

            # update
            self.repaint()
            if (diff > 0):
                self.parent.graphSamples(self.samplesSelected)

    def leaveEvent(self, event):
        self.coordsMouse = [-1, -1]
        self.repaint()

    def resizeEvent(self, event):
        self.computeBounds()

    def contextMenuEvent(self, event):
        # nothing to do if no photo loaded
        if (self.myPhoto.isNull()):
            return

        self.parent.triggerContextMenu(self, event)

    def computeSelectedSamples(self, type, mode):
        px = 0
        py = 0
        x1 = 0
        y1 = 0
        x2 = 0
        y2 = 0

        # in select mode, clear current selection
        if (mode == ViewFisheye.SelectionMode.Select):
            self.samplesSelected = []

        # these are the sample we will be adding or removing
        sampleAdjustments = []

        # which single sample did user select by point
        if (type == ViewFisheye.SelectionType.Exact):
            px = self.coordsMouse[0]
            py = self.coordsMouse[1]
            for i in range(0, len(self.samplesLocations)):
                x1 = self.samplesLocations[i].x()
                y1 = self.samplesLocations[i].y()
                x2 = self.samplesLocations[i].x() + self.samplesLocations[i].width()
                y2 = self.samplesLocations[i].y() + self.samplesLocations[i].width()
                if (px >= x1 and px <= x2 and py >= y1 and py <= y2):
                    sampleAdjustments.append(i)
                    break
        # which single sample is the closest to the mouse coordinate
        elif (type == ViewFisheye.SelectionType.Closest):
            px = self.coordsMouse[0]
            py = self.coordsMouse[1]
            dist = math.sqrt((py-self.viewCenter[1])*(py-self.viewCenter[1]) + (px-self.viewCenter[0])*(px-self.viewCenter[0]))
            if (dist <= self.myPhotoRadius):
                close = math.inf
                closest = -1
                for i in range(0, len(self.samplesLocations)):
                    x1 = self.samplesLocations[i].center().x()
                    y1 = self.samplesLocations[i].center().y()
                    dist = math.sqrt((y1-py)*(y1-py) + (x1-px)*(x1-px))
                    if (dist < close):
                        close = dist
                        closest = i
                if (closest >= 0):
                    sampleAdjustments.append(closest)
        # which samples are in the drag selection rect
        elif (type == ViewFisheye.SelectionType.Rect):
            x1 = self.dragSelectRect.x()
            y1 = self.dragSelectRect.y()
            x2 = self.dragSelectRect.x() + self.dragSelectRect.width()
            y2 = self.dragSelectRect.y() + self.dragSelectRect.height()
            for i in range(0, len(self.samplesLocations)):
                px = self.samplesLocations[i].center().x()
                py = self.samplesLocations[i].center().y()
                if (px >= x1 and px <= x2 and py >= y1 and py <= y2):
                    sampleAdjustments.append(i)

        # no changes
        if (len(sampleAdjustments) <= 0):
            return

        # finally modify sample selection and return difference
        if (mode == ViewFisheye.SelectionMode.Select or mode == ViewFisheye.SelectionMode.Add):
            for i in range(0, len(sampleAdjustments)):
                if (sampleAdjustments[i] not in self.samplesSelected): # don't readd existing indices
                    self.samplesSelected.append(sampleAdjustments[i])
        elif (mode == ViewFisheye.SelectionMode.Remove):
            for i in range(0, len(sampleAdjustments)):
                try:
                    self.samplesSelected.remove(sampleAdjustments[i])
                except:
                    pass # ignore trying to remove indices that aren't currently selected

    def computeBounds(self):
        if (self.myPhoto.isNull()):
            self.myPhotoDestRect = QRect(0, 0, self.width(), self.height())
            self.viewCenter = [self.width() / 2, self.height() / 2]
            self.myPhotoRadius = 0
            for i in range(0, len(ViewFisheye.SamplingPattern)):
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
        photoDiameter = self.myPhotoRadius * 2
        sampleRadius = self.myPhotoRadius / 50
        sampleDiameter = sampleRadius * 2
        ViewFisheye.SelectionRectMin = sampleDiameter # minimum selection rect is based on this
        u, v = 0, 0
        for i in range(0, len(ViewFisheye.SamplingPattern)):
            u, v = utility_angles.FisheyeAngleWarp(ViewFisheye.SamplingPattern[i][0], ViewFisheye.SamplingPattern[i][1], inRadians=False)
            u, v = utility_angles.GetUVFromAngle(u, v, inRadians=False)
            u = (self.viewCenter[0] - self.myPhotoRadius) + (u * photoDiameter)
            v = (self.viewCenter[1] - self.myPhotoRadius) + (v * photoDiameter)
            self.samplesLocations[i].setRect(u - sampleRadius, v - sampleRadius, sampleDiameter, sampleDiameter)

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
            x = (self.viewCenter[0] - self.myPhotoRadius) + (u * photoDiameter)
            y = (self.viewCenter[1] - self.myPhotoRadius) + (v * photoDiameter)
            self.pathSun.moveTo(x, y)
            for i in range(1, len(self.sunPathPoints)):
                t, p, dt = self.sunPathPoints[i]
                t, p = utility_angles.FisheyeAngleWarp(t, p, inRadians=False)
                u, v = utility_angles.GetUVFromAngle(t, p, inRadians=False)
                x = (self.viewCenter[0] - self.myPhotoRadius) + (u * photoDiameter)
                y = (self.viewCenter[1] - self.myPhotoRadius) + (v * photoDiameter)
                self.pathSun.lineTo(x, y)

        # compute new mask
        self.mask = QPixmap(self.width(), self.height()).toImage()

    def paintEvent(self, event):
        super().paintEvent(event)

        # start draw
        painter = QPainter()
        painter.begin(self)

        # background
        if (not self.enableMask):
            self.brushBG.setColor(Qt.darkGray)
            self.brushBG.setStyle(Qt.Dense1Pattern)
            painter.setBackground(Qt.gray)

        else:
            self.brushBG.setColor(Qt.black)
            self.brushBG.setStyle(Qt.SolidPattern)
            painter.setBackground(Qt.black)
        painter.setBackgroundMode(Qt.OpaqueMode)
        painter.setBrush(self.brushBG)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width(), self.height())

        # draw photo
        if (not self.myPhoto.isNull()):
            # rotate and draw photo as specified by user
            transform = QTransform()
            transform.translate(self.myPhotoDestRect.center().x(), self.myPhotoDestRect.center().y())
            transform.rotate(self.myPhotoRotation)
            transform.translate(-self.myPhotoDestRect.center().x(), -self.myPhotoDestRect.center().y())
            painter.setTransform(transform)
            painter.drawImage(self.myPhotoDestRect, self.myPhoto, self.myPhotoSrcRect) # draw it
            painter.resetTransform()

            # useful local vars
            destRect = QRect(0, 0, self.fontBounds, self.fontBounds)
            diameter = self.myPhotoRadius * 2

            # mask
            if (self.enableMask):
                maskPainter = QPainter()
                maskPainter.begin(self.mask)
                maskPainter.setBrush(QBrush(Qt.magenta, Qt.SolidPattern))
                maskPainter.drawEllipse(self.viewCenter[0] - self.myPhotoRadius, self.viewCenter[1] - self.myPhotoRadius, diameter, diameter)
                maskPainter.end()
                painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                painter.drawImage(0, 0, self.mask)
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # HUD
            if (self.enableHUD):
                painter.setBackgroundMode(Qt.TransparentMode)
                #painter.setBackground(Qt.black)
                painter.setBrush(Qt.NoBrush)
                painter.setFont(self.fontScaled)

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
                    destRect.moveTo(self.viewCenter[0] - self.myPhotoRadius + self.fontScaled.pointSizeF(), self.viewCenter[1] - self.myPhotoRadius + self.fontScaled.pointSizeF())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "0")
                    destRect.moveTo(self.viewCenter[0] + self.myPhotoRadius - self.fontScaled.pointSizeF()*2, self.viewCenter[1] - self.myPhotoRadius + self.fontScaled.pointSizeF())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    destRect.moveTo(self.viewCenter[0] - self.myPhotoRadius + self.fontScaled.pointSizeF(), self.viewCenter[1] + self.myPhotoRadius - self.fontScaled.pointSizeF()*3)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    destRect.moveTo(self.viewCenter[0] + self.myPhotoRadius - self.fontScaled.pointSizeF()*2, self.viewCenter[1] + self.myPhotoRadius - self.fontScaled.pointSizeF()*3)
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

                # always draw selected samples
                painter.setPen(self.penSelected)
                r = QRect()
                for i in self.samplesSelected:
                    r.setCoords(self.samplesLocations[i].x(), self.samplesLocations[i].y(), self.samplesLocations[i].right()+1, self.samplesLocations[i].bottom()+1)
                    painter.drawEllipse(r)

                # draw selection bounds
                if (abs(self.dragSelectRect.right()-self.dragSelectRect.left()) >= ViewFisheye.SelectionRectMin and
                    abs(self.dragSelectRect.bottom()-self.dragSelectRect.top()) >= ViewFisheye.SelectionRectMin):
                    painter.setPen(self.penSelectRect)
                    painter.drawRect(self.dragSelectRect)

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
