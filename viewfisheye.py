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
                    painter.drawLine(cx - radius, cy, cx + radius, cy)
                    painter.drawLine(cx, cy - radius, cx, cy + radius)
                    painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
                    destRect.setCoords(cx - radius + 5, cy + 5, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "0")
                    destRect.setCoords(cx + radius - 15, cy + 5, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")
                    destRect.setCoords(cx + 5, cy - radius + 5, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "0")
                    destRect.setCoords(cx + 5, cy + radius - 20, self.width()-1, self.height()-1)
                    painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, "1")

                # coordinates we are interested in
                #self.coordsMouse   # x,y of this widget
                coordsXY = [-1, -1] # x,y over photo as scaled on this widget
                coordsUV = [-1, -1] # u,v lookup in actual photo on disk
                coordsUC = [-1, -1] # unit circle coords from center of photo to edge of fisheye radius
                coordsFC = [-1, -1] # "fractional" coords of fisheye photo w/ 0,0 top left and 1,1 bottom right
                coordsTP = [-1, -1] # theta,phi polar coordinates

                # compute all relevant coordinates only when mouse is over fisheye portion of photo
                if (self.coordsMouse[0] >= destRectPhoto.x() and
                    self.coordsMouse[1] >= destRectPhoto.y() and
                    self.coordsMouse[0] < destRectPhoto.x() + destRectPhoto.width() and
                    self.coordsMouse[1] < destRectPhoto.y() + destRectPhoto.height()):
                    coordsXY[0] = self.coordsMouse[0] - destRectPhoto.x()
                    coordsXY[1] = self.coordsMouse[1] - destRectPhoto.y()
                    coordsUC[0] = (coordsXY[0] - destRectPhoto.width()/2) / radius
                    coordsUC[1] = (coordsXY[1] - destRectPhoto.height()/2) / radius
                    coordsUV[0] = int(coordsXY[0] / destRectPhoto.width() * self.myPhoto.width())
                    coordsUV[1] = int(coordsXY[1] / destRectPhoto.height() * self.myPhoto.height())
                    coordsFC[0] = (coordsUC[0] + 1) / 2
                    coordsFC[1] = (coordsUC[1] + 1) / 2
                    coordsTP = angle_utilities.GetAngleFromUV(coordsFC[0], coordsFC[1])

                # draw x,y coords
                destRect.setCoords(10, 10, self.width()-10, self.height()- 124)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight,
                                 str(coordsXY[0]) + ", " + str(coordsXY[1]) + " xy")

                # draw u,v coords
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 114)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight,
                                 str(coordsUV[0]).format("{:0>4d}") + ", " + str(coordsUV[1]).format("{:0>4d}") + " uv")

                # draw unit circle coords
                text = "-1, -1 uc"
                if (coordsXY[0] >= 0 and coordsXY[1] >= 0):
                    text = "{:.2f}".format(coordsUC[0]) + ", " + "{:.2f}".format(coordsUC[1]) + " uc"
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 104)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, text)

                # draw fractional coords
                text = "-1, -1 fr"
                if (coordsXY[0] >= 0 and coordsXY[1] >= 0):
                    text = "{:.2f}".format(coordsFC[0]) + ", " + "{:.2f}".format(coordsFC[1]) + " fr"
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 94)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, text)

                # draw t,p coords
                text = "-1, -1 θφ"
                if (coordsXY[0] >= 0 and coordsXY[1] >= 0):
                    text = "{:.2f}".format(coordsTP[0]) + ", " + "{:.2f}".format(coordsTP[1]) + " θφ"
                destRect.setCoords(10, 10, self.width() - 10, self.height() - 84)
                painter.drawText(destRect, Qt.AlignBottom | Qt.AlignRight, text)

                # draw cursor visual indicators (outlines)
                circleX = self.width() - 10 - 64 - 10 - 64
                circleY = self.height() - 10 - 64
                pixelX = self.width() - 64 - 10
                pixelY = self.height() - 64 - 10
                painter.drawEllipse(circleX, circleY, 64, 64)
                painter.drawRect(pixelX, pixelY, 64, 64)
                # only fill if cursor is within fisheye radius
                distance = math.sqrt((coordsUC[0] * coordsUC[0]) + (coordsUC[1] * coordsUC[1]))
                if (distance <= 1.0):
                    color = self.myPhoto.pixelColor(coordsUV[0], coordsUV[1])
                    painter.setBackgroundMode(Qt.OpaqueMode)
                    painter.setBackground(color)
                    painter.setBrush(QBrush(color, Qt.SolidPattern))
                    cx = circleX + (coordsFC[0] * 64)
                    cy = circleY + (coordsFC[1] * 64)
                    painter.drawEllipse(cx - 5, cy - 5, 10, 10)
                    painter.drawRect(pixelX, pixelY, 64, 64)

                # raw notice
                if (not self.rawAvailable):
                    painter.drawPixmap(self.width()-16-16, 16, self.iconWarning)

        # end draw
        painter.end()
