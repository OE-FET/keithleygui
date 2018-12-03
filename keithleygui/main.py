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


class KeithleyGuiApp(QtWidgets.QMainWindow):
    """ Provides a GUI for transfer and output sweeps on the Keithley 2600."""
    def __init__(self, keithley):
        super(self.__class__, self).__init__()
        # load user interface layout from .ui file
        uic.loadUi(MAIN_UI_PATH, self)

        self.keithley = keithley
        # create new list of smu's instead of referenceto old list
        self.smu_list = list(self.keithley.SMU_LIST)

        self._set_up_tabs()  # create Keithley settings tabs
        self._set_up_fig()  # create figure area

        # restore last position and size
        self.restoreGeometry()

        # create connection dialog
        self.connectionDialog = ConnectionDialog(self, self.keithley)

        # create LED indicator
        self.led = LedIndicator(self)
        self.led.setDisabled(True)  # Make the led non clickable
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

    def _string_to_Vd(self, string):
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

    def restoreGeometry(self):
        x = CONF.get('Window', 'x')
        y = CONF.get('Window', 'y')
        w = CONF.get('Window', 'width')
        h = CONF.get('Window', 'height')

        self.setGeometry(x, y, w, h)

    def saveGeometry(self):
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

        # This needs to be done programatically: it is impossible to specify
        # different labelcolors and tickcolors in a .mplstyle file
        self.ax.tick_params(axis='both', which='major', direction='out', labelcolor='black',
                            color=[0.5, 0.5, 0.5, 1], labelsize=9)

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color:transparent;")

        height = self.frameGeometry().height()
        self.canvas.setMinimumWidth(height)
        self.canvas.draw()

        self.gridLayout2.addWidget(self.canvas)

    def _set_up_tabs(self):
        """Create a settings tab for every SMU."""

        # get number of SMUs, create tab and grid tayout lists
        self.ntabs = len(self.smu_list)
        self.tabs = [None]*self.ntabs
        self.gridLayouts = [None]*self.ntabs

        self.labelsCbx = [None]*self.ntabs
        self.comboBoxes = [None]*self.ntabs

        self.labelsLimI = [None]*self.ntabs
        self.scienDSpinBoxsLimI = [None]*self.ntabs
        self.labelsUnitI = [None]*self.ntabs

        self.labelsLimV = [None]*self.ntabs
        self.scienDSpinBoxsLimV = [None]*self.ntabs
        self.labelsUnitV = [None]*self.ntabs

        # create a tab with combobox and scienDSpinBoxs for each SMU
        # the tab number i corresonds to the SMU number
        for i in range(0, self.ntabs):
            self.tabs[i] = QtWidgets.QWidget()
            self.tabs[i].setObjectName('tab_%s' % str(i))
            self.tabWidgetSettings.addTab(self.tabs[i], self.smu_list[i])

            self.gridLayouts[i] = QtWidgets.QGridLayout(self.tabs[i])
            self.gridLayouts[i].setObjectName('gridLayout_%s' % str(i))

            self.labelsCbx[i] = QtWidgets.QLabel(self.tabs[i])
            self.labelsCbx[i].setObjectName('labelsCbx_%s' % str(i))
            self.labelsCbx[i].setAlignment(QtCore.Qt.AlignRight)
            self.labelsCbx[i].setText('Sense type:')
            self.gridLayouts[i].addWidget(self.labelsCbx[i], 0, 0, 1, 1)

            self.comboBoxes[i] = QtWidgets.QComboBox(self.tabs[i])
            self.comboBoxes[i].setObjectName('comboBox_%s' % str(i))
            self.comboBoxes[i].setMinimumWidth(150)
            self.comboBoxes[i].setMaximumWidth(150)
            self.comboBoxes[i].addItems(['local (2-wire)', 'remote (4-wire)'])
            if CONF.get(self.smu_list[i], 'sense') is 'SENSE_LOCAL':
                self.comboBoxes[i].setCurrentIndex(0)
            elif CONF.get(self.smu_list[i], 'sense') is 'SENSE_REMOTE':
                self.comboBoxes[i].setCurrentIndex(1)
            self.gridLayouts[i].addWidget(self.comboBoxes[i], 0, 1, 1, 2)

            self.labelsLimI[i] = QtWidgets.QLabel(self.tabs[i])
            self.labelsLimI[i].setObjectName('labelLimI_%s' % str(i))
            self.labelsLimI[i].setAlignment(QtCore.Qt.AlignRight)
            self.labelsLimI[i].setText('Current limit:')
            self.gridLayouts[i].addWidget(self.labelsLimI[i], 1, 0, 1, 1)

            self.scienDSpinBoxsLimI[i] = ScienDSpinBox(self.tabs[i])
            self.scienDSpinBoxsLimI[i].setObjectName('scienDSpinBoxLimI_%s' % str(i))
            self.scienDSpinBoxsLimI[i].setMinimumWidth(90)
            self.scienDSpinBoxsLimI[i].setMaximumWidth(90)
            self.scienDSpinBoxsLimI[i].setAlignment(QtCore.Qt.AlignRight)
            self.scienDSpinBoxsLimI[i].setValue(CONF.get(self.smu_list[i], 'limiti'))
            self.scienDSpinBoxsLimI[i].setSuffix("A")
            self.gridLayouts[i].addWidget(self.scienDSpinBoxsLimI[i], 1, 1, 1, 1)

            self.labelsLimV[i] = QtWidgets.QLabel(self.tabs[i])
            self.labelsLimV[i].setObjectName('labelLimV_%s' % str(i))
            self.labelsLimV[i].setAlignment(QtCore.Qt.AlignRight)
            self.labelsLimV[i].setText('Voltage limit:')
            self.gridLayouts[i].addWidget(self.labelsLimV[i], 2, 0, 1, 1)

            self.scienDSpinBoxsLimV[i] = ScienDSpinBox(self.tabs[i])
            self.scienDSpinBoxsLimV[i].setObjectName('scienDSpinBoxLimV_%s' % str(i))
            self.scienDSpinBoxsLimV[i].setMinimumWidth(90)
            self.scienDSpinBoxsLimV[i].setMaximumWidth(90)
            self.scienDSpinBoxsLimV[i].setAlignment(QtCore.Qt.AlignRight)
            self.scienDSpinBoxsLimV[i].setValue(CONF.get(self.smu_list[i], 'limitv'))
            self.scienDSpinBoxsLimV[i].setSuffix("V")
            self.gridLayouts[i].addWidget(self.scienDSpinBoxsLimV[i], 2, 1, 1, 1)

    def connect_ui_callbacks(self):
        """Connect buttons and menues to callbacks."""
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
        for i in range(0, self.ntabs):

            smu = getattr(self.keithley, self.smu_list[i])

            if self.comboBoxes[i].currentIndex() == 0:
                smu.sense = smu.SENSE_LOCAL
            elif self.comboBoxes[i].currentIndex() == 1:
                smu.sense = smu.SENSE_REMOTE

            lim_i = self.scienDSpinBoxsLimI[i].value()
            smu.source.limiti = lim_i
            smu.trigger.source.limiti = lim_i

            lim_v = self.scienDSpinBoxsLimV[i].value()
            smu.source.limitv = lim_v
            smu.trigger.source.limitv = lim_v

    @QtCore.Slot()
    def _on_sweep_clicked(self):
        """ Start a transfer measurement with current settings."""

        if self.keithley.busy:
            msg = ('Keithley is currently used by antoher program. ' +
                   'Please try again later.')
            QtWidgets.QMessageBox.information(self, str('error'), msg)

            return

        self.apply_smu_settings()

        if self.sender() == self.pushButtonTransfer:
            self.statusBar.showMessage('    Recording transfer curve.')
            # get sweep settings
            params = {'Measurement': 'transfer'}
            params['VgStart'] = self.scienDSpinBoxVgStart.value()
            params['VgStop'] = self.scienDSpinBoxVgStop.value()
            params['VgStep'] = self.scienDSpinBoxVgStep.value()
            VdListString = self.lineEditVdList.text()
            VdStringList = VdListString.split(',')
            params['VdList'] = [self._string_to_Vd(x) for x in VdStringList]

        elif self.sender() == self.pushButtonOutput:
            self.statusBar.showMessage('    Recording output curve.')
            # get sweep settings
            params = {'Measurement': 'output'}
            params['VdStart'] = self.scienDSpinBoxVdStart.value()
            params['VdStop'] = self.scienDSpinBoxVdStop.value()
            params['VdStep'] = self.scienDSpinBoxVdStep.value()
            VgListString = self.lineEditVgList.text()
            VgStringList = VgListString.split(',')
            params['VgList'] = [float(x) for x in VgStringList]

        elif self.sender() == self.pushButtonIV:
            self.statusBar.showMessage('    Recording IV curve.')
            # get sweep settings
            params = {'Measurement': 'iv'}
            params['VStart'] = self.scienDSpinBoxVStart.value()
            params['VStop'] = self.scienDSpinBoxVStop.value()
            params['VStep'] = self.scienDSpinBoxVStep.value()

            smusweep = self.comboBoxSweepSMU.currentText()
            params['smu_sweep'] = getattr(self.keithley, smusweep)

        # get aquisition settings
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

        self.sweepData = sd
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
    def _on_smu_gate_changed(self, intSMU):
        """ Triggered when the user selects a different gate SMU. """

        if intSMU == 0 and len(self.smu_list) < 3:
            self.comboBoxDrainSMU.setCurrentIndex(1)
        elif intSMU == 1 and len(self.smu_list) < 3:
            self.comboBoxDrainSMU.setCurrentIndex(0)

    @QtCore.Slot(int)
    def _on_smu_drain_changed(self, intSMU):
        """ Triggered when the user selects a different drain SMU. """

        if intSMU == 0 and len(self.smu_list) < 3:
            self.comboBoxGateSMU.setCurrentIndex(1)
        elif intSMU == 1 and len(self.smu_list) < 3:
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
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(self, prompt, filename, formats)
        if len(filepath) < 4:
            return
        self.sweepData.save(filepath)

    @QtCore.Slot()
    def _on_load_clicked(self):
        """Show GUI to load sweep data from file."""
        prompt = 'Please select a data file.'
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(self, prompt)
        if not osp.isfile(filepath):
            return
        try:
            self.sweepData = TransistorSweepData()
            self.sweepData.load(filepath)
        except RuntimeError:
            self.sweepData = IVSweepData()
            self.sweepData.load(filepath)

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
        vd_list = [self._string_to_Vd(x) for x in vdlist_str]
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

        for i in range(0, self.ntabs):

            if self.comboBoxes[i].currentIndex() == 0:
                CONF.set(self.smu_list[i], 'sense', 'SENSE_LOCAL')
            elif self.comboBoxes[i].currentIndex() == 1:
                CONF.set(self.smu_list[i], 'sense', 'SENSE_REMOTE')

            CONF.set(self.smu_list[i], 'limiti', self.scienDSpinBoxsLimI[i].value())
            CONF.set(self.smu_list[i], 'limitv', self.scienDSpinBoxsLimV[i].value())

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

        # We have to comboBoxes. If there are less SMU's, extend list.
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

        for i in range(0, self.ntabs):
            sense = CONF.get(self.smu_list[i], 'sense')
            if sense == 'SENSE_LOCAL':
                self.comboBoxes[i].setCurrentIndex(0)
            elif sense == 'SENSE_REMOTE':
                self.comboBoxes[i].setCurrentIndex(1)

            self.scienDSpinBoxsLimI[i].setValue(CONF.get(self.smu_list[i], 'limiti'))
            self.scienDSpinBoxsLimV[i].setValue(CONF.get(self.smu_list[i], 'limitv'))

    @QtCore.Slot()
    def exit_(self):
        self.keithley.disconnect()
        self.timer.stop()
        self.saveGeometry()
        self.deleteLater()

