# -*- coding: utf-8 -*-
#
# Copyright © keithleygui Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

from __future__ import division, absolute_import, print_function
from qtpy import QtGui, QtCore, QtWidgets


class LedIndicator(QtWidgets.QAbstractButton):
    scaledSize = 1000.0

    def __init__(self, parent=None):
        QtWidgets.QAbstractButton.__init__(self, parent)

        self.setMinimumSize(12, 12)
        self.setCheckable(True)
        self.setDisabled(True)  # Make the led non clickable
        self._checked = False

        # Green
        self.on_color_1 = QtGui.QColor(0, 255, 0)
        self.on_color_2 = QtGui.QColor(0, 192, 0)
        # Red
        self.off_color_1 = QtGui.QColor(255, 0, 0)
        self.off_color_2 = QtGui.QColor(176, 0, 0)

    def resizeEvent(self, QResizeEvent):
        self.update()

    def paintEvent(self, QPaintEvent):
        real_size = min(self.width(), self.height())

        painter = QtGui.QPainter(self)
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidth(1)

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(self.width()/2, self.height()/2)
        painter.scale(real_size/self.scaledSize, real_size/self.scaledSize)

        gradient = QtGui.QRadialGradient(QtCore.QPointF(-500, -500), 1500,
                                         QtCore.QPointF(-500, -500))
        gradient.setColorAt(0, QtGui.QColor(224, 224, 224))
        gradient.setColorAt(1, QtGui.QColor(28, 28, 28))
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(gradient))
        painter.drawEllipse(QtCore.QPointF(0, 0), 500, 500)

        gradient = QtGui.QRadialGradient(QtCore.QPointF(500, 500), 1500,
                                         QtCore.QPointF(500, 500))
        gradient.setColorAt(0, QtGui.QColor(224, 224, 224))
        gradient.setColorAt(1, QtGui.QColor(28, 28, 28))
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(gradient))
        painter.drawEllipse(QtCore.QPointF(0, 0), 450, 450)

        painter.setPen(pen)
        if self.isChecked():
            gradient = QtGui.QRadialGradient(QtCore.QPointF(-500, -500), 1500,
                                             QtCore.QPointF(-500, -500))
            gradient.setColorAt(0, self.on_color_1)
            gradient.setColorAt(1, self.on_color_2)
        else:
            gradient = QtGui.QRadialGradient(QtCore.QPointF(500, 500), 1500,
                                             QtCore.QPointF(500, 500))
            gradient.setColorAt(0, self.off_color_1)
            gradient.setColorAt(1, self.off_color_2)

        painter.setBrush(gradient)
        painter.drawEllipse(QtCore.QPointF(0, 0), 400, 400)
