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
# @since: 11/16/2017
# @summary: Dialog for exporting sky data.
# ====================================================================
import os
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt


class DialogExport(QDialog):

    # export attributes
    ExportAttributes = [
        "Header",
        "Date",
        "Time",
        "Exposure",
        "Pattern Index",
        "Azimuth (E from N)",
        "Altitude (90 - Zenith)",
        "1 Pixel",
        "9 Pixels",
        "9 Pixels Downsampled to 1",
        "25 Pixels",
        "25 Pixels Downsampled to 1",
        "1° Steridian Pixels",
        "1° Steridian Pixels Downsampled to 1",
        "Solar Irradiance Spectrum (350-2500)"
    ]

    # default export options
    ExportOptions = {
        "Filename": "",
        "Delimiter": ",",
        "Attributes": [0, 1, 2, 5, 6, 7, 14]
    }

    @staticmethod
    def validateOptions(options):
        # must have all available options defined
        # ok to have extras, but must have the at least the default set
        for key in DialogExport.ExportOptions:
            if (key not in options):
                return False
        return True

    @staticmethod
    def attributeFromIndex(index):
        return DialogExport.ExportAttributes[index]

    def __init__(self, options=None):
        super().__init__(None, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        # initial export options are either specified or set from defaults
        if (options != None and DialogExport.validateOptions(options)):
            self.exportOptions = dict(options)
        else:
            self.exportOptions = dict(DialogExport.ExportOptions)

        # init
        self.initWidgets()
        self.setWindowTitle("Export Configuration")
        self.setWindowIcon(QIcon('res/icon.png'))
        # self.setGeometry(0, 0, 1024, 768)
        # self.resize(20, 20)
        # self.setFixedSize(self.size())

    def initWidgets(self):
        # layout
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        # layout.setSizeConstraint(QLayout.SetFixedSize)

        # file
        lblFile = QLabel("Export Data To:")
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

        # format
        self.radCSV = QRadioButton("CSV")
        self.radCSV.clicked.connect(lambda: self.formatPressed(self.radCSV))
        self.radTab = QRadioButton("Tab")
        self.radTab.clicked.connect(lambda: self.formatPressed(self.radTab))
        self.radSpace = QRadioButton("Space")
        self.radSpace.clicked.connect(lambda: self.formatPressed(self.radSpace))
        if (self.exportOptions["Delimiter"] == "\t"):
            self.radTab.setChecked(True)
        elif (self.exportOptions["Delimiter"] == " "):
            self.radSpace.setChecked(True)
        else:
            self.radCSV.setChecked(True)
        boxFormat = QHBoxLayout()
        boxFormat.addWidget(self.radCSV)
        boxFormat.addWidget(self.radTab)
        boxFormat.addWidget(self.radSpace)
        grpFormat = QGroupBox("File Format:", self)
        grpFormat.setLayout(boxFormat)
        layout.addWidget(grpFormat, 0, Qt.AlignTop)

        # attributes
        self.lstAttributes = QListView()
        model = QStandardItemModel()
        for i in range(0, len(DialogExport.ExportAttributes)):
            item = QStandardItem(DialogExport.ExportAttributes[i])
            item.setCheckable(True)
            if (i in self.exportOptions["Attributes"]):
                item.setCheckState(Qt.Checked)
            model.appendRow(item)
        self.lstAttributes.setModel(model)
        boxAttr = QVBoxLayout()
        boxAttr.addWidget(self.lstAttributes)
        grpAttr = QGroupBox("Export Attributes:", self)
        grpAttr.setLayout(boxAttr)
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
        if (filename is None or len(filename) <= 0):
            return

        # apply default extension, if missing
        base, extension = os.path.splitext(filename)
        if (extension is None or len(extension) <= 0):
            if (self.radCSV.isChecked()):
                extension = ".csv"
            else:
                extension = ".txt"
        self.txtFile.setText(base + extension)

    def formatPressed(self, button):
        if (self.txtFile.text() is None or len(self.txtFile.text()) <= 0):
            return

        # updated extension when format selected
        base, extension = os.path.splitext(self.txtFile.text())
        if (button == self.radCSV):
            extension = ".csv"
        else:
            extension = ".txt"
        self.txtFile.setText(base + extension)

    def savePressed(self):
        # validate the export before proceeding
        if (self.txtFile.text() == None or len(self.txtFile.text()) <= 0):
            QMessageBox.critical(self, "Error", "Invalid export filename!", QMessageBox.Ok)
            return
        if (os.path.exists(self.txtFile.text())):
            if (QMessageBox.warning(self, "Warning", "Exported samples will be appended to existing file.\nAre you sure you want to do this?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes):
                return

        # save export filename
        self.exportOptions["Filename"] = self.txtFile.text()

        # save file format
        if (self.radCSV.isChecked()):     self.exportOptions["Delimiter"] = ","
        elif (self.radTab.isChecked()):   self.exportOptions["Delimiter"] = "\t"
        elif (self.radSpace.isChecked()): self.exportOptions["Delimiter"] = " "

        # save selected attributes
        attributes = []
        for i in range(0, self.lstAttributes.model().rowCount()):
            item = self.lstAttributes.model().item(i)
            if (item.checkState() == Qt.Checked):
                attributes.append(i)
        self.exportOptions.update({"Attributes": attributes})

        self.accept()