# =============================================================================
# Interface states
# =============================================================================

    def _update_gui_connection(self):
        """Check if Keithley is connected and update GUI."""
        if self.keithley.connected and not self.keithley.busy:
            try:
                self.keithley.localnode.model
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
        Plots the transfer or output curves.
        """
        self.ax.clear()  # clear current plot

        if self.sweepData.sweepType == 'transfer':
            for v in self.sweepData.step_list():
                self.ax.semilogy(self.sweepData.vSweep[v], abs(self.sweepData.iDrain[v]), '-',
                                 label='Drain current, Vd = %s' % v)
                self.ax.semilogy(self.sweepData.vSweep[v], abs(self.sweepData.iGate[v]), '--',
                                 label='Gate current, Vd = %s' % v)
                self.ax.legend(loc=3)

            self.ax.autoscale(axis='x', tight=True)
            self.ax.set_title('Transfer data')
            self.ax.set_xlabel('Gate voltage [V]')
            self.ax.set_ylabel('Current [A]')

            self.canvas.draw()

        elif self.sweepData.sweepType == 'output':
            for v in self.sweepData.step_list():
                self.ax.plot(self.sweepData.vSweep[v],
                             abs(self.sweepData.iDrain[v]),
                             '-', label='Drain current, Vg = %s' % v)
                self.ax.plot(self.sweepData.vSweep[v],
                             abs(self.sweepData.iGate[v]),
                             '--', label='Gate current, Vg = %s' % v)
                self.ax.legend()

            self.ax.autoscale(axis='x', tight=True)
            self.ax.set_title('Output data')
            self.ax.set_xlabel('Drain voltage [V]')
            self.ax.set_ylabel('Current [A]')
            self.canvas.draw()

        elif self.sweepData.sweepType == 'iv':

            self.ax.plot(self.sweepData.v, self.sweepData.i, '-',
                         label='Current')
            self.ax.legend()

            self.ax.autoscale(axis='x', tight=True)
            self.ax.set_title('IV sweep data')
            self.ax.set_xlabel('Voltage [V]')
            self.ax.set_ylabel('Current [A]')
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

        if self.params['Measurement'] == 'transfer':
            sweepData = self.keithley.transferMeasurement(
                    self.params['smu_gate'], self.params['smu_drain'], self.params['VgStart'],
                    self.params['VgStop'], self.params['VgStep'], self.params['VdList'],
                    self.params['tInt'], self.params['delay'], self.params['pulsed']
                    )
        elif self.params['Measurement'] == 'output':
            sweepData = self.keithley.outputMeasurement(
                    self.params['smu_gate'], self.params['smu_drain'], self.params['VdStart'],
                    self.params['VdStop'], self.params['VdStep'], self.params['VgList'],
                    self.params['tInt'], self.params['delay'], self.params['pulsed']
                    )

        elif self.params['Measurement'] == 'iv':
            step = np.sign(self.params['VStop'] - self.params['VStart']) * abs(self.params['VStep'])
            sweeplist = np.arange(self.params['VStart'], self.params['VStop'] + step, step)
            vSweep, iSweep = self.keithley.voltageSweepSingleSMU(
                    self.params['smu_sweep'], sweeplist, self.params['tInt'], self.params['delay'],
                    self.params['pulsed']
                    )

            self.keithley.reset()

            sweepData = IVSweepData(vSweep, iSweep)

        self.finishedSig.emit(sweepData)


def run():

    import sys
    from keithley2600 import Keithley2600

    KEITHLEY_ADDRESS = CONF.get('Connection', 'VISA_ADDRESS')
    VISA_LIBRARY = CONF.get('Connection', 'VISA_LIBRARY')
    keithley = Keithley2600(KEITHLEY_ADDRESS, VISA_LIBRARY)

    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)

    keithleyGUI = KeithleyGuiApp(keithley)
    keithleyGUI.show()

    app.exec_()


if __name__ == '__main__':
    run()
