# -*- coding: utf-8 -*-
#
# Copyright © keithleygui Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)


# system imports
from __future__ import division, print_function, absolute_import
import os.path as osp
import pkg_resources as pkgr
import visa
from qtpy import QtCore, QtWidgets, uic
from matplotlib.figure import Figure
from keithley2600 import TransistorSweepData, IVSweepData
import matplotlib as mpl
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# local imports
from keithleygui.utils.led_indicator_widget import LedIndicator
from keithleygui.utils.scientific_spinbox import ScienDSpinBox
from keithleygui.connection_dialog import ConnectionDialog
from keithleygui.config.main import CONF

MAIN_UI_PATH = pkgr.resource_filename('keithleygui', 'main.ui')
MPL_STYLE_PATH = pkgr.resource_filename('keithleygui', 'figure_style.mplstyle')


class SMUSettingsTab(QtWidgets.QWidget):

    def __init__(self, smu_name):
        super(self.__class__, self).__init__()

        self.smu_name = smu_name
        self.setObjectName('tab_%s' % self.smu_name)

        self.gridLayouts = QtWidgets.QGridLayout(self)
        self.gridLayouts.setObjectName('gridLayout')

        self.labelComboBox = QtWidgets.QLabel(self)
        self.labelComboBox.setObjectName('labelComboBox')
        self.labelComboBox.setAlignment(QtCore.Qt.AlignRight)
        self.labelComboBox.setText('Sense type:')
        self.gridLayouts.addWidget(self.labelComboBox, 0, 0, 1, 1)

        self.comboBox = QtWidgets.QComboBox(self)
        self.comboBox.setObjectName('comboBox')
        self.comboBox.setMinimumWidth(150)
        self.comboBox.setMaximumWidth(150)
        self.comboBox.addItems(['local (2-wire)', 'remote (4-wire)'])
        if CONF.get(self.smu_name, 'sense') is 'SENSE_LOCAL':
            self.comboBox.setCurrentIndex(0)
        elif CONF.get(self.smu_name, 'sense') is 'SENSE_REMOTE':
            self.comboBox.setCurrentIndex(1)
        self.gridLayouts.addWidget(self.comboBox, 0, 1, 1, 2)

        self.labelLimI = QtWidgets.QLabel(self)
        self.labelLimI.setObjectName('labelLimI')
        self.labelLimI.setAlignment(QtCore.Qt.AlignRight)
        self.labelLimI.setText('Current limit:')
        self.gridLayouts.addWidget(self.labelLimI, 1, 0, 1, 1)

        self.scienceSpinBoxLimI = ScienDSpinBox(self)
        self.scienceSpinBoxLimI.setObjectName('scienceSpinBoxLimI')
        self.scienceSpinBoxLimI.setMinimumWidth(90)
        self.scienceSpinBoxLimI.setMaximumWidth(90)
        self.scienceSpinBoxLimI.setAlignment(QtCore.Qt.AlignRight)
        self.scienceSpinBoxLimI.setValue(CONF.get(self.smu_name, 'limiti'))
        self.scienceSpinBoxLimI.setSuffix("A")
        self.gridLayouts.addWidget(self.scienceSpinBoxLimI, 1, 1, 1, 1)

        self.labelLimV = QtWidgets.QLabel(self)
        self.labelLimV.setObjectName('labelLimV')
        self.labelLimV.setAlignment(QtCore.Qt.AlignRight)
        self.labelLimV.setText('Voltage limit:')
        self.gridLayouts.addWidget(self.labelLimV, 2, 0, 1, 1)

        self.scienceSpinBoxLimV = ScienDSpinBox(self)
        self.scienceSpinBoxLimV.setObjectName('scienceSpinBoxLimV')
        self.scienceSpinBoxLimV.setMinimumWidth(90)
        self.scienceSpinBoxLimV.setMaximumWidth(90)
        self.scienceSpinBoxLimV.setAlignment(QtCore.Qt.AlignRight)
        self.scienceSpinBoxLimV.setValue(CONF.get(self.smu_name, 'limitv'))
        self.scienceSpinBoxLimV.setSuffix("V")
        self.gridLayouts.addWidget(self.scienceSpinBoxLimV, 2, 1, 1, 1)


