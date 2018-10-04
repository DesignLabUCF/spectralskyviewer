#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 11/16/2017
# @summary: Dialog for exporting sky data.
# ====================================================================
import os
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel, QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import common


class DialogExport(QDialog):

    @staticmethod
    def validateOptions(options):
        # must have all available options defined
        # ok to have extras, but must have the at least the default set
        for key in common.DefExportOptions:
            if (key not in options):
                return False
        return True

    @staticmethod
    def attributeFromIndex(index):
        return common.SampleFeatures[index][0]

    def __init__(self, options=None):
        super().__init__(None, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        # initial export options are either specified or set from defaults
        if options != None and DialogExport.validateOptions(options):
            self.exportOptions = dict(options)
        else:
            self.exportOptions = dict(common.DefExportOptions)

        # init
        self.initWidgets()
        self.setWindowTitle("Sample Export Options")
        self.setWindowIcon(QIcon('res/icon.png'))
        if self.exportOptions["Delimiter"] == "\t":
            self.radTab.setChecked(True)
        elif self.exportOptions["Delimiter"] == " ":
            self.radSpace.setChecked(True)
        else:
            self.radCSV.setChecked(True)
        for i in range(0, self.cbxPixRegFixed.count()):
            if int(self.cbxPixRegFixed.itemText(i)) == self.exportOptions["PixelRegion"]:
                self.cbxPixRegFixed.setCurrentIndex(i)
        pw = common.PixelWeighting(self.exportOptions["PixelWeighting"])
        if pw == common.PixelWeighting.Mean:
            self.radPixelMean.setChecked(True)
        elif pw == common.PixelWeighting.Median:
            self.radPixelMedian.setChecked(True)
        elif pw == common.PixelWeighting.Gaussian:
            self.radPixelGaussian.setChecked(True)
        self.chxPixRegCalc.setChecked(self.exportOptions["ComputePixelRegion"])
        self.cbxPixRegFixed.setEnabled(not self.exportOptions["ComputePixelRegion"])
        self.chxHDR.setChecked(self.exportOptions["IsHDR"])
        self.txtResolution.setText(str(self.exportOptions["SpectrumResolution"]))

    def initWidgets(self):
        # layout
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        # layout.setSizeConstraint(QLayout.SetFixedSize)

        # file
        lblFile = QLabel("Export Samples To:")
        self.txtFile = QLineEdit()
        self.txtFile.setMinimumWidth(400)
        self.txtFile.setText(self.exportOptions["Filename"])
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

        # file format
        self.radCSV = QRadioButton("CSV")
        self.radCSV.clicked.connect(lambda: self.formatPressed(self.radCSV))
        self.radTab = QRadioButton("Tab")
        self.radTab.clicked.connect(lambda: self.formatPressed(self.radTab))
        self.radSpace = QRadioButton("Space")
        self.radSpace.clicked.connect(lambda: self.formatPressed(self.radSpace))
        boxFormat = QHBoxLayout()
        boxFormat.addWidget(self.radCSV)
        boxFormat.addWidget(self.radTab)
        boxFormat.addWidget(self.radSpace)
        grpFormat = QGroupBox("File Format:", self)
        grpFormat.setLayout(boxFormat)
        layout.addWidget(grpFormat, 0, Qt.AlignTop)

        # pixel region
        self.chxPixRegCalc = QCheckBox()
        self.chxPixRegCalc.stateChanged.connect(self.pixRegCalcChanged)
        lblPixRegCalc = QLabel("compute")
        self.cbxPixRegFixed = QComboBox()
        self.cbxPixRegFixed.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # self.cbxPixelRegion.currentIndexChanged.connect(self.pixelRegionEntered)
        self.cbxPixRegFixed.addItems([str(x) for x in range(common.PixelRegionMin, common.PixelRegionMax + 1, 2)])
        lblPixRegFixed = QLabel("fixed")
        boxPixelRegion = QHBoxLayout()
        boxPixelRegion.addWidget(self.chxPixRegCalc)
        boxPixelRegion.addWidget(lblPixRegCalc)
        boxPixelRegion.addWidget(self.cbxPixRegFixed)
        boxPixelRegion.addWidget(lblPixRegFixed)
        grpPixelRegion = QGroupBox("Pixel Region:", self)
        grpPixelRegion.setLayout(boxPixelRegion)

        # pixel weighting
        self.radPixelMean = QRadioButton("Mean")
        self.radPixelMedian = QRadioButton("Median")
        self.radPixelGaussian = QRadioButton("Gaussian")
        boxPixelWeighting = QHBoxLayout()
        boxPixelWeighting.addWidget(self.radPixelMean)
        boxPixelWeighting.addWidget(self.radPixelMedian)
        boxPixelWeighting.addWidget(self.radPixelGaussian)
        grpPixelWeighting = QGroupBox("Pixel Weighting:", self)
        grpPixelWeighting.setLayout(boxPixelWeighting)

        # add all pixel options to window
        boxPixelOptions = QHBoxLayout()
        boxPixelOptions.addWidget(grpPixelRegion, 0, Qt.AlignLeft)
        boxPixelOptions.addWidget(grpPixelWeighting, 1)
        boxPixelOptions.setContentsMargins(0,0,0,0)
        pnlPixelOptions = QWidget()
        pnlPixelOptions.setLayout(boxPixelOptions)
        layout.addWidget(pnlPixelOptions, 0, Qt.AlignTop)

        # HDR
        self.chxHDR = QCheckBox()
        boxHDR = QHBoxLayout()
        boxHDR.addWidget(self.chxHDR)
        grpHDR = QGroupBox("HDR", self)
        grpHDR.setLayout(boxHDR)

        # color model
        self.cbxColorModel = QComboBox()
        self.cbxColorModel.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cbxColorModel.addItems([str(cm.name) for cm in common.ColorModel])
        boxColor = QHBoxLayout()
        boxColor.addWidget(self.cbxColorModel)
        grpColor = QGroupBox("Color Model:", self)
        grpColor.setLayout(boxColor)

        # spectrum resolution
        self.txtResolution = QLineEdit()
        self.txtResolution.setValidator(QIntValidator(1, 100))
        lblResolution = QLabel("(nm)")
        boxResolution = QHBoxLayout()
        boxResolution.addWidget(self.txtResolution)
        boxResolution.addWidget(lblResolution, 0, Qt.AlignRight)
        grpResolution = QGroupBox("Spectrum Resolution:", self)
        grpResolution.setLayout(boxResolution)

        # add final row of options
        boxStuffOptions = QHBoxLayout()
        boxStuffOptions.addWidget(grpHDR)
        boxStuffOptions.addWidget(grpColor)
        boxStuffOptions.addWidget(grpResolution, 1)
        boxStuffOptions.setContentsMargins(0, 0, 0, 0)
        pnlStuffOptions = QWidget()
        pnlStuffOptions.setLayout(boxStuffOptions)
        layout.addWidget(pnlStuffOptions, 0, Qt.AlignTop)

        # sample features
        self.lstSampleFeatures = QListView()
        model = QStandardItemModel()
        # optional attributes
        for i in range(0, len(common.SampleFeatures)):
            item = QStandardItem(common.SampleFeatures[i][1])
            item.setEditable(False)
            item.setCheckable(True)
            # id, date, time - are required
            if i <= 1:
                item.setCheckState(Qt.Checked)
                item.setEnabled(False)
            # everything else is optional
            elif i in self.exportOptions["Features"]:
                item.setCheckState(Qt.Checked)
            model.appendRow(item)
        self.lstSampleFeatures.setModel(model)
        boxFeatures = QVBoxLayout()
        boxFeatures.addWidget(self.lstSampleFeatures)
        grpAttr = QGroupBox("Sample Features:", self)
        grpAttr.setLayout(boxFeatures)
        layout.addWidget(grpAttr, 1)

        # accept/decline buttons
        boxButtons = QDialogButtonBox()
        btn = boxButtons.addButton("Cancel", QDialogButtonBox.RejectRole)
        btn.clicked.connect(self.reject)
        btn = boxButtons.addButton("Save", QDialogButtonBox.AcceptRole)
        btn.clicked.connect(self.savePressed)
        layout.addWidget(boxButtons, 0, Qt.AlignBottom | Qt.AlignRight)

        self.setLayout(layout)

    def browseForFile(self):
        filename, filetype = QFileDialog.getSaveFileName(self, 'Select Export File', '')
        if filename is None or len(filename) <= 0:
            return

        # apply default extension, if missing
        base, extension = os.path.splitext(filename)
        if extension is None or len(extension) <= 0:
            if self.radCSV.isChecked():
                extension = ".csv"
            else:
                extension = ".txt"
        self.txtFile.setText(base + extension)

    def formatPressed(self, button):
        if self.txtFile.text() is None or len(self.txtFile.text()) <= 0:
            return

        # updated extension when format selected
        base, extension = os.path.splitext(self.txtFile.text())
        if button == self.radCSV:
            extension = ".csv"
        else:
            extension = ".txt"
        self.txtFile.setText(base + extension)

    def pixRegCalcChanged(self, int):
        if (self.chxPixRegCalc.isChecked()):
            self.cbxPixRegFixed.setEnabled(False)
        else:
            self.cbxPixRegFixed.setEnabled(True)

    def savePressed(self):
        # validate the export before proceeding
        if self.txtFile.text() == None or len(self.txtFile.text()) <= 0:
            QMessageBox.critical(self, "Error", "Invalid export filename!", QMessageBox.Ok)
            return
        if os.path.exists(self.txtFile.text()):
            if QMessageBox.warning(self, "Warning", "Exported samples will be appended to existing file.\nAre you sure you want to do this?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return

        # save export file
        self.exportOptions["Filename"] = self.txtFile.text()
        if self.radCSV.isChecked():     self.exportOptions["Delimiter"] = ","
        elif self.radTab.isChecked():   self.exportOptions["Delimiter"] = "\t"
        elif self.radSpace.isChecked(): self.exportOptions["Delimiter"] = " "

        # save pixel options
        self.exportOptions["ComputePixelRegion"] = self.chxPixRegCalc.isChecked()
        self.exportOptions["PixelRegion"]     = int(self.cbxPixRegFixed.currentText())
        if self.radPixelMean.isChecked():       self.exportOptions["PixelWeighting"] = common.PixelWeighting.Mean.value
        elif self.radPixelMedian.isChecked():   self.exportOptions["PixelWeighting"] = common.PixelWeighting.Median.value
        elif self.radPixelGaussian.isChecked(): self.exportOptions["PixelWeighting"] = common.PixelWeighting.Gaussian.value

        # save other options
        self.exportOptions["IsHDR"] = self.chxHDR.isChecked()
        self.exportOptions["ColorModel"] = common.ColorModel[self.cbxColorModel.currentText()].value
        self.exportOptions["SpectrumResolution"] = int(self.txtResolution.text())

        # save selected sample features
        attributes = []
        for i in range(0, self.lstSampleFeatures.model().rowCount()):
            item = self.lstSampleFeatures.model().item(i)
            if item.checkState() != Qt.Unchecked:
                attributes.append(i)
        self.exportOptions.update({"Features": attributes})

        self.accept()
