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
import colorsys
from enum import Enum
from datetime import datetime
from PyQt5.QtCore import Qt, QRect, QPoint, QPointF
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QImage, QPixmap, QPainterPath, QTransform, QIcon, QColor
from PyQt5.QtWidgets import QWidget, QStyle, QAction, QMenu
import numpy as np
from common import *
import utility
import utility_angles
import utility_data


class ViewFisheye(QWidget):

    # sample selection
    SelectionType = Enum('SelectType', 'Exact Closest Rect')
    SelectionMode = Enum('SelectMode', 'Select Add Remove')
    SelectionRectMin = 10   # pixels, width and height, scales as photo scales
    SelectedPixelBox = 64   # pixels, width and height

    def __init__(self, parent):
        super().__init__()

        # members
        self.parent = parent
        self.myPhoto = QImage()
        self.myPhotoPixels = np.zeros(shape=(1, 1, 4))
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
        self.coordsMouse = (0, 0)
        self.viewCenter = (0, 0)
        self.dragSelectRect = QRect(0, 0, 0, 0)
        self.sunPosition = (0, 0)       # (azimuth (theta), altitude (phi)(90-zenith))
        self.sunPositionVisible = (0,0) # point (x,y) of sun location rendered on screen (scaled)
        self.sunPathPoints = []         # [(azimuth (theta), altitude (phi)(90-zenith), datetime)]
        self.compassTicks = []          # [[x1, y1, x2, y2, x1lbl, y1lbl, angle]]
        self.sampleBoundsVisible = []   # bounds QRect(x,y,w,h) of all samples on the photo rendered on screen (scaled)
        self.samplePointsInFile = []    # points (x,y) of all samples in the photo on file
        self.samplesSelected = []       # indices of selected samples
        self.pixelRegion = 1
        self.pixelWeighting = PixelWeighting.Mean
        self.skyCover = SkyCover.UNK

        # members - preloaded graphics
        self.painter = QPainter()
        self.mask = QImage()
        self.pathSun = QPainterPath()
        self.brushBG = QBrush(Qt.black, Qt.SolidPattern)
        self.penText = QPen(Qt.white, 1, Qt.SolidLine)
        self.penSelected = [] # list of pens, one for each sampling pattern location
        self.penSelectRect = QPen(Qt.white, 1, Qt.DashLine)
        self.penSun = QPen(Qt.yellow, 1, Qt.SolidLine)
        self.fontFixed = QFont('Courier New', 8)
        self.fontScaled = QFont('Courier New', 8)
        self.fontBounds = 50
        self.iconWarning = self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(ViewFisheye.SelectedPixelBox / 2)

        # init
        self.setMouseTracking(True)
        color = QColor(255, 255, 255)
        for t,p in SamplingPattern:
            self.sampleBoundsVisible.append(QRect(0, 0, 0, 0)) # these will need to be recomputed as photo scales
            self.samplePointsInFile.append((0, 0))             # these only need to be computed once per photo
            color.setHsv(t, int(utility.normalize(p, 0, 90)*127+128), 255)
            self.penSelected.append(QPen(color, 3, Qt.SolidLine))

    def getSamplePatternRGB(self, index):
        if (index < 0 or index >= len(SamplingPattern)):
            return (0,0,0)
        color = self.penSelected[index].color()
        return (color.red(), color.green(), color.blue())

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

            # compute each sample's coordinate in the photo
            self.samplePointsInFile = []
            center = (int(self.myPhotoSrcRect.width() / 2), int(self.myPhotoSrcRect.height()/2))
            radius = self.myPhotoSrcRect.height() / 2
            diameter = radius * 2
            for i in range(0, len(SamplingPattern)):
                u, v = utility_angles.FisheyeAngleWarp(SamplingPattern[i][0], SamplingPattern[i][1], inRadians=False)
                u, v = utility_angles.GetUVFromAngle(u, v, inRadians=False)
                x = (center[0] - radius) + (u * diameter)
                y = (center[1] - radius) + (v * diameter)
                self.samplePointsInFile.append((int(x), int(y)))

            # keep a copy the image's pixels in memory (used later for exporting, etc.)
            ptr = self.myPhoto.bits()
            ptr.setsize(self.myPhoto.byteCount())
            pixbgr = np.asarray(ptr).reshape(self.myPhoto.height(), self.myPhoto.width(), 4)
            # HACKAROONIE: byte order is not the same as image format, so swapped it around. should handle this better :/
            self.myPhotoPixels = np.copy(pixbgr)
            red = np.copy(self.myPhotoPixels[:, :, 0])
            self.myPhotoPixels[:, :, 0] = self.myPhotoPixels[:, :, 2]
            self.myPhotoPixels[:, :, 2] = red
            # rgba = self.myPhoto.pixelColor(center[0], center[1])
            # print((rgba.red(), rgba.green(), rgba.blue()))
            # rgba = pixrgb[center[1], center[0]]
            # print(rgba)

        # photo is null or missing
        else:
            self.myPhoto = QImage()
            self.myPhotoPixels = np.zeros(shape=(1,1,4))
            self.myPhotoPath = ""
            self.myPhotoTime = datetime(1, 1, 1)
            self.myPhotoSrcRect = QRect()
            self.myPhotoDestRect = QRect()
            self.rawAvailable = False

        # precompute as much as we can before any drawing
        self.computeBounds()

    def setSunPath(self, sunpath):
        self.sunPathPoints = sunpath

    def setSunPosition(self, pos):
        self.sunPosition = pos

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

    def setPixelRegion(self, r):
        if (r < PixelRegionMin):
            self.pixelRegion = PixelRegionMin
        else:
            self.pixelRegion = r

    def setPixelWeighting(self, w):
        if (w not in PixelWeighting):
            self.pixelWeighting = PixelWeighting.Mean
        else:
            self.pixelWeighting = w

    def setSkycover(self, sc):
        self.skyCover = sc

    def selectSamples(self, message="none"):
        # nothing to do if no photo loaded
        if (self.myPhoto.isNull()):
            return

        # first clear selection
        self.samplesSelected.clear()

        # if (message == "none"):
        if (message == "all"):
            self.samplesSelected.clear()
            for i in range(0, len(self.sampleBoundsVisible)):
                self.samplesSelected.append(i)

        # update
        self.repaint()
        self.parent.graphSamples(self.samplesSelected)

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
        elif (event.buttons() == Qt.MidButton):
            old = (self.coordsMouse[0] - self.viewCenter[0], self.coordsMouse[1] - self.viewCenter[1])
            new = (event.x() - self.viewCenter[0], event.y() - self.viewCenter[1])
            # clockwise drag decreases rotation
            if (old[1]*new[0] < old[0]*new[1]):
                self.myPhotoRotation -= 1
            # counter-clockwise drag increases rotation
            else:
                self.myPhotoRotation += 1
            # rotation
            if (self.myPhotoRotation >= 0):
                self.myPhotoRotation %= 360
            else:
                self.myPhotoRotation %= -360

        # lastly, cache mouse coordinates and update
        self.coordsMouse = (event.x(), event.y())
        self.repaint()

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
            prevSelected = list(self.samplesSelected)
            if (self.dragSelectRect.width() < ViewFisheye.SelectionRectMin and
                self.dragSelectRect.height() < ViewFisheye.SelectionRectMin):
                self.computeSelectedSamples(ViewFisheye.SelectionType.Closest, mode)
            else:
                self.computeSelectedSamples(ViewFisheye.SelectionType.Rect, mode)

            # reset drag selection
            self.dragSelectRect.setX(event.x())
            self.dragSelectRect.setY(event.y())
            self.dragSelectRect.setWidth(0)
            self.dragSelectRect.setHeight(0)

            # update
            self.repaint()
            if (self.samplesSelected != prevSelected):
                self.parent.graphSamples(self.samplesSelected)

    def wheelEvent(self, event):
        # nothing to do if no photo loaded
        if (self.myPhoto.isNull()):
            return

        self.parent.timeChangeWheelEvent(event)

    def leaveEvent(self, event):
        self.coordsMouse = (-1, -1)
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
            for i in range(0, len(self.sampleBoundsVisible)):
                x1 = self.sampleBoundsVisible[i].x()
                y1 = self.sampleBoundsVisible[i].y()
                x2 = self.sampleBoundsVisible[i].x() + self.sampleBoundsVisible[i].width()
                y2 = self.sampleBoundsVisible[i].y() + self.sampleBoundsVisible[i].width()
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
                for i in range(0, len(self.sampleBoundsVisible)):
                    x1 = self.sampleBoundsVisible[i].center().x()
                    y1 = self.sampleBoundsVisible[i].center().y()
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
            for i in range(0, len(self.sampleBoundsVisible)):
                px = self.sampleBoundsVisible[i].center().x()
                py = self.sampleBoundsVisible[i].center().y()
                if (px >= x1 and px <= x2 and py >= y1 and py <= y2):
                    sampleAdjustments.append(i)

        # no changes to be made
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

        # sort selection for easier searching later
        self.samplesSelected.sort()

    def computeBounds(self):
        if (self.myPhoto.isNull()):
            self.myPhotoDestRect = QRect(0, 0, self.width(), self.height())
            self.viewCenter = (self.width() / 2, self.height() / 2)
            self.myPhotoRadius = 0
            for i in range(0, len(SamplingPattern)):
                self.sampleBoundsVisible[i].setRect(self.viewCenter[0], self.viewCenter[1], 0, 0)
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
        self.viewCenter = (self.myPhotoDestRect.x() + self.myPhotoDestRect.width() / 2,
                           self.myPhotoDestRect.y() + self.myPhotoDestRect.height() / 2)
        self.myPhotoRadius = self.myPhotoDestRect.height() / 2

        # compute new scaled font size
        self.fontScaled = QFont('Courier New', self.myPhotoRadius / 40)

        # compute sampling pattern locations
        photoDiameter = self.myPhotoRadius * 2
        sampleRadius = self.myPhotoRadius / 50
        sampleDiameter = sampleRadius * 2
        ViewFisheye.SelectionRectMin = sampleDiameter # minimum selection rect is based on this
        u, v = 0, 0
        for i in range(0, len(SamplingPattern)):
            u, v = utility_angles.FisheyeAngleWarp(SamplingPattern[i][0], SamplingPattern[i][1], inRadians=False)
            u, v = utility_angles.GetUVFromAngle(u, v, inRadians=False)
            u = (self.viewCenter[0] - self.myPhotoRadius) + (u * photoDiameter)
            v = (self.viewCenter[1] - self.myPhotoRadius) + (v * photoDiameter)
            self.sampleBoundsVisible[i].setRect(u - sampleRadius, v - sampleRadius, sampleDiameter, sampleDiameter)

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

        # compute sun path screen points
        # v = 0.7159*u - 0.0048*math.pow(u, 2) - 0.032*math.pow(u, 3) + 0.0021*math.pow(u, 4)
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

        # compute sun position screen point
        t, p = self.sunPosition
        t, p = utility_angles.FisheyeAngleWarp(t, p, inRadians=False)
        u, v = utility_angles.GetUVFromAngle(t, p, inRadians=False)
        x = (self.viewCenter[0] - self.myPhotoRadius) + (u * photoDiameter)
        y = (self.viewCenter[1] - self.myPhotoRadius) + (v * photoDiameter)
        self.sunPositionVisible = (x, y)

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
            transform.rotate(-self.myPhotoRotation)
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
                    sunradius = self.myPhotoRadius*0.1
                    painter.drawEllipse(self.sunPositionVisible[0]-sunradius/2, self.sunPositionVisible[1]-sunradius/2, sunradius, sunradius)
                    painter.drawPath(self.pathSun)
                    for i in range(0, self.pathSun.elementCount()):
                        e = self.pathSun.elementAt(i)
                        destRect.moveTo(e.x, e.y + 5)
                        painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft,
                                         str(self.sunPathPoints[i][2].hour))

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
                    for i, r in enumerate(self.sampleBoundsVisible):
                        painter.drawEllipse(r)
                        painter.drawText(r.x()-r.width(), r.y(), str(i))

                # always draw selected samples
                #painter.setPen(self.penSelected)
                r = QRect()
                for i in self.samplesSelected:
                    r.setCoords(self.sampleBoundsVisible[i].x(), self.sampleBoundsVisible[i].y(), self.sampleBoundsVisible[i].right() + 1, self.sampleBoundsVisible[i].bottom() + 1)
                    painter.setPen(self.penSelected[i])
                    painter.drawEllipse(r)

                # draw selection bounds
                if (abs(self.dragSelectRect.right()-self.dragSelectRect.left()) >= ViewFisheye.SelectionRectMin and
                    abs(self.dragSelectRect.bottom()-self.dragSelectRect.top()) >= ViewFisheye.SelectionRectMin):
                    painter.setPen(self.penSelectRect)
                    painter.drawRect(self.dragSelectRect)

                # draw timestamp
                painter.setPen(self.penText)
                painter.setFont(self.fontFixed)
                destRect.setCoords(10, 10, self.width() / 2, 50)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.myPhotoTime))
                # draw sky cover assessment
                destRect.moveTo(10, 25)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "Sky: " + self.skyCover.name + "/" + SkyCoverDesc[self.skyCover])
                # draw photo rotation
                if (self.myPhotoRotation != 0):
                    destRect.moveTo(10, self.height()-25)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "Rotation: " + str(self.myPhotoRotation) + "°")

                # information we are interested in displaying
                #self.coordsMouse   # x,y of this widget
                coordsxy = (-1, -1) # x,y over photo as scaled/rendered on this widget
                coordsXY = (-1, -1) # x,y over actual original photo on disk
                coordsUC = (-1, -1) # unit circle coords [0-1] from center of photo to edge of fisheye radius
                coordsUV = (-1, -1) # u,v coords of fisheye portion of photo w/ 0,0 top left and 1,1 bottom right
                coordsTP = (-1, -1) # theta,phi polar coordinates
                distance = math.inf # distance from center of fisheye to mouse in unit circle

                # compute all relevant information only when mouse is within fisheye portion of photo
                if (self.coordsMouse[0] >= self.myPhotoDestRect.x() and
                    self.coordsMouse[1] >= self.myPhotoDestRect.y() and
                    self.coordsMouse[0] < self.myPhotoDestRect.x() + self.myPhotoDestRect.width() and
                    self.coordsMouse[1] < self.myPhotoDestRect.y() + self.myPhotoDestRect.height()):
                    coordsxy = (self.coordsMouse[0] - self.myPhotoDestRect.x(),
                                self.coordsMouse[1] - self.myPhotoDestRect.y())
                    coordsUC = ((coordsxy[0] - self.myPhotoDestRect.width()/2) / self.myPhotoRadius,
                                (coordsxy[1] - self.myPhotoDestRect.height()/2) / self.myPhotoRadius)
                    coordsXY = (int(coordsxy[0] / self.myPhotoDestRect.width() * self.myPhoto.width()),
                                int(coordsxy[1] / self.myPhotoDestRect.height() * self.myPhoto.height()))
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
                    coordsUV = ((coordsUC[0] + 1) / 2,
                                (coordsUC[1] + 1) / 2)
                    coordsTP = utility_angles.GetAngleFromUV(coordsUV[0], coordsUV[1])
                    distance = math.sqrt((coordsUC[0] * coordsUC[0]) + (coordsUC[1] * coordsUC[1]))

                # pixels colors
                colorsRegion = np.zeros((self.pixelRegion, self.pixelRegion, 4))
                colorFinal = colorsRegion[0,0] # RGBA of pixel under mouse of photo on disk
                # colorFinal = self.myPhoto.pixelColor(coordsXY[0], coordsXY[1])
                if (distance <= 1.0):
                    halfdim = int(self.pixelRegion / 2)
                    rstart = coordsXY[1] - halfdim
                    rstop = coordsXY[1]+halfdim+1
                    cstart = coordsXY[0]-halfdim
                    cstop = coordsXY[0]+halfdim+1
                    if (rstart >= 0 and rstop<=self.myPhotoPixels.shape[0] and
                        cstart >= 0 and cstop<=self.myPhotoPixels.shape[1]):
                        colorsRegion = self.myPhotoPixels[rstart:rstop, cstart:cstop]
                        colorFinal = colorsRegion[halfdim, halfdim]
                        # pixel color weighting
                        if self.pixelRegion > 1:
                            colorFinal = utility_data.collectPixels([coordsXY], pixels=self.myPhotoPixels, region=self.pixelRegion, weighting=self.pixelWeighting)[0]

                # text strings for information we want to display on HUD
                textxy = "-1, -1 xy"
                textXY = "-1, -1 xy"
                textUC = "-1, -1 uc"
                textUV = "-1, -1 uv"
                textTP = "-1, -1 θφ"
                textPX = "0 0 0 px"
                if (distance <= 1.0):
                    textxy = str(coordsxy[0]) + ", " + str(coordsxy[1]) + " xy"
                    textXY = str(coordsXY[0]) + ", " + str(coordsXY[1]) + " xy"
                    textUC = "{:.2f}".format(coordsUC[0]) + ", " + "{:.2f}".format(coordsUC[1]) + " uc"
                    textUV = "{:.2f}".format(coordsUV[0]) + ", " + "{:.2f}".format(coordsUV[1]) + " uv"
                    textTP = "{:.2f}".format(coordsTP[0]) + ", " + "{:.2f}".format(coordsTP[1]) + " θφ"
                    textPX = str(colorFinal[0]) + " " + str(colorFinal[1]) + " " + str(colorFinal[2]) + " px"
                # draw x,y coords
                destRect.setCoords(10, 10, self.width()-10, self.height()- 134)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textxy)
                # draw u,v coords
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 124)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textXY)
                # draw unit circle coords
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 114)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textUC)
                # draw fractional coords
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 104)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textUV)
                # draw t,p coords
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 94)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textTP)
                # draw pixel color
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 84)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, textPX)

                # compute pixel visualization coordinates
                circleX = self.width() - 10 - ViewFisheye.SelectedPixelBox - 10 - ViewFisheye.SelectedPixelBox - 10 - ViewFisheye.SelectedPixelBox
                circleY = self.height() - 10 - ViewFisheye.SelectedPixelBox
                pixelsX = self.width() - 10 - ViewFisheye.SelectedPixelBox - 10 - ViewFisheye.SelectedPixelBox
                pixelsY = self.height() - 10 - ViewFisheye.SelectedPixelBox
                pixelsWeightedX = self.width() - ViewFisheye.SelectedPixelBox - 10
                pixelsWeightedY = self.height() - 10 - ViewFisheye.SelectedPixelBox

                # draw cursor visual indicators - fills (if cursor is within fisheye radius)
                if (distance <= 1.0):
                    painter.setPen(Qt.NoPen)
                    # pixel region
                    pixdim = ViewFisheye.SelectedPixelBox / self.pixelRegion
                    for row in range(0, self.pixelRegion):
                        for col in range(0, self.pixelRegion):
                            color = colorsRegion[row, col]
                            color = QColor(color[0], color[1], color[2])
                            painter.setBrush(QBrush(color, Qt.SolidPattern))
                            painter.drawRect(pixelsX + (col * pixdim), pixelsY + (row * pixdim), math.ceil(pixdim), math.ceil(pixdim))
                    # final pixel color
                    color = QColor(colorFinal[0], colorFinal[1], colorFinal[2])
                    painter.setBrush(QBrush(color, Qt.SolidPattern))
                    cx = circleX + (coordsUV[0] * ViewFisheye.SelectedPixelBox)
                    cy = circleY + (coordsUV[1] * ViewFisheye.SelectedPixelBox)
                    painter.drawEllipse(cx - 5, cy - 5, 10, 10)
                    painter.drawRect(pixelsWeightedX, pixelsWeightedY, ViewFisheye.SelectedPixelBox, ViewFisheye.SelectedPixelBox)

                # draw cursor visual indicators - outlines
                painter.setPen(self.penText)
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(circleX, circleY, ViewFisheye.SelectedPixelBox, ViewFisheye.SelectedPixelBox)
                painter.drawRect(pixelsX, pixelsY, ViewFisheye.SelectedPixelBox, ViewFisheye.SelectedPixelBox)
                painter.drawRect(pixelsWeightedX, pixelsWeightedY, ViewFisheye.SelectedPixelBox, ViewFisheye.SelectedPixelBox)

                # raw data missing indicator
                # if (not self.rawAvailable):
                #     painter.drawPixmap(pixelX + ViewFisheye.SelectedPixelBox / 2,
                #                        pixelY + ViewFisheye.SelectedPixelBox / 2,
                #                        self.iconWarning)

        # end draw
        painter.end()