class KeithleyGuiApp(QtWidgets.QMainWindow):
    """ Provides a GUI for transfer and output sweeps on the Keithley 2600."""
    def __init__(self, keithley):
        super(self.__class__, self).__init__()
        # load user interface layout from .ui file
        uic.loadUi(MAIN_UI_PATH, self)

        self.keithley = keithley
        # create new list of smu's instead of reference to old list
        self.smu_list = list(self.keithley.SMU_LIST)

        self._set_up_tabs()  # create Keithley settings tabs
        self._set_up_fig()  # create figure area

        # restore last position and size
        self.restore_geometry()

        # create connection dialog
        self.connectionDialog = ConnectionDialog(self, self.keithley)

        # create LED indicator
        self.led = LedIndicator(self)
        self.statusBar.addPermanentWidget(self.led)
        self.led.setChecked(False)

        # prepare GUI
        self.connect_ui_callbacks()  # connect to callbacks
        self._on_load_default()  # load default settings into GUI
        self.actionSaveSweepData.setEnabled(False)  # disable save menu

        # update when keithley is connected
        self._update_gui_connection()

        # connection update timer: check periodically if keithley is connected
        # and busy, act accordingly
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_gui_connection)
        self.timer.start(10000)  # Call every 10 seconds

    @staticmethod
    def _string_to_vd(string):
        try:
            return float(string)
        except ValueError:
            if 'trailing' in string:
                return 'trailing'
            else:
                raise ValueError('Invalid drain voltage.')

    def closeEvent(self, event):
        self.exit_()

# =============================================================================
# GUI setup
# =============================================================================

    def restore_geometry(self):
        x = CONF.get('Window', 'x')
        y = CONF.get('Window', 'y')
        w = CONF.get('Window', 'width')
        h = CONF.get('Window', 'height')

        self.setGeometry(x, y, w, h)

    def save_geometry(self):
        geo = self.geometry()
        CONF.set('Window', 'height', geo.height())
        CONF.set('Window', 'width', geo.width())
        CONF.set('Window', 'x', geo.x())
        CONF.set('Window', 'y', geo.y())

    def _set_up_fig(self):

        # set up figure itself
        with mpl.style.context(['default', MPL_STYLE_PATH]):
            self.fig = Figure(facecolor="None")
            self.fig.set_tight_layout('tight')
            self.ax = self.fig.add_subplot(111)

        self.ax.set_title('Sweep data', fontsize=10)
        self.ax.set_xlabel('Voltage [V]', fontsize=9)
        self.ax.set_ylabel('Current [A]', fontsize=9)

        # This needs to be done programmatically: it is impossible to specify
        # differing label colors and tick colors in a '.mplstyle' file
        self.ax.tick_params(axis='both', which='major', direction='out',
                            labelcolor='black', color=[0.5, 0.5, 0.5, 1], labelsize=9)

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color:transparent;")

        height = self.frameGeometry().height()
        self.canvas.setMinimumWidth(height)
        self.canvas.draw()

        self.gridLayout2.addWidget(self.canvas)

    def _set_up_tabs(self):
        """Create a settings tab for every SMU."""

        self.smu_tabs = []
        self.ntabs = len(self.smu_list)

        for smu_name in self.smu_list:
            tab = SMUSettingsTab(smu_name)
            self.tabWidgetSettings.addTab(tab, smu_name)
            self.smu_tabs.append(tab)

    def connect_ui_callbacks(self):
        """Connect buttons and menus to callbacks."""
        self.pushButtonTransfer.clicked.connect(self._on_sweep_clicked)
        self.pushButtonOutput.clicked.connect(self._on_sweep_clicked)
        self.pushButtonIV.clicked.connect(self._on_sweep_clicked)
        self.pushButtonAbort.clicked.connect(self._on_abort_clicked)

        self.comboBoxGateSMU.currentIndexChanged.connect(self._on_smu_gate_changed)
        self.comboBoxDrainSMU.currentIndexChanged.connect(self._on_smu_drain_changed)

        self.actionSettings.triggered.connect(self.connectionDialog.open)
        self.actionConnect.triggered.connect(self._on_connect_clicked)
        self.actionDisconnect.triggered.connect(self._on_disconnect_clicked)
        self.action_Exit.triggered.connect(self.exit_)
        self.actionSaveSweepData.triggered.connect(self._on_save_clicked)
        self.actionLoad_data_from_file.triggered.connect(self._on_load_clicked)
        self.actionSaveDefaults.triggered.connect(self._on_save_default)
        self.actionLoadDefaults.triggered.connect(self._on_load_default)

