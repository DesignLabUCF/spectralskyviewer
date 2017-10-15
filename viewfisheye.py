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
# @summary: A widget for displaying the fisheye view of the HDR data
# ====================================================================
import os
from datetime import datetime
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QImage, QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QStyle
import utility


class ViewFisheye(QWidget):
    def __init__(self):
        super().__init__()
        self.myPhoto = QImage()
        self.myPhotoPath = ""
        self.myPhotoTimestamp = datetime.now()
        self.srcRect = QRect()
        self.hudEnabled = True
        self.rawAvailable = False
        # preloaded graphics
        self.pen = QPen(Qt.black, 1, Qt.SolidLine)
        self.brush = QBrush(Qt.darkGray, Qt.Dense1Pattern)
        self.font = QFont('Courier New', 8)
        self.iconWarning = self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(16)

    def setPhoto(self, path):
        if os.path.exists(path):
            self.myPhotoPath = path
            self.myPhotoTimestamp = utility.imageEXIFDateTime(path)
            self.myPhoto = QImage(path)
            self.srcRect = QRect(0, 0, self.myPhoto.width(), self.myPhoto.height())
        else:
            self.clear()

    def clear(self):
        self.myPhoto = QImage()
        self.myPhotoPath = ""
        self.myPhotoTimestamp = datetime.now()
        self.srcRect = QRect()
        self.rawAvailable = False

    def showHUD(self, b):
        self.hudEnabled = b

    def setRAWAvailable(self, b):
        self.rawAvailable = b

    def paintEvent(self, event):
        super().paintEvent(event)

        # start draw
        painter = QPainter()
        painter.begin(self)

        # background
        painter.setBackgroundMode(Qt.OpaqueMode)
        painter.setBackground(Qt.gray)
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawRect(0, 0, self.width()-1, self.height()-1)

        # draw photo
        if not self.myPhoto.isNull():
            destRect = QRect()

            # use the appropriate scaling factor that requires the most scaling ( - 2 to fit in border )
            wRatio = self.width()/self.myPhoto.width()
            hRatio = self.height()/self.myPhoto.height()
            if wRatio <= hRatio:
                destRect.setWidth(self.srcRect.width() * wRatio - 2)
                destRect.setHeight(self.srcRect.height() * wRatio - 2)
            else:
                destRect.setWidth(self.srcRect.width() * hRatio - 2)
                destRect.setHeight(self.srcRect.height() * hRatio - 2)

            # center and draw it
            destRect.moveTo(self.width()/2-destRect.width()/2, self.height()/2-destRect.height()/2)
            painter.drawImage(destRect, self.myPhoto, self.srcRect)

            # HUD
            if self.hudEnabled:
                painter.setPen(Qt.white)
                painter.setBackgroundMode(Qt.TransparentMode)
                painter.setBrush(Qt.NoBrush)
                painter.setFont(self.font)
                destRect.setCoords(10, 10, self.width() - 10, 20)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, os.path.basename(self.myPhotoPath))
                destRect.moveTo(10, 25)
                painter.drawText(destRect, Qt.AlignTop | Qt.AlignLeft, str(self.myPhotoTimestamp.time()))

                if not self.rawAvailable:
                    painter.drawPixmap(self.width()-10-16, 10, self.iconWarning)

        # end draw
        painter.end()
