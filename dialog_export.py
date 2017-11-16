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
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt


class DialogExport(QDialog):

    # default export options
    ExportOptions = {
        "ExportOptions": {
            "Filename": "",
            "Delimiter": ",",
            "Attributes": [0, 1, 2, 3, 5, 6]
        }
    }

    def __init__(self):
        super().__init__(None, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        # member variables
        self.exportOptions = dict(DialogExport.ExportOptions)

        # init
        self.initWidgets()
        self.setWindowTitle("Export Sky Samples")
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
        self.radTab = QRadioButton("Tab")
        self.radSpace = QRadioButton("Space")
        self.radCSV.setChecked(True)
        boxFormat = QHBoxLayout()
        boxFormat.addWidget(self.radCSV)
        boxFormat.addWidget(self.radTab)
        boxFormat.addWidget(self.radSpace)
        grpFormat = QGroupBox("File Format:", self)
        grpFormat.setLayout(boxFormat)
        layout.addWidget(grpFormat)

        # accept/decline buttons
        boxButtons = QDialogButtonBox()
        btn = boxButtons.addButton("Cancel", QDialogButtonBox.RejectRole)
        btn.clicked.connect(self.reject)
        btn = boxButtons.addButton("Export", QDialogButtonBox.AcceptRole)
        btn.clicked.connect(self.accept)
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
        filename = base + extension
        #print(filename)


