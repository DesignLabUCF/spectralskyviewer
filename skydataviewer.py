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
import json
from PyQt5.QtCore import QCoreApplication, Qt, QDir
from PyQt5.QtGui import QIcon, QFont, QPainter
from PyQt5.QtWidgets import *
#from PyQt5.QtWidgets import qApp
import utility
from viewfisheye import ViewFisheye


class SkyDataViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # available settings, set to defaults
        self.Settings = {
            "Filename": "settings.json",
            "DataDirectory": "",
            "WindowWidth": 1024,
            "WindowHeight": 768,
            "HorizSplitLeft": -1,
            "HorizSplitRight": -1,
            "VertSplitTop": -1,
            "VertSplitBottom": -1,
            "ShowHUD": True,
            "ShowStatusBar": True,
        }

        # load and validate settings
        if os.path.exists(self.Settings["Filename"]):
            with open(self.Settings["Filename"], 'r') as file:
                self.Settings = json.load(file)
        if len(self.Settings["DataDirectory"]) > 0 and not os.path.exists(self.Settings["DataDirectory"]):
            self.Settings["DataDirectory"] = ""

        # init
        self.hdrCaptures = [] # some number of these per day
        self.asdMeasures = [] # 81 of these per capture time
        QToolTip.setFont(QFont('SansSerif', 8))

        # init GUI
        # uic.loadUi('design.ui', self)
        self.initMenu()
        self.initWidgets()

        # startup
        self.loadData()

    def initMenu(self):
        # file menu actions
        actExit = QAction(QIcon(), 'E&xit', self)
        actExit.setShortcut('Ctrl+Q')
        actExit.setStatusTip('Exit the application')
        actExit.triggered.connect(self.close)
        actLoad = QAction(QIcon(), '&Load', self)
        actLoad.setShortcut('Ctrl+L')
        actLoad.setStatusTip('Load the data directory...')
        actLoad.triggered.connect(self.browseForData)

        # view menu actions
        self.actHUD = QAction(QIcon(), 'Show &HUD', self)
        self.actHUD.setCheckable(True)
        self.actHUD.setChecked(self.Settings["ShowHUD"])
        self.actHUD.setStatusTip('Toggle display of HUD')
        self.actHUD.triggered.connect(self.toggleHUD)
        self.actStatusBar = QAction(QIcon(), 'Show Status &Bar', self)
        self.actStatusBar.setCheckable(True)
        self.actStatusBar.setChecked(self.Settings["ShowStatusBar"])
        self.actStatusBar.setStatusTip('Toggle display of status bar')
        self.actStatusBar.triggered.connect(self.toggleStatusBar)

        # help menu actions
        actAbout = QAction(QIcon(), '&About', self)
        actAbout.setStatusTip('Information about this application')
        #actAbout.triggered.connect(self.close)

        # menubar
        menubar = self.menuBar()
        menuFile = menubar.addMenu('&File')
        menuFile.addAction(actLoad)
        menuFile.addSeparator()
        menuFile.addAction(actExit)
        menuView = menubar.addMenu('&View')
        menuView.addAction(self.actHUD)
        menuView.addAction(self.actStatusBar)
        menuHelp = menubar.addMenu('&Help')
        menuHelp.addAction(actAbout)

        # # toolbar
        # toolbar = self.addToolBar('Toolbar')
        # toolbar.addAction(actExit)

    def initWidgets(self):
        # data panel
        self.btnDataDir = QPushButton('Data', self)
        self.btnDataDir.setIcon(self.btnDataDir.style().standardIcon(QStyle.SP_DirIcon))
        self.btnDataDir.setToolTip('Load data directory...')
        self.btnDataDir.clicked.connect(self.browseForData)
        self.lblData = QLabel()
        self.lblData.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.cbxDate = QComboBox()
        self.cbxDate.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cbxDate.currentIndexChanged.connect(self.dateSelected)
        self.lblTime = QLabel("00:00:00")
        self.lblTime.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.sldTime = QSlider(Qt.Horizontal, self)
        self.sldTime.setTickPosition(QSlider.TicksAbove)
        self.sldTime.setRange(0, 0)
        self.sldTime.setTickInterval(1)
        self.sldTime.setPageStep(1)
        self.sldTime.valueChanged.connect(self.timeSelected)
        gridData = QGridLayout()
        #gridData.setVerticalSpacing(5)
        #gridData.setHorizontalSpacing(5)
        gridData.setSpacing(5)
        gridData.setContentsMargins(0,0,0,0)
        gridData.addWidget(self.btnDataDir, 0, 0)
        gridData.addWidget(self.lblData, 0, 1, 1, 2)
        gridData.addWidget(self.cbxDate, 1, 0)
        gridData.addWidget(self.lblTime, 1, 1)
        gridData.addWidget(self.sldTime, 1, 2)
        pnlData = QWidget()
        pnlData.setLayout(gridData)

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
        self.wgtRender.showHUD(self.actHUD.isChecked())

        # info view
        self.lblHDRFile = QLabel()
        self.lblHDRFile.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        boxInfo = QVBoxLayout()
        boxInfo.setSpacing(0)
        boxInfo.setContentsMargins(0, 0, 0, 0)
        boxInfo.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        boxInfo.addWidget(self.lblHDRFile)
        pnlInfo = QWidget()
        pnlInfo.setLayout(boxInfo)

        # horizontal splitter
        self.splitHoriz = QSplitter(Qt.Horizontal)
        self.splitHoriz.addWidget(self.wgtRender)
        self.splitHoriz.addWidget(pnlInfo)
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
        self.wgtGraph.setFocusPolicy(Qt.ClickFocus)

        # vertical splitter
        self.splitVert = QSplitter(Qt.Vertical)
        self.splitVert.addWidget(pnlUpperHalf)
        self.splitVert.addWidget(self.wgtGraph)
        self.splitVert.setSizes([self.Settings["VertSplitTop"] if self.Settings["VertSplitTop"] >= 0 else self.Settings["WindowHeight"] * 0.75,
                                 self.Settings["VertSplitBottom"] if self.Settings["VertSplitBottom"] >= 0 else self.Settings["WindowHeight"] * 0.25])

        # attach high level panels and vertical splitter to layout of window
        gridMain = QGridLayout()
        gridMain.setSpacing(5)
        gridMain.setContentsMargins(10, 10, 10, 10)
        gridMain.addWidget(pnlData, 0, 0)
        gridMain.addWidget(self.splitVert, 1, 0)
        pnlMain = QWidget()
        pnlMain.setLayout(gridMain)
        self.setCentralWidget(pnlMain)

        # window
        # self.setGeometry(0, 0, 1024, 768)
        self.resize(self.Settings["WindowWidth"], self.Settings["WindowHeight"])
        self.setWindowTitle("Sky Data Viewer")
        self.setWindowIcon(QIcon('res/icon.png'))
        self.statusBar().showMessage('Ready')

    def resetAllUI(self):
        self.lblData.clear()
        self.lblTime.setText("00:00:00")
        self.cbxDate.clear()
        self.sldTime.setRange(0, 0)
        self.wgtRender.clear()
        self.wgtRender.repaint()

    def resetDayUI(self):
        self.lblData.setText(self.Settings["DataDirectory"])
        self.lblTime.setText("00:00:00")
        self.sldTime.setRange(0, 0)
        self.wgtRender.clear()
        self.wgtRender.repaint()

    def loadData(self):
        if len(self.Settings["DataDirectory"]) <= 0 or not os.path.exists(self.Settings["DataDirectory"]):
            return

        # GUI
        self.resetAllUI()
        self.lblData.setText(self.Settings["DataDirectory"])

        # find capture dates and times
        captureDateDirs = utility.findFiles(self.Settings["DataDirectory"], mode=2)
        captureDateDirs[:] = [dir for dir in captureDateDirs if utility.verifyDateTime(os.path.basename(dir), "%Y-%m-%d")]
        captureDates = [os.path.basename(dir) for dir in captureDateDirs]
        if len(captureDates) > 0:
            self.cbxDate.addItems(captureDates)
            #self.cbxDate.setCurrentIndex(-1) # trigger manual date selection
            #self.cbxDate.setCurrentIndex(0)  # trigger manual date selection

    def browseForData(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Data Directory', self.Settings["DataDirectory"])
        directory = QDir.toNativeSeparators(directory)
        if directory is not None and len(directory) > 0 and directory != self.Settings["DataDirectory"]:
            self.Settings["DataDirectory"] = directory
            self.loadData()

    def dateSelected(self, index):
        if index < 0 or index >= self.cbxDate.count():
            return

        # GUI
        self.resetDayUI()

        # find HDR photos
        pathDate = os.path.join(self.Settings["DataDirectory"], self.cbxDate.itemText(index))
        pathHDR = os.path.join(pathDate, "HDR")
        if not os.path.exists(pathHDR):
            return
        photos = utility.findFiles(pathHDR, mode=1, ext="jpg")
        if len(photos) <= 0:
            return

        # filter HDR photos down to those we are interested in
        captures = []
        captureIntervals = []
        captureIntervals.append(utility.imageEXIFDateTime(photos[0])) # start with the first photo timestamp
        threshold = 5 # look for next timestamp at least 5 mins later (next capture interval)
        pPrev = photos[0]
        for p in photos:
            last = captureIntervals[-1]
            next = utility.imageEXIFDateTime(p)
            if (next - last).total_seconds() / 60.0 >= threshold:
                captureIntervals.append(next)
                captures.append(pPrev)
            pPrev = p
        captures.append(photos[-1])
        self.hdrCaptures = captures[1:]
        if len(self.hdrCaptures) <= 0:
            return

        # load GUI
        self.sldTime.setRange(0, len(self.hdrCaptures)-1)
        self.sldTime.valueChanged.emit(0)

    def timeSelected(self, index):
        self.lblData.setText(self.hdrCaptures[index])
        self.lblTime.setText(str(utility.imageEXIFDateTime(self.hdrCaptures[index]).time()))
        self.wgtRender.setPhoto(self.hdrCaptures[index])
        if os.path.exists(os.path.splitext(self.hdrCaptures[index])[0]+'.cr2'):
            self.wgtRender.setRAWAvailable(True)
        self.wgtRender.repaint()

    # def contextMenuEvent(self, event):
    #     menuCtx = QMenu(self)
    #     actExit = QAction(QIcon(), '&Exit', self)
    #     menuCtx.addAction(actExit)
    #     action = menuCtx.exec_(self.mapToGlobal(event.pos()))
    #     if action == actExit:
    #         self.close()

    def toggleHUD(self, state):
        self.wgtRender.showHUD(state)
        self.wgtRender.repaint()

    def toggleStatusBar(self, state):
        if state:
            self.statusBar().show()
            #self.centralWidget().layout().setContentsMargins(10,10,10,0)
        else:
            self.statusBar().hide()
            #self.centralWidget().layout().setContentsMargins(10,10,10,10)

    def center(self):
        frame = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(centerPoint)
        self.move(frame.topLeft())

    def closeEvent(self, event):
        # answer = QMessageBox.question(self, 'Quit Confirmation', 'Are you sure?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No )
        # if answer == QMessageBox.Yes:
        #     event.accept()
        # else:
        #     event.ignore()
        # btn.clicked.connect(QApplication.instance().quit)
        event.accept()

        # cache settings
        self.Settings["WindowWidth"] = self.width()
        self.Settings["WindowHeight"] = self.height()
        left, right = self.splitHoriz.sizes()
        self.Settings["HorizSplitLeft"] = left
        self.Settings["HorizSplitRight"] = right
        top, bottom = self.splitVert.sizes()
        self.Settings["VertSplitTop"] = top
        self.Settings["VertSplitBottom"] = bottom
        self.Settings["ShowHUD"] = self.actHUD.isChecked()
        self.Settings["ShowStatusBar"] = self.actStatusBar.isChecked()

        # dump settings to file
        with open(self.Settings["Filename"], 'w') as file:
            json.dump(self.Settings, file, indent=4)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = SkyDataViewer()
    w.center()
    w.show()

    status = app.exec_()
    sys.exit(status)
