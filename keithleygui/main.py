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
from keithley2600 import FETResultTable
import numpy as np

# local imports
from keithleygui.utils.led_indicator import LedIndicator
from keithleygui.utils.settings_panes import (SMUSettingsWidget, SweepSettingsWidget,
                                              TransferSweepSettingsWidget,
                                              OutputSweepSettingsWidget,
                                              IVSweepSettingsWidget)
from keithleygui.utils.pyqtplot_canvas import SweepDataPlot
from keithleygui.connection_dialog import ConnectionDialog
from keithleygui.config.main import CONF

MAIN_UI_PATH = pkgr.resource_filename('keithleygui', 'main.ui')


class KeithleyGuiApp(QtWidgets.QMainWindow):
    """ Provides a GUI for transfer and output sweeps on the Keithley 2600."""

    QUIT_ON_CLOSE = True

    def __init__(self, keithley):
        super(self.__class__, self).__init__()
        # load user interface layout from .ui file
        uic.loadUi(MAIN_UI_PATH, self)

        self.keithley = keithley
        self.smu_list = list(self.keithley.SMU_LIST)
        self.sweep_data = None

        # create sweep settings panes
        self.transfer_sweep_settings = TransferSweepSettingsWidget()
        self.output_sweep_settings = OutputSweepSettingsWidget()
        self.iv_sweep_settings = IVSweepSettingsWidget(self.smu_list)
        self.general_sweep_settings = SweepSettingsWidget(self.keithley)

        self.tabWidgetSweeps.widget(0).layout().addWidget(self.transfer_sweep_settings)
        self.tabWidgetSweeps.widget(1).layout().addWidget(self.output_sweep_settings)
        self.tabWidgetSweeps.widget(2).layout().addWidget(self.iv_sweep_settings)
        self.groupBoxSweepSettings.layout().addWidget(self.general_sweep_settings)

        # create tabs for smu settings
        self.smu_tabs = []
        for smu_name in self.smu_list:
            tab = SMUSettingsWidget(smu_name)
            self.tabWidgetSettings.addTab(tab, smu_name)
            self.smu_tabs.append(tab)

        # create plot widget
        self.canvas = SweepDataPlot()
        self.gridLayout2.addWidget(self.canvas)

        # create LED indicator
        self.led = LedIndicator(self)
        self.statusBar.addPermanentWidget(self.led)
        self.led.setChecked(False)

        # create connection dialog
        self.connectionDialog = ConnectionDialog(self, self.keithley)

        # restore last position and size
        self.restore_geometry()

        # update GUI status and connect callbacks
        self.actionSaveSweepData.setEnabled(False)
        self.connect_ui_callbacks()
        self.on_load_default()
        self.update_gui_connection()

        # connection update timer: check periodically if keithley is connected
        # and busy, act accordingly
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_gui_connection)
        self.timer.start(10000)

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
        if self.QUIT_ON_CLOSE:
            self.exit_()
        else:
            self.hide()

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

    def connect_ui_callbacks(self):
        """Connect buttons and menus to callbacks."""
        self.pushButtonRun.clicked.connect(self.on_sweep_clicked)
        self.pushButtonAbort.clicked.connect(self.on_abort_clicked)

        self.actionSettings.triggered.connect(self.connectionDialog.open)
        self.actionConnect.triggered.connect(self.on_connect_clicked)
        self.actionDisconnect.triggered.connect(self.on_disconnect_clicked)
        self.action_Exit.triggered.connect(self.exit_)
        self.actionSaveSweepData.triggered.connect(self.on_save_clicked)
        self.actionLoad_data_from_file.triggered.connect(self.on_load_clicked)
        self.actionSaveDefaults.triggered.connect(self.on_save_default)
        self.actionLoadDefaults.triggered.connect(self.on_load_default)

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

            if tab.sense_type.currentIndex() == tab.SENSE_LOCAL:
                smu.sense = smu.SENSE_LOCAL
            elif tab.sense_type.currentIndex() == tab.SENSE_REMOTE:
                smu.sense = smu.SENSE_REMOTE

            lim_i = tab.limit_i.value()
            smu.source.limiti = lim_i
            smu.trigger.source.limiti = lim_i

            lim_v = tab.limit_v.value()
            smu.source.limitv = lim_v
            smu.trigger.source.limitv = lim_v

    @QtCore.Slot()
    def on_sweep_clicked(self):
        """ Start a transfer measurement with current settings."""

        if self.keithley.busy:
            msg = ('Keithley is currently used by another program. ' +
                   'Please try again later.')
            QtWidgets.QMessageBox.information(self, str('error'), msg)

            return

        self.apply_smu_settings()

        params = dict()

        if self.tabWidgetSweeps.currentIndex() == 0:
            self.statusBar.showMessage('    Recording transfer curve.')
            # get sweep settings
            params['sweep_type'] = 'transfer'
            params['VgStart'] = self.transfer_sweep_settings.vg_start.value()
            params['VgStop'] = self.transfer_sweep_settings.vg_stop.value()
            params['VgStep'] = self.transfer_sweep_settings.vg_step.value()
            params['VdList'] = self.transfer_sweep_settings.vd_list.value()

        elif self.tabWidgetSweeps.currentIndex() == 1:
            self.statusBar.showMessage('    Recording output curve.')
            # get sweep settings
            params['sweep_type'] = 'output'
            params['VdStart'] = self.output_sweep_settings.vd_start.value()
            params['VdStop'] = self.output_sweep_settings.vd_stop.value()
            params['VdStep'] = self.output_sweep_settings.vd_step.value()
            params['VgList'] = self.output_sweep_settings.vg_list.value()

        elif self.tabWidgetSweeps.currentIndex() == 2:
            self.statusBar.showMessage('    Recording IV curve.')
            # get sweep settings
            params['sweep_type'] = 'iv'
            params['VStart'] = self.iv_sweep_settings.v_start.value()
            params['VStop'] = self.iv_sweep_settings.v_stop.value()
            params['VStep'] = self.iv_sweep_settings.v_step.value()
            smusweep = self.iv_sweep_settings.smu_sweep.currentText()
            params['smu_sweep'] = getattr(self.keithley, smusweep)

        else:
            return

        # get general sweep settings
        smu_gate = self.general_sweep_settings.smu_gate.currentText()
        smu_drain = self.general_sweep_settings.smu_drain.currentText()
        params['tInt'] = self.general_sweep_settings.t_int.value()
        params['delay'] = self.general_sweep_settings.t_settling.value()
        params['smu_gate'] = getattr(self.keithley, smu_gate)
        params['smu_drain'] = getattr(self.keithley, smu_drain)
        params['pulsed'] = bool(self.general_sweep_settings.sweep_type.currentIndex())

        # check if integration time is valid, return otherwise
        freq = self.keithley.localnode.linefreq

        if not 0.001/freq < params['tInt'] < 25.0/freq:
            msg = ('Integration time must be between 0.001 and 25 ' +
                   'power line cycles of 1/(%s Hz).' % freq)
            QtWidgets.QMessageBox.information(self, str('error'), msg)

            return

        # create measurement thread with params dictionary
        self.measureThread = MeasureThread(self.keithley, params)
        self.measureThread.finished_sig.connect(self.on_measure_done)

        # run measurement
        self._gui_state_busy()
        self.measureThread.start()

    def on_measure_done(self, sd):
        self.statusBar.showMessage('    Ready.')
        self._gui_state_idle()
        self.actionSaveSweepData.setEnabled(True)

        self.sweep_data = sd
        self.canvas.plot(self.sweep_data)
        if not self.keithley.abort_event.is_set():
            self.on_save_clicked()

    @QtCore.Slot()
    def on_abort_clicked(self):
        """
        Aborts current measurement.
        """
        self.keithley.abort_event.set()

