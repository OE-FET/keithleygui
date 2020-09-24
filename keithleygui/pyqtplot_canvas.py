# -*- coding: utf-8 -*-
#
# Copyright © keithleygui Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

import sys
import itertools
import pyqtgraph as pg
from pyqtgraph import functions as fn
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui


pg.setConfigOptions(antialias=True, exitCleanup=False)

COLORS = [
    [0.0, 114.0, 189.0],
    [216.8, 82.9, 25.0],
    [236.9, 177.0, 31.9],
    [126.0, 46.9, 141.8],
    [118.8, 171.9, 47.9],
    [76.8, 190.0, 237.9],
    [161.9, 19.9, 46.9],
]


# ========================================================================================
# The actual plot item
# ========================================================================================


class SweepDataPlot(pg.GraphicsView):

    if sys.platform == "darwin":
        LW = 3
    else:
        LW = 1.5

    _init_done = False

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # create layout
        self.layout = pg.GraphicsLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(-1.0)
        self.setBackground(None)
        self.setCentralItem(self.layout)

        # create axes and apply formatting
        axisItems = dict()

        for pos in ["bottom", "left", "top", "right"]:
            axisItems[pos] = pg.AxisItem(orientation=pos, maxTickLength=-7)

        self.p = pg.PlotItem(axisItems=axisItems)
        self.setTitle("Sweep data", fontScaling=1.3, color="k")
        self.layout.addItem(self.p)

        self.p.vb.setBackgroundColor("w")
        self.p.setContentsMargins(10, 10, 10, 10)

        for pos in ["bottom", "left", "top", "right"]:
            ax = self.p.getAxis(pos)
            ax.setZValue(0)  # draw on top of patch
            ax.setVisible(True)  # make all axes visible
            ax.setPen(width=self.LW * 2 / 3, color=0.5)  # grey spines and ticks
            try:
                ax.setTextPen("k")  # black text
            except AttributeError:
                pass
            ax.setStyle(autoExpandTextSpace=True, tickTextOffset=4)

        self.p.getAxis("top").setTicks([])
        self.p.getAxis("top").setHeight(0)
        self.p.getAxis("right").setTicks([])

        self.x_axis = self.p.getAxis("bottom")
        self.y_axis = self.p.getAxis("left")

        self.x_axis.setLabel("Voltage", units="V", color="k", size="12pt")
        self.y_axis.setLabel("Current", units="A", color="k", size="12pt")
        self.y_axis.setStyle(tickTextWidth=35)

        # set auto range and mouse panning / zooming
        self.p.enableAutoRange(x=True, y=True)
        self.p.setLimits(xMin=-1e20, xMax=1e20, yMin=-1e20, yMax=1e20)

        def suggestPadding(axis):
            length = self.p.vb.width() if axis == 0 else self.p.vb.height()
            if length > 0:
                if axis == 0:
                    padding = 0
                else:
                    padding = np.clip(1.0 / (length ** 0.5), 0.02, 0.1)
            else:
                padding = 0.02
            return padding

        self.p.vb.suggestPadding = suggestPadding

        # set default ranges to start
        self.p.setXRange(-10, 10)
        self.p.setYRange(-10, 10)

        # add legend
        self.legend = pg.LegendItem(
            brush=fn.mkBrush(255, 255, 255, 150), labelTextColor="k", offset=(20, -20)
        )
        self.legend.setParentItem(self.p.vb)

        # update colors
        self.update_darkmode()

        self._init_done = True

    def clear(self):
        self.p.clear()  # clear current plot
        self.legend.clear()  # clear current legend

    def plot(self, sweep_data):
        self.clear()

        xdata = sweep_data.get_column(0)
        xdata_title = sweep_data.titles[0]
        ydata = sweep_data.values()[1:]

        # format plot according to sweep type
        unit = xdata_title.unit if xdata_title.has_unit() else "a.u."
        self.x_axis.setLabel(xdata_title.name, unit=unit)
        self.y_axis.setLabel("Current", unit="A")

        if sweep_data.params["sweep_type"] == "transfer":
            self.setTitle("Transfer curve")
            self.p.setLogMode(x=False, y=True)
            self.legend.setOffset((20, -20))  # legend in bottom-left corner
            ydata = [np.abs(y) for y in ydata]

        elif sweep_data.params["sweep_type"] == "output":
            self.setTitle("Output curve")
            self.p.setLogMode(x=False, y=False)
            self.legend.setOffset((-20, 20))  # legend in top-right corner
            ydata = [np.abs(y) for y in ydata]

        else:
            self.setTitle("Sweep curve")
            self.p.setLogMode(x=False, y=False)
            ydata = [np.abs(y) for y in ydata]

        # plot data
        self.lines = []
        for y, c in zip(ydata, itertools.cycle(COLORS)):
            p = self.p.plot(xdata, y, pen=fn.mkPen(color=c, width=self.LW))
            self.lines.append(p)

        # add legend
        for l, t in zip(self.lines, sweep_data.column_names[1:]):
            self.legend.addItem(l, str(t))

        self.p.autoRange()

        self.update_darkmode()

    def setTitle(self, text, fontScaling=None, color=None, font=None):
        # work around pyqtplot which forces the title to be HTML
        if text is None:
            self.p.setTitle(None)  # clears title and hides title column
        else:
            self.p.setTitle("")  # makes title column visible, sets placeholder text
            self.p.titleLabel.item.setPlainText(text)  # replace HTML with plain text

        if color is not None:
            color = fn.mkColor(color)
            self.p.titleLabel.item.setDefaultTextColor(color)

        if font is not None:
            self.p.titleLabel.item.setFont(font)

        if fontScaling is not None:
            font = self.p.titleLabel.item.font()
            defaultFontSize = QtWidgets.QLabel("test").font().pointSize()
            fontSize = round(defaultFontSize * fontScaling, 1)
            font.setPointSize(fontSize)
            self.p.titleLabel.item.setFont(font)

    def changeEvent(self, QEvent):

        if QEvent.type() == QtCore.QEvent.PaletteChange and self._init_done:
            self.update_darkmode()

    def update_darkmode(self):

        # get colors
        bg_color = self.palette().color(QtGui.QPalette.Base)
        bg_color_rgb = [bg_color.red(), bg_color.green(), bg_color.blue()]
        font_color = self.palette().color(QtGui.QPalette.Text)
        font_color_rgb = [font_color.red(), font_color.green(), font_color.blue()]

        # set bg colors
        self.setBackground(None)  # reload background
        self.p.vb.setBackgroundColor(bg_color_rgb)
        self.legend.opts["brush"] = fn.mkBrush(bg_color_rgb)

        # change label colors
        for pos in ["bottom", "left", "top", "right"]:
            ax = self.p.getAxis(pos)
            try:
                ax.setTextPen(font_color_rgb)
            except AttributeError:
                pass

        self.x_axis.setTextPen(font_color_rgb)
        self.y_axis.setTextPen(font_color_rgb)
        self.legend.opts["labelTextColor"] = fn.mkColor(font_color_rgb)
        self.p.titleLabel.item.setDefaultTextColor(fn.mkColor(font_color_rgb))

        for sample, label in self.legend.items:
            label.setAttr("color", fn.mkColor(font_color_rgb))
            label.setText(label.text)  # force redraw

        self.legend.update()
