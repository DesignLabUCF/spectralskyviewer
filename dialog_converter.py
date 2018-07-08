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
# @since: 03/20/2018
# @summary: Dialog for converting (importing/exporting) sky data.
# ====================================================================
import os
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import common


class DialogConverter(QDialog):

    def __init__(self):
        super().__init__(None, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        # convert options - will be filled in with desired conversions
        self.convertOptions = {}

        # init
        self.initWidgets()
        self.setWindowTitle("Converter Options")
        self.setWindowIcon(QIcon('res/icon.png'))

    def initWidgets(self):
        # layout
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        # layout.setSizeConstraint(QLayout.SetFixedSize)

        # file
        lblFile = QLabel("Sample Dataset to Convert:")
        self.txtFile = QLineEdit()
        self.txtFile.setMinimumWidth(400)
        #self.txtFile.setText(self.exportOptions["Filename"])
        btnFile = QPushButton("...")
        btnFile.setMaximumWidth(btnFile.fontMetrics().boundingRect("   ...   ").width())
        btnFile.clicked.connect(self.browseForFile)
        boxFile = QGridLayout()
        boxFile.setContentsMargins(0, 0, 0, 0)
        boxFile.addWidget(lblFile, 0, 0, 1, 2)
        boxFile.addWidget(self.txtFile, 1, 0, 1, 1)
        boxFile.addWidget(btnFile, 1, 1, 1, 1)
        pnlFile = QWidget()
        pnlFile.setLayout(boxFile)
        layout.addWidget(pnlFile, 0, Qt.AlignTop)

        # hdr
        self.radHDRNo = QRadioButton("No")
        self.radHDRYes = QRadioButton("Yes")
        boxHDR = QHBoxLayout()
        boxHDR.addWidget(self.radHDRNo)
        boxHDR.addWidget(self.radHDRYes)
        grpHDR = QGroupBox("HDR (multiple exposures)", self)
        grpHDR.setLayout(boxHDR)
        layout.addWidget(grpHDR, 0, Qt.AlignTop)

        # attributes
        self.lstAttributes = QListView()
        model = QStandardItemModel()
        model.itemChanged.connect(self.attributeSelected)
        # pixel region
        self.itmPixelRegion = QStandardItem(common.ExportAttributes[common.ExportIdxMap["PixelRegion"]][1])
        self.itmPixelRegion.setEditable(False)
        self.itmPixelRegion.setCheckable(True)
        model.appendRow(self.itmPixelRegion)
        # pixel weighting
        self.itmPixelWeighting = QStandardItem(common.ExportAttributes[common.ExportIdxMap["PixelWeighting"]][1])
        self.itmPixelWeighting.setEditable(False)
        self.itmPixelWeighting.setCheckable(True)
        model.appendRow(self.itmPixelWeighting)
        # pixel exposure
        self.itmExposure = QStandardItem(common.ExportAttributes[common.ExportIdxMap["Exposure"]][1])
        self.itmExposure.setEditable(False)
        self.itmExposure.setCheckable(True)
        model.appendRow(self.itmExposure)
        self.lstAttributes.setModel(model)
        boxAttr = QVBoxLayout()
        boxAttr.addWidget(self.lstAttributes)
        grpAttr = QGroupBox("Attributes To Convert:", self)
        grpAttr.setLayout(boxAttr)
        layout.addWidget(grpAttr, 1)

        # pixel region
        self.cbxPixelRegion = QComboBox()
        self.cbxPixelRegion.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        #self.cbxPixelRegion.currentIndexChanged.connect(self.pixelRegionEntered)
        self.cbxPixelRegion.addItems([str(x) for x in range(common.PixelRegionMin, common.PixelRegionMax+1, 2)])
        self.cbxPixelRegion.setEnabled(False)
        boxPixelRegion = QHBoxLayout()
        boxPixelRegion.addWidget(self.cbxPixelRegion)
        grpPixelRegion = QGroupBox("(n x n) Pixel Region:", self)
        grpPixelRegion.setLayout(boxPixelRegion)
        layout.addWidget(grpPixelRegion, 0, Qt.AlignTop)

        # pixel weighting
        self.radPixelMean = QRadioButton("Mean")
        self.radPixelMean.setEnabled(False)
        self.radPixelMedian = QRadioButton("Median")
        self.radPixelMedian.setEnabled(False)
        self.radPixelGaussian = QRadioButton("Gaussian")
        self.radPixelGaussian.setEnabled(False)
        boxPixelWeighting = QHBoxLayout()
        boxPixelWeighting.addWidget(self.radPixelMean)
        boxPixelWeighting.addWidget(self.radPixelMedian)
        boxPixelWeighting.addWidget(self.radPixelGaussian)
        grpPixelWeighting = QGroupBox("Pixel Weighting:", self)
        grpPixelWeighting.setLayout(boxPixelWeighting)
        layout.addWidget(grpPixelWeighting, 0, Qt.AlignTop)

        # exposure
        self.cbxExposure = QComboBox()
        self.cbxExposure.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # self.cbxExposure.currentIndexChanged.connect(self.pixelRegionEntered)
        self.cbxExposure.addItems([str(x) for x in common.Exposures])
        self.cbxExposure.setEnabled(False)
        boxExposure = QHBoxLayout()
        boxExposure.addWidget(self.cbxExposure)
        grpExposure = QGroupBox("Photo Exposure:", self)
        grpExposure.setLayout(boxExposure)
        layout.addWidget(grpExposure, 0, Qt.AlignTop)

        # accept/decline buttons
        boxButtons = QDialogButtonBox()
        btn = boxButtons.addButton("Cancel", QDialogButtonBox.RejectRole)
        btn.clicked.connect(self.reject)
        btn = boxButtons.addButton("Convert!", QDialogButtonBox.AcceptRole)
        btn.clicked.connect(self.convertPressed)
        layout.addWidget(boxButtons, 0, Qt.AlignBottom | Qt.AlignRight)

        self.setLayout(layout)

    def browseForFile(self):
        filename, filetype = QFileDialog.getOpenFileName(self, 'Select Sample Dataset', '')
        if filename is None or len(filename) <= 0:
            return

        self.txtFile.setText(filename)

    def attributeSelected(self, item):
        enabled = False
        if item.checkState() > 0:
            enabled = True

        if item == self.itmPixelRegion:
            self.cbxPixelRegion.setEnabled(enabled)
        elif item == self.itmPixelWeighting:
            self.radPixelMean.setEnabled(enabled)
            self.radPixelMedian.setEnabled(enabled)
            self.radPixelGaussian.setEnabled(enabled)
        elif item == self.itmExposure:
            self.cbxExposure.setEnabled(enabled)

    def convertPressed(self):
        # validate dataset before proceeding
        if self.txtFile.text() == None or len(self.txtFile.text()) <= 0:
            QMessageBox.critical(self, "Error", "Invalid sample dataset filename!", QMessageBox.Ok)
            return
        if not os.path.exists(self.txtFile.text()):
            QMessageBox.critical(self, "Error", "Sample dataset file not found!", QMessageBox.Ok)
            return

        # save convert filename
        self.convertOptions["Filename"] = self.txtFile.text()

        # save hdr
        self.convertOptions["IsHDR"] = self.radHDRYes.isChecked()

        # save pixel region
        self.convertOptions["PixelRegion"] = int(self.cbxPixelRegion.currentText())

        # save pixel weighting
        if (self.radPixelMean.isChecked()):
            self.convertOptions["PixelWeighting"] = common.PixelWeighting.Mean.value
        elif (self.radPixelMedian.isChecked()):
            self.convertOptions["PixelWeighting"] = common.PixelWeighting.Median.value
        elif (self.radPixelGaussian.isChecked()):
            self.convertOptions["PixelWeighting"] = common.PixelWeighting.Gaussian.value

        # save pixel region
        self.convertOptions["Exposure"] = float(self.cbxExposure.currentText())

        self.accept()
