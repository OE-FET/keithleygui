# -*- coding: utf-8 -*-
import sys
import itertools
import pyqtgraph as pg
from pyqtgraph import (AxisItem, PlotItem, GraphicsView, LegendItem,
                       GraphicsWidget, ScatterPlotItem, PlotDataItem,
                       LabelItem, Point)
from pyqtgraph.graphicsItems.ScatterPlotItem import drawSymbol
from pyqtgraph import getConfigOption
from pyqtgraph import functions as fn
import numpy as np
from qtpy import QtGui, QtWidgets, QtCore

from keithley2600 import ResultTable

PY2 = sys.version[0] == '2'


class MyAxisItem(AxisItem):

    _textPen = None

    def textPen(self):
        if self._textPen is None:
            return fn.mkPen(getConfigOption('foreground'))
        return fn.mkPen(self._textPen)

    def setTextPen(self, *args, **kwargs):
        """
        Set the pen used for drawing text.
        If no arguments are given, the default foreground color will be used.
        """
        self.picture = None
        if args or kwargs:
            self._textPen = fn.mkPen(*args, **kwargs)
        else:
            self._textPen = fn.mkPen(getConfigOption('foreground'))
        self.labelStyle['color'] = '#' + fn.colorStr(self._textPen.color())[:6]
        self.setLabel()
        self.update()

    def tickSpacing(self, minVal, maxVal, size):

        """Return values describing the desired spacing and offset of ticks.

        This method is called whenever the axis needs to be redrawn and is a
        good method to override in subclasses that require control over tick locations.

        The return value must be a list of tuples, one for each set of ticks::

            [
                (major tick spacing, offset),
                (minor tick spacing, offset),
                (sub-minor tick spacing, offset),
                ...
            ]
        """
        # First check for override tick spacing
        if self._tickSpacing is not None:
            return self._tickSpacing

        dif = abs(maxVal - minVal)
        if dif == 0:
            return []

        # decide optimal minor tick spacing in pixels (this is just aesthetics)
        optimalTickCount = max(2., np.log(size))

        # optimal minor tick spacing
        optimalSpacing = dif / optimalTickCount

        # the largest power-of-10 spacing which is smaller than optimal
        p10unit = 10 ** np.floor(np.log10(optimalSpacing))

        # Determine major/minor tick spacings which flank the optimal spacing.
        intervals = np.array([1., 2., 10., 20., 100.]) * p10unit
        minorIndex = 0
        while intervals[minorIndex+1] <= optimalSpacing:
            minorIndex += 1

        levels = [
            (intervals[minorIndex+2], 0),
            (intervals[minorIndex+1], 0),
        ]

        if self.style['maxTickLevel'] >= 2:
            # decide whether to include the last level of ticks
            minSpacing = min(size / 20., 30.)
            maxTickCount = size / minSpacing
            if dif / intervals[minorIndex] <= maxTickCount:
                levels.append((intervals[minorIndex], 0))

        return levels

    def drawPicture(self, p, axisSpec, tickSpecs, textSpecs):

        p.setRenderHint(p.Antialiasing, False)
        p.setRenderHint(p.TextAntialiasing, True)

        # draw long line along axis
        pen, p1, p2 = axisSpec
        p.setPen(pen)
        p.drawLine(p1, p2)
        p.translate(0.5, 0)  # resolves some damn pixel ambiguity

        # draw ticks
        for pen, p1, p2 in tickSpecs:
            p.setPen(pen)
            p.drawLine(p1, p2)

        # Draw all text
        if self.tickFont is not None:
            p.setFont(self.tickFont)
        p.setPen(self.textPen())
        for rect, flags, text in textSpecs:
            p.drawText(rect, flags, text)

        p.setPen(pen)


class MyItemSample(GraphicsWidget):
    """ Class responsible for drawing a single item in a LegendItem (sans label).

    This may be subclassed to draw custom graphics in a Legend.
    """
    # Todo: make this more generic; let each item decide how it should be represented.
    def __init__(self, item):
        GraphicsWidget.__init__(self)
        self.item = item

    def boundingRect(self):
        return QtCore.QRectF(0, 0, 20, 20)

    def paint(self, p, *args):
        opts = self.item.opts

        if opts['antialias']:
            p.setRenderHint(p.Antialiasing)

        if opts.get('fillLevel', None) is not None and opts.get('fillBrush', None) is not None:
            p.setBrush(fn.mkBrush(opts['fillBrush']))
            p.setPen(fn.mkPen(None))
            p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(-5, 11),
                                           QtCore.QPointF(5, 11),
                                           QtCore.QPointF(5, 0),
                                           QtCore.QPointF(-5, 0)]))

        if not isinstance(self.item, ScatterPlotItem):
            p.setPen(fn.mkPen(opts['pen']))
            p.drawLine(-5, 11, 5, 11)

        symbol = opts.get('symbol', None)
        if symbol is not None:
            if isinstance(self.item, PlotDataItem):
                opts = self.item.scatter.opts

            pen = fn.mkPen(opts['pen'])
            brush = fn.mkBrush(opts['brush'])
            size = opts['size']

            p.translate(10, 10)
            path = drawSymbol(p, symbol, size, pen, brush)