# =============================================================================
# Interface callbacks
# =============================================================================

    @QtCore.Slot()
    def on_connect_clicked(self):
        self.keithley.connect()
        self.update_gui_connection()
        if not self.keithley.connected:
            msg = ('Keithley cannot be reached at %s. ' % self.keithley.visa_address
                   + 'Please check if address is correct and Keithley is ' +
                   'turned on.')
            QtWidgets.QMessageBox.information(self, str('error'), msg)

    @QtCore.Slot()
    def on_disconnect_clicked(self):
        self.keithley.disconnect()
        self.update_gui_connection()
        self.statusBar.showMessage('    No Keithley connected.')

    @QtCore.Slot()
    def on_save_clicked(self):
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
    def on_load_clicked(self):
        """Show GUI to load sweep data from file."""
        prompt = 'Please select a data file.'
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(self, prompt)
        if not osp.isfile(filepath):
            return

        self.sweep_data = FETResultTable()
        self.sweep_data.load(filepath)

        self.canvas.plot(self.sweep_data)
        self.actionSaveSweepData.setEnabled(True)

    @QtCore.Slot()
    def on_save_default(self):
        """Saves current settings from GUI as defaults."""

        # save sweep settings
        self.transfer_sweep_settings.save_defaults()
        self.output_sweep_settings.save_defaults()
        self.iv_sweep_settings.save_defaults()
        self.general_sweep_settings.save_defaults()

        # save smu specific settings
        for tab in self.smu_tabs:
            tab.save_defaults()

    @QtCore.Slot()
    def on_load_default(self):
        """Load default settings to interface."""

        # load sweep settings
        self.transfer_sweep_settings.load_defaults()
        self.output_sweep_settings.load_defaults()
        self.iv_sweep_settings.load_defaults()
        self.general_sweep_settings.load_defaults()

        # smu settings
        for tab in self.smu_tabs:
            tab.load_defaults()

    @QtCore.Slot()
    def exit_(self):
        self.keithley.disconnect()
        self.timer.stop()
        self.save_geometry()
        self.deleteLater()

