#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 03/20/2018
# @summary: Dialog for converting (importing/exporting) sky data.
# ====================================================================
import os
import csv
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt


class DialogConverter(QDialog):

    def __init__(self):
        super().__init__(None, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        self.datasetIn = ""
        self.datasetOut = ""

        # init
        self.initWidgets()
        self.setWindowTitle("Sample Dataset Converter")
        self.setWindowIcon(QIcon('res/icon.png'))

    def initWidgets(self):
        # layout
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # message
        msg = "Run 'Setup Export File' first.\nExport dialog options will be used for this conversion.\n\n" \
              "'Date' 'Time' and 'SamplePatternIndex' features are required for conversion.\n" \
              "'Exposure' feature will be used if found, current exposure otherwise.\n"
        lblMessage = QLabel()
        lblMessage.setText(msg)
        layout.addWidget(lblMessage, 0, Qt.AlignTop)

        # file in
        lblFile = QLabel("Re-export samples from:")
        self.txtFileIn = QLineEdit()
        self.txtFileIn.setMinimumWidth(400)
        self.txtFileIn.setReadOnly(True)
        btnFile = QPushButton("...")
        btnFile.setMaximumWidth(btnFile.fontMetrics().boundingRect("   ...   ").width())
        btnFile.clicked.connect(self.browseForFile)
        boxFile = QGridLayout()
        boxFile.setContentsMargins(0, 0, 0, 0)
        boxFile.addWidget(lblFile, 0, 0, 1, 2)
        boxFile.addWidget(self.txtFileIn, 1, 0, 1, 1)
        boxFile.addWidget(btnFile, 1, 1, 1, 1)
        pnlFile = QWidget()
        pnlFile.setLayout(boxFile)
        layout.addWidget(pnlFile, 0, Qt.AlignTop)

        # file out
        lblFile = QLabel("Re-export samples to:")
        self.txtFileOut = QLineEdit()
        boxFile = QGridLayout()
        boxFile.setContentsMargins(0, 0, 0, 0)
        boxFile.addWidget(lblFile, 0, 0, 1, 2)
        boxFile.addWidget(self.txtFileOut, 1, 0, 1, 1)
        pnlFile = QWidget()
        pnlFile.setLayout(boxFile)
        layout.addWidget(pnlFile, 0, Qt.AlignTop)

        # accept/decline buttons
        boxButtons = QDialogButtonBox()
        btn = boxButtons.addButton("Cancel", QDialogButtonBox.RejectRole)
        btn.clicked.connect(self.reject)
        btn = boxButtons.addButton("Convert!", QDialogButtonBox.AcceptRole)
        btn.clicked.connect(self.convertPressed)
        layout.addWidget(boxButtons, 0, Qt.AlignBottom | Qt.AlignRight)

        self.setLayout(layout)

    def browseForFile(self):
        filename, filetype = QFileDialog.getOpenFileName(self, 'Select Dataset', '')
        if filename is None or len(filename) <= 0:
            QMessageBox.critical(self, "Error", "Invalid sample dataset filename.", QMessageBox.Ok)
            return

        self.txtFileIn.setText(filename)
        name, ext = os.path.splitext(filename)
        self.txtFileOut.setText(name + "_new" + ext)

    def convertPressed(self):
        # validate files before proceeding
        if self.txtFileIn.text() is None or len(self.txtFileIn.text()) <= 0:
            QMessageBox.critical(self, "Error", "Invalid sample dataset filename.", QMessageBox.Ok)
            return
        if not os.path.exists(self.txtFileIn.text()):
            QMessageBox.critical(self, "Error", "Sample dataset file not found.", QMessageBox.Ok)
            return
        if self.txtFileIn.text() == self.txtFileOut.text():
            QMessageBox.critical(self, "Error", "Dataset In and Out filenames cannot be the same.", QMessageBox.Ok)
            return
        # validate dataset before proceeding (required features)
        with open(self.txtFileIn.text(), 'r') as filein:
            reader = csv.reader(filein, delimiter=",")
            header = next(reader, None)
            if 'Date' not in header or 'Time' not in header or 'SamplePatternIndex' not in header:
                QMessageBox.critical(self, "Error", "Dataset missing required features:\n'Date', 'Time', or 'SamplePatternIndex'.", QMessageBox.Ok)
                return

        # save filenames
        self.datasetIn = self.txtFileIn.text()
        self.datasetOut = self.txtFileOut.text()

        self.accept()
