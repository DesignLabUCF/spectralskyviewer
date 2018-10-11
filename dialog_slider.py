#!/usr/bin/python
# -*- coding: utf-8 -*-
# ====================================================================
# @author: Joe Del Rocco
# @since: 10/10/2018
# @summary: Dialog for getting a value from the user with a slider.
# ====================================================================
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt


class DialogSlider(QDialog):

    def __init__(self, parent, title, message, value, min, max, step, winflags=Qt.WindowSystemMenuHint | Qt.WindowTitleHint):
        super().__init__(parent, winflags | Qt.WindowCloseButtonHint | Qt.Window)

        # window
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon('res/icon.png'))

        # layout
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        label = QLabel(message)
        layout.addWidget(label)
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setTickPosition(QSlider.TicksAbove)
        self.slider.setRange(min, max)
        self.slider.setValue(value)
        self.slider.setTickInterval(step)
        self.slider.setPageStep(step)
        layout.addWidget(self.slider)

        # accept/decline buttons
        boxButtons = QDialogButtonBox()
        btn = boxButtons.addButton("OK", QDialogButtonBox.AcceptRole)
        btn.clicked.connect(self.accept)
        btn = boxButtons.addButton("Cancel", QDialogButtonBox.RejectRole)
        btn.clicked.connect(self.reject)
        layout.addWidget(boxButtons, 0, Qt.AlignBottom)

        self.setLayout(layout)
        layout.setSizeConstraint(QLayout.SetFixedSize)