# =============================================================================
# Measurement callbacks
# =============================================================================

    def apply_smu_settings(self):
        """
        Applies SMU settings to Keithley before a measurement.
        Warning: self.keithley.reset() will reset those settings.
        """
        for tab in self.smu_tabs:

            smu = getattr(self.keithley, tab.smu_name)

            if tab.comboBox.currentIndex() == 0:
                smu.sense = smu.SENSE_LOCAL
            elif tab.comboBox.currentIndex() == 1:
                smu.sense = smu.SENSE_REMOTE

            lim_i = tab.scienceSpinBoxLimI.value()
            smu.source.limiti = lim_i
            smu.trigger.source.limiti = lim_i

            lim_v = tab.scienceSpinBoxLimV.value()
            smu.source.limitv = lim_v
            smu.trigger.source.limitv = lim_v

    @QtCore.Slot()
    def _on_sweep_clicked(self):
        """ Start a transfer measurement with current settings."""

        if self.keithley.busy:
            msg = ('Keithley is currently used by another program. ' +
                   'Please try again later.')
            QtWidgets.QMessageBox.information(self, str('error'), msg)

            return

        self.apply_smu_settings()

        params = dict()

        if self.sender() == self.pushButtonTransfer:
            self.statusBar.showMessage('    Recording transfer curve.')
            # get sweep settings
            params['sweep_type'] = 'transfer'
            params['VgStart'] = self.scienDSpinBoxVgStart.value()
            params['VgStop'] = self.scienDSpinBoxVgStop.value()
            params['VgStep'] = self.scienDSpinBoxVgStep.value()
            vd_list_string = self.lineEditVdList.text()
            vd_string_list = vd_list_string.split(',')
            params['VdList'] = [self._string_to_vd(x) for x in vd_string_list]

        elif self.sender() == self.pushButtonOutput:
            self.statusBar.showMessage('    Recording output curve.')
            # get sweep settings
            params['sweep_type'] = 'output'
            params['VdStart'] = self.scienDSpinBoxVdStart.value()
            params['VdStop'] = self.scienDSpinBoxVdStop.value()
            params['VdStep'] = self.scienDSpinBoxVdStep.value()
            vg_list_string = self.lineEditVgList.text()
            vg_string_list = vg_list_string.split(',')
            params['VgList'] = [float(x) for x in vg_string_list]

        elif self.sender() == self.pushButtonIV:
            self.statusBar.showMessage('    Recording IV curve.')
            # get sweep settings
            params['sweep_type'] = 'iv'
            params['VStart'] = self.scienDSpinBoxVStart.value()
            params['VStop'] = self.scienDSpinBoxVStop.value()
            params['VStep'] = self.scienDSpinBoxVStep.value()
            smusweep = self.comboBoxSweepSMU.currentText()
            params['smu_sweep'] = getattr(self.keithley, smusweep)

        else:
            return

        # get acquisition settings
        params['tInt'] = self.scienDSpinBoxInt.value()  # integration time
        params['delay'] = self.scienDSpinBoxSettling.value()  # stabilization

        smugate = self.comboBoxGateSMU.currentText()  # gate SMU
        params['smu_gate'] = getattr(self.keithley, smugate)
        smudrain = self.comboBoxDrainSMU.currentText()
        params['smu_drain'] = getattr(self.keithley, smudrain)  # drain SMU

        params['pulsed'] = bool(self.comboBoxSweepType.currentIndex())

        # check if integration time is valid, return otherwise
        freq = self.keithley.localnode.linefreq

        if params['tInt'] > 25.0/freq or params['tInt'] < 0.001/freq:
            msg = ('Integration time must be between 0.001 and 25 ' +
                   'power line cycles of 1/(%s Hz).' % freq)
            QtWidgets.QMessageBox.information(self, str('error'), msg)

            return

        # create measurement thread with params dictionary
        self.measureThread = MeasureThread(self.keithley, params)
        self.measureThread.finishedSig.connect(self._on_measure_done)

        # run measurement
        self._gui_state_busy()
        self.measureThread.start()

    def _on_measure_done(self, sd):
        self.statusBar.showMessage('    Ready.')
        self._gui_state_idle()
        self.actionSaveSweepData.setEnabled(True)

        self.sweep_data = sd
        self.plot_new_data()
        if not self.keithley.abort_event.is_set():
            self._on_save_clicked()

    @QtCore.Slot()
    def _on_abort_clicked(self):
        """
        Aborts current measurement.
        """
        self.keithley.abort_event.set()