class MyLegendItem(LegendItem):

    def __init__(self, size=None, offset=None, pen=None, brush=None, **kwargs):
        LegendItem.__init__(self, size, offset)

        self.layout.setSpacing(0)
        self.layout.setColumnSpacing(0, 10)
        self.layout.setColumnSpacing(1, 10)

        self.opts = {
            'pen': fn.mkPen(None),
            'brush': fn.mkBrush(color=(255, 255, 255, 150)),
            'box': False
        }

        for name, value in kwargs.items():
            if name in self.opts.keys():
                self.opts[name] = value
            else:
                raise ValueError('Keyword not in %s.' % self.opts.keys())

    def setOffset(self, offset):
        self.offset = offset

        offset = Point(self.offset)
        anchorx = 1 if offset[0] <= 0 else 0
        anchory = 1 if offset[1] <= 0 else 0
        anchor = (anchorx, anchory)
        self.anchor(itemPos=anchor, parentPos=anchor, offset=offset)

    def addItem(self, item, name):
        """
        Add a new entry to the legend.

        ==============  ========================================================
        **Arguments:**
        item            A PlotDataItem from which the line and point style
                        of the item will be determined or an instance of
                        ItemSample (or a subclass), allowing the item display
                        to be customized.
        title           The title to display for this item. Simple HTML allowed.
        ==============  ========================================================
        """
        label = LabelItem(name, color='k', justify='left')
        if isinstance(item, MyItemSample):
            sample = item
        else:
            sample = MyItemSample(item)
        row = self.layout.rowCount()
        self.items.append((sample, label))
        self.layout.addItem(sample, row, 0)
        self.layout.addItem(label, row, 1)
        self.layout.setRowMaximumHeight(row, 20)
        self.updateSize()

    def setPen(self, *args, **kargs):
        """
        Sets the pen used to draw lines between points.
        *pen* can be a QPen or any argument accepted by
        :func:`pyqtgraph.mkPen() <pyqtgraph.mkPen>`
        """
        pen = fn.mkPen(*args, **kargs)
        self.opts['pen'] = pen

    def setBrush(self, *args, **kargs):
        brush = fn.mkBrush(*args, **kargs)
        if self.opts['brush'] == brush:
            return
        self.opts['brush'] = brush

    def clear(self):
        for sample, label in self.items:
            self.removeItem(label.text)

    def paint(self, p, *args):
        p.setPen(self.opts['pen'])
        p.setBrush(self.opts['brush'])
        p.drawRect(self.boundingRect())


class SweepDataPlot(GraphicsView):

    GREEN = [0, 204, 153]
    BLUE = [100, 171, 246]
    RED = [221, 61, 53]
    PURPLE = [175, 122, 197]
    ASH = [52, 73, 94]
    GRAY = [178, 186, 187]

    COLORS = [BLUE, RED, GREEN, PURPLE, ASH, GRAY]

    LW = 3.5

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
            axisItems[pos] = MyAxisItem(orientation=pos, maxTickLength=7)

        self.p = PlotItem(axisItems=axisItems)
        self.p.setTitle('Sweep data', color='k', size='15pt')
        self.layout.addItem(self.p)

        self.p.vb.setBackgroundColor('w')
        self.p.setContentsMargins(10, 10, 10, 10)

        for pos in ['bottom', 'left', 'top', 'right']:
            ax = self.p.getAxis(pos)
            ax.setZValue(0)  # draw on top of patch
            ax.setVisible(True)  # make all axes visible
            ax.setPen(width=2, color=0.5)  # grey spines and ticks
            ax.setTextPen('k')  # black text
            ax.setStyle(autoExpandTextSpace=False, tickTextOffset=4)

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

        # set default ranges to start
        self.p.setXRange(-10, 10)
        self.p.setYRange(-10, 10)

        # override default padding with constant 0.2% padding
        # self.p.vb.suggestPadding = lambda x: 0.05

        # add legend
        self.legend = MyLegendItem(offset=(20, -20))
        self.legend.setParentItem(self.p.vb)

    def plot(self, sweep_data):

        self.p.clear()  # clear current plot
        self.legend.clear()  # clear current legend

        xdata = sweep_data.get_column(0)
        xdata_title = sweep_data.titles[0]
        ydata = sweep_data.values()[1:]

        # format plot according to sweep type
        unit = xdata_title.unit if xdata_title.has_unit() else 'a.u.'
        self.x_axis.setLabel(xdata_title.name, unit=unit)
        self.y_axis.setLabel('Current', unit='A')

        if sweep_data.sweep_type == 'transfer':
            self.p.setTitle('Transfer curve')
            self.p.setLogMode(x=False, y=True)
            self.legend.setOffset((20, -20))  # legend in bottom-left corner
            ydata = [np.abs(y) for y in ydata]

        elif sweep_data.sweep_type == 'output':
            self.p.setTitle('Output curve')
            self.p.setLogMode(x=False, y=False)
            self.legend.setOffset((-20, 20))  # legend in top-right corner

        else:
            self.p.setTitle('Sweep curve')
            self.p.setLogMode(x=False, y=False)
            ydata = [np.abs(y) for y in ydata]

        # plot data
        self.lines = []
        for y, c in zip(ydata, itertools.cycle(self.COLORS)):
            p = self.p.plot(xdata, y, antialias=True, pen=fn.mkPen(color=c, width=self.LW))
            self.lines.append(p)

        # add legend
        for l, t in zip(self.lines, sweep_data.column_names[1:]):
            self.legend.addItem(l, str(t))


if __name__ == '__main__!':

    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)

    view = SweepDataPlot()
    view.show()

    app.exec_()
