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
from datetime import datetime
from PyQt5.QtCore import QCoreApplication, Qt, QDir
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import *
#from PyQt5.QtWidgets import qApp
import utility
import utility_data
from view_fisheye import ViewFisheye


class SkyDataViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # app settings, set to defaults
        self.Settings = {
            "Filename": "res\\settings.json",
            "DataDirectory": "",
            "WindowWidth": 1024,
            "WindowHeight": 768,
            "HorizSplitLeft": -1,
            "HorizSplitRight": -1,
            "VertSplitTop": -1,
            "VertSplitBottom": -1,
            "ShowGrid": False,
            "ShowSunPath": False,
            "ShowHUD": True,
            "ShowInfo": True,
            "ShowStatusBar": True,
        }
        # different possible exposure times of the HDR data (in seconds)
        self.Exposures = [
            0.000125,
            0.001000,
            0.008000,
            0.066000,
            0.033000,
            0.250000,
            1.000000,
            2.000000,
            4.000000,
        ]

        # member variables
        self.hdrCaptureDirs = []  # some number of these per day
        self.asdMeasures = []     # 81 of these per capture time
        self.exposure = 0

        # load and validate settings
        if (os.path.exists(self.Settings["Filename"])):
            with open(self.Settings["Filename"], 'r') as file:
                self.Settings = json.load(file)
        if (len(self.Settings["DataDirectory"]) > 0 and not os.path.exists(self.Settings["DataDirectory"])):
            self.Settings["DataDirectory"] = ""

        # init
        QToolTip.setFont(QFont('SansSerif', 8))
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
        self.actGrid = QAction(QIcon(), 'Show &Grid', self)
        self.actGrid.setCheckable(True)
        self.actGrid.setChecked(self.Settings["ShowGrid"])
        self.actGrid.setStatusTip('Toggle display of grid')
        self.actGrid.triggered.connect(self.toggleGrid)
        self.actSunPath = QAction(QIcon(), 'Show &Sun Path', self)
        self.actSunPath.setCheckable(True)
        self.actSunPath.setChecked(self.Settings["ShowSunPath"])
        self.actSunPath.setStatusTip('Toggle display of sun path')
        self.actSunPath.triggered.connect(self.toggleSunPath)
        self.actHUD = QAction(QIcon(), 'Show &HUD', self)
        self.actHUD.setCheckable(True)
        self.actHUD.setChecked(self.Settings["ShowHUD"])
        self.actHUD.setStatusTip('Toggle display of HUD')
        self.actHUD.triggered.connect(self.toggleHUD)
        self.actInfo = QAction(QIcon(), 'Show &Info', self)
        self.actInfo.setCheckable(True)
        self.actInfo.setChecked(self.Settings["ShowInfo"])
        self.actInfo.setStatusTip('Toggle display of info panel')
        self.actInfo.triggered.connect(self.toggleInfoPanel)
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
        menuView.addAction(self.actGrid)
        menuView.addAction(self.actSunPath)
        menuView.addAction(self.actHUD)
        menuView.addAction(self.actInfo)
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
        self.cbxTime = QComboBox()
        self.cbxTime.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cbxTime.currentIndexChanged.connect(self.timeSelected)
        self.cbxExposure = QComboBox()
        self.cbxExposure.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cbxExposure.currentIndexChanged.connect(self.exposureSelected)
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
        gridData.addWidget(self.lblData, 0, 1, 1, 3)
        gridData.addWidget(self.cbxDate, 1, 0)
        gridData.addWidget(self.cbxTime, 1, 1)
        gridData.addWidget(self.cbxExposure, 1, 2)
        gridData.addWidget(self.sldTime, 1, 3)
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
        self.wgtFisheye = ViewFisheye()
        self.wgtFisheye.showHUD(self.actHUD.isChecked())

        # info view
        self.tblInfo = QTableWidget()
        self.tblInfo.setShowGrid(False)
        self.tblInfo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tblInfo.verticalHeader().hide()
        #self.tblInfo.horizontalHeader().hide()
        self.tblInfo.setColumnCount(2)
        self.tblInfo.setHorizontalHeaderItem(0, QTableWidgetItem("Field"))
        self.tblInfo.setHorizontalHeaderItem(1, QTableWidgetItem("Value"))
        self.tblInfo.horizontalHeader().setStretchLastSection(True)
        boxInfo = QVBoxLayout()
        boxInfo.setSpacing(0)
        boxInfo.setContentsMargins(0, 0, 0, 0)
        boxInfo.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        boxInfo.addWidget(self.tblInfo)
        pnlInfo = QWidget()
        pnlInfo.setLayout(boxInfo)

        # horizontal splitter
        self.splitHoriz = QSplitter(Qt.Horizontal)
        self.splitHoriz.addWidget(self.wgtFisheye)
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

    def resetAll(self):
        self.hdrCaptureDirs = []
        self.asdMeasures = []
        self.lblData.clear()
        self.cbxDate.clear()
        self.cbxDate.addItem("-date-")
        self.cbxTime.clear()
        self.cbxTime.addItem("-time-")
        self.cbxExposure.clear()
        self.cbxExposure.addItem("-exposure-")
        self.cbxExposure.addItems([str(x) for x in self.Exposures])
        self.exposure = -1
        self.sldTime.setRange(0, 0)
        self.wgtFisheye.setPhoto(None)
        self.wgtFisheye.showGrid(self.Settings["ShowGrid"])
        self.wgtFisheye.showSunPath(self.Settings["ShowSunPath"])
        self.wgtFisheye.showHUD(self.Settings["ShowHUD"])
        self.wgtFisheye.repaint()
        self.tblInfo.clearContents()

    def resetDay(self):
        self.hdrCaptureDirs = []
        self.asdMeasures = []
        self.lblData.setText(self.Settings["DataDirectory"])
        self.cbxTime.clear()
        self.cbxTime.addItem("-time-")
        self.sldTime.setRange(0, 0)
        self.wgtFisheye.setPhoto(None)
        self.wgtFisheye.repaint()
        self.tblInfo.clearContents()

    def browseForData(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Data Directory', self.Settings["DataDirectory"])
        directory = QDir.toNativeSeparators(directory)
        if (directory is not None and len(directory) > 0 and directory != self.Settings["DataDirectory"]):
            self.Settings["DataDirectory"] = directory
            self.loadData()

    def loadData(self):
        if (len(self.Settings["DataDirectory"]) <= 0 or not os.path.exists(self.Settings["DataDirectory"])):
            return

        # GUI
        self.resetAll()

        # find capture dates
        captureDateDirs = utility.findFiles(self.Settings["DataDirectory"], mode=2)
        captureDateDirs[:] = [dir for dir in captureDateDirs if utility.verifyDateTime(os.path.basename(dir), "%Y-%m-%d")]
        captureDates = [os.path.basename(dir) for dir in captureDateDirs]
        if (len(captureDates) > 0):
            self.cbxDate.addItems(captureDates)

    def dateSelected(self, index):
        if (index < 0 or index >= self.cbxDate.count()):
            return

        # GUI
        self.resetDay()

        # find HDR data path
        pathDate = os.path.join(self.Settings["DataDirectory"], self.cbxDate.itemText(index))
        if not os.path.exists(pathDate):
            return
        pathHDR = os.path.join(pathDate, "HDR")
        if not os.path.exists(pathHDR):
            QMessageBox.critical(self, "Error", "No HDR dir of photos found.", QMessageBox.Ok)
            return

        # find all capture time dirs
        self.hdrCaptureDirs = utility.findFiles(pathHDR, mode=2)
        self.hdrCaptureDirs[:] = [dir for dir in self.hdrCaptureDirs if utility.verifyDateTime(os.path.basename(dir), "%H.%M.%S")]
        if (len(self.hdrCaptureDirs) <= 0):
            QMessageBox.critical(self, "Error", "No HDR capture folders found.\nFormat is time of capture (e.g. 08.57.23).", QMessageBox.Ok)
            return

        # find ASD data

        # load sun path for this capture date
        sunpath = utility_data.loadSunPath(pathDate)
        self.wgtFisheye.setSunPath(sunpath)

        # load GUI
        self.cbxTime.addItems([os.path.basename(x) for x in self.hdrCaptureDirs])
        self.cbxTime.setCurrentIndex(1) # because combobox first element is not a valid value
        self.sldTime.setRange(0, len(self.hdrCaptureDirs)-1)
        self.sldTime.valueChanged.emit(0)
        if (self.exposure < 0):
            self.cbxExposure.setCurrentIndex(1) # because combobox first element is not a valid value
            self.exposure = 0

    def timeSelected(self, index):
        if (index < 0 or index >= self.cbxTime.count()):
            return

        # get sender of event
        widget = self.sender()
        if (widget == self.cbxTime):
            index -= 1  # because combobox first element is not a valid value

        # handle unselected time, exposure, or rare events triggered when we have no data loaded yet
        if (index < 0 or self.exposure < 0 or len(self.hdrCaptureDirs) <= 0):
            self.wgtFisheye.setPhoto(None)
            self.wgtFisheye.repaint()
            return

        # At this point we are assuming the photos are sorted (increasing) by exposure time!!!
        # A safer method would be to gather all EXIF DateTimeOriginal fields and sort manually

        # gather all exposure photos taken at time selected
        photos = utility.findFiles(self.hdrCaptureDirs[index], mode=1, ext=["jpg"])
        if (len(photos) <= 0):
            #QMessageBox.critical(self, "Error", "No photos found in:\n" + self.hdrCaptureDirs[index], QMessageBox.Ok)
            return

        # is there a photo for the currently selected exposure?
        if (self.exposure >= len(photos)):
            self.wgtFisheye.setPhoto(None)
            self.wgtFisheye.repaint()
            return

        # extract EXIF data from photo
        exif = utility_data.imageEXIF(photos[self.exposure])
        exif = {k: v for k, v in exif.items() if k.startswith("EXIF")} # filter down to EXIF tags only

        # datetime panel
        self.lblData.setText(photos[self.exposure])
        if (widget == self.cbxTime):
            self.sldTime.setSliderPosition(index)
        elif (widget == self.sldTime):
            self.cbxTime.setCurrentIndex(index+1) # because combobox first element is not a valid value

        # info panel
        self.tblInfo.setRowCount(len(exif.keys()))
        row = 0
        for key in sorted(exif.keys()):
            self.tblInfo.setItem(row, 0, QTableWidgetItem(str(key)[5:]))
            self.tblInfo.setItem(row, 1, QTableWidgetItem(str(exif[key])))
            row += 1
        self.tblInfo.resizeColumnToContents(0)

        # render pane
        self.wgtFisheye.setPhoto(photos[self.exposure], exif=exif)
        self.wgtFisheye.repaint()

    def exposureSelected(self, index):
        index -= 1 # -1 because combobox first element is not a valid value

        self.exposure = index

        if (self.hdrCaptureDirs is not None and len(self.hdrCaptureDirs) > 0):
            self.sldTime.valueChanged.emit(self.sldTime.value())

    # def contextMenuEvent(self, event):
    #     menuCtx = QMenu(self)
    #     actExit = QAction(QIcon(), '&Exit', self)
    #     menuCtx.addAction(actExit)
    #     action = menuCtx.exec_(self.mapToGlobal(event.pos()))
    #     if action == actExit:
    #         self.close()

    def toggleGrid(self, state):
        self.wgtFisheye.showGrid(state)
        self.wgtFisheye.repaint()

    def toggleSunPath(self, state):
        self.wgtFisheye.showSunPath(state)
        self.wgtFisheye.repaint()

    def toggleHUD(self, state):
        self.wgtFisheye.showHUD(state)
        self.wgtFisheye.repaint()

    def toggleInfoPanel(self, state):
        if (state):
            self.splitHoriz.setSizes([self.width() * 0.75, self.width() * 0.25])
        else:
            left, right = self.splitHoriz.sizes()
            self.splitHoriz.setSizes([left + right, 0])

    def toggleStatusBar(self, state):
        if (state):
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
        self.Settings["ShowGrid"] = self.actGrid.isChecked()
        self.Settings["ShowSunPath"] = self.actSunPath.isChecked()
        self.Settings["ShowHUD"] = self.actHUD.isChecked()
        self.Settings["ShowInfo"] = self.actInfo.isChecked()
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
