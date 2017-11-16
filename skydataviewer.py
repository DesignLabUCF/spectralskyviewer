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
from PyQt5.QtWidgets import qApp, QGraphicsPixmapItem
import numpy as np
import pyqtgraph as pg
import utility
import utility_data
from view_fisheye import ViewFisheye
from dialog_export import DialogExport


class SkyDataViewer(QMainWindow):
    # exposure times of the HDR data (in seconds)
    Exposures = [
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

    # ASD graph settings
    XAxisMin = 0
    XAxisMax = 3000 # nm
    XAxisMinDef = 350
    XAxisMaxDef = 2500
    YAxisMin = 0
    YAxisMax = 1.0  # W/m²/nm
    YAxisMinDef = 0
    YAxisMaxDef = 0.4

    # default application settings
    Settings = {
        "Filename": "res\\settings.json",
        "DataDirectory": "",
        "WindowWidth": 1024,
        "WindowHeight": 768,
        "HorizSplitLeft": -1,
        "HorizSplitRight": -1,
        "VertSplitTop": -1,
        "VertSplitBottom": -1,
        "ShowMask": True,
        "ShowHUD": True,
        "ShowCompass": False,
        "ShowSunPath": False,
        "ShowSamples": False,
        "ShowUVGrid": False,
        "ShowEXIF": True,
        "ShowStatusBar": True,
    }
    Settings.update({"ExportOptions": DialogExport.ExportOptions})

    def __init__(self):
        super().__init__()

        # member variables
        self.capture = datetime.min
        self.captureTimeHDRDirs = [] # some number of these per day
        self.captureTimeASDDir = []  # ASD capture time directory of selected HDR capture time
        self.exposure = 0

        # load and validate settings
        self.settings = dict(SkyDataViewer.Settings)  # this must be first!
        if (os.path.exists(self.settings["Filename"])):
            with open(self.settings["Filename"], 'r') as file:
                self.settings = json.load(file)
        if (len(self.settings["DataDirectory"]) > 0 and not os.path.exists(self.settings["DataDirectory"])):
            self.settings["DataDirectory"] = ""

        # init
        QToolTip.setFont(QFont('SansSerif', 8))
        # uic.loadUi('design.ui', self)
        self.initMenu()
        self.initWidgets()
        # self.setGeometry(0, 0, 1024, 768)
        self.resize(self.settings["WindowWidth"], self.settings["WindowHeight"])
        self.setWindowTitle("Sky Data Viewer")
        self.setWindowIcon(QIcon('res/icon.png'))
        self.statusBar().showMessage('Ready')
        if (self.settings["ShowStatusBar"]):
            self.statusBar().show()
        else:
            self.statusBar().hide()

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
        self.actEXIF = QAction(QIcon(), 'Show E&XIF', self)
        self.actEXIF = QAction(QIcon(), 'Show E&XIF', self)
        self.actEXIF.setCheckable(True)
        self.actEXIF.setChecked(self.settings["ShowEXIF"])
        self.actEXIF.setStatusTip('Toggle display of EXIF panel')
        self.actEXIF.triggered.connect(self.toggleEXIFPanel)
        self.actStatusBar = QAction(QIcon(), 'Show Status &Bar', self)
        self.actStatusBar.setCheckable(True)
        self.actStatusBar.setChecked(self.settings["ShowStatusBar"])
        self.actStatusBar.setStatusTip('Toggle display of status bar')
        self.actStatusBar.triggered.connect(self.toggleStatusBar)
        self.actMask = QAction(QIcon(), 'Show &Mask', self)
        self.actMask.setCheckable(True)
        self.actMask.setChecked(self.settings["ShowMask"])
        self.actMask.setStatusTip('Toggle display of fisheye mask')
        self.actMask.triggered.connect(self.toggleMask)
        self.actHUD = QAction(QIcon(), 'Show &HUD', self)
        self.actHUD.setCheckable(True)
        self.actHUD.setChecked(self.settings["ShowHUD"])
        self.actHUD.setStatusTip('Toggle display of HUD')
        self.actHUD.triggered.connect(self.toggleHUD)
        self.actCompass = QAction(QIcon(), 'Show &Compass', self)
        self.actCompass.setCheckable(True)
        self.actCompass.setChecked(self.settings["ShowCompass"])
        self.actCompass.setStatusTip('Toggle display of compass')
        self.actCompass.triggered.connect(self.toggleCompass)
        self.actSunPath = QAction(QIcon(), 'Show Su&n Path', self)
        self.actSunPath.setCheckable(True)
        self.actSunPath.setChecked(self.settings["ShowSunPath"])
        self.actSunPath.setStatusTip('Toggle display of sun path')
        self.actSunPath.triggered.connect(self.toggleSunPath)
        self.actSamples = QAction(QIcon(), 'Show &Samples', self)
        self.actSamples.setCheckable(True)
        self.actSamples.setChecked(self.settings["ShowSamples"])
        self.actSamples.setStatusTip('Toggle display of sampling pattern')
        self.actSamples.triggered.connect(self.toggleSamples)
        self.actUVGrid = QAction(QIcon(), 'Show &UVGrid', self)
        self.actUVGrid.setCheckable(True)
        self.actUVGrid.setChecked(self.settings["ShowUVGrid"])
        self.actUVGrid.setStatusTip('Toggle display of UV grid')
        self.actUVGrid.triggered.connect(self.toggleUVGrid)

        # sky sample menu actions
        self.actClearAll = QAction(QIcon(), '&Clear', self)
        self.actClearAll.setStatusTip('Clear selected samples')
        self.actClearAll.triggered.connect(lambda: self.selectSamples('none'))
        self.actSelectAll = QAction(QIcon(), 'Select &All', self)
        self.actSelectAll.setShortcut('Ctrl+A')
        self.actSelectAll.setStatusTip('Select all samples')
        self.actSelectAll.triggered.connect(lambda: self.selectSamples('all'))
        self.actExportSetup = QAction(QIcon(), 'Setup Export &File', self)
        self.actExportSetup.setStatusTip('Setup export file')
        self.actExportSetup.triggered.connect(self.setupExportFile)
        self.actExportSelected = QAction(QIcon(), '&Export Selected', self)
        self.actExportSelected.setShortcut('Ctrl+E')
        self.actExportSelected.setStatusTip('Export selected samples')
        self.actExportSelected.setEnabled(False)
        self.actExportSelected.triggered.connect(lambda: self.exportSamples('selected'))

        # help menu actions
        actAbout = QAction(QIcon(), '&About', self)
        actAbout.setStatusTip('Information about this application')
        #actAbout.triggered.connect(self.close)

        # menubar
        menubar = self.menuBar()
        menu = menubar.addMenu('&File')
        menu.addAction(actLoad)
        menu.addSeparator()
        menu.addAction(actExit)
        menu = menubar.addMenu('&View')
        menu.addAction(self.actEXIF)
        menu.addAction(self.actStatusBar)
        menu.addSeparator()
        menu.addAction(self.actMask)
        menu.addAction(self.actHUD)
        menu.addSeparator()
        menu.addAction(self.actCompass)
        menu.addAction(self.actSunPath)
        menu.addAction(self.actSamples)
        menu.addAction(self.actUVGrid)
        menu = menubar.addMenu('&Samples')
        menu.addAction(self.actSelectAll)
        menu.addAction(self.actClearAll)
        menu.addSeparator()
        menu.addAction(self.actExportSetup)
        menu.addAction(self.actExportSelected)
        menu = menubar.addMenu('&Help')
        menu.addAction(actAbout)

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
        #self.lblData.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum, QSizePolicy.Label))
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
        self.btnResetView = QPushButton(self)
        self.btnResetView.setIcon(self.btnOrthoRender.style().standardIcon(QStyle.SP_BrowserReload))
        self.btnResetView.setToolTip('Reset View')
        self.btnResetView.clicked.connect(self.resetViewPressed)
        boxToolbox = QVBoxLayout()
        boxToolbox.setSpacing(0)
        boxToolbox.setContentsMargins(0, 0, 0, 0)
        boxToolbox.setAlignment(Qt.AlignTop)
        boxToolbox.addWidget(self.btn2DRender)
        boxToolbox.addWidget(self.btn3DRender)
        boxToolbox.addWidget(self.btnOrthoRender)
        boxToolbox.addStretch(1)
        boxToolbox.addWidget(self.btnResetView)
        pnlToolbox = QWidget()
        pnlToolbox.setLayout(boxToolbox)

        # render pane
        self.wgtFisheye = ViewFisheye(self)
        self.wgtFisheye.showHUD(self.actHUD.isChecked())

        # info view
        self.tblEXIF = QTableWidget()
        self.tblEXIF.setShowGrid(False)
        self.tblEXIF.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tblEXIF.verticalHeader().hide()
        #self.tblEXIF.horizontalHeader().hide()
        self.tblEXIF.setColumnCount(2)
        self.tblEXIF.setHorizontalHeaderItem(0, QTableWidgetItem("Field"))
        self.tblEXIF.setHorizontalHeaderItem(1, QTableWidgetItem("Value"))
        self.tblEXIF.horizontalHeader().setStretchLastSection(True)
        boxEXIF = QVBoxLayout()
        boxEXIF.setSpacing(0)
        boxEXIF.setContentsMargins(0, 0, 0, 0)
        boxEXIF.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        boxEXIF.addWidget(self.tblEXIF)
        pnlEXIF = QWidget()
        pnlEXIF.setLayout(boxEXIF)

        # horizontal splitter
        self.splitHoriz = QSplitter(Qt.Horizontal)
        self.splitHoriz.addWidget(self.wgtFisheye)
        self.splitHoriz.addWidget(pnlEXIF)
        self.splitHoriz.setSizes([self.settings["HorizSplitLeft"] if self.settings["HorizSplitLeft"] >= 0 else self.settings["WindowWidth"] * 0.75,
                                  self.settings["HorizSplitRight"] if self.settings["HorizSplitRight"] >= 0 else self.settings["WindowWidth"] * 0.25])

        # upper panel
        boxUpperHalf = QHBoxLayout()
        boxUpperHalf.setSpacing(10)
        boxUpperHalf.setContentsMargins(0, 0, 0, 0)
        boxUpperHalf.addWidget(pnlToolbox)
        boxUpperHalf.addWidget(self.splitHoriz)
        pnlUpperHalf = QWidget()
        pnlUpperHalf.setLayout(boxUpperHalf)

        # energy graph
        self.wgtGraph = pg.PlotWidget(name='ASD')
        self.wgtGraph.setLabel('left', 'Solar Irradiance', units='W/m²/nm')
        self.wgtGraph.setLabel('bottom', 'Wavelength', units='nm')
        self.resetGraph()
        #self.wgtGraph = QTextEdit()
        #self.wgtGraph.setFocusPolicy(Qt.ClickFocus)

        # vertical splitter
        self.splitVert = QSplitter(Qt.Vertical)
        self.splitVert.addWidget(pnlUpperHalf)
        self.splitVert.addWidget(self.wgtGraph)
        self.splitVert.setSizes([self.settings["VertSplitTop"] if self.settings["VertSplitTop"] >= 0 else self.settings["WindowHeight"] * 0.75,
                                 self.settings["VertSplitBottom"] if self.settings["VertSplitBottom"] >= 0 else self.settings["WindowHeight"] * 0.25])

        # attach high level panels and vertical splitter to layout of window
        gridMain = QGridLayout()
        gridMain.setSpacing(5)
        gridMain.setContentsMargins(10, 10, 10, 10)
        gridMain.addWidget(pnlData, 0, 0)
        gridMain.addWidget(self.splitVert, 1, 0)
        pnlMain = QWidget()
        pnlMain.setLayout(gridMain)
        self.setCentralWidget(pnlMain)

    def resetAll(self):
        self.captureTimeHDRDirs = []
        self.captureTimeASDDir = []
        self.lblData.clear()
        self.cbxDate.clear()
        self.cbxDate.addItem("-date-")
        self.cbxTime.clear()
        self.cbxTime.addItem("-time-")
        self.cbxExposure.clear()
        self.cbxExposure.addItem("-exposure-")
        self.cbxExposure.addItems([str(x) for x in SkyDataViewer.Exposures])
        self.exposure = -1
        self.sldTime.setRange(0, 0)
        self.tblEXIF.clearContents()
        self.wgtFisheye.setPhoto(None)
        self.wgtFisheye.showMask(self.settings["ShowMask"])
        self.wgtFisheye.showHUD(self.settings["ShowHUD"])
        self.wgtFisheye.showCompass(self.settings["ShowCompass"])
        self.wgtFisheye.showSunPath(self.settings["ShowSunPath"])
        self.wgtFisheye.showSamples(self.settings["ShowSamples"])
        self.wgtFisheye.showUVGrid(self.settings["ShowUVGrid"])
        self.wgtFisheye.repaint()
        self.wgtGraph.clear()
        self.resetGraph()

    def resetDay(self):
        self.captureTimeHDRDirs = []
        self.captureTimeASDDir = []
        self.lblData.setText(self.settings["DataDirectory"])
        self.cbxTime.clear()
        self.cbxTime.addItem("-time-")
        self.sldTime.setRange(0, 0)
        self.tblEXIF.clearContents()
        self.wgtFisheye.setPhoto(None)
        self.wgtFisheye.resetRotation()
        self.wgtFisheye.repaint()
        self.wgtGraph.clear()
        self.resetGraph()

    def browseForData(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Data Directory', self.settings["DataDirectory"])
        directory = QDir.toNativeSeparators(directory)
        if (directory is not None and len(directory) > 0 and directory != self.settings["DataDirectory"]):
            self.settings["DataDirectory"] = directory
            self.loadData()

    def loadData(self):
        if (len(self.settings["DataDirectory"]) <= 0 or not os.path.exists(self.settings["DataDirectory"])):
            return

        # GUI
        self.resetAll()

        # find capture dates
        captureDateDirs = utility.findFiles(self.settings["DataDirectory"], mode=2)
        captureDateDirs[:] = [dir for dir in captureDateDirs if utility.verifyDateTime(os.path.basename(dir), "%Y-%m-%d")]
        captureDates = [os.path.basename(dir) for dir in captureDateDirs]
        if (len(captureDates) > 0):
            self.cbxDate.addItems(captureDates)

    def dateSelected(self, index):
        if (index < 0 or index >= self.cbxDate.count()):
            return

        self.resetDay()

        # find HDR data path
        pathDate = os.path.join(self.settings["DataDirectory"], self.cbxDate.itemText(index))
        if not os.path.exists(pathDate):
            return
        pathHDR = os.path.join(pathDate, "HDR")
        if not os.path.exists(pathHDR):
            QMessageBox.critical(self, "Error", "No HDR dir of photos found.", QMessageBox.Ok)
            return

        # find all capture time dirs
        self.captureTimeHDRDirs = utility.findFiles(pathHDR, mode=2)
        self.captureTimeHDRDirs[:] = [dir for dir in self.captureTimeHDRDirs if utility.verifyDateTime(os.path.basename(dir), "%H.%M.%S")]
        if (len(self.captureTimeHDRDirs) <= 0):
            QMessageBox.critical(self, "Error", "No HDR capture folders found.\nFormat is time of capture (e.g. 08.57.23).", QMessageBox.Ok)
            return

        # load sun path for this capture date
        sunpath = utility_data.loadSunPath(pathDate)
        self.wgtFisheye.setSunPath(sunpath)

        # update datetime panel
        self.cbxTime.blockSignals(True) # prevent calling event handlers until we're ready
        self.sldTime.blockSignals(True)
        self.cbxExposure.blockSignals(True)
        self.cbxTime.addItems([os.path.basename(x) for x in self.captureTimeHDRDirs])
        self.cbxTime.setCurrentIndex(1) # because combobox first element is not a valid value
        self.sldTime.setRange(0, len(self.captureTimeHDRDirs) - 1)
        if (self.exposure < 0):
            self.cbxExposure.setCurrentIndex(1) # because combobox first element is not a valid value
            self.exposure = 0
        self.cbxTime.blockSignals(False)
        self.sldTime.blockSignals(False)
        self.cbxExposure.blockSignals(False) # ok, we're ready

        # cache capture datetime
        captureStr = self.cbxDate.itemText(index) + " " + os.path.basename(self.captureTimeHDRDirs[0])
        self.capture = datetime.strptime(captureStr, "%Y-%m-%d %H.%M.%S")
        #print("date: " + str(self.capture))

        # trigger event for selecting first capture time
        self.sldTime.valueChanged.emit(0)

        # reset sample selection
        self.wgtFisheye.selectSamples("none")

    def timeSelected(self, index):
        if (index < 0 or index >= self.cbxTime.count()):
            return

        # get sender of event
        # both capture time choicebox and slider route to this event handler, so we need to know who sent the event
        widget = self.sender()
        if (widget == self.cbxTime):
            index -= 1  # because combobox first element is not a valid value

        # handle unselected time, exposure, or rare events triggered when we have no data loaded yet
        if (index < 0 or self.exposure < 0 or len(self.captureTimeHDRDirs) <= 0):
            self.wgtFisheye.setPhoto(None)
            self.wgtFisheye.repaint()
            return

        # At this point we are assuming the photos are sorted (increasing) by exposure time!!!
        # A safer method would be to gather all EXIF DateTimeOriginal fields and sort manually

        # gather all exposure photos taken at time selected
        photos = utility.findFiles(self.captureTimeHDRDirs[index], mode=1, ext=["jpg"])
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

        # update datetime panel
        # both capture time choicebox and slider route to this event handler, so only update the other one
        self.lblData.setText(photos[self.exposure])
        if (widget == self.cbxTime):
            self.sldTime.blockSignals(True)       # prevent calling this event handler again
            self.sldTime.setSliderPosition(index)
            self.sldTime.blockSignals(False)
        elif (widget == self.sldTime):
            self.cbxTime.blockSignals(True)       # prevent calling this event handler again
            self.cbxTime.setCurrentIndex(index+1) # because combobox first element is not a valid value
            self.cbxTime.blockSignals(False)

        # exif panel
        self.tblEXIF.setRowCount(len(exif.keys()))
        row = 0
        for key in sorted(exif.keys()):
            self.tblEXIF.setItem(row, 0, QTableWidgetItem(str(key)[5:]))
            self.tblEXIF.setItem(row, 1, QTableWidgetItem(str(exif[key])))
            row += 1
        self.tblEXIF.resizeColumnToContents(0)

        # render pane
        self.wgtFisheye.setPhoto(photos[self.exposure], exif=exif)
        self.wgtFisheye.repaint()

        # cache capture datetime
        captureStr = str(self.capture.date()) + " " + os.path.basename(self.captureTimeHDRDirs[index])
        self.capture = datetime.strptime(captureStr, "%Y-%m-%d %H.%M.%S")
        #print("date: " + str(self.capture), widget)
        self.statusBar().showMessage("Capture: " + str(self.capture) + ", Exposure: " + str(SkyDataViewer.Exposures[self.exposure]) + "s")

        # graph
        self.graphSamples(self.wgtFisheye.samplesSelected)

    def exposureSelected(self, index):
        index -= 1 # -1 because combobox first element is not a valid value
        self.exposure = index
        if (self.captureTimeHDRDirs is not None and len(self.captureTimeHDRDirs) > 0):
            self.sldTime.valueChanged.emit(self.sldTime.value())

    def graphSamples(self, indices):
        # clear it
        self.wgtGraph.clear()

        if (len(indices) <= 0):
            return
        if (len(self.captureTimeHDRDirs) <= 0):
            return

        # find ASD data path
        pathDate = os.path.join(self.settings["DataDirectory"], str(self.capture.date()))
        if not os.path.exists(pathDate):
            return
        pathASD = os.path.join(pathDate, "ASD")
        if not os.path.exists(pathASD):
            print("Error: No ASD data found for: " + str(self.capture.date()))
            return

        # find all capture time dirs
        captureTimeASDDirs = utility.findFiles(pathASD, mode=2)
        captureTimeASDDirs[:] = [dir for dir in captureTimeASDDirs if utility.verifyDateTime(os.path.basename(dir), "%H.%M.%S")]
        if (len(captureTimeASDDirs) <= 0):
            print("Error: No ASD capture time dirs found: " + str(self.capture.date()))
            return

        # find an ASD capture time within small threshold of HDR capture time
        asdTime = None
        threshold = 60 # seconds
        for dir in captureTimeASDDirs:
            timestr = str(self.capture.date()) + " " + os.path.basename(dir)
            time = datetime.strptime(timestr, "%Y-%m-%d %H.%M.%S")
            delta = (self.capture - time).total_seconds()
            if (abs(delta) <= threshold):
                asdTime = time
                break

        # is there an equivalent ASD capture?
        if (asdTime is None):
            print("Error: No ASD capture time dir found within " + str(threshold) + "s of HDR capture time: " + str(self.capture))
            return

        # gather all ASD files for capture time
        asdTimeDir = os.path.join(pathASD, str(asdTime.time()).replace(":", "."))
        asdFiles = utility.findFiles(asdTimeDir, mode=1, ext=[".txt"])
        if (len(asdFiles) <= 0):
            print("Error: No .txt files found for: " + str(asdTime))
            return
        if (len(asdFiles) < 81):
            QMessageBox.critical(self, "Warning!", "Number of ASD .txt files is " + str(len(asdFiles)) + ".\nSample pattern should have " + str(len(ViewFisheye.SamplingPattern)), QMessageBox.Ok)
            #print("WARNING!")
            #rect = QtGui.QGraphicsRectItem(QtCore.QRectF(0, 0, 1, 5e-11))
            #rect.setPen(pg.mkPen(100, 200, 100))
            #pw.addItem(rect)
            #self.wgtGraph.addItem(QGraphicsPixmapItem(self.wgtFisheye.iconWarning))

        # load and plot the data
        for i in indices:
            if (i >= len(asdFiles)):
                break
            # load ASD .txt files
            xs, ys = utility_data.loadASDFile(asdFiles[i])
            # plot it
            self.wgtGraph.plot(y=ys, x=xs, pen=(i, len(indices)))
            #self.wgtGraph.addItem() # add a label/icon to graph with number of samples available

    def selectSamples(self, message):
        self.wgtFisheye.selectSamples(message)

    def exportSamples(self, message):
        #if (message == "selected"):
        print("hi")

    def setupExportFile(self):
        dialog = DialogExport()

        code = dialog.exec()
        if (code == QDialog.Accepted):
            print("yay!")

    def resetViewPressed(self):
        self.wgtFisheye.resetRotation()
        self.wgtFisheye.repaint()

    def resetGraph(self):
        self.wgtGraph.setXRange(SkyDataViewer.XAxisMinDef, SkyDataViewer.XAxisMaxDef)
        self.wgtGraph.setYRange(SkyDataViewer.YAxisMinDef, SkyDataViewer.YAxisMaxDef)
        self.wgtGraph.setLimits(xMin=SkyDataViewer.XAxisMin, xMax=SkyDataViewer.XAxisMax,
                                minXRange=100, maxXRange=SkyDataViewer.XAxisMax - SkyDataViewer.XAxisMin,
                                yMin=SkyDataViewer.YAxisMin, yMax=SkyDataViewer.YAxisMax,
                                minYRange=0.05, maxYRange=SkyDataViewer.YAxisMax-SkyDataViewer.YAxisMin)
        #self.wgtGraph.setAspectLocked(True, None)

    def triggerContextMenu(self, widget, event):
        if (widget == self.wgtFisheye):
            menuCtx = QMenu(self)
            menuCtx.addAction(self.actMask)
            menuCtx.addAction(self.actHUD)
            menuCtx.addSeparator()
            menuCtx.addAction(self.actCompass)
            menuCtx.addAction(self.actSunPath)
            menuCtx.addAction(self.actSamples)
            menuCtx.addAction(self.actUVGrid)
            menuCtx.addSeparator()
            menuCtx.addAction(self.actSelectAll)
            menuCtx.addAction(self.actClearAll)
            menuCtx.exec_(widget.mapToGlobal(event.pos()))

    def toggleEXIFPanel(self, state):
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

    def toggleMask(self, state):
        self.wgtFisheye.showMask(state)
        self.wgtFisheye.repaint()

    def toggleHUD(self, state):
        self.wgtFisheye.showHUD(state)
        self.wgtFisheye.repaint()
        self.actUVGrid.setEnabled(state)
        self.actCompass.setEnabled(state)
        self.actSunPath.setEnabled(state)
        self.actSamples.setEnabled(state)

    def toggleUVGrid(self, state):
        self.wgtFisheye.showUVGrid(state)
        self.wgtFisheye.repaint()

    def toggleCompass(self, state):
        self.wgtFisheye.showCompass(state)
        self.wgtFisheye.repaint()

    def toggleSunPath(self, state):
        self.wgtFisheye.showSunPath(state)
        self.wgtFisheye.repaint()

    def toggleSamples(self, state):
        self.wgtFisheye.showSamples(state)
        self.wgtFisheye.repaint()

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
        self.settings["WindowWidth"] = self.width()
        self.settings["WindowHeight"] = self.height()
        left, right = self.splitHoriz.sizes()
        self.settings["HorizSplitLeft"] = left
        self.settings["HorizSplitRight"] = right
        top, bottom = self.splitVert.sizes()
        self.settings["VertSplitTop"] = top
        self.settings["VertSplitBottom"] = bottom
        self.settings["ShowEXIF"] = self.actEXIF.isChecked()
        self.settings["ShowStatusBar"] = self.actStatusBar.isChecked()
        self.settings["ShowMask"] = self.actMask.isChecked()
        self.settings["ShowHUD"] = self.actHUD.isChecked()
        self.settings["ShowCompass"] = self.actCompass.isChecked()
        self.settings["ShowSunPath"] = self.actSunPath.isChecked()
        self.settings["ShowSamples"] = self.actSamples.isChecked()
        self.settings["ShowUVGrid"] = self.actUVGrid.isChecked()

        # dump settings to file
        with open(self.settings["Filename"], 'w') as file:
            json.dump(self.settings, file, indent=4)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = SkyDataViewer()
    w.center()
    w.show()

    status = app.exec_()
    sys.exit(status)
