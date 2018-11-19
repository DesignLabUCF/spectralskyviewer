#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 09/25/2018
# @summary: About dialog.
# ====================================================================
import os
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import common


class DialogAbout(QDialog):

    def __init__(self):
        super().__init__(None, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        # init
        self.initWidgets()
        self.setWindowTitle("About SpectralSkyViewer")
        self.setWindowIcon(QIcon('res/icon.png'))

    def initWidgets(self):
        # layout
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        # layout.setSizeConstraint(QLayout.SetFixedSize)

        # # file
        # lblFile = QLabel("Sample Dataset to Convert:")
        # self.txtFile = QLineEdit()
        # self.txtFile.setMinimumWidth(400)
        # #self.txtFile.setText(self.exportOptions["Filename"])
        # btnFile = QPushButton("...")
        # btnFile.setMaximumWidth(btnFile.fontMetrics().boundingRect("   ...   ").width())
        # btnFile.clicked.connect(self.browseForFile)
        # boxFile = QGridLayout()
        # boxFile.setContentsMargins(0, 0, 0, 0)
        # boxFile.addWidget(lblFile, 0, 0, 1, 2)
        # boxFile.addWidget(self.txtFile, 1, 0, 1, 1)
        # boxFile.addWidget(btnFile, 1, 1, 1, 1)
        # pnlFile = QWidget()
        # pnlFile.setLayout(boxFile)
        # layout.addWidget(pnlFile, 0, Qt.AlignTop)
        #
        # # hdr
        # self.radHDRNo = QRadioButton("No")
        # self.radHDRYes = QRadioButton("Yes")
        # boxHDR = QHBoxLayout()
        # boxHDR.addWidget(self.radHDRNo)
        # boxHDR.addWidget(self.radHDRYes)
        # grpHDR = QGroupBox("HDR (multiple exposures)", self)
        # grpHDR.setLayout(boxHDR)
        # layout.addWidget(grpHDR, 0, Qt.AlignTop)
        #
        # # attributes
        # self.lstSampleFeatures = QListView()
        # model = QStandardItemModel()
        # model.itemChanged.connect(self.attributeSelected)
        # # pixel region
        # self.itmPixelRegion = QStandardItem(common.SampleFeatures[common.SampleFeatureIdxMap["PixelRegion"]][1])
        # self.itmPixelRegion.setEditable(False)
        # self.itmPixelRegion.setCheckable(True)
        # model.appendRow(self.itmPixelRegion)
        # # pixel weighting
        # self.itmPixelWeighting = QStandardItem(common.SampleFeatures[common.SampleFeatureIdxMap["PixelWeighting"]][1])
        # self.itmPixelWeighting.setEditable(False)
        # self.itmPixelWeighting.setCheckable(True)
        # model.appendRow(self.itmPixelWeighting)
        # # pixel exposure
        # self.itmExposure = QStandardItem(common.SampleFeatures[common.SampleFeatureIdxMap["Exposure"]][1])
        # self.itmExposure.setEditable(False)
        # self.itmExposure.setCheckable(True)
        # model.appendRow(self.itmExposure)
        # self.lstSampleFeatures.setModel(model)
        # boxAttr = QVBoxLayout()
        # boxAttr.addWidget(self.lstSampleFeatures)
        # grpAttr = QGroupBox("Attributes To Convert:", self)
        # grpAttr.setLayout(boxAttr)
        # layout.addWidget(grpAttr, 1)
        #
        # # pixel region
        # self.cbxPixelRegion = QComboBox()
        # self.cbxPixelRegion.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # #self.cbxPixelRegion.currentIndexChanged.connect(self.pixelRegionEntered)
        # self.cbxPixelRegion.addItems([str(x) for x in range(common.PixelRegionMin, common.PixelRegionMax+1, 2)])
        # self.cbxPixelRegion.setEnabled(False)
        # boxPixelRegion = QHBoxLayout()
        # boxPixelRegion.addWidget(self.cbxPixelRegion)
        # grpPixelRegion = QGroupBox("(n x n) Pixel Region:", self)
        # grpPixelRegion.setLayout(boxPixelRegion)
        # layout.addWidget(grpPixelRegion, 0, Qt.AlignTop)
        #
        # # pixel weighting
        # self.radPixelMean = QRadioButton("Mean")
        # self.radPixelMean.setEnabled(False)
        # self.radPixelMedian = QRadioButton("Median")
        # self.radPixelMedian.setEnabled(False)
        # self.radPixelGaussian = QRadioButton("Gaussian")
        # self.radPixelGaussian.setEnabled(False)
        # boxPixelWeighting = QHBoxLayout()
        # boxPixelWeighting.addWidget(self.radPixelMean)
        # boxPixelWeighting.addWidget(self.radPixelMedian)
        # boxPixelWeighting.addWidget(self.radPixelGaussian)
        # grpPixelWeighting = QGroupBox("Pixel Weighting:", self)
        # grpPixelWeighting.setLayout(boxPixelWeighting)
        # layout.addWidget(grpPixelWeighting, 0, Qt.AlignTop)
        #
        # # exposure
        # self.cbxExposure = QComboBox()
        # self.cbxExposure.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # # self.cbxExposure.currentIndexChanged.connect(self.pixelRegionEntered)
        # self.cbxExposure.addItems([str(x) for x in common.Exposures])
        # self.cbxExposure.setEnabled(False)
        # boxExposure = QHBoxLayout()
        # boxExposure.addWidget(self.cbxExposure)
        # grpExposure = QGroupBox("Photo Exposure:", self)
        # grpExposure.setLayout(boxExposure)
        # layout.addWidget(grpExposure, 0, Qt.AlignTop)

        # accept/decline buttons
        boxButtons = QDialogButtonBox()
        btn = boxButtons.addButton("Close", QDialogButtonBox.AcceptRole)
        #btn.clicked.connect(self.convertPressed)
        layout.addWidget(boxButtons, 0, Qt.AlignBottom | Qt.AlignRight)

        self.setLayout(layout)