# =============================================================================
# Interface callbacks
# =============================================================================

    @QtCore.Slot(int)
    def _on_smu_gate_changed(self, int_smu):
        """ Triggered when the user selects a different gate SMU. """

        if int_smu == 0 and len(self.smu_list) < 3:
            self.comboBoxDrainSMU.setCurrentIndex(1)
        elif int_smu == 1 and len(self.smu_list) < 3:
            self.comboBoxDrainSMU.setCurrentIndex(0)

    @QtCore.Slot(int)
    def _on_smu_drain_changed(self, int_smu):
        """ Triggered when the user selects a different drain SMU. """

        if int_smu == 0 and len(self.smu_list) < 3:
            self.comboBoxGateSMU.setCurrentIndex(1)
        elif int_smu == 1 and len(self.smu_list) < 3:
            self.comboBoxGateSMU.setCurrentIndex(0)

    @QtCore.Slot()
    def _on_connect_clicked(self):
        self.keithley.connect()
        self._update_gui_connection()
        if not self.keithley.connected:
            msg = ('Keithley cannot be reached at %s. ' % self.keithley.visa_address
                   + 'Please check if address is correct and Keithley is ' +
                   'turned on.')
            QtWidgets.QMessageBox.information(self, str('error'), msg)

    @QtCore.Slot()
    def _on_disconnect_clicked(self):
        self.keithley.disconnect()
        self._update_gui_connection()
        self.statusBar.showMessage('    No Keithley connected.')

    @QtCore.Slot()
    def _on_save_clicked(self):
        """Show GUI to save current sweep data as text file."""
        prompt = 'Save as .txt file.'
        filename = 'untitled.txt'
        formats = 'Text file (*.txt)'
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(self, prompt, filename,
                                                            formats)
        if len(filepath) < 4:
            return
        self.sweep_data.save(filepath)

    @QtCore.Slot()
    def _on_load_clicked(self):
        """Show GUI to load sweep data from file."""
        prompt = 'Please select a data file.'
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(self, prompt)
        if not osp.isfile(filepath):
            return

        self.sweep_data = TransistorSweepData()
        self.sweep_data.load(filepath)

        with mpl.style.context(['default', MPL_STYLE_PATH]):
            self.plot_new_data()
        self.actionSaveSweepData.setEnabled(True)

    @QtCore.Slot()
    def _on_save_default(self):
        """Saves current settings from GUI as defaults."""

        # save transfer settings
        CONF.set('Sweep', 'VgStart', self.scienDSpinBoxVgStart.value())
        CONF.set('Sweep', 'VgStop', self.scienDSpinBoxVgStop.value())
        CONF.set('Sweep', 'VgStep', self.scienDSpinBoxVgStep.value())

        vdlist_str = self.lineEditVdList.text().split(',')
        vd_list = [self._string_to_vd(x) for x in vdlist_str]
        CONF.set('Sweep', 'VdList', vd_list)

        # save output settings
        CONF.set('Sweep', 'VdStart', self.scienDSpinBoxVdStart.value())
        CONF.set('Sweep', 'VdStop', self.scienDSpinBoxVdStop.value())
        CONF.set('Sweep', 'VdStep', self.scienDSpinBoxVdStep.value())

        vglist_str = self.lineEditVgList.text().split(',')
        vg_list = [float(x) for x in vglist_str]
        CONF.set('Sweep', 'VgList', vg_list)

        # save iv settings
        CONF.set('Sweep', 'VStart', self.scienDSpinBoxVStart.value())
        CONF.set('Sweep', 'VStop', self.scienDSpinBoxVStop.value())
        CONF.set('Sweep', 'VStep', self.scienDSpinBoxVStep.value())

        CONF.set('Sweep', 'smu_sweep', self.comboBoxSweepSMU.currentText())

        # save general settings
        CONF.set('Sweep', 'tInt', self.scienDSpinBoxInt.value())
        CONF.set('Sweep', 'delay', self.scienDSpinBoxSettling.value())

        # get combo box status
        idx_pulsed = self.comboBoxSweepType.currentIndex()
        CONF.set('Sweep', 'pulsed', bool(idx_pulsed))

        CONF.set('Sweep', 'gate', self.comboBoxGateSMU.currentText())
        CONF.set('Sweep', 'drain', self.comboBoxDrainSMU.currentText())

        for tab in self.smu_tabs:

            if tab.comboBox.currentIndex() == 0:
                CONF.set(tab.smu_name, 'sense', 'SENSE_LOCAL')
            elif tab.comboBox.currentIndex() == 1:
                CONF.set(tab.smu_name, 'sense', 'SENSE_REMOTE')

            CONF.set(tab.smu_name, 'limiti', tab.scienceSpinBoxLimI.value())
            CONF.set(tab.smu_name, 'limitv', tab.scienceSpinBoxLimV.value())

    @QtCore.Slot()
    def _on_load_default(self):
        """Load default settings to interface."""

        # Set SMU selection comboBox status
        cmb_list = list(self.smu_list)  # get list of all SMUs

        # transfer curve settings
        self.scienDSpinBoxVgStart.setValue(CONF.get('Sweep', 'VgStart'))
        self.scienDSpinBoxVgStop.setValue(CONF.get('Sweep', 'VgStop'))
        self.scienDSpinBoxVgStep.setValue(CONF.get('Sweep', 'VgStep'))
        txt = str(CONF.get('Sweep', 'VdList')).strip('[]')
        self.lineEditVdList.setText(txt)

        # output curve settings
        self.scienDSpinBoxVdStart.setValue(CONF.get('Sweep', 'VdStart'))
        self.scienDSpinBoxVdStop.setValue(CONF.get('Sweep', 'VdStop'))
        self.scienDSpinBoxVdStep.setValue(CONF.get('Sweep', 'VdStep'))
        txt = str(CONF.get('Sweep', 'VgList')).strip('[]')
        self.lineEditVgList.setText(txt)

        # iv curve settings
        self.scienDSpinBoxVStart.setValue(CONF.get('Sweep', 'VStart'))
        self.scienDSpinBoxVStop.setValue(CONF.get('Sweep', 'VStop'))
        self.scienDSpinBoxVStep.setValue(CONF.get('Sweep', 'VStep'))
        try:
            idx_sweep = cmb_list.index(CONF.get('Sweep', 'smu_sweep'))
        except ValueError:
            idx_sweep = 0
            msg = 'Could not find last used SMUs in Keithley driver.'
            QtWidgets.QMessageBox.information(self, str('error'), msg)

        self.comboBoxGateSMU.setCurrentIndex(idx_sweep)

        # other
        self.scienDSpinBoxInt.setValue(CONF.get('Sweep', 'tInt'))
        self.scienDSpinBoxSettling.setValue(CONF.get('Sweep', 'delay'))

        # set PULSED comboBox index (0 if pulsed == False, 1 if pulsed == True)
        pulsed = CONF.get('Sweep', 'pulsed')
        self.comboBoxSweepType.setCurrentIndex(int(pulsed))

        # We have two comboBoxes. If there are less SMU's, extend list.
        while len(cmb_list) < 2:
            cmb_list.append('--')

        self.comboBoxGateSMU.clear()
        self.comboBoxDrainSMU.clear()
        self.comboBoxSweepSMU.clear()
        self.comboBoxGateSMU.addItems(cmb_list)
        self.comboBoxDrainSMU.addItems(cmb_list)
        self.comboBoxSweepSMU.addItems(self.smu_list)

        try:
            idx_gate = cmb_list.index(CONF.get('Sweep', 'gate'))
            idx_drain = cmb_list.index(CONF.get('Sweep', 'drain'))
            self.comboBoxGateSMU.setCurrentIndex(idx_gate)
            self.comboBoxDrainSMU.setCurrentIndex(idx_drain)
        except ValueError:
            self.comboBoxGateSMU.setCurrentIndex(0)
            self.comboBoxDrainSMU.setCurrentIndex(1)
            msg = 'Could not find last used SMUs in Keithley driver.'
            QtWidgets.QMessageBox.information(self, str('error'), msg)

        for tab in self.smu_tabs:
            sense = CONF.get(tab.smu_name, 'sense')
            if sense == 'SENSE_LOCAL':
                tab.comboBox.setCurrentIndex(0)
            elif sense == 'SENSE_REMOTE':
                tab.comboBox.setCurrentIndex(1)

            tab.scienceSpinBoxLimI.setValue(CONF.get(tab.smu_name, 'limiti'))
            tab.scienceSpinBoxLimV.setValue(CONF.get(tab.smu_name, 'limitv'))

    @QtCore.Slot()
    def exit_(self):
        self.keithley.disconnect()
        self.timer.stop()
        self.save_geometry()
        self.deleteLater()

