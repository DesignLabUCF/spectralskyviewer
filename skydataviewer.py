#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 10/06/2017
# @summary: SkyDataViewer main program file
# ====================================================================
import sys
import os
import json
import csv
import math
from datetime import datetime
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import *
import pyqtgraph as pg
from colormath.color_objects import sRGBColor, HSVColor, LabColor
from colormath.color_conversions import convert_color
import common
import utility
import utility_data
import utility_angles
from view_fisheye import ViewFisheye
from dialog_export import DialogExport
from dialog_converter import DialogConverter
from dialog_slider import DialogSlider


class SkyDataViewer(QMainWindow):

    def __init__(self):
        super().__init__()

        # member variables
        self.capture = datetime.min
        self.captureTimeHDRDirs = []   # some number of these per day
        self.captureTimeASDFiles = []  # length should be equal to sampling pattern length
        self.exposure = 0
        self.dontSaveSettings = False

        # load application settings
        utility_data.loadAppSettings()

        # init
        QToolTip.setFont(QFont('SansSerif', 8))
        # uic.loadUi('design.ui', self)
        self.initMenu()
        self.initWidgets()
        # self.setGeometry(0, 0, 1024, 768)
        self.resize(common.AppSettings["WindowWidth"], common.AppSettings["WindowHeight"])
        self.setWindowTitle("SkyDataViewer")
        self.setWindowIcon(QIcon('res/icon.png'))
        self.statusBar().showMessage('Ready')
        if common.AppSettings["ShowStatusBar"]:
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
        self.actEXIF.setChecked(common.AppSettings["ShowEXIF"])
        self.actEXIF.setStatusTip('Toggle display of EXIF panel')
        self.actEXIF.triggered.connect(self.toggleEXIFPanel)
        self.actStatusBar = QAction(QIcon(), 'Show Status &Bar', self)
        self.actStatusBar.setCheckable(True)
        self.actStatusBar.setChecked(common.AppSettings["ShowStatusBar"])
        self.actStatusBar.setStatusTip('Toggle display of status bar')
        self.actStatusBar.triggered.connect(self.toggleStatusBar)
        self.actHUD = QAction(QIcon(), 'Show &HUD', self)
        self.actHUD.setCheckable(True)
        self.actHUD.setChecked(common.AppSettings["ShowHUD"])
        self.actHUD.setStatusTip('Toggle display of HUD')
        self.actHUD.triggered.connect(lambda: self.toggleHUDView(self.actHUD))
        self.actMask = QAction(QIcon(), 'Show &Mask', self)
        self.actMask.setCheckable(True)
        self.actMask.setChecked(common.AppSettings["ShowMask"])
        self.actMask.setStatusTip('Toggle display of fisheye mask')
        self.actMask.triggered.connect(lambda: self.toggleHUDView(self.actMask))
        self.actCompass = QAction(QIcon(), 'Show &Compass', self)
        self.actCompass.setCheckable(True)
        self.actCompass.setChecked(common.AppSettings["ShowCompass"])
        self.actCompass.setStatusTip('Toggle display of compass')
        self.actCompass.triggered.connect(lambda: self.toggleHUDView(self.actCompass))
        self.actLensWarp = QAction(QIcon(), 'Show &Lens Warp', self)
        self.actLensWarp.setCheckable(True)
        self.actLensWarp.setChecked(common.AppSettings["ShowLensWarp"])
        self.actLensWarp.setStatusTip('Toggle display of lens warp amount')
        self.actLensWarp.triggered.connect(lambda: self.toggleHUDView(self.actLensWarp))
        self.actSunPath = QAction(QIcon(), 'Show Su&n Path', self)
        self.actSunPath.setCheckable(True)
        self.actSunPath.setChecked(common.AppSettings["ShowSunPath"])
        self.actSunPath.setStatusTip('Toggle display of sun path')
        self.actSunPath.triggered.connect(lambda: self.toggleHUDView(self.actSunPath))
        self.actSamples = QAction(QIcon(), 'Show &Samples', self)
        self.actSamples.setCheckable(True)
        self.actSamples.setChecked(common.AppSettings["ShowSamples"])
        self.actSamples.setStatusTip('Toggle display of sampling pattern')
        self.actSamples.triggered.connect(lambda: self.toggleHUDView(self.actSamples))
        self.actShadows = QAction(QIcon(), 'Show Shadows', self)
        self.actShadows.setCheckable(True)
        self.actShadows.setChecked(common.AppSettings["ShowShadows"])
        self.actShadows.setStatusTip('Toggle display of shadows on HUD')
        self.actShadows.triggered.connect(lambda: self.toggleHUDView(self.actShadows))
        self.actUVGrid = QAction(QIcon(), 'Show &UVGrid', self)
        self.actUVGrid.setCheckable(True)
        self.actUVGrid.setChecked(common.AppSettings["ShowUVGrid"])
        self.actUVGrid.setStatusTip('Toggle display of UV grid')
        self.actUVGrid.triggered.connect(lambda: self.toggleHUDView(self.actUVGrid))
        self.actPixelRegion = QAction(QIcon(), 'Pixel (n x n) Region', self)
        self.actPixelRegion.setStatusTip('Use an (n x n) pixel region')
        self.actPixelRegion.triggered.connect(lambda: self.togglePixelOptions(self.actPixelRegion))
        self.actPixelMean = QAction(QIcon(), 'Mean Weighting', self)
        self.actPixelMean.setCheckable(True)
        self.actPixelMean.setStatusTip('Apply mean weighting to pixels')
        self.actPixelMean.triggered.connect(lambda: self.togglePixelOptions(self.actPixelMean))
        self.actPixelMedian = QAction(QIcon(), 'Median Weighting', self)
        self.actPixelMedian.setCheckable(True)
        self.actPixelMedian.setStatusTip('Apply median weighting to pixels')
        self.actPixelMedian.triggered.connect(lambda: self.togglePixelOptions(self.actPixelMedian))
        self.actPixelGaussian = QAction(QIcon(), 'Gaussian Weighting', self)
        self.actPixelGaussian.setCheckable(True)
        self.actPixelGaussian.setStatusTip('Apply Gaussian weighting to pixels')
        self.actPixelGaussian.triggered.connect(lambda: self.togglePixelOptions(self.actPixelGaussian))
        self.actGraphRes = QAction(QIcon(), 'Graph Resolution', self)
        self.actGraphRes.setStatusTip('Specify radiance graph resolution')
        self.actGraphRes.triggered.connect(lambda: self.toggleGraphOptions(self.actGraphRes))
        self.actGraphLine = QAction(QIcon(), 'Graph Line Thickness', self)
        self.actGraphLine.setStatusTip('Specify radiance graph line thickness')
        self.actGraphLine.triggered.connect(lambda: self.toggleGraphOptions(self.actGraphLine))
        self.actHUDTextScale = QAction(QIcon(), 'HUD Text Scale', self)
        self.actHUDTextScale.setStatusTip('Adjust scale of HUD text')
        self.actHUDTextScale.triggered.connect(self.toggleHUDTextScale)
        pixWeightGroup = QActionGroup(self)
        pixWeightGroup.addAction(self.actPixelMean)
        pixWeightGroup.addAction(self.actPixelMedian)
        pixWeightGroup.addAction(self.actPixelGaussian)
        pixWeight = common.PixelWeighting(common.AppSettings["PixelWeighting"])
        if pixWeight == common.PixelWeighting.Mean:
            self.actPixelMean.setChecked(True)
        elif pixWeight == common.PixelWeighting.Median:
            self.actPixelMedian.setChecked(True)
        elif pixWeight == common.PixelWeighting.Gaussian:
            self.actPixelGaussian.setChecked(True)

        # sky sample menu actions
        self.actExportSetup = QAction(QIcon(), 'Setup Export &File', self)
        self.actExportSetup.setStatusTip('Setup export file')
        self.actExportSetup.triggered.connect(self.setupExportFile)
        self.actExportSelected = QAction(QIcon(), '&Export Selected', self)
        self.actExportSelected.setShortcut('Ctrl+E')
        self.actExportSelected.setStatusTip('Export selected samples')
        self.actExportSelected.setEnabled(False)
        self.actExportSelected.triggered.connect(lambda: self.exportSamples('selected'))
        self.actSelectAll = QAction(QIcon(), 'Select &All', self)
        self.actSelectAll.setShortcut('Ctrl+A')
        self.actSelectAll.setStatusTip('Select all samples')
        self.actSelectAll.triggered.connect(lambda: self.selectSamples('all'))
        self.actSelectInv = QAction(QIcon(), 'Select &Inverse', self)
        self.actSelectInv.setShortcut('Ctrl+I')
        self.actSelectInv.setStatusTip('Invert current selected samples')
        self.actSelectInv.triggered.connect(lambda: self.selectSamples('inverse'))
        self.actClearAll = QAction(QIcon(), '&Clear All', self)
        self.actClearAll.setStatusTip('Clear selected samples')
        self.actClearAll.triggered.connect(lambda: self.selectSamples('none'))
        self.actAvoidSun = QAction(QIcon(), 'Avoid Circumsolar', self)
        self.actAvoidSun.setStatusTip('Deselect samples around sun within a specified angle')
        self.actAvoidSun.triggered.connect(self.toggleAvoidSun)
        self.actSampleConverter = QAction(QIcon(), 'Sample &Converter', self)
        self.actSampleConverter.setStatusTip('Re-export samples with different properties')
        self.actSampleConverter.triggered.connect(self.convertSamples)

        # help menu actions
        actAbout = QAction(QIcon(), '&About', self)
        actAbout.setStatusTip('Information about this application')
        actAbout.triggered.connect(self.toggleAbout)
        actDontSave = QAction(QIcon(), 'Don\'t Save Settings', self)
        actDontSave.setCheckable(True)
        actDontSave.setChecked(False)
        actDontSave.setStatusTip('Use this to prevent the application from stomping your settings')
        actDontSave.triggered.connect(self.toggleDontSave)

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
        menu.addAction(self.actHUD)
        menu.addAction(self.actMask)
        menu.addAction(self.actCompass)
        menu.addAction(self.actLensWarp)
        menu.addAction(self.actSunPath)
        menu.addAction(self.actSamples)
        menu.addAction(self.actShadows)
        menu.addAction(self.actUVGrid)
        menu.addSeparator()
        menu.addAction(self.actPixelRegion)
        submenu = menu.addMenu('Pixel Weighting')
        submenu.addAction(self.actPixelMean)
        submenu.addAction(self.actPixelMedian)
        submenu.addAction(self.actPixelGaussian)
        menu.addSeparator()
        menu.addAction(self.actGraphRes)
        menu.addAction(self.actGraphLine)
        menu.addSeparator()
        menu.addAction(self.actHUDTextScale)
        menu = menubar.addMenu('&Samples')
        menu.addAction(self.actExportSetup)
        menu.addSeparator()
        menu.addAction(self.actExportSelected)
        menu.addAction(self.actSampleConverter)
        menu.addSeparator()
        menu.addAction(self.actSelectAll)
        menu.addAction(self.actSelectInv)
        menu.addAction(self.actClearAll)
        menu.addSeparator()
        menu.addAction(self.actAvoidSun)
        menu = menubar.addMenu('&Help')
        menu.addAction(actAbout)
        menu.addAction(actDontSave)

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
        self.btn2DRender.setToolTip('2D View')
        self.btn3DRender = QPushButton(self)
        self.btn3DRender.setIcon(self.btn3DRender.style().standardIcon(QStyle.SP_DesktopIcon))
        self.btn3DRender.setToolTip('3D View')
        # self.btnOrthoRender = QPushButton(self)
        # self.btnOrthoRender.setIcon(self.btnOrthoRender.style().standardIcon(QStyle.SP_DesktopIcon))
        # self.btnOrthoRender.setToolTip('Orthographic')
        self.btnResetView = QPushButton(self)
        self.btnResetView.setIcon(self.btnResetView.style().standardIcon(QStyle.SP_BrowserReload))
        self.btnResetView.setToolTip('Reset View')
        self.btnResetView.clicked.connect(self.resetViewPressed)
        boxToolbox = QVBoxLayout()
        boxToolbox.setSpacing(0)
        boxToolbox.setContentsMargins(0, 0, 0, 0)
        boxToolbox.setAlignment(Qt.AlignTop)
        boxToolbox.addWidget(self.btn2DRender)
        boxToolbox.addWidget(self.btn3DRender)
        #boxToolbox.addWidget(self.btnOrthoRender)
        boxToolbox.addStretch(1)
        boxToolbox.addWidget(self.btnResetView)
        pnlToolbox = QWidget()
        pnlToolbox.setLayout(boxToolbox)

        # render pane
        self.wgtFisheye = ViewFisheye(self)

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
        self.splitHoriz.setSizes([common.AppSettings["HorizSplitLeft"] if common.AppSettings["HorizSplitLeft"] >= 0 else common.AppSettings["WindowWidth"] * 0.75,
                                  common.AppSettings["HorizSplitRight"] if common.AppSettings["HorizSplitRight"] >= 0 else common.AppSettings["WindowWidth"] * 0.25])

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
        self.wgtGraph.setLabel('left', 'Radiance', units='W/m²/sr/nm')
        self.wgtGraph.setLabel('bottom', 'Wavelength', units='nm')
        self.resetGraph()
        #self.wgtGraphErrors = QLabel()
        #self.wgtGraphErrors.setText("hello, world!")
        #self.wgtGraph = QTextEdit()
        #self.wgtGraph.setFocusPolicy(Qt.ClickFocus)

        # vertical splitter
        self.splitVert = QSplitter(Qt.Vertical)
        self.splitVert.addWidget(pnlUpperHalf)
        self.splitVert.addWidget(self.wgtGraph)
        self.splitVert.setSizes([common.AppSettings["VertSplitTop"] if common.AppSettings["VertSplitTop"] >= 0 else common.AppSettings["WindowHeight"] * 0.75,
                                 common.AppSettings["VertSplitBottom"] if common.AppSettings["VertSplitBottom"] >= 0 else common.AppSettings["WindowHeight"] * 0.25])

        # attach high level panels and vertical splitter to layout of window
        gridMain = QGridLayout()
        gridMain.setSpacing(5)
        gridMain.setContentsMargins(10, 10, 10, 10)
        gridMain.addWidget(pnlData, 0, 0)
        gridMain.addWidget(self.splitVert, 1, 0)
        pnlMain = QWidget()
        pnlMain.setLayout(gridMain)
        self.setCentralWidget(pnlMain)

    def resetDay(self):
        self.captureTimeHDRDirs = []
        self.captureTimeASDFiles = []
        self.lblData.setText(common.AppSettings["DataDirectory"])
        self.cbxTime.clear()
        self.cbxTime.addItem("-time-")
        self.sldTime.setRange(0, 0)
        self.tblEXIF.clearContents()
        self.wgtFisheye.setPhoto(None)
        self.wgtFisheye.resetRotation()
        self.wgtFisheye.repaint()
        self.wgtGraph.clear()
        self.resetGraph()

    def resetViewPressed(self):
        self.wgtFisheye.resetRotation()
        self.wgtFisheye.repaint()

    def resetGraph(self):
        # XAxisMin = 0
        # XAxisMax = 3000  # nm
        # XAxisMinDef = 350
        # XAxisMaxDef = 2500
        # YAxisMin = 0
        # YAxisMax = 1.0  # W/m²/sr/nm
        # YAxisMinDef = 0
        # YAxisMaxDef = 0.4
        # self.wgtGraph.setXRange(XAxisMinDef, XAxisMaxDef)
        # self.wgtGraph.setYRange(YAxisMinDef, YAxisMaxDef)
        # self.wgtGraph.setLimits(xMin=XAxisMin, xMax=XAxisMax,
        #                         minXRange=100, maxXRange=XAxisMax - XAxisMin,
        #                         yMin=YAxisMin, yMax=YAxisMax,
        #                         minYRange=0.05, maxYRange=YAxisMax-YAxisMin)
        self.wgtGraph.getPlotItem().getAxis('left').enableAutoSIPrefix(enable=False)
        self.wgtGraph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(enable=False)
        #self.wgtGraph.setAspectLocked(True, None)

    def loadData(self):
        # only if user set a valid data directory
        if len(common.AppSettings["DataDirectory"]) <= 0 or not os.path.exists(common.AppSettings["DataDirectory"]):
            return

        # reset GUI
        self.captureTimeHDRDirs = []
        self.captureTimeASDFiles = []
        self.lblData.clear()
        self.cbxDate.clear()
        self.cbxDate.addItem("-date-")
        self.cbxTime.clear()
        self.cbxTime.addItem("-time-")
        self.cbxExposure.clear()
        self.cbxExposure.addItem("-exposure-")
        self.exposure = -1
        self.sldTime.setRange(0, 0)
        self.tblEXIF.clearContents()
        self.wgtGraph.clear()
        self.resetGraph()

        # load data directory configuration
        utility_data.loadDataConfig()

        # # load sampling pattern
        # common.SamplingPattern = utility_data.loadSamplingPattern(common.AppSettings["DataDirectory"])
        # common.SamplingPatternRads = [(math.radians(s[0]), math.radians(s[1])) for s in common.SamplingPattern]
        # common.SamplingPatternAlts = list(set([s[1] for s in common.SamplingPattern]))
        # common.SamplingPatternAlts = sorted(common.SamplingPatternAlts)
        #
        # # load exposures
        # common.Exposures = utility_data.loadExposures(common.AppSettings["DataDirectory"])
        # common.ExposureIdxMap = {common.Exposures[i]: i for i in range(0, len(common.Exposures))}
        # self.cbxExposure.addItems([str(x) for x in common.Exposures])
        #
        # # load lens warp data
        # common.LensWarp = utility_data.loadLensWarp(common.AppSettings["DataDirectory"])
        #
        # # load site data
        # common.SPASiteData = utility_data.loadSPASiteData(common.AppSettings["DataDirectory"])
        #
        # # load sky cover data
        # common.SkyCoverData = utility_data.loadSkyCoverData(common.AppSettings["DataDirectory"])

        # add exposures
        self.cbxExposure.addItems([str(x) for x in common.Exposures])

        # find capture dates
        captureDateDirs = utility.findFiles(common.AppSettings["DataDirectory"], mode=2)
        captureDateDirs[:] = [dir for dir in captureDateDirs if utility.verifyDateTime(os.path.basename(dir), "%Y-%m-%d")]
        captureDates = [os.path.basename(dir) for dir in captureDateDirs]
        if len(captureDates) > 0:
            self.cbxDate.addItems(captureDates)

        # init view widgets
        self.wgtFisheye.dataLoaded()
        self.wgtFisheye.setPhoto(None)
        self.wgtFisheye.repaint()

    def browseForData(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Data Directory', common.AppSettings["DataDirectory"])
        directory = QDir.toNativeSeparators(directory)
        if directory is not None and len(directory) > 0 and directory != common.AppSettings["DataDirectory"]:
            common.AppSettings["DataDirectory"] = directory
            self.loadData()

    def dateSelected(self, index):
        if index < 0 or index >= self.cbxDate.count():
            return

        # reset
        self.resetDay()

        # find HDR data path
        pathDate = os.path.join(common.AppSettings["DataDirectory"], self.cbxDate.itemText(index))
        if not os.path.exists(pathDate):
            return
        pathHDR = os.path.join(pathDate, "HDR")
        if not os.path.exists(pathHDR):
            QMessageBox.critical(self, "Error", "No HDR dir of photos found.", QMessageBox.Ok)
            return

        # find all capture time dirs
        self.captureTimeHDRDirs = utility.findFiles(pathHDR, mode=2)
        self.captureTimeHDRDirs[:] = [dir for dir in self.captureTimeHDRDirs if utility.verifyDateTime(os.path.basename(dir), "%H.%M.%S")]
        if len(self.captureTimeHDRDirs) <= 0:
            QMessageBox.critical(self, "Error", "No HDR capture folders found.\nFormat is time of capture (e.g. 08.57.23).", QMessageBox.Ok)
            return

        # cache capture datetime
        captureStr = self.cbxDate.itemText(index) + " " + os.path.basename(self.captureTimeHDRDirs[0])
        self.capture = datetime.strptime(captureStr, "%Y-%m-%d %H.%M.%S")
        # print("date: " + str(self.capture))

        # compute and apply sun path
        #data = utility_data.loadSPASiteData(pathDate) # reload site info per date directory if exists
        #if data != None:
        #    common.SPASiteData = data
        utility_data.fillSPADateTime(common.SPASiteData, self.capture)
        sunpath = utility_data.computeSunPath(common.SPASiteData)
        self.wgtFisheye.setSunPath(sunpath)

        # update datetime panel
        self.cbxTime.blockSignals(True) # prevent calling event handlers until we're ready
        self.sldTime.blockSignals(True)
        self.cbxExposure.blockSignals(True)
        self.cbxTime.addItems([os.path.basename(x) for x in self.captureTimeHDRDirs])
        self.cbxTime.setCurrentIndex(1) # because combobox first element is not a valid value
        self.sldTime.setRange(0, len(self.captureTimeHDRDirs) - 1)
        if self.exposure < 0:
            self.cbxExposure.setCurrentIndex(1) # because combobox first element is not a valid value
            self.exposure = 0
        self.cbxTime.blockSignals(False)
        self.sldTime.blockSignals(False)
        self.cbxExposure.blockSignals(False) # ok, we're ready

        # trigger event for selecting first capture time
        self.sldTime.valueChanged.emit(0)

        # reset sample selection
        self.wgtFisheye.selectSamples("none")

    def timeSelected(self, index):
        if index < 0 or index >= self.cbxTime.count():
            return

        # reset
        self.captureTimeASDFiles = []
        self.wgtGraph.clear()

        # get sender of event
        # both capture time choicebox and slider route to this event handler, so we need to know who sent the event
        widget = self.sender()
        if widget == self.cbxTime:
            index -= 1  # because combobox first element is not a valid value

        # handle unselected time, exposure, or rare events triggered when we have no data loaded yet
        if index < 0 or self.exposure < 0 or len(self.captureTimeHDRDirs) <= 0:
            self.wgtFisheye.setPhoto(None)
            self.wgtFisheye.repaint()
            return

        # At this point we are assuming the photos are sorted (increasing) by exposure time!!!
        # TODO: A safer method would be to gather all EXIF DateTimeOriginal fields and sort manually

        # gather all exposure photos taken at time selected
        photos = utility.findFiles(self.captureTimeHDRDirs[index], mode=1, ext=["jpg"])
        if len(photos) <= 0:
            self.log("Error: No photos found in:\n" + self.captureTimeHDRDirs[index])
            return

        # is there a photo for the currently selected exposure?
        if self.exposure >= len(photos):
            self.wgtFisheye.setPhoto(None)
            self.wgtFisheye.repaint()
            return

        # cache capture datetime
        captureStr = str(self.capture.date()) + " " + os.path.basename(self.captureTimeHDRDirs[index])
        self.capture = datetime.strptime(captureStr, "%Y-%m-%d %H.%M.%S")
        # print("date: " + str(self.capture), widget)
        self.statusBar().showMessage("Capture: " + str(self.capture) + ", Exposure: " + str(common.Exposures[self.exposure]) + "s")

        # extract EXIF data from photo
        exif = utility_data.imageEXIF(photos[self.exposure])
        #exif = {k: v for k, v in exif.items() if k.startswith("EXIF")} # filter down to EXIF tags only

        # update datetime panel
        # both capture time choicebox and slider route to this event handler, so only update the other one
        self.lblData.setText(photos[self.exposure])
        if widget == self.cbxTime:
            self.sldTime.blockSignals(True)       # prevent calling this event handler again
            self.sldTime.setSliderPosition(index)
            self.sldTime.blockSignals(False)
        elif widget == self.sldTime:
            self.cbxTime.blockSignals(True)       # prevent calling this event handler again
            self.cbxTime.setCurrentIndex(index+1) # because combobox first element is not a valid value
            self.cbxTime.blockSignals(False)

        # exif panel
        self.tblEXIF.setRowCount(len(exif.keys()))
        row = 0
        for key in sorted(exif.keys()):
            self.tblEXIF.setItem(row, 0, QTableWidgetItem(str(key)))
            self.tblEXIF.setItem(row, 1, QTableWidgetItem(str(exif[key])))
            row += 1
        self.tblEXIF.resizeColumnToContents(0)

        # render pane
        utility_data.fillSPADateTime(common.SPASiteData, self.capture)
        sunpos = utility_data.computeSunPosition(common.SPASiteData)
        self.wgtFisheye.setSunPosition(sunpos)
        self.wgtFisheye.setPhoto(photos[self.exposure], exif=exif)
        self.wgtFisheye.setSkycover(utility_data.findCaptureSkyCover(self.capture, common.SkyCoverData))
        self.wgtFisheye.repaint()

        # find ASD data path
        pathDate = os.path.join(common.AppSettings["DataDirectory"], str(self.capture.date()))
        if not os.path.exists(pathDate):
            return
        pathASD = os.path.join(pathDate, "ASD")
        if not os.path.exists(pathASD):
            self.log("Error: No ASD data found for: " + str(self.capture.date()))
            return

        # find all capture time dirs
        captureTimeASDDirs = utility.findFiles(pathASD, mode=2)
        captureTimeASDDirs[:] = [dir for dir in captureTimeASDDirs if utility.verifyDateTime(os.path.basename(dir), "%H.%M.%S")]
        if len(captureTimeASDDirs) <= 0:
            self.log("Error: No ASD capture time dirs found: " + str(self.capture.date()))
            return

        # find an ASD capture time within small threshold of HDR capture time
        asdTime = None
        threshold = common.DataConfig["CaptureEpsilon"]  # seconds
        for dir in captureTimeASDDirs:
            timestr = str(self.capture.date()) + " " + os.path.basename(dir)
            time = datetime.strptime(timestr, "%Y-%m-%d %H.%M.%S")
            delta = (self.capture - time).total_seconds()
            if abs(delta) <= threshold:
                asdTime = time
                break

        # is there an equivalent ASD capture?
        if asdTime is None:
            self.log("Error: No ASD capture time dir found within " + str(threshold) + "s of HDR capture time: " + str(self.capture))
            return

        # gather all ASD files for capture time
        asdTimeDir = os.path.join(pathASD, str(asdTime.time()).replace(":", "."))
        self.captureTimeASDFiles = utility.findFiles(asdTimeDir, mode=1, ext=[".txt"])
        if len(self.captureTimeASDFiles) <= 0:
            self.log("Error: No ASD .txt files found for: " + str(asdTime))
            return
        if len(self.captureTimeASDFiles) < len(common.SamplingPattern):
            self.log("Error: Found only " + str(len(self.captureTimeASDFiles)) + " ASD files. Sample pattern should have " + str(len(common.SamplingPattern)))
            return

        # graph ASD data
        self.graphSamples(self.wgtFisheye.samplesSelected)

    def timeChangeWheelEvent(self, event):
        self.sldTime.event(event)

    def exposureSelected(self, index):
        index -= 1 # -1 because combobox first element is not a valid value
        self.exposure = index
        if self.captureTimeHDRDirs is not None and len(self.captureTimeHDRDirs) > 0:
            self.sldTime.valueChanged.emit(self.sldTime.value())

    def graphSamples(self, indices):
        # clear the graph
        self.wgtGraph.clear()

        # nothing to graph
        if len(indices) <= 0:
            return
        if len(self.captureTimeHDRDirs) <= 0:   # no HDR photo
            return
        if len(self.captureTimeASDFiles) <= 0:  # no ASD files
            return

        # load and plot data
        for i in indices:
            if i >= len(self.captureTimeASDFiles):
                break
            wavelengths, radiances = utility_data.loadASDFile(self.captureTimeASDFiles[i], common.AppSettings["GraphResolution"])
            #wavelengths = wavelengths[::common.AppSettings["GraphResolution"]]
            #radiances = radiances[::common.AppSettings["GraphResolution"]]
            self.wgtGraph.plot(y=radiances, x=wavelengths, pen=pg.mkPen(color=self.wgtFisheye.getSamplePatternRGB(i), width=common.AppSettings["GraphLineThickness"])) # pen=(i, len(indices))
            #self.wgtGraph.addItem() # add a label/icon to graph with number of samples available

    def selectSamples(self, message):
        self.wgtFisheye.selectSamples(message)

    def exportSamples(self, message):
        xoptions = common.AppSettings["ExportOptions"]

        # we shouldn't be here if export file hasn't been configured
        if len(xoptions["Filename"]) <= 0:
            QMessageBox.critical(self, "Error", "Please configure export file first.", QMessageBox.Ok)
            return

        # nothing to export
        if len(self.captureTimeHDRDirs) <= 0:          # no HDR photo
            self.log("Info: No HDR directories found. Nothing to export.")
            return
        if len(self.captureTimeASDFiles) <= 0:         # no ASD files
            self.log("Info: No ASD files found. Nothing to export.")
            return
        if len(self.wgtFisheye.samplesSelected) <= 0:  # nothing selected
            self.log("Info: No samples selected. Nothing to export.")
            return

        # make sure there are photos for every exposure we intend to export
        exposures = []  # list of exposures to export
        expphotos = []  # list of photos per exposure
        if not xoptions["IsHDR"]:
            photo = utility_data.findHDRFile(common.AppSettings["DataDirectory"], self.capture, self.exposure)
            if not photo or len(photo) <= 0:
                self.log("Error: Photo for " + self.exposure + "s exposure not found. Export canceled.")
                return
            exposures.append(self.exposure)
            expphotos.append(photo)
        else:
            for exp in common.Exposures:
                photo = utility_data.findHDRFile(common.AppSettings["DataDirectory"], self.capture, exp)
                if not photo or len(photo) <= 0:
                    self.log("Error: Photo for exposure '" + str(exp) + "' not found. Canceled export.")
                    return
                exposures.append(exp)
                expphotos.append(photo)

        self.log("Exporting... ")

        # init / pre-compute
        sampleidx = 0
        delimiter = ","
        sunpos = utility_data.computeSunPosition(common.SPASiteData)
        skycover = utility_data.findCaptureSkyCover(self.capture, common.SkyCoverData)
        resolution = xoptions["SpectrumResolution"]
        coordsys = common.CoordSystem(xoptions["CoordSystem"])
        coords = [common.SamplingPattern[i] for i in self.wgtFisheye.samplesSelected]
        points = [self.wgtFisheye.samplePointsInFile[i] for i in self.wgtFisheye.samplesSelected]
        pixweight = common.PixelWeighting(xoptions["PixelWeighting"])
        # pixel regions
        if xoptions["ComputePixelRegion"]:
            # TODO: this is hardcoded to our sampling pattern. compute it properly by projecting area and taking width and height!!
            altitudeRegionMap = {90:1, 71.9187:3, 53.3665:5, 33.749:7, 12.1151:9}
            pixregions = [altitudeRegionMap[c[1]] for c in coords]
        else:
            reg = xoptions["PixelRegion"]
            pixregions = [reg for i in range(0, len(points))]
        # pixels
        exppixels = []  # list of lists of pixels per exposure
        for i in range(0, len(exposures)):
            exppixels.append(utility_data.collectPixels(points, pixregions, file=expphotos[i], weighting=pixweight))
        # color model
        color = common.ColorModel(xoptions["ColorModel"])
        if color == common.ColorModel.HSV:
            for pixels in exppixels:
                for i in range(0, len(self.wgtFisheye.samplesSelected)):
                    rgb = sRGBColor(pixels[i][0], pixels[i][1], pixels[i][2], is_upscaled=True)
                    hsv = convert_color(rgb, HSVColor)
                    pixels[i] = hsv.get_value_tuple()
        elif color == common.ColorModel.LAB:
            for pixels in exppixels:
                for i in range(0, len(self.wgtFisheye.samplesSelected)):
                    rgb = sRGBColor(pixels[i][0], pixels[i][1], pixels[i][2], is_upscaled=True)
                    lab = convert_color(rgb, LabColor)
                    pixels[i] = lab.get_value_tuple()
        # UV coordinate system
        if coordsys == common.CoordSystem.UV:
            coordsfinal = [(utility_angles.SkyCoord2FisheyeUV(c[0], c[1])) for c in coords]
            sunposfinal = (utility_angles.SkyCoord2FisheyeUV(sunpos[0], sunpos[1]))
        else:
            coordsfinal = coords
            sunposfinal = sunpos

        # create file if not exists
        if not os.path.exists(xoptions["Filename"]):
            # create dirs if not exists
            if not os.path.exists(os.path.dirname(xoptions["Filename"])):
                os.makedirs(os.path.dirname(xoptions["Filename"]))
            # write header
            with open(xoptions["Filename"], "w") as file:
                for fidx in xoptions["Features"]:
                    feature = DialogExport.attributeFromIndex(fidx)
                    if feature == "Exposure":
                        if xoptions["IsHDR"]:
                            for j in range(0, len(common.Exposures)):
                                file.write("Exposure" + str(j+1) + delimiter)
                        else:
                            file.write("Exposure" + delimiter)
                    elif feature == "PixelColor":
                        if xoptions["IsHDR"]:
                            for j in range(0, len(common.Exposures)):
                                file.write("ColorA" + str(j+1) + delimiter + "ColorB" + str(j+1) + delimiter + "ColorC" + str(j+1) + delimiter)
                        else:
                            file.write("ColorA" + delimiter + "ColorB" + delimiter + "ColorC" + delimiter)
                    elif feature == "Radiance":
                        file.write(str(350))  # first wavelength, no delimiter
                        for w in range(350 + resolution, 2501, resolution):
                            file.write(delimiter + str(w))  # delimiter plus next wavelength
                    else:
                        file.write(feature)
                        file.write(delimiter)
                file.write("\n")
        # otherwise count existing samples
        else:
            with open(xoptions["Filename"], 'r') as file:
                reader = csv.reader(file, delimiter=',')
                next(reader, None) # skip header
                sampleidx = sum(1 for row in reader)

        # append export to existing file
        with open(xoptions["Filename"], "a") as file:
            # export each selected sample
            for i, sIdx in enumerate(self.wgtFisheye.samplesSelected):

                # export each required attribute
                # date
                file.write(str(self.capture.date()))
                file.write(delimiter)
                # time
                file.write(str(self.capture.time()))
                file.write(delimiter)
                # space
                file.write(str(coordsys.value))
                file.write(delimiter)

                # export each optional attribute
                for aIdx in xoptions["Features"]:
                    feature = common.SampleFeatures[aIdx][0]

                    # export sun azimuth
                    if feature == "SunAzimuth":
                        file.write('{0:07.04f}'.format(sunposfinal[0]))
                        file.write(delimiter)
                    # export sun altitude
                    elif feature == "SunAltitude":
                        file.write('{0:07.04f}'.format(sunposfinal[1]))
                        file.write(delimiter)
                    # export sky cover
                    elif feature == "SkyCover":
                        file.write(str(skycover.value))
                        file.write(delimiter)
                    # export index
                    elif feature == "SamplePatternIndex":
                        file.write(str(sIdx))
                        file.write(delimiter)
                    # export sample azimuth
                    elif feature == "SampleAzimuth":
                        file.write('{0:07.04f}'.format(coordsfinal[i][0]))
                        file.write(delimiter)
                    # export sample altitude
                    elif feature == "SampleAltitude":
                        file.write('{0:07.04f}'.format(coordsfinal[i][1]))
                        file.write(delimiter)
                    # export sun point/sample angle
                    elif feature == "SunPointAngle":
                        angle = utility_angles.CentralAngle(sunpos, coords[i])
                        angle = math.degrees(angle)
                        file.write('{0:07.03f}'.format(angle))
                        file.write(delimiter)
                    # export pixel neighborhood
                    elif (feature == "PixelRegion"):
                        file.write(str(pixregions[i]))
                        file.write(delimiter)
                    # export pixel weighting method
                    elif feature == "PixelWeighting":
                        file.write(str(pixweight.value))
                        file.write(delimiter)
                    # export pixel color model
                    elif feature == "ColorModel":
                        file.write(str(color.value))
                        file.write(delimiter)
                    # export photo exposure time(s)
                    elif feature == "Exposure":
                        for exp in exposures:
                            file.write(str(exp))
                            file.write(delimiter)
                    # export sample pixel color(s)
                    elif feature == "PixelColor":
                        for pixels in exppixels:
                            file.write(str(pixels[i][0]))  # color component 1
                            file.write(delimiter)
                            file.write(str(pixels[i][1]))  # color component 2
                            file.write(delimiter)
                            file.write(str(pixels[i][2]))  # color component 3
                            file.write(delimiter)
                    # export spectral radiance
                    elif feature == "Radiance":
                        xs, ys = utility_data.loadASDFile(self.captureTimeASDFiles[sIdx])
                        count = len(xs)
                        file.write(str(max(ys[0],0)))  # first wavelength, no delimiter
                        for j in range(resolution, count, resolution):
                            file.write(delimiter + str(max(ys[j],0)))  # delimiter plus next wavelength

                # next sample
                file.write("\n")
                sampleidx += 1

        self.log("Exported " + str(len(self.wgtFisheye.samplesSelected)) + " sample(s) of capture " + str(self.capture))

    def convertSamples(self):
        dialog = DialogConverter()
        code = dialog.exec()
        if (code != QDialog.Accepted):
            return

        self.log("Converting... ")

        # init
        fpath, fext = os.path.splitext(dialog.convertOptions["Filename"])
        fnamein = dialog.convertOptions["Filename"]
        fnameout = fpath + "_new" + fext
        numrows = 0
        pixregion = common.PixelRegionMin
        pixweight = common.PixelWeighting.Mean
        colormodel = common.ColorModel.RGB
        resolution = 1

        # open files
        with open(fnamein, 'r') as filein:
            with open(fnameout, 'w') as fileout:
                reader = csv.reader(filein, delimiter=",")
                writer = csv.writer(fileout, delimiter=",", lineterminator='\n')

                # read header
                header = next(reader, None)
                mapping = {header[i]: i for i in range(0, len(header))}

                # read first row for taste of current values
                firstrow = next(reader, None)

                # what pixel region to use?
                if "PixelRegion" in mapping:  # overwrite with value in file if exists
                    pixregion = firstrow[mapping["PixelRegion"]]
                if "PixelRegion" in dialog.convertOptions:  # overwrite with desired conversion
                    pixregion = dialog.convertOptions["PixelRegion"]

                # what pixel weighting to use?
                if "PixelWeighting" in mapping:  # overwrite with value in file if exists
                    pixweight = common.PixelWeighting(int(firstrow[mapping["PixelWeighting"]]))
                if "PixelWeighting" in dialog.convertOptions:  # overwrite with desired conversion
                    pixweight = common.PixelWeighting(dialog.convertOptions["PixelWeighting"])

                # what color model to use?
                if "ColorModel" in mapping:  # overwrite with value in file if exists
                    colormodel = common.ColorModel(int(firstrow[mapping["ColorModel"]]))
                if "ColorModel" in dialog.convertOptions:  # overwrite with desired conversion
                    colormodel = common.ColorModel(dialog.convertOptions["ColorModel"])

                # what spectrum resolution to use?
                prevrez = int(((2500-350)+1) / (len(header) - mapping["350"]))
                if "SpectrumResolution" not in dialog.convertOptions:  # use same resolution
                    resolution = prevrez
                else:  # overwrite with desired conversion
                    resolution = dialog.convertOptions["SpectrumResolution"]

                # reset read file
                filein.seek(0)
                next(reader, None)  # skip header

                # init
                currtime = datetime.min
                currHDRfile = ''
                currexposure = 0
                currcoords = []
                currrows = []
                # TODO: this is hardcoded to our sampling pattern. compute it properly!!
                altitudeRegionMap = {90: 1, 71.9187: 3, 53.3665: 5, 33.749: 7, 12.1151: 9}

                # write header
                if resolution == prevrez:
                    writer.writerow(header)  # use exact same header
                else:  # write new header to account for different spectrum resolution
                    newheader = []
                    newheader.extend(header[0:mapping["350"]])
                    for w in range(350, 2501, resolution):
                        newheader.append(str(w))
                    writer.writerow(newheader)

                # read and write rows
                for row in reader:
                    # is this row a new capture timestamp of samples?
                    ts = datetime.strptime(row[mapping["Date"]] + " " + row[mapping["Time"]], "%Y-%m-%d %H:%M:%S")
                    exp = float(row[mapping["Exposure"]])
                    if ts != currtime or exp != currexposure:
                        # if so, flush our cached rows read so far
                        if os.path.exists(currHDRfile):
                            if dialog.convertOptions["ComputePixelRegion"]:
                                pixregions = [altitudeRegionMap[c[1]] for c in currcoords]
                            else:
                                pixregions = [pixregion for i in range(0, len(currcoords))]
                            points = utility_data.computePointsInImage(currHDRfile, currcoords)
                            pixels = utility_data.collectPixels(points, pixregions, file=currHDRfile, weighting=pixweight)
                            if colormodel == common.ColorModel.HSV:
                                for i, p in enumerate(pixels):
                                    rgb = sRGBColor(p[0], p[1], p[2], is_upscaled=True)
                                    hsv = convert_color(rgb, HSVColor)
                                    pixels[i] = hsv.get_value_tuple()
                            elif colormodel == common.ColorModel.LAB:
                                for i, p in enumerate(pixels):
                                    for i, p in enumerate(pixels):
                                        rgb = sRGBColor(p[0], p[1], p[2], is_upscaled=True)
                                        lab = convert_color(rgb, LabColor)
                                        pixels[i] = lab.get_value_tuple()
                            # update cached row with new values and write to convert file
                            for i in range(0, len(currrows)):
                                # update
                                currrows[i][mapping["PixelRegion"]] = pixregions[i]
                                currrows[i][mapping["PixelWeighting"]] = pixweight.value
                                currrows[i][mapping["ColorModel"]] = colormodel.value
                                currrows[i][mapping["ColorA"]] = pixels[i][0]
                                currrows[i][mapping["ColorB"]] = pixels[i][1]
                                currrows[i][mapping["ColorC"]] = pixels[i][2]
                                # write
                                writer.writerow(currrows[i])
                                numrows += 1
                        # get ready for a new capture timestamp of samples that this row kicked off
                        currtime = ts
                        currexposure = exp
                        currHDRfile = utility_data.findHDRFile(common.AppSettings["DataDirectory"], currtime, currexposure)
                        currrows = []
                        currcoords = []

                    # collect sample coordinate
                    currcoords.append((float(row[mapping["SampleAzimuth"]]), float(row[mapping["SampleAltitude"]])))

                    # collect sample row to be written
                    if resolution == prevrez:
                        currrows.append(row)
                    else:
                        newrow = []
                        newrow.extend(row[0:mapping["350"]])
                        currASDfile = utility_data.findASDFile(common.AppSettings["DataDirectory"], currtime, int(row[mapping["SamplePatternIndex"]]))
                        ws, rs = utility_data.loadASDFile(currASDfile, resolution)
                        rs[:] = [max(r, 0) for r in rs]
                        newrow.extend(rs)
                        currrows.append(newrow)

                # flush any remaining cached rows
                if len(currrows) > 0 and os.path.exists(currHDRfile):
                    if dialog.convertOptions["ComputePixelRegion"]:
                        pixregions = [altitudeRegionMap[c[1]] for c in currcoords]
                    else:
                        pixregions = [pixregion for i in range(0, len(currcoords))]
                    points = utility_data.computePointsInImage(currHDRfile, currcoords)
                    pixels = utility_data.collectPixels(points, pixregions, file=currHDRfile, weighting=pixweight)
                    if colormodel == common.ColorModel.HSV:
                        for i, p in enumerate(pixels):
                            rgb = sRGBColor(p[0], p[1], p[2], is_upscaled=True)
                            hsv = convert_color(rgb, HSVColor)
                            pixels[i] = hsv.get_value_tuple()
                    elif colormodel == common.ColorModel.LAB:
                        for i, p in enumerate(pixels):
                            for i, p in enumerate(pixels):
                                rgb = sRGBColor(p[0], p[1], p[2], is_upscaled=True)
                                lab = convert_color(rgb, LabColor)
                                pixels[i] = lab.get_value_tuple()
                    # update cached row with new values and write to convert file
                    for i in range(0, len(currrows)):
                        # update
                        currrows[i][mapping["PixelRegion"]] = pixregions[i]
                        currrows[i][mapping["PixelWeighting"]] = pixweight.value
                        currrows[i][mapping["ColorModel"]] = colormodel.value
                        currrows[i][mapping["ColorA"]] = pixels[i][0]
                        currrows[i][mapping["ColorB"]] = pixels[i][1]
                        currrows[i][mapping["ColorC"]] = pixels[i][2]
                        # write
                        writer.writerow(currrows[i])
                        numrows += 1

        self.log("Converted " + str(numrows) + " sample(s)")

    def setupExportFile(self):
        dialog = DialogExport(common.AppSettings["ExportOptions"])
        code = dialog.exec()
        if code != QDialog.Accepted:
            return

        # save the export options in app settings
        common.AppSettings.update({"ExportOptions": dialog.exportOptions})

        # now that export options are configured, enable export commands
        self.actExportSelected.setEnabled(True)

    def triggerContextMenu(self, widget, event):
        if widget == self.wgtFisheye:
            menuCtx = QMenu(self)
            menuCtx.addAction(self.actHUD)
            menuCtx.addAction(self.actMask)
            menuCtx.addAction(self.actCompass)
            menuCtx.addAction(self.actLensWarp)
            menuCtx.addAction(self.actSunPath)
            menuCtx.addAction(self.actSamples)
            menuCtx.addAction(self.actShadows)
            menuCtx.addAction(self.actUVGrid)
            menuCtx.addAction(self.actGraphRes)
            menuCtx.addAction(self.actGraphLine)
            menuCtx.addSeparator()
            menuCtx.addAction(self.actSelectAll)
            menuCtx.addAction(self.actSelectInv)
            menuCtx.addAction(self.actClearAll)
            menuCtx.addAction(self.actAvoidSun)
            menuCtx.addSeparator()
            menuCtx.addAction(self.actExportSelected)
            menuCtx.exec_(widget.mapToGlobal(event.pos()))

    def toggleEXIFPanel(self, state):
        if state:
            self.splitHoriz.setSizes([self.width() * 0.75, self.width() * 0.25])
        else:
            left, right = self.splitHoriz.sizes()
            self.splitHoriz.setSizes([left + right, 0])

    def toggleStatusBar(self, state):
        if state:
            self.statusBar().show()
            #self.centralWidget().layout().setContentsMargins(10,10,10,0)
        else:
            self.statusBar().hide()
            #self.centralWidget().layout().setContentsMargins(10,10,10,10)

    def toggleHUDView(self, action):
        state = action.isChecked()

        if action == self.actHUD:
            common.AppSettings["ShowHUD"] = state
            self.actUVGrid.setEnabled(state)
            self.actCompass.setEnabled(state)
            self.actSunPath.setEnabled(state)
            self.actSamples.setEnabled(state)
            self.actShadows.setEnabled(state)
        elif action == self.actMask:
            common.AppSettings["ShowMask"] = state
        elif action == self.actUVGrid:
            common.AppSettings["ShowUVGrid"] = state
        elif action == self.actCompass:
            common.AppSettings["ShowCompass"] = state
        elif action == self.actLensWarp:
            common.AppSettings["ShowLensWarp"] = state
        elif action == self.actSunPath:
            common.AppSettings["ShowSunPath"] = state
        elif action == self.actSamples:
            common.AppSettings["ShowSamples"] = state
        elif action == self.actShadows:
            common.AppSettings["ShowShadows"] = state

        self.wgtFisheye.repaint()

    def togglePixelOptions(self, action):
        # pixel region
        if action == self.actPixelRegion:
            region = common.PixelRegionMin  # n for (n x n) pixel region
            ok = True
            region, ok = QInputDialog.getInt(self, "Pixel Region", "Input n for (n x n) region:", 5, common.PixelRegionMin, common.PixelRegionMax, 2, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
            if not ok or region % 2 == 0:
                QMessageBox.warning(self, "Input Validation", "Pixel Region must be an odd positive number.", QMessageBox.Ok)
                return
            common.AppSettings["PixelRegion"] = region

        # pixel weighting
        elif action == self.actPixelMean or action == self.actPixelMedian or action == self.actPixelGaussian:
            if action == self.actPixelMean:
                common.AppSettings["PixelWeighting"] = common.PixelWeighting.Mean.value
            elif action == self.actPixelMedian:
                common.AppSettings["PixelWeighting"] = common.PixelWeighting.Median.value
            elif action == self.actPixelGaussian:
                common.AppSettings["PixelWeighting"] = common.PixelWeighting.Gaussian.value

    def toggleGraphOptions(self, action):
        ok = True
        value = 0
        if action == self.actGraphRes:
            value, ok = QInputDialog.getInt(self, "Radiance Graph Resolution", "Plot every (nm):", 1, 1, 50, 1, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
            if ok and value > 0 and value <= 50:
                common.AppSettings["GraphResolution"] = value
                self.graphSamples(self.wgtFisheye.samplesSelected)
            else:
                QMessageBox.warning(self, "Input Validation", "Radiance graph resolution must be 1-50(nm).", QMessageBox.Ok)
        elif action == self.actGraphLine:
            value, ok = QInputDialog.getInt(self, "Radiance Graph Line Thickness", "Thickness:", 1, 1, 5, 1, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
            if ok and value > 0 and value <= 5:
                common.AppSettings["GraphLineThickness"] = value
                self.graphSamples(self.wgtFisheye.samplesSelected)
            else:
                QMessageBox.warning(self, "Input Validation", "Radiance graph line thickness must be between 1-5.", QMessageBox.Ok)

    def toggleAvoidSun(self):
        angle = 0
        ok = True
        angle, ok = QInputDialog.getInt(self, "Circumsolar Avoidance", "Angle around sun:", 20, 0, 180, 1, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        if ok and angle >= 0 and angle <= 180:
            common.AppSettings["AvoidSunAngle"] = angle
            #self.wgtFisheye.repaint()
        else:
            QMessageBox.warning(self, "Input Validation", "Circumsolar angle must be 0-180°.", QMessageBox.Ok)

    def toggleHUDTextScale(self):
        dialog = DialogSlider(self, "HUD Text Scale", "Select scale:", common.AppSettings["HUDTextScale"], common.HUDTextScaleMin, common.HUDTextScaleMax, 2)
        dialog.slider.valueChanged.connect(lambda: self.textScaleChanged(dialog.slider.value()))
        dialog.show()
        #self.slider.valueChanged.connect(self.timeSelected)

    def textScaleChanged(self, value):
        common.AppSettings["HUDTextScale"] = value
        self.wgtFisheye.computeBounds()
        self.wgtFisheye.repaint()

    def toggleDontSave(self, state):
        self.dontSaveSettings = state

    def toggleAbout(self, state):
        self.dontSaveSettings = state

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

        if self.dontSaveSettings:
            return

        # cache settings
        common.AppSettings["WindowWidth"] = self.width()
        common.AppSettings["WindowHeight"] = self.height()
        left, right = self.splitHoriz.sizes()
        common.AppSettings["HorizSplitLeft"] = left
        common.AppSettings["HorizSplitRight"] = right
        top, bottom = self.splitVert.sizes()
        common.AppSettings["VertSplitTop"] = top
        common.AppSettings["VertSplitBottom"] = bottom
        common.AppSettings["ShowEXIF"] = self.actEXIF.isChecked()
        common.AppSettings["ShowStatusBar"] = self.actStatusBar.isChecked()

        # dump settings to file
        with open(common.AppSettings["Filename"], 'w') as file:
            json.dump(common.AppSettings, file, indent=4)

    def log(self, message):
        self.statusBar().showMessage(message)
        print(message)
        #QMessageBox.critical(self, "Error", message, QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = SkyDataViewer()
    w.center()
    w.show()

    status = app.exec_()
    sys.exit(status)
