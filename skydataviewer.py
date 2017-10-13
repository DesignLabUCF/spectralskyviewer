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
# @since: 10/06/2017
# @summary: SkyDataViewer main program file
# ====================================================================
import sys
import os
import random
import json
from PyQt5.QtCore import QCoreApplication, Qt, QDir
from PyQt5.QtGui import QIcon, QFont, QPainter
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import qApp
import utility
from viewfisheye import ViewFisheye


class SkyDataViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # available settings, set to defaults
        self.Settings = {
            "Filename": "settings.json",
            "WindowWidth": 1024,
            "WindowHeight": 768,
            "DataDirectory": "",
            "HorizSplitLeft": -1,
            "HorizSplitRight": -1,
            "VertSplitTop": -1,
            "VertSplitBottom": -1,
        }

        # load settings
        if os.path.exists(self.Settings["Filename"]):
            with open(self.Settings["Filename"], 'r') as file:
                self.Settings = json.load(file)

        # init
        QToolTip.setFont(QFont('SansSerif', 8))

        # init GUI
        # uic.loadUi('design.ui', self)
        self.initWidgets()
        self.initMenu()

        # startup
        if self.Settings["Filename"] is not None and len(self.Settings["Filename"]) > 0:
            self.loadData()

    def initMenu(self):
        # menu actions
        actExit = QAction(QIcon(), 'E&xit', self)
        actExit.setShortcut('Ctrl+Q')
        actExit.setStatusTip('Exit application')
        actExit.triggered.connect(self.close)

        # menubar
        menubar = self.menuBar()
        menuFile = menubar.addMenu('&File')
        menuFile.addAction(actExit)

        # # toolbar
        # toolbar = self.addToolBar('Toolbar')
        # toolbar.addAction(actExit)

    def initWidgets(self):
        # data directory panel
        self.btnDataDir = QPushButton('Data', self)
        self.btnDataDir.setIcon(self.btnDataDir.style().standardIcon(QStyle.SP_DirIcon))
        self.btnDataDir.setToolTip('Set data directory...')
        self.btnDataDir.clicked.connect(self.browseForFolder)
        self.lblDataDir = QLabel()
        boxDataDir = QHBoxLayout()
        boxDataDir.setSpacing(10)
        boxDataDir.setContentsMargins(0, 0, 0, 0)
        boxDataDir.addWidget(self.btnDataDir)
        boxDataDir.addWidget(self.lblDataDir, 1)
        pnlDataDir = QWidget()
        pnlDataDir.setLayout(boxDataDir)

        # date time panel
        self.timeSlider = QSlider(Qt.Horizontal, self)
        self.timeSlider.setFocusPolicy(Qt.NoFocus)
        self.timeSlider.setTickPosition(QSlider.TicksAbove)
        # timeSlider.setRange(1, 4)
        # timeSlider.setSingleStep(1)
        boxDateTime = QHBoxLayout()
        boxDateTime.setSpacing(10)
        boxDateTime.setContentsMargins(0, 0, 0, 0)
        boxDateTime.addWidget(QComboBox())
        boxDateTime.addWidget(self.timeSlider, 1)
        pnlDatetime = QWidget()
        pnlDatetime.setLayout(boxDateTime)

        # toolbox
        self.btn2DRender = QPushButton(self)
        self.btn2DRender.setIcon(self.btn2DRender.style().standardIcon(QStyle.SP_DesktopIcon))
        self.btn2DRender.setToolTip('Original')
        self.btn3DRender = QPushButton(self)
        self.btn3DRender.setIcon(self.btn3DRender.style().standardIcon(QStyle.SP_DesktopIcon))
        self.btn3DRender.setToolTip('3D Render')
        self.btnOrthoRender = QPushButton(self)
        self.btnOrthoRender.setIcon(self.btnOrthoRender.style().standardIcon(QStyle.SP_DesktopIcon))
        self.btnOrthoRender.setToolTip('Orthographic')
        boxToolbox = QVBoxLayout()
        boxToolbox.setSpacing(0)
        boxToolbox.setContentsMargins(0, 0, 0, 0)
        boxToolbox.setAlignment(Qt.AlignTop)
        boxToolbox.addWidget(self.btn2DRender)
        boxToolbox.addWidget(self.btn3DRender)
        boxToolbox.addWidget(self.btnOrthoRender)
        pnlToolbox = QWidget()
        pnlToolbox.setLayout(boxToolbox)

        # render pane
        self.wgtRender = ViewFisheye()
        #self.wgtRender.setPhoto("sky.jpg")

        # info view
        self.wgtInfo = QTextEdit()

        # horizontal splitter
        self.splitHoriz = QSplitter(Qt.Horizontal)
        self.splitHoriz.addWidget(self.wgtRender)
        self.splitHoriz.addWidget(self.wgtInfo)
        self.splitHoriz.setSizes([self.Settings["HorizSplitLeft"] if self.Settings["HorizSplitLeft"] >= 0 else self.Settings["WindowWidth"] * 0.75,
                                  self.Settings["HorizSplitRight"] if self.Settings["HorizSplitRight"] >= 0 else self.Settings["WindowWidth"] * 0.25])

        # upper panel
        boxUpperHalf = QHBoxLayout()
        boxUpperHalf.setSpacing(10)
        boxUpperHalf.setContentsMargins(0, 0, 0, 0)
        boxUpperHalf.addWidget(pnlToolbox)
        boxUpperHalf.addWidget(self.splitHoriz)
        pnlUpperHalf = QWidget()
        pnlUpperHalf.setLayout(boxUpperHalf)

        # energy graph
        self.wgtGraph = QTextEdit()

        # vertical splitter
        self.splitVert = QSplitter(Qt.Vertical)
        self.splitVert.addWidget(pnlUpperHalf)
        self.splitVert.addWidget(self.wgtGraph)
        self.splitVert.setSizes([self.Settings["VertSplitTop"] if self.Settings["VertSplitTop"] >= 0 else self.Settings["WindowHeight"] * 0.75,
                                 self.Settings["VertSplitBottom"] if self.Settings["VertSplitBottom"] >= 0 else self.Settings["WindowHeight"] * 0.25])

        # attach high level panels and vertical splitter to layout of window
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(10, 10, 10, 0)
        grid.addWidget(pnlDataDir, 0, 0)
        grid.addWidget(pnlDatetime, 1, 0)
        grid.addWidget(self.splitVert, 2, 0)
        #     grid.addWidget(edtReview, 3, 1, 5, 1)
        pnlMain = QWidget()
        pnlMain.setLayout(grid)
        self.setCentralWidget(pnlMain)

        # window
        # self.setGeometry(0, 0, 1024, 768)
        self.resize(self.Settings["WindowWidth"], self.Settings["WindowHeight"])
        self.setWindowTitle("Sky Data Viewer")
        self.setWindowIcon(QIcon('icon.png'))
        self.statusBar().showMessage('Ready')

    def drawRenderFrame(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setPen(Qt.red)
        size = self.size()
        for i in range(1000):
            x = random.randint(1, size.width() - 1)
            y = random.randint(1, size.height() - 1)
            painter.drawPoint(x, y)
        painter.end()

    def center(self):
        frame = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(centerPoint)
        self.move(frame.topLeft())

    def browseForFolder(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Data Directory', self.Settings["DataDirectory"])
        directory = QDir.toNativeSeparators(directory)
        if directory is not None and len(directory) > 0 and directory != self.Settings["DataDirectory"]:
            self.Settings["DataDirectory"] = directory
            self.loadData()

    def loadData(self):
        if self.Settings["DataDirectory"] is None or len(self.Settings["DataDirectory"]) <= 0:
            return

        self.lblDataDir.setText(self.Settings["DataDirectory"])
        captureDateDirs = utility.findFiles(self.Settings["DataDirectory"], type=2)
        captureDateDirs[:] = [dir for dir in captureDateDirs if utility.verifyDateTime(os.path.basename(dir), "%Y-%m-%d")]

        for dir in captureDateDirs:
            print(dir)

    def closeEvent(self, event):
        # answer = QMessageBox.question(self, 'Quit Confirmation', 'Are you sure?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No )
        # if answer == QMessageBox.Yes:
        #     event.accept()
        # else:
        #     event.ignore()

        # btn.clicked.connect(QApplication.instance().quit)
        event.accept()

        # cache settings to file
        self.Settings["WindowWidth"] = self.width()
        self.Settings["WindowHeight"] = self.height()
        left, right = self.splitHoriz.sizes()
        self.Settings["HorizSplitLeft"] = left
        self.Settings["HorizSplitRight"] = right
        top, bottom = self.splitVert.sizes()
        self.Settings["VertSplitTop"] = top
        self.Settings["VertSplitBottom"] = bottom
        with open(self.Settings["Filename"], 'w') as file:
            json.dump(self.Settings, file, indent=4)

    def contextMenuEvent(self, event):
        menuCtx = QMenu(self)
        actExit = QAction(QIcon(), '&Exit', self)
        menuCtx.addAction(actExit)
        action = menuCtx.exec_(self.mapToGlobal(event.pos()))
        if action == actExit:
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = SkyDataViewer()
    w.center()
    w.show()

    status = app.exec_()
    sys.exit(status)