# =============================================================================
# Interface states
# =============================================================================

    def _update_gui_connection(self):
        """Check if Keithley is connected and update GUI."""
        if self.keithley.connected and not self.keithley.busy:
            try:
                test = self.keithley.localnode.model
                self._gui_state_idle()
            except (visa.VisaIOError, visa.InvalidSession, OSError):
                self.keithley.disconnect()
                self._gui_state_disconnected()

        elif self.keithley.connected and self.keithley.busy:
            self._gui_state_busy()

        elif not self.keithley.connected:
            self._gui_state_disconnected()

    def _gui_state_busy(self):
        """Set GUI to state for running measurement."""

        self.pushButtonTransfer.setEnabled(False)
        self.pushButtonOutput.setEnabled(False)
        self.pushButtonIV.setEnabled(False)
        self.pushButtonAbort.setEnabled(True)

        self.actionConnect.setEnabled(False)
        self.actionDisconnect.setEnabled(False)

        self.statusBar.showMessage('    Measuring.')
        self.led.setChecked(True)

    def _gui_state_idle(self):
        """Set GUI to state for IDLE Keithley."""

        self.pushButtonTransfer.setEnabled(True)
        self.pushButtonOutput.setEnabled(True)
        self.pushButtonIV.setEnabled(True)
        self.pushButtonAbort.setEnabled(False)

        self.actionConnect.setEnabled(False)
        self.actionDisconnect.setEnabled(True)
        self.statusBar.showMessage('    Ready.')
        self.led.setChecked(True)

    def _gui_state_disconnected(self):
        """Set GUI to state for disconnected Keithley."""

        self.pushButtonTransfer.setEnabled(False)
        self.pushButtonOutput.setEnabled(False)
        self.pushButtonIV.setEnabled(False)
        self.pushButtonAbort.setEnabled(False)

        self.actionConnect.setEnabled(True)
        self.actionDisconnect.setEnabled(False)
        self.statusBar.showMessage('    No Keithley connected.')
        self.led.setChecked(False)

