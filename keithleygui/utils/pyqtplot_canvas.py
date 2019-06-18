# -*- coding: utf-8 -*-
#
# Copyright © keithleygui Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

import sys
import itertools
import pyqtgraph as pg
from pyqtgraph import (AxisItem, PlotItem, GraphicsView, LegendItem,
                       GraphicsWidget, ScatterPlotItem, PlotDataItem,
                       LabelItem, Point)
from pyqtgraph.graphicsItems.ScatterPlotItem import drawSymbol
from pyqtgraph import functions as fn
import numpy as np
from qtpy import QtWidgets, QtCore

pg.setConfigOptions(antialias=True, exitCleanup=False)


# ========================================================================================
# The actual plot item
# ========================================================================================

class SweepDataPlot(GraphicsView):

    GREEN = [0, 204, 153]
    BLUE = [100, 171, 246]
    RED = [221, 61, 53]
    PURPLE = [175, 122, 197]
    ASH = [52, 73, 94]
    GRAY = [178, 186, 187]

    COLORS = [BLUE, RED, GREEN, PURPLE, ASH, GRAY]

    if sys.platform == 'darwin':
        LW = 3
    else:
        LW = 1.5

    def __init__(self):
        GraphicsView.__init__(self)

        # create layout
        self.layout = pg.GraphicsLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(-1.)
        self.setBackground(None)
        self.setCentralItem(self.layout)

        # create axes and apply formatting
        axisItems = dict()

        for pos in ['bottom', 'left', 'top', 'right']:
            axisItems[pos] = AxisItem(orientation=pos, maxTickLength=-7)

        self.p = PlotItem(axisItems=axisItems)
        self.setTitle('Sweep data', fontScaling=1.3, color='k')
        self.layout.addItem(self.p)

        self.p.vb.setBackgroundColor('w')
        self.p.setContentsMargins(10, 10, 10, 10)

        for pos in ['bottom', 'left', 'top', 'right']:
            ax = self.p.getAxis(pos)
            ax.setZValue(0)  # draw on top of patch
            ax.setVisible(True)  # make all axes visible
            ax.setPen(width=self.LW*2/3, color=0.5)  # grey spines and ticks
            try:
                ax.setTextPen('k')  # black text
            except AttributeError:
                pass
            ax.setStyle(autoExpandTextSpace=True, tickTextOffset=4)

        self.p.getAxis('top').setTicks([])
        self.p.getAxis('top').setHeight(0)
        self.p.getAxis('right').setTicks([])

        self.x_axis = self.p.getAxis('bottom')
        self.y_axis = self.p.getAxis('left')

        self.x_axis.setLabel('Voltage', units='V', color='k', size='12pt')
        self.y_axis.setLabel('Current', units='A', color='k', size='12pt')
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
                    padding = np.clip(1./(length**0.5), 0.02, 0.1)
            else:
                padding = 0.02
            return padding

        self.p.vb.suggestPadding = suggestPadding

        # set default ranges to start
        self.p.setXRange(-10, 10)
        self.p.setYRange(-10, 10)

        # add legend
        self.legend = LegendItem(brush=fn.mkBrush(255, 255, 255, 150),
                                 labelTextColor='k', offset=(20, -20))
        self.legend.setParentItem(self.p.vb)

    def clear(self):
        self.p.clear()  # clear current plot
        self.legend.clear()  # clear current legend

    def plot(self, sweep_data):
        self.clear()

        xdata = sweep_data.get_column(0)
        xdata_title = sweep_data.titles[0]
        ydata = sweep_data.values()[1:]

        # format plot according to sweep type
        unit = xdata_title.unit if xdata_title.has_unit() else 'a.u.'
        self.x_axis.setLabel(xdata_title.name, unit=unit)
        self.y_axis.setLabel('Current', unit='A')

        if sweep_data.params['sweep_type'] == 'transfer':
            self.setTitle('Transfer curve')
            self.p.setLogMode(x=False, y=True)
            self.legend.setOffset((20, -20))  # legend in bottom-left corner
            ydata = [np.abs(y) for y in ydata]

        elif sweep_data.params['sweep_type'] == 'output':
            self.setTitle('Output curve')
            self.p.setLogMode(x=False, y=False)
            self.legend.setOffset((-20, 20))  # legend in top-right corner
            ydata = [np.abs(y) for y in ydata]

        else:
            self.setTitle('Sweep curve')
            self.p.setLogMode(x=False, y=False)
            ydata = [np.abs(y) for y in ydata]

        # plot data
        self.lines = []
        for y, c in zip(ydata, itertools.cycle(self.COLORS)):
            p = self.p.plot(xdata, y, pen=fn.mkPen(color=c, width=self.LW))
            self.lines.append(p)

        # add legend
        for l, t in zip(self.lines, sweep_data.column_names[1:]):
            self.legend.addItem(l, str(t))

        self.p.autoRange()

    def setTitle(self, text, fontScaling=None, color=None, font=None):
        # work around pyqtplot which forces the title to be HTML
        if text is None:
            self.p.setTitle(None)  # clears title and hides title column
        else:
            self.p.setTitle('')  # makes title column visible, sets placeholder text
            self.p.titleLabel.item.setPlainText(text)  # replace HTML with plain text

        if color is not None:
            color = fn.mkColor(color)
            self.p.titleLabel.item.setDefaultTextColor(color)

        if font is not None:
            self.p.titleLabel.item.setFont(font)

        if fontScaling is not None:
            font = self.p.titleLabel.item.font()
            defaultFontSize = QtWidgets.QLabel('test').font().pointSize()
            fontSize = round(defaultFontSize*fontScaling, 1)
            font.setPointSize(fontSize)
            self.p.titleLabel.item.setFont(font)


if __name__ == '__main__':

    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)

    view = SweepDataPlot()
    view.show()

    app.exec_()
