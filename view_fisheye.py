#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 10/13/2017
# @summary: A widget for displaying the original fisheye view of the HDR data
# ====================================================================
import os
import math
from enum import Enum
from datetime import datetime
from PyQt5.QtCore import Qt, QRect, QPoint, QPointF, QLine, QLineF
from PyQt5.QtGui import QFont, QFontMetrics, QPainter, QPen, QBrush, QImage, QPixmap, QPainterPath, QTransform, QColor
from PyQt5.QtWidgets import QWidget, QStyle
import numpy as np
import common
import utility
import utility_angles
import utility_data


class ViewFisheye(QWidget):

    # sample selection
    SelectionType = Enum('SelectType', 'Exact Closest Rect')
    SelectionMode = Enum('SelectMode', 'Select Add Remove')
    SelectionRectMin = 10   # pixels, width and height, scales as photo scales
    SampleRadius = 10       # pixels, scales as photo scales
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
        self.rawAvailable = False
        self.coordsMouse = (0, 0)
        self.viewCenter = (0, 0)
        self.dragSelectRect = QRect(0, 0, 0, 0)
        self.sunPosition = (0, 0)        # (azimuth (theta), altitude (phi)(90-zenith))
        self.sunPositionVisible = (0,0)  # point (x,y) of sun location rendered on screen (scaled)
        self.sunPathPoints = []          # [(azimuth (theta), altitude (phi)(90-zenith), datetime)]
        self.compassTicks = []           # [[x1, y1, x2, y2, x1lbl, y1lbl, angle]]
        self.lensIdealRadii = []         # list of radii for ideal lens latitudes to draw
        self.lensRealRadii = []          # list of radii for real/warped lens latitudes to draw
        self.samplePoints = []           # (x,y) coords of all samples on the photo rendered on screen (scaled)
        self.sampleAreaVisible = []      # area of 4 points for each sample rendered on screen (scaled)
        self.samplePointsInFile = []     # points (x,y) of all samples in the photo on file
        self.samplesSelected = []        # indices of selected samples
        self.skyCover = common.SkyCover.UNK

        # members - preloaded graphics
        self.painter = QPainter()
        self.mask = QImage()
        self.pathSun = QPainterPath()
        self.penText = QPen(Qt.white, 1, Qt.SolidLine)
        self.penLens = QPen(Qt.magenta, 1, Qt.SolidLine)
        self.penSun = QPen(QColor(255, 165, 0), 2, Qt.SolidLine)
        self.penSelected = []  # list of pens, one for each sampling pattern location
        self.penSelectRect = QPen(Qt.white, 1, Qt.DashLine)
        self.penShadowText = QPen(Qt.black, 1, Qt.SolidLine)
        self.penShadowSun = QPen(Qt.black, 2, Qt.SolidLine)
        self.penShadowSelected = QPen(Qt.black, 3, Qt.SolidLine)
        self.fontFixed = QFont('Courier New', 8)
        self.fontScaled = QFont('Courier New', 8)
        self.fontMetrics = QFontMetrics(self.fontScaled)
        self.iconWarning = self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(ViewFisheye.SelectedPixelBox / 2)

    def dataLoaded(self):
        # this stuff only runs once the data directory has been loaded

        self.setMouseTracking(True)
        color = QColor(255, 255, 255)
        self.samplesSelected.clear()
        self.samplePoints.clear()
        self.sampleAreaVisible.clear()
        self.samplePointsInFile.clear()
        self.penSelected.clear()

        for t, p in common.SamplingPattern:
            self.samplePoints.append((0, 0))  # these will need to be recomputed as photo scales
            self.samplePointsInFile.append((0, 0))  # these only need to be computed once per photo
            self.sampleAreaVisible.append([])
            color.setHsv(t, int(utility.normalize(p, 0, 90) * 127 + 128), 255)
            self.penSelected.append(QPen(color, 3, Qt.SolidLine))

    def setPhoto(self, path, exif=None):
        # if photo is valid
        if path is not None and os.path.exists(path):
            self.myPhotoPath = path
            self.myPhoto = QImage(path)
            self.myPhotoSrcRect = QRect(0, 0, self.myPhoto.width(), self.myPhoto.height())
            self.myPhotoDestRect = QRect(0, 0, self.width(), self.height())
            self.rawAvailable = utility_data.isHDRRawAvailable(path)
            if exif is not None:
                self.myPhotoTime = datetime.strptime(str(exif["EXIF DateTimeOriginal"]), '%Y:%m:%d %H:%M:%S')
            else:
                self.myPhotoTime = utility_data.imageEXIFDateTime(path)

            # cache each sample's coordinate in the photo
            # note: technically doesn't need to be recalculated if all photos have same resolution!
            self.samplePointsInFile = utility_data.computePointsInImage(path, common.SamplingPattern)

            # keep a copy the image's pixels in memory (used later for exporting, etc.)
            ptr = self.myPhoto.bits()
            ptr.setsize(self.myPhoto.byteCount())
            pixbgr = np.asarray(ptr).reshape(self.myPhoto.height(), self.myPhoto.width(), 4)
            # HACKAROONIE: byte order is not the same as image format, so swapped it around :/
            # TODO: should handle this better
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

    def setSkycover(self, sc):
        self.skyCover = sc

    def getSamplePatternRGB(self, index):
        if index < 0 or index >= len(common.SamplingPattern):
            return (0,0,0)
        color = self.penSelected[index].color()
        return (color.red(), color.green(), color.blue())

    def resetRotation(self, angles=0):
        self.myPhotoRotation = angles

    def selectSamples(self, message="none"):
        # nothing to do if no photo loaded
        if self.myPhoto.isNull():
            return

        # handle selection message
        if message == "none":
            self.samplesSelected.clear()
        elif message == "all":
            self.samplesSelected[:] = [i for i in range(0, len(common.SamplingPattern))]
        elif message == "inverse":
            allidx = set([i for i in range(0, len(common.SamplingPattern))])
            selidx = set(self.samplesSelected)
            self.samplesSelected[:] = list(allidx - selidx)

        # remove samples in circumsolar avoidance region if necessary
        sunAvoid = common.AppSettings["AvoidSunAngle"]
        if sunAvoid > 0:
            sunAvoidRads = math.radians(common.AppSettings["AvoidSunAngle"])
            sunPosRads = (math.radians(self.sunPosition[0]), math.radians(self.sunPosition[1]))
            self.samplesSelected[:] = [idx for idx in self.samplesSelected if utility_angles.CentralAngle(sunPosRads, common.SamplingPatternRads[idx], inRadians=True) > sunAvoidRads]

        # update
        self.repaint()
        self.parent.graphSamples(self.samplesSelected)

    def mouseMoveEvent(self, event):
        # nothing to do if no photo loaded
        if self.myPhoto.isNull():
            return

        # detect primary mouse button drag for sample selection
        if event.buttons() == Qt.LeftButton:
            # update drag selection bounds
            self.dragSelectRect.setWidth(event.x() - self.dragSelectRect.x())
            self.dragSelectRect.setHeight(event.y() - self.dragSelectRect.y())

        # detect middle mouse button drag for image rotation
        elif (event.buttons() == Qt.MidButton):
            old = (self.coordsMouse[0] - self.viewCenter[0], self.coordsMouse[1] - self.viewCenter[1])
            new = (event.x() - self.viewCenter[0], event.y() - self.viewCenter[1])
            # clockwise drag decreases rotation
            if old[1]*new[0] < old[0]*new[1]:
                self.myPhotoRotation -= 1
            # counter-clockwise drag increases rotation
            else:
                self.myPhotoRotation += 1
            # rotation
            if self.myPhotoRotation >= 0:
                self.myPhotoRotation %= 360
            else:
                self.myPhotoRotation %= -360

        # lastly, cache mouse coordinates and update
        self.coordsMouse = (event.x(), event.y())
        self.repaint()

    def mousePressEvent(self, event):
        # nothing to do if no photo loaded
        if self.myPhoto.isNull():
            return
        # we only care about a left click for point and drag selection
        # right click is for context menu - handled elsewhere
        # middle click is for rotation - handled elsewhere
        if event.buttons() != Qt.LeftButton:
            return

        # start logging drag selection (whether user drags or not)
        self.dragSelectRect.setX(event.x())
        self.dragSelectRect.setY(event.y())
        self.dragSelectRect.setWidth(0)
        self.dragSelectRect.setHeight(0)

    def mouseReleaseEvent(self, event):
        # nothing to do if no photo loaded
        if self.myPhoto.isNull():
            return

        # detect primary mouse button release for stopping sample selection
        if event.button() == Qt.LeftButton:
            # read modifier keys for user desired selection mode
            mode = ViewFisheye.SelectionMode.Select
            if event.modifiers() == Qt.ControlModifier:
                mode = ViewFisheye.SelectionMode.Add
            elif event.modifiers() == Qt.ShiftModifier:
                mode = ViewFisheye.SelectionMode.Remove

            # unflip coordinates of rect so that width and height are always positive
            r = self.dragSelectRect
            r = utility.rectForwardFacing([r.x(), r.y(), r.right(), r.bottom()])
            self.dragSelectRect.setCoords(r[0], r[1], r[2], r[3])

            # select samples
            prevSelected = list(self.samplesSelected)
            if self.dragSelectRect.width() < ViewFisheye.SelectionRectMin and self.dragSelectRect.height() < ViewFisheye.SelectionRectMin:
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
            if self.samplesSelected != prevSelected:
                self.parent.graphSamples(self.samplesSelected)

    def wheelEvent(self, event):
        # nothing to do if no photo loaded
        if self.myPhoto.isNull():
            return

        self.parent.timeChangeWheelEvent(event)

    def leaveEvent(self, event):
        self.coordsMouse = (-1, -1)
        self.repaint()

    def resizeEvent(self, event):
        self.computeBounds()

    def contextMenuEvent(self, event):
        # nothing to do if no photo loaded
        if self.myPhoto.isNull():
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
        if mode == ViewFisheye.SelectionMode.Select:
            self.samplesSelected = []

        # these are the samples we will be adding or removing
        sampleAdjustments = []

        # which single sample did user select by point
        if type == ViewFisheye.SelectionType.Exact:
            px = self.coordsMouse[0]
            py = self.coordsMouse[1]
            for i in range(0, len(self.samplePoints)):
                x, y = self.samplePoints[i]
                x1 = x - ViewFisheye.SampleRadius
                y1 = y - ViewFisheye.SampleRadius
                x2 = x + ViewFisheye.SampleRadius
                y2 = y + ViewFisheye.SampleRadius
                if px >= x1 and px <= x2 and py >= y1 and py <= y2:
                    sampleAdjustments.append(i)
                    break
        # which single sample is the closest to the mouse coordinate
        elif type == ViewFisheye.SelectionType.Closest:
            px = self.coordsMouse[0]
            py = self.coordsMouse[1]
            dist = math.sqrt((py-self.viewCenter[1])*(py-self.viewCenter[1]) + (px-self.viewCenter[0])*(px-self.viewCenter[0]))
            if dist <= self.myPhotoRadius:
                close = math.inf
                closest = -1
                for i in range(0, len(self.samplePoints)):
                    x, y = self.samplePoints[i]
                    dist = math.sqrt((y-py)*(y-py) + (x-px)*(x-px))
                    if dist < close:
                        close = dist
                        closest = i
                if closest >= 0:
                    sampleAdjustments.append(closest)
        # which samples are in the drag selection rect
        elif type == ViewFisheye.SelectionType.Rect:
            x1 = self.dragSelectRect.x()
            y1 = self.dragSelectRect.y()
            x2 = self.dragSelectRect.x() + self.dragSelectRect.width()
            y2 = self.dragSelectRect.y() + self.dragSelectRect.height()
            for i in range(0, len(self.samplePoints)):
                x, y = self.samplePoints[i]
                if x >= x1 and x <= x2 and y >= y1 and y <= y2:
                    sampleAdjustments.append(i)

        # remove samples in circumsolar avoidance region
        sunAvoid = common.AppSettings["AvoidSunAngle"]
        if sunAvoid > 0:
            sunAvoidRads = math.radians(common.AppSettings["AvoidSunAngle"])
            sunPosRads = (math.radians(self.sunPosition[0]), math.radians(self.sunPosition[1]))
            sampleAdjustments[:] = [idx for idx in sampleAdjustments if utility_angles.CentralAngle(sunPosRads, common.SamplingPatternRads[idx], inRadians=True) > sunAvoidRads]

        # no changes to be made
        if len(sampleAdjustments) <= 0:
            return

        # finally modify sample selection and return difference
        if mode == ViewFisheye.SelectionMode.Select or mode == ViewFisheye.SelectionMode.Add:
            for i in range(0, len(sampleAdjustments)):
                if sampleAdjustments[i] not in self.samplesSelected:  # don't readd existing indices
                    self.samplesSelected.append(sampleAdjustments[i])
        elif mode == ViewFisheye.SelectionMode.Remove:
            for i in range(0, len(sampleAdjustments)):
                try:
                    self.samplesSelected.remove(sampleAdjustments[i])
                except:
                    pass # ignore trying to remove indices that aren't currently selected

        # sort selection for easier searching later
        self.samplesSelected.sort()

    def computeBounds(self):
        if self.myPhoto.isNull():
            self.myPhotoDestRect = QRect(0, 0, self.width(), self.height())
            self.viewCenter = (self.width() / 2, self.height() / 2)
            self.myPhotoRadius = 0
            for i in range(0, len(common.SamplingPattern)):
                self.samplePoints[i] = (0, 0)
                self.sampleAreaVisible[i] = []
            return

        # scale the photo dest rect
        # scale by the scaling factor that requires the most scaling ( - 2 to fit in border )
        wRatio = self.width() / self.myPhoto.width()
        hRatio = self.height() / self.myPhoto.height()
        if wRatio <= hRatio:
            self.myPhotoDestRect.setWidth(self.myPhotoSrcRect.width() * wRatio - 2)
            self.myPhotoDestRect.setHeight(self.myPhotoSrcRect.height() * wRatio - 2)
        else:
            self.myPhotoDestRect.setWidth(self.myPhotoSrcRect.width() * hRatio - 2)
            self.myPhotoDestRect.setHeight(self.myPhotoSrcRect.height() * hRatio - 2)

        # center the photo dest rect
        self.myPhotoDestRect.moveTo(self.width() / 2 - self.myPhotoDestRect.width() / 2,
                                    self.height() / 2 - self.myPhotoDestRect.height() / 2)

        # compute plotting center and radius
        self.viewCenter = (self.myPhotoDestRect.x() + self.myPhotoDestRect.width() / 2,
                          self.myPhotoDestRect.y() + self.myPhotoDestRect.height() / 2)
        self.myPhotoRadius = self.myPhotoDestRect.height() / 2
        # debug - hardcoded image center and radius for 8/30/2013 0900
        # wr = 2182.0 / self.myPhoto.width()
        # hr = 1448.0 / self.myPhoto.height()
        # rr = 1436.0 / self.myPhoto.height()
        # sw = (self.myPhotoDestRect.width() * wr) + self.myPhotoDestRect.x()
        # sh = (self.myPhotoDestRect.height() * hr) + self.myPhotoDestRect.y()
        # sr = (self.myPhotoDestRect.height() * rr)
        # self.viewCenter = (int(sw), int(sh))
        # self.myPhotoRadius = int(sr)
        myPhotoDiameter = self.myPhotoRadius * 2

        # compute new scaled font size
        self.fontScaled = QFont('Courier New', self.myPhotoRadius * (1/(101-common.AppSettings["HUDTextScale"])))
        self.fontMetrics = QFontMetrics(self.fontScaled)

        # compute sampling pattern collision bounds
        ViewFisheye.SampleRadius = self.myPhotoRadius / 50
        hFOV = common.DataConfig["RadianceFOV"] / 2
        for i in range(0, len(common.SamplingPattern)):
            # compute sample bounds
            u, v = utility_angles.SkyCoord2FisheyeUV(common.SamplingPattern[i][0], common.SamplingPattern[i][1])
            x = (u * myPhotoDiameter) + (self.viewCenter[0] - self.myPhotoRadius)
            y = (v * myPhotoDiameter) + (self.viewCenter[1] - self.myPhotoRadius)
            self.samplePoints[i] = (x, y)
            # compute sampling pattern actual sampling areas (projected differential angle area)
            p1 = utility_angles.SkyCoord2FisheyeUV(common.SamplingPattern[i][0] - hFOV, common.SamplingPattern[i][1] - hFOV)
            p2 = utility_angles.SkyCoord2FisheyeUV(common.SamplingPattern[i][0] - hFOV, common.SamplingPattern[i][1] + hFOV)
            p3 = utility_angles.SkyCoord2FisheyeUV(common.SamplingPattern[i][0] + hFOV, common.SamplingPattern[i][1] + hFOV)
            p4 = utility_angles.SkyCoord2FisheyeUV(common.SamplingPattern[i][0] + hFOV, common.SamplingPattern[i][1] - hFOV)
            p1 = QPoint((self.viewCenter[0] - self.myPhotoRadius) + (p1[0] * myPhotoDiameter),
                        (self.viewCenter[1] - self.myPhotoRadius) + (p1[1] * myPhotoDiameter))
            p2 = QPoint((self.viewCenter[0] - self.myPhotoRadius) + (p2[0] * myPhotoDiameter),
                        (self.viewCenter[1] - self.myPhotoRadius) + (p2[1] * myPhotoDiameter))
            p3 = QPoint((self.viewCenter[0] - self.myPhotoRadius) + (p3[0] * myPhotoDiameter),
                        (self.viewCenter[1] - self.myPhotoRadius) + (p3[1] * myPhotoDiameter))
            p4 = QPoint((self.viewCenter[0] - self.myPhotoRadius) + (p4[0] * myPhotoDiameter),
                        (self.viewCenter[1] - self.myPhotoRadius) + (p4[1] * myPhotoDiameter))
            self.sampleAreaVisible[i] = [p1, p2, p3, p4]

        # compute compass lines
        self.compassTicks.clear()
        tickLength = self.myPhotoRadius / 90
        for angle in range(0, 360, 10):
            theta = 360 - ((angle + 270) % 360)  # angles eastward from North, North facing down
            rads = theta * math.pi / 180.0
            cx1 = math.cos(rads) * (self.myPhotoRadius - tickLength) + self.viewCenter[0]
            cy1 = math.sin(rads) * (self.myPhotoRadius - tickLength) + self.viewCenter[1]
            cx2 = math.cos(rads) * self.myPhotoRadius + self.viewCenter[0]
            cy2 = math.sin(rads) * self.myPhotoRadius + self.viewCenter[1]
            lx1 = (math.cos(rads) * (self.myPhotoRadius - tickLength*4)) + self.viewCenter[0] - self.fontMetrics.width(str(angle))/2
            ly1 = (math.sin(rads) * (self.myPhotoRadius - tickLength*4)) + self.viewCenter[1] - self.fontMetrics.height()/2
            self.compassTicks.append([cx1, cy1, cx2, cy2, lx1, ly1, angle])  # x1, y1, x2, y2, x1lbl, y1lbl, angle

        # compute lens (ideal and actual) radii for drawn latitude ellipses along zenith
        self.lensIdealRadii.clear()
        self.lensRealRadii.clear()
        for alt in common.SamplingPatternAlts:
            # ideal lens
            u, v = utility_angles.SkyCoord2FisheyeUV(90, alt, lenswarp=False)
            x = (self.viewCenter[0] - self.myPhotoRadius) + (u * myPhotoDiameter)
            r = x - self.viewCenter[0]
            self.lensIdealRadii.append((r, alt))  # (radius, altitude)
            # warped lens
            u, v = utility_angles.SkyCoord2FisheyeUV(90, alt)
            x = (self.viewCenter[0] - self.myPhotoRadius) + (u * myPhotoDiameter)
            r = x - self.viewCenter[0]
            self.lensRealRadii.append((r, alt))   # (radius, altitude)

        # compute sun path screen points
        self.pathSun = QPainterPath()
        if len(self.sunPathPoints) > 0:
            azi, alt, dt = self.sunPathPoints[0]
            u, v = utility_angles.SkyCoord2FisheyeUV(azi, alt)
            x = (u * myPhotoDiameter) + (self.viewCenter[0] - self.myPhotoRadius)
            y = (v * myPhotoDiameter) + (self.viewCenter[1] - self.myPhotoRadius)
            self.pathSun.moveTo(x, y)
            for i in range(1, len(self.sunPathPoints)):
                azi, alt, dt = self.sunPathPoints[i]
                u, v = utility_angles.SkyCoord2FisheyeUV(azi, alt)
                x = (u * myPhotoDiameter) + (self.viewCenter[0] - self.myPhotoRadius)
                y = (v * myPhotoDiameter) + (self.viewCenter[1] - self.myPhotoRadius)
                self.pathSun.lineTo(x, y)

        # compute sun position screen point
        u, v = utility_angles.SkyCoord2FisheyeUV(self.sunPosition[0], self.sunPosition[1])
        x = (u * myPhotoDiameter) + (self.viewCenter[0] - self.myPhotoRadius)
        y = (v * myPhotoDiameter) + (self.viewCenter[1] - self.myPhotoRadius)
        self.sunPositionVisible = (x, y)

        # compute new mask
        self.mask = QPixmap(self.width(), self.height()).toImage()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter()
        painter.begin(self)

        # background
        brushBG = QBrush(Qt.black, Qt.SolidPattern)
        if not common.AppSettings["ShowMask"]:
            brushBG.setColor(Qt.darkGray)
            brushBG.setStyle(Qt.Dense1Pattern)
            painter.setBackground(Qt.gray)
        else:
            brushBG.setColor(Qt.black)
            brushBG.setStyle(Qt.SolidPattern)
            painter.setBackground(Qt.black)
        painter.setBackgroundMode(Qt.OpaqueMode)
        painter.setBrush(brushBG)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width(), self.height())

        # draw photo
        if not self.myPhoto.isNull():
            # rotate and draw photo as specified by user
            transform = QTransform()
            transform.translate(self.myPhotoDestRect.center().x(), self.myPhotoDestRect.center().y())
            transform.rotate(-self.myPhotoRotation)
            transform.translate(-self.myPhotoDestRect.center().x(), -self.myPhotoDestRect.center().y())
            painter.setTransform(transform)
            painter.drawImage(self.myPhotoDestRect, self.myPhoto, self.myPhotoSrcRect) # draw it
            painter.resetTransform()

            # useful local vars
            centerPoint = QPoint(self.viewCenter[0], self.viewCenter[1])
            diameter = self.myPhotoRadius * 2
            destRect = QRect(0, 0, self.myPhotoDestRect.width(), self.myPhotoDestRect.height())
            fontWidth = self.fontMetrics.width("X")

            # mask
            if common.AppSettings["ShowMask"]:
                maskPainter = QPainter()
                maskPainter.begin(self.mask)
                maskPainter.setBrush(QBrush(Qt.magenta, Qt.SolidPattern))
                maskPainter.drawEllipse(self.viewCenter[0] - self.myPhotoRadius, self.viewCenter[1] - self.myPhotoRadius, diameter, diameter)
                maskPainter.end()
                painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                painter.drawImage(0, 0, self.mask)
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # HUD
            if common.AppSettings["ShowHUD"]:
                painter.setBackgroundMode(Qt.TransparentMode)
                #painter.setBackground(Qt.black)
                painter.setBrush(Qt.NoBrush)
                painter.setFont(self.fontScaled)

                # draw UV grid
                if common.AppSettings["ShowUVGrid"]:
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
                    painter.drawLine(self.viewCenter[0] - self.myPhotoRadius, self.viewCenter[1],
                                     self.viewCenter[0] + self.myPhotoRadius, self.viewCenter[1])
                    painter.drawLine(self.viewCenter[0], self.viewCenter[1] - self.myPhotoRadius,
                                     self.viewCenter[0], self.viewCenter[1] + self.myPhotoRadius)
                    # labels
                    destRect.setCoords(self.viewCenter[0] - self.myPhotoRadius + 4,
                                       self.viewCenter[1] - self.myPhotoRadius + 4,
                                       self.width(), self.height())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "0")
                    destRect.setCoords(self.viewCenter[0] + self.myPhotoRadius - (fontWidth+4),
                                       self.viewCenter[1] - self.myPhotoRadius + 4,
                                       self.width(), self.height())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    destRect.setCoords(self.viewCenter[0] - self.myPhotoRadius + 3,
                                       self.viewCenter[1] + self.myPhotoRadius - (self.fontMetrics.height()+3),
                                       self.width(), self.height())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    destRect.setCoords(self.viewCenter[0] + self.myPhotoRadius - (fontWidth+3),
                                       self.viewCenter[1] + self.myPhotoRadius - (self.fontMetrics.height()+3),
                                       self.width(), self.height())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")

                # draw lens warp
                if common.AppSettings["ShowLensWarp"]:
                    # ideal lens longitudes along azimuth
                    painter.setPen(self.penText)
                    for i in range(0, int(len(self.compassTicks)/2), 3):
                        p1 = QPoint(self.compassTicks[i][2], self.compassTicks[i][3])
                        p2 = QPoint(self.compassTicks[i+18][2], self.compassTicks[i+18][3])  # tick opposite 180 degrees
                        painter.drawLine(p1, p2)
                    # ideal lens latitudes along zenith
                    for r, alt in self.lensIdealRadii:
                        painter.drawEllipse(centerPoint, r, r)
                    # actual/warped lens latitudes along zenith
                    painter.setPen(self.penLens)
                    for r, alt in self.lensRealRadii:
                        painter.drawEllipse(centerPoint, r, r)
                        destRect.setCoords(self.viewCenter[0] + r + 3, self.viewCenter[1] - (self.fontMetrics.height() + 3), self.width(), self.height())
                        painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "{0:d}°".format(int(alt)))

                # draw compass
                if common.AppSettings["ShowCompass"]:
                    # compass ticks text shadows
                    if common.AppSettings["ShowShadows"]:
                        painter.setPen(self.penShadowText)
                        for tick in self.compassTicks:
                            destRect.setCoords(tick[4] + 1, tick[5] + 1, self.width(), self.height())
                            painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(tick[6])+"°")
                    # compass ticks text
                    painter.setPen(self.penText)
                    for tick in self.compassTicks:
                        painter.drawLine(tick[0], tick[1], tick[2], tick[3])
                        destRect.setCoords(tick[4], tick[5], self.width(), self.height())
                        painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(tick[6])+"°")
                    # photo radius
                    #painter.drawEllipse(self.viewCenter[0] - self.myPhotoRadius, self.viewCenter[1] - self.myPhotoRadius, diameter, diameter)
                    painter.drawEllipse(centerPoint, self.myPhotoRadius, self.myPhotoRadius)
                    # cardinal directions
                    destRect.setCoords(self.viewCenter[0] - self.myPhotoRadius - (fontWidth+4), self.viewCenter[1] - self.fontMetrics.height()/2, self.width(), self.height())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "W")
                    destRect.setCoords(self.viewCenter[0] + self.myPhotoRadius + 4, self.viewCenter[1] - self.fontMetrics.height()/2, self.width(), self.height())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "E")
                    destRect.setCoords(self.viewCenter[0] - fontWidth/2, self.viewCenter[1] - self.myPhotoRadius - (self.fontMetrics.height()+3), self.width(), self.height())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "S")
                    destRect.setCoords(self.viewCenter[0] - fontWidth/2, self.viewCenter[1] + self.myPhotoRadius + 3, self.width(), self.height())
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "N")

                # draw sampling pattern
                if common.AppSettings["ShowSamples"]:
                    painter.setPen(self.penText)
                    for i, points in enumerate(self.sampleAreaVisible):
                        painter.drawLine(QLine(points[0], points[1]))
                        painter.drawLine(QLine(points[1], points[2]))
                        painter.drawLine(QLine(points[2], points[3]))
                        painter.drawLine(QLine(points[3], points[0]))
                    for i in range(0, len(self.samplePoints)):
                        p = self.samplePoints[i]
                        painter.drawEllipse(QPoint(p[0],p[1]), ViewFisheye.SampleRadius, ViewFisheye.SampleRadius)
                        painter.drawText(p[0] - ViewFisheye.SampleRadius, p[1], str(i))

                # draw sun path
                if common.AppSettings["ShowSunPath"]:
                    sunradius = self.myPhotoRadius * 0.1
                    # shadows
                    painter.setPen(self.penShadowSun)
                    if common.AppSettings["ShowShadows"]:
                        painter.drawEllipse(self.sunPositionVisible[0] - sunradius / 2 + 1,
                                            self.sunPositionVisible[1] - sunradius / 2 + 1, sunradius,
                                            sunradius)
                        self.pathSun.translate(1.0, 1.0)
                        painter.drawPath(self.pathSun)
                        self.pathSun.translate(-1.0, -1.0)
                        for i in range(0, self.pathSun.elementCount()):
                            e = self.pathSun.elementAt(i)
                            destRect.setCoords(e.x, e.y + self.fontMetrics.height()/2 + 1, self.width(), self.height())
                            painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.sunPathPoints[i][2].hour))
                    # sun, path, hours
                    painter.setPen(self.penSun)
                    painter.drawEllipse(self.sunPositionVisible[0] - sunradius / 2,
                                        self.sunPositionVisible[1] - sunradius / 2, sunradius, sunradius)
                    painter.drawPath(self.pathSun)
                    for i in range(0, self.pathSun.elementCount()):
                        e = self.pathSun.elementAt(i)
                        destRect.setCoords(e.x, e.y + self.fontMetrics.height() / 2, self.width(), self.height())
                        painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.sunPathPoints[i][2].hour))

                # draw selected samples (ALWAYS)
                r = QRect()
                # shadows
                if common.AppSettings["ShowShadows"]:
                    painter.setPen(self.penShadowSelected)
                    for i in self.samplesSelected:
                        x, y = self.samplePoints[i]
                        painter.drawEllipse(QPoint(x+1, y+1), ViewFisheye.SampleRadius, ViewFisheye.SampleRadius)
                # samples
                for i in self.samplesSelected:
                    painter.setPen(self.penSelected[i])
                    x, y = self.samplePoints[i]
                    painter.drawEllipse(QPoint(x, y), ViewFisheye.SampleRadius, ViewFisheye.SampleRadius)

                # draw user's selection bounds
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
                destRect.setCoords(10, 25, self.width(), self.height())
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, self.skyCover.name + "/" + common.SkyCoverDesc[self.skyCover])
                # draw photo rotation
                if self.myPhotoRotation != 0:
                    destRect.setCoords(10, self.height()-25, self.width(), self.height())
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
                    coordsUV = ((coordsUC[0] + 1) / 2, (coordsUC[1] + 1) / 2)
                    coordsTP = utility_angles.FisheyeUV2SkyCoord(coordsUV[0], coordsUV[1])
                    distance = math.sqrt((coordsUC[0] * coordsUC[0]) + (coordsUC[1] * coordsUC[1]))

                # pixels colors
                pixreg = common.AppSettings["PixelRegion"]
                colorsRegion = np.zeros((pixreg, pixreg, 4))
                colorFinal = colorsRegion[0,0]  # RGBA of pixel under mouse of photo on disk
                # colorFinal = self.myPhoto.pixelColor(coordsXY[0], coordsXY[1])
                if distance <= 1.0:
                    halfdim = int(pixreg / 2)
                    rstart = coordsXY[1] - halfdim
                    rstop = coordsXY[1]+halfdim+1
                    cstart = coordsXY[0]-halfdim
                    cstop = coordsXY[0]+halfdim+1
                    if (rstart >= 0 and rstop<=self.myPhotoPixels.shape[0] and
                        cstart >= 0 and cstop<=self.myPhotoPixels.shape[1]):
                        colorsRegion = self.myPhotoPixels[rstart:rstop, cstart:cstop]
                        colorFinal = colorsRegion[halfdim, halfdim]
                        # pixel color weighting
                        if pixreg > 1:
                            colorFinal = utility_data.collectPixels([coordsXY], [pixreg], pixels=self.myPhotoPixels, weighting=common.PixelWeighting(common.AppSettings["PixelWeighting"]))[0]

                # text strings for information we want to display on HUD
                textxy = "-1, -1 xy"
                textXY = "-1, -1 xy"
                textUC = "-1, -1 uc"
                textUV = "-1, -1 uv"
                textTP = "-1, -1 θφ"
                textPX = "0 0 0 px"
                if distance <= 1.0:
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
                pixreg = common.AppSettings["PixelRegion"]
                if distance <= 1.0:
                    painter.setPen(Qt.NoPen)
                    # pixel region
                    pixdim = ViewFisheye.SelectedPixelBox / pixreg
                    for row in range(0, pixreg):
                        for col in range(0, pixreg):
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
