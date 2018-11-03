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
        self.chxHDR.setChecked(self.exportOptions["IsHDR"])
        self.cbxColorModel.setCurrentText(common.ColorModel(self.exportOptions["ColorModel"]).name)
        self.chxPixRegCalc.setChecked(self.exportOptions["ComputePixelRegion"])
        self.cbxPixRegFixed.setEnabled(not self.exportOptions["ComputePixelRegion"])
        for i in range(0, self.cbxPixRegFixed.count()):
            if int(self.cbxPixRegFixed.itemText(i)) == self.exportOptions["PixelRegion"]:
                self.cbxPixRegFixed.setCurrentIndex(i)
                break
        self.cbxPixelWeighting.setCurrentText(common.PixelWeighting(self.exportOptions["PixelWeighting"]).name)
        self.cbxCoords.setCurrentText(common.CoordSystem(self.exportOptions["CoordSystem"]).name)
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

        # sample features
        self.lstSampleFeatures = QListView()
        model = QStandardItemModel()
        # optional attributes
        for i in range(0, len(common.SampleFeatures)):
            item = QStandardItem(common.SampleFeatures[i][1])
            item.setEditable(False)
            item.setCheckable(True)
            # date, time, space - are required
            if i < 3:
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
        grpColor = QGroupBox("Color:", self)
        grpColor.setLayout(boxColor)

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
        self.cbxPixelWeighting = QComboBox()
        self.cbxPixelWeighting.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cbxPixelWeighting.addItems([str(pw.name) for pw in common.PixelWeighting])
        boxPixelWeighting = QHBoxLayout()
        boxPixelWeighting.addWidget(self.cbxPixelWeighting)
        grpPixelWeighting = QGroupBox("Pixel Weighting:", self)
        grpPixelWeighting.setLayout(boxPixelWeighting)

        # add all pixel options to window
        boxPixelOptions = QHBoxLayout()
        boxPixelOptions.addWidget(grpHDR, 0, Qt.AlignLeft)
        boxPixelOptions.addWidget(grpColor, 0, Qt.AlignLeft)
        boxPixelOptions.addWidget(grpPixelRegion, 0, Qt.AlignLeft)
        boxPixelOptions.addWidget(grpPixelWeighting, 1)
        boxPixelOptions.setContentsMargins(0,0,0,0)
        pnlPixelOptions = QWidget()
        pnlPixelOptions.setLayout(boxPixelOptions)
        layout.addWidget(pnlPixelOptions, 0, Qt.AlignTop)

        # color model
        self.cbxCoords = QComboBox()
        self.cbxCoords.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cbxCoords.addItems([str(c.name) for c in common.CoordSystem])
        boxCoords = QHBoxLayout()
        boxCoords.addWidget(self.cbxCoords)
        grpCoords = QGroupBox("Coordinates:", self)
        grpCoords.setLayout(boxCoords)

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
        boxStuffOptions.addWidget(grpCoords, 0, Qt.AlignLeft)
        boxStuffOptions.addWidget(grpResolution, 1)
        boxStuffOptions.setContentsMargins(0, 0, 0, 0)
        pnlStuffOptions = QWidget()
        pnlStuffOptions.setLayout(boxStuffOptions)
        layout.addWidget(pnlStuffOptions, 0, Qt.AlignTop)

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
            extension = ".csv"
        elif extension.lower() != ".csv":
            extension += ".csv"
        self.txtFile.setText(base + extension)

    def pixRegCalcChanged(self, int):
        if (self.chxPixRegCalc.isChecked()):
            self.cbxPixRegFixed.setEnabled(False)
        else:
            self.cbxPixRegFixed.setEnabled(True)

    def savePressed(self):
        # validate the export before proceeding
        if self.txtFile.text() == None or len(self.txtFile.text()) <= 0:
            QMessageBox.critical(self, "Error", "Invalid export filename.", QMessageBox.Ok)
            return
        if os.path.exists(self.txtFile.text()):
            if QMessageBox.warning(self, "Warning", "Exported samples will be appended to an existing file.\nAre you sure you want to do this?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return

        # append .csv extension if not done already
        base, extension = os.path.splitext(self.txtFile.text())
        if extension.lower() != ".csv":
            self.txtFile.setText(base + extension + ".csv")

        # save export file
        self.exportOptions["Filename"] = self.txtFile.text()

        # save pixel options
        self.exportOptions["IsHDR"] = self.chxHDR.isChecked()
        self.exportOptions["ColorModel"] = common.ColorModel[self.cbxColorModel.currentText()].value
        self.exportOptions["ComputePixelRegion"] = self.chxPixRegCalc.isChecked()
        self.exportOptions["PixelRegion"] = int(self.cbxPixRegFixed.currentText())
        self.exportOptions["PixelWeighting"] = common.PixelWeighting[self.cbxPixelWeighting.currentText()].value

        # save other options
        self.exportOptions["CoordSystem"] = common.CoordSystem[self.cbxCoords.currentText()].value
        self.exportOptions["SpectrumResolution"] = int(self.txtResolution.text())

        # save selected sample features
        attributes = []
        for i in range(0, self.lstSampleFeatures.model().rowCount()):
            item = self.lstSampleFeatures.model().item(i)
            if item.checkState() != Qt.Unchecked:
                attributes.append(i)
        self.exportOptions.update({"Features": attributes})

        self.accept()