# =============================================================================
# Interface states
# =============================================================================

    def update_gui_connection(self):
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

        self.pushButtonRun.setEnabled(False)
        self.pushButtonAbort.setEnabled(True)

        self.actionConnect.setEnabled(False)
        self.actionDisconnect.setEnabled(False)

        self.statusBar.showMessage('    Measuring.')
        self.led.setChecked(True)

    def _gui_state_idle(self):
        """Set GUI to state for IDLE Keithley."""

        self.pushButtonRun.setEnabled(True)
        self.pushButtonAbort.setEnabled(False)

        self.actionConnect.setEnabled(False)
        self.actionDisconnect.setEnabled(True)
        self.statusBar.showMessage('    Ready.')
        self.led.setChecked(True)

    def _gui_state_disconnected(self):
        """Set GUI to state for disconnected Keithley."""

        self.pushButtonRun.setEnabled(False)
        self.pushButtonAbort.setEnabled(False)

        self.actionConnect.setEnabled(True)
        self.actionDisconnect.setEnabled(False)
        self.statusBar.showMessage('    No Keithley connected.')
        self.led.setChecked(False)


class MeasureThread(QtCore.QThread):

    started_sig = QtCore.Signal()
    finished_sig = QtCore.Signal(object)

    def __init__(self, keithley, params):
        QtCore.QThread.__init__(self)
        self.keithley = keithley
        self.params = params

    def __del__(self):
        self.wait()

    def run(self):
        self.started_sig.emit()
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

            params = {'sweep_type': 'iv', 't_int': self.params['tInt'],
                      'delay': self.params['delay'], 'pulsed': self.params['pulsed']}

            sweep_data = FETResultTable(['Voltage', 'Current'], ['V', 'A'],
                                        np.array([v,i]).transpose(), params)

        self.finished_sig.emit(sweep_data)


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

    keithley_gui = KeithleyGuiApp(keithley)
    keithley_gui.show()
    app.exec_()


if __name__ == '__main__':

    run()