# =============================================================================
# Plotting commands
# =============================================================================

    def plot_new_data(self):
        """
        Plots the sweep data curves.
        """
        self.ax.clear()  # clear current plot

        xdata = self.sweep_data.get_column(0)
        ydata = self.sweep_data.data[:, 1:]

        if self.sweep_data.sweep_type == 'transfer':
            self.ax.set_title('Transfer data')
            lines = self.ax.semilogy(xdata, np.abs(ydata))

        elif self.sweep_data.sweep_type == 'output':
            self.ax.set_title('Output data')
            lines = self.ax.plot(xdata, np.abs(ydata))

        else:
            self.ax.set_title('IV sweep data')
            lines = self.ax.plot(xdata, ydata)

        self.ax.legend(lines, self.sweep_data.column_names[1:])
        self.ax.set_xlabel(str(self.sweep_data.titles[0]))
        self.ax.set_ylabel('Current [A]')
        self.ax.autoscale(axis='x', tight=True)
        self.canvas.draw()


class MeasureThread(QtCore.QThread):

    startedSig = QtCore.Signal()
    finishedSig = QtCore.Signal(object)

    def __init__(self, keithley, params):
        QtCore.QThread.__init__(self)
        self.keithley = keithley
        self.params = params

    def __del__(self):
        self.wait()

    def run(self):
        self.startedSig.emit()
        sweep_data = None

        if self.params['sweep_type'] == 'transfer':
            sweep_data = self.keithley.transferMeasurement(
                    self.params['smu_gate'], self.params['smu_drain'],
                    self.params['VgStart'], self.params['VgStop'], self.params['VgStep'],
                    self.params['VdList'], self.params['tInt'], self.params['delay'],
                    self.params['pulsed']
                    )
        elif self.params['sweep_type'] == 'output':
            sweep_data = self.keithley.outputMeasurement(
                    self.params['smu_gate'], self.params['smu_drain'],
                    self.params['VdStart'], self.params['VdStop'], self.params['VdStep'],
                    self.params['VgList'], self.params['tInt'], self.params['delay'],
                    self.params['pulsed']
                    )

        elif self.params['sweep_type'] == 'iv':
            direction = np.sign(self.params['VStop'] - self.params['VStart'])
            stp = direction * abs(self.params['VStep'])
            sweeplist = np.arange(self.params['VStart'], self.params['VStop'] + stp, stp)
            v_sweep, i_sweep = self.keithley.voltageSweepSingleSMU(
                    self.params['smu_sweep'], sweeplist, self.params['tInt'],
                    self.params['delay'], self.params['pulsed']
                    )

            self.keithley.reset()

            sweep_data = IVSweepData(v_sweep, i_sweep)
            sweep_data.params = {'sweep_type': 'iv', 't_int': self.params['tInt'],
                                 'delay': self.params['delay'],
                                 'pulsed': self.params['pulsed']}

        self.finishedSig.emit(sweep_data)


def run():

    import sys
    import argparse
    from keithley2600 import Keithley2600

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    args = parser.parse_args()
    if args.verbose:
        import keithley2600
        keithley2600.log_to_screen()

    keithley_address = CONF.get('Connection', 'VISA_ADDRESS')
    visa_library = CONF.get('Connection', 'VISA_LIBRARY')
    keithley = Keithley2600(keithley_address, visa_library)

    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)

    keithley_gui = KeithleyGuiApp(keithley)
    keithley_gui.show()
    app.exec_()


if __name__ == '__main__':

    run()
