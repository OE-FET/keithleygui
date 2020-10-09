# -*- coding: utf-8 -*-
#
# Copyright © keithleygui Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

# system imports
import os.path as osp
import pkg_resources as pkgr
import pyvisa
from PyQt5 import QtCore, QtWidgets, uic
from keithley2600 import Keithley2600, FETResultTable
import numpy as np

# local imports
from keithleygui.pyqt_labutils import LedIndicator, SettingsWidget, ConnectionDialog
from keithleygui.pyqtplot_canvas import SweepDataPlot
from keithleygui.config.main import CONF

MAIN_UI_PATH = pkgr.resource_filename("keithleygui", "main.ui")


class SMUSettingsWidget(SettingsWidget):

    SENSE_LOCAL = 0
    SENSE_REMOTE = 1

    def __init__(self, smu_name):
        SettingsWidget.__init__(self)

        self.smu_name = smu_name

        self.sense_type = self.addSelectionField(
            "Sense type:", ["local (2-wire)", "remote (4-wire)"]
        )
        self.limit_i = self.addDoubleField("Current limit:", 0.1, "A", limits=[0, 100])
        self.limit_v = self.addDoubleField("Voltage limit:", 200, "V", limits=[0, 200])
        self.high_c = self.addCheckBox("High capacitance mode", checked=False)

        self.load_defaults()

    def load_defaults(self):

        if CONF.get(self.smu_name, "sense") == "SENSE_LOCAL":
            self.sense_type.setCurrentIndex(self.SENSE_LOCAL)
        elif CONF.get(self.smu_name, "sense") == "SENSE_REMOTE":
            self.sense_type.setCurrentIndex(self.SENSE_REMOTE)

        self.limit_i.setValue(CONF.get(self.smu_name, "limiti"))
        self.limit_v.setValue(CONF.get(self.smu_name, "limitv"))
        self.high_c.setChecked(CONF.get(self.smu_name, "highc"))

    def save_defaults(self):

        if self.sense_type.currentIndex() == self.SENSE_LOCAL:
            CONF.set(self.smu_name, "sense", "SENSE_LOCAL")
        elif self.sense_type.currentIndex() == self.SENSE_REMOTE:
            CONF.set(self.smu_name, "sense", "SENSE_REMOTE")

        CONF.set(self.smu_name, "limiti", self.limit_i.value())
        CONF.set(self.smu_name, "limitv", self.limit_v.value())
        CONF.set(self.smu_name, "highc", self.high_c.isChecked())


# noinspection PyArgumentList
class SweepSettingsWidget(SettingsWidget):
    def __init__(self, keithley):
        SettingsWidget.__init__(self)

        self.keithley = keithley
        self.smu_list = list(self.keithley.SMU_LIST)

        while len(self.smu_list) < 2:
            self.smu_list.append("--")

        self.t_int = self.addDoubleField("Integration time:", 0.1, "s", [0.000016, 0.5])
        self.t_settling = self.addDoubleField(
            "Settling time (auto = -1):", -1, "s", [-1, 100]
        )
        self.sweep_type = self.addSelectionField(
            "Sweep type:", ["Continuous", "Pulsed"]
        )
        self.smu_gate = self.addSelectionField("Gate SMU:", self.smu_list, 0)
        self.smu_drain = self.addSelectionField("Drain SMU:", self.smu_list, 1)

        self.load_defaults()

        self.smu_gate.currentIndexChanged.connect(self.on_smu_gate_changed)
        self.smu_drain.currentIndexChanged.connect(self.on_smu_drain_changed)

    def load_defaults(self):

        self.t_int.setValue(CONF.get("Sweep", "tInt"))
        self.t_settling.setValue(CONF.get("Sweep", "delay"))
        self.sweep_type.setCurrentIndex(int(CONF.get("Sweep", "pulsed")))
        self.smu_gate.setCurrentText(CONF.get("Sweep", "gate"))
        self.smu_drain.setCurrentText(CONF.get("Sweep", "drain"))

    def save_defaults(self):
        CONF.set("Sweep", "tInt", self.t_int.value())
        CONF.set("Sweep", "delay", self.t_settling.value())
        CONF.set("Sweep", "gate", self.smu_gate.currentText())
        CONF.set("Sweep", "drain", self.smu_drain.currentText())

    @QtCore.pyqtSlot(int)
    def on_smu_gate_changed(self, int_smu):
        """Triggered when the user selects a different gate SMU. """

        if int_smu == 0 and len(self.smu_list) < 3:
            self.smu_drain.setCurrentIndex(1)
        elif int_smu == 1 and len(self.smu_list) < 3:
            self.smu_drain.setCurrentIndex(0)

    @QtCore.pyqtSlot(int)
    def on_smu_drain_changed(self, int_smu):
        """Triggered when the user selects a different drain SMU. """

        if int_smu == 0 and len(self.smu_list) < 3:
            self.smu_gate.setCurrentIndex(1)
        elif int_smu == 1 and len(self.smu_list) < 3:
            self.smu_gate.setCurrentIndex(0)


class TransferSweepSettingsWidget(SettingsWidget):
    def __init__(self):
        SettingsWidget.__init__(self)

        self.vg_start = self.addDoubleField("Vg start:", 0, "V")
        self.vg_stop = self.addDoubleField("Vg stop:", 0, "V")
        self.vg_step = self.addDoubleField("Vg step:", 0, "V")
        self.vd_list = self.addListField("Drain voltages:", [-5, -60])
        self.vd_list.setAcceptedStrings(["trailing"])

        self.load_defaults()

    def load_defaults(self):

        self.vg_start.setValue(CONF.get("Sweep", "VgStart"))
        self.vg_stop.setValue(CONF.get("Sweep", "VgStop"))
        self.vg_step.setValue(CONF.get("Sweep", "VgStep"))
        self.vd_list.setValue(CONF.get("Sweep", "VdList"))

    def save_defaults(self):
        CONF.set("Sweep", "VgStart", self.vg_start.value())
        CONF.set("Sweep", "VgStop", self.vg_stop.value())
        CONF.set("Sweep", "VgStep", self.vg_step.value())
        CONF.set("Sweep", "VdList", self.vd_list.value())


class OutputSweepSettingsWidget(SettingsWidget):
    def __init__(self):
        SettingsWidget.__init__(self)

        self.vd_start = self.addDoubleField("Vd start:", 0, "V")
        self.vd_stop = self.addDoubleField("Vd stop:", 0, "V")
        self.vd_step = self.addDoubleField("Vd step:", 0, "V")
        self.vg_list = self.addListField("Gate voltages:", [0, -20, -40, -60])

        self.load_defaults()

    def load_defaults(self):

        self.vd_start.setValue(CONF.get("Sweep", "VdStart"))
        self.vd_stop.setValue(CONF.get("Sweep", "VdStop"))
        self.vd_step.setValue(CONF.get("Sweep", "VdStep"))
        self.vg_list.setValue(CONF.get("Sweep", "VgList"))

    def save_defaults(self):
        CONF.set("Sweep", "VdStart", self.vd_start.value())
        CONF.set("Sweep", "VdStop", self.vd_stop.value())
        CONF.set("Sweep", "VdStep", self.vd_step.value())
        CONF.set("Sweep", "VgList", self.vg_list.value())


class IVSweepSettingsWidget(SettingsWidget):
    def __init__(self, smu_list):
        SettingsWidget.__init__(self)

        self.v_start = self.addDoubleField("Vd start:", 0, "V")
        self.v_stop = self.addDoubleField("Vd stop:", 0, "V")
        self.v_step = self.addDoubleField("Vd step:", 0, "V")
        self.smu_sweep = self.addSelectionField("Sweep SMU:", smu_list, 0)

        self.load_defaults()

    def load_defaults(self):

        self.v_start.setValue(CONF.get("Sweep", "VStart"))
        self.v_stop.setValue(CONF.get("Sweep", "VStop"))
        self.v_step.setValue(CONF.get("Sweep", "VStep"))
        self.smu_sweep.setCurrentText(CONF.get("Sweep", "smu_sweep"))

    def save_defaults(self):
        CONF.set("Sweep", "VStart", self.v_start.value())
        CONF.set("Sweep", "VStop", self.v_stop.value())
        CONF.set("Sweep", "VStep", self.v_step.value())
        CONF.set("Sweep", "smu_sweep", self.smu_sweep.currentText())


# noinspection PyArgumentList
class KeithleyGuiApp(QtWidgets.QMainWindow):
    """ Provides a GUI for transfer and output sweeps on the Keithley 2600."""

    QUIT_ON_CLOSE = True

    def __init__(self, keithley=None):
        super().__init__()
        # load user interface layout from .ui file
        uic.loadUi(MAIN_UI_PATH, self)

        if keithley:
            self.keithley = keithley
        else:
            address = CONF.get("Connection", "VISA_ADDRESS")
            lib = CONF.get("Connection", "VISA_LIBRARY")
            self.keithley = Keithley2600(address, lib)

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
        self.connectionDialog = ConnectionDialog(self, self.keithley, CONF)

        # restore last position and size
        self.restore_geometry()

        # update GUI status and connect callbacks
        self.actionSaveSweepData.setEnabled(False)
        self.connect_ui_callbacks()
        self.on_load_default()
        self.update_gui_connection()

        # connection update timer: check periodically if keithley is connected
        self.connection_status_update = QtCore.QTimer()
        self.connection_status_update.timeout.connect(self.update_gui_connection)
        self.connection_status_update.start(10000)  # 10 sec

    @staticmethod
    def _string_to_vd(string):
        try:
            return float(string)
        except ValueError:
            if "trailing" in string:
                return "trailing"
            else:
                raise ValueError("Invalid drain voltage.")

    def closeEvent(self, event):
        if self.QUIT_ON_CLOSE:
            self.exit_()
        else:
            self.hide()

    # =============================================================================
    # GUI setup
    # =============================================================================

    def restore_geometry(self):
        x = CONF.get("Window", "x")
        y = CONF.get("Window", "y")
        w = CONF.get("Window", "width")
        h = CONF.get("Window", "height")

        self.setGeometry(x, y, w, h)

    def save_geometry(self):
        geo = self.geometry()
        CONF.set("Window", "height", geo.height())
        CONF.set("Window", "width", geo.width())
        CONF.set("Window", "x", geo.x())
        CONF.set("Window", "y", geo.y())

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

            smu.source.highc = int(tab.high_c.isChecked())

    @QtCore.pyqtSlot()
    def on_sweep_clicked(self):
        """ Start a transfer measurement with current settings."""

        if self.keithley.busy:
            msg = (
                "Keithley is currently used by another program. "
                + "Please try again later."
            )
            QtWidgets.QMessageBox.information(self, str("error"), msg)

            return

        self.apply_smu_settings()

        params = dict()

        if self.tabWidgetSweeps.currentIndex() == 0:
            self.statusBar.showMessage("    Recording transfer curve.")
            # get sweep settings
            params["sweep_type"] = "transfer"
            params["VgStart"] = self.transfer_sweep_settings.vg_start.value()
            params["VgStop"] = self.transfer_sweep_settings.vg_stop.value()
            params["VgStep"] = self.transfer_sweep_settings.vg_step.value()
            params["VdList"] = self.transfer_sweep_settings.vd_list.value()

        elif self.tabWidgetSweeps.currentIndex() == 1:
            self.statusBar.showMessage("    Recording output curve.")
            # get sweep settings
            params["sweep_type"] = "output"
            params["VdStart"] = self.output_sweep_settings.vd_start.value()
            params["VdStop"] = self.output_sweep_settings.vd_stop.value()
            params["VdStep"] = self.output_sweep_settings.vd_step.value()
            params["VgList"] = self.output_sweep_settings.vg_list.value()

        elif self.tabWidgetSweeps.currentIndex() == 2:
            self.statusBar.showMessage("    Recording IV curve.")
            # get sweep settings
            params["sweep_type"] = "iv"
            params["VStart"] = self.iv_sweep_settings.v_start.value()
            params["VStop"] = self.iv_sweep_settings.v_stop.value()
            params["VStep"] = self.iv_sweep_settings.v_step.value()
            smusweep = self.iv_sweep_settings.smu_sweep.currentText()
            params["smu_sweep"] = getattr(self.keithley, smusweep)

        else:
            return

        # get general sweep settings
        smu_gate = self.general_sweep_settings.smu_gate.currentText()
        smu_drain = self.general_sweep_settings.smu_drain.currentText()
        params["tInt"] = self.general_sweep_settings.t_int.value()
        params["delay"] = self.general_sweep_settings.t_settling.value()
        params["smu_gate"] = getattr(self.keithley, smu_gate)
        params["smu_drain"] = getattr(self.keithley, smu_drain)
        params["pulsed"] = bool(self.general_sweep_settings.sweep_type.currentIndex())

        # check if integration time is valid, return otherwise
        freq = self.keithley.localnode.linefreq

        if not 0.001 / freq < params["tInt"] < 25.0 / freq:
            msg = (
                "Integration time must be between 0.001 and 25 "
                + "power line cycles of 1/(%s Hz)." % freq
            )
            QtWidgets.QMessageBox.information(self, str("error"), msg)

            return

        # create measurement thread with params dictionary
        self.measureThread = MeasureThread(self.keithley, params)
        self.measureThread.finished_sig.connect(self.on_measure_done)

        # run measurement
        self._gui_state_busy()
        self.measureThread.start()

    def on_measure_done(self, sd):
        self.statusBar.showMessage("    Ready.")
        self._gui_state_idle()
        self.actionSaveSweepData.setEnabled(True)

        self.sweep_data = sd
        self.canvas.plot(self.sweep_data)
        if not self.keithley.abort_event.is_set():
            self.on_save_clicked()

    @QtCore.pyqtSlot()
    def on_abort_clicked(self):
        """
        Aborts current measurement.
        """
        self.keithley.abort_event.set()

    # =============================================================================
    # Interface callbacks
    # =============================================================================

    @QtCore.pyqtSlot()
    def on_connect_clicked(self):
        self.keithley.connect()
        self.update_gui_connection()
        if not self.keithley.connected:
            msg = (
                "Keithley cannot be reached at %s. " % self.keithley.visa_address
                + "Please check if address is correct and Keithley is "
                + "turned on."
            )
            QtWidgets.QMessageBox.information(self, str("error"), msg)

    @QtCore.pyqtSlot()
    def on_disconnect_clicked(self):
        self.keithley.disconnect()
        self.update_gui_connection()
        self.statusBar.showMessage("    No Keithley connected.")

    @QtCore.pyqtSlot()
    def on_save_clicked(self):
        """Show GUI to save current sweep data as text file."""
        prompt = "Save as .txt file."
        filename = "untitled.txt"
        formats = "Text file (*.txt)"
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, prompt, filename, formats
        )
        if len(filepath) < 4:
            return
        self.sweep_data.save(filepath)

    @QtCore.pyqtSlot()
    def on_load_clicked(self):
        """Show GUI to load sweep data from file."""
        prompt = "Please select a data file."
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(self, prompt)
        if not osp.isfile(filepath):
            return

        self.sweep_data = FETResultTable()
        self.sweep_data.load(filepath)

        self.canvas.plot(self.sweep_data)
        self.actionSaveSweepData.setEnabled(True)

    @QtCore.pyqtSlot()
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

    @QtCore.pyqtSlot()
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

    @QtCore.pyqtSlot()
    def exit_(self):
        self.keithley.disconnect()
        self.connection_status_update.stop()
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
            except (pyvisa.VisaIOError, pyvisa.InvalidSession, OSError):
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

        self.statusBar.showMessage("    Measuring.")
        self.led.setChecked(True)

    def _gui_state_idle(self):
        """Set GUI to state for IDLE Keithley."""

        self.pushButtonRun.setEnabled(True)
        self.pushButtonAbort.setEnabled(False)

        self.actionConnect.setEnabled(False)
        self.actionDisconnect.setEnabled(True)
        self.statusBar.showMessage("    Ready.")
        self.led.setChecked(True)

    def _gui_state_disconnected(self):
        """Set GUI to state for disconnected Keithley."""

        self.pushButtonRun.setEnabled(False)
        self.pushButtonAbort.setEnabled(False)

        self.actionConnect.setEnabled(True)
        self.actionDisconnect.setEnabled(False)
        self.statusBar.showMessage("    No Keithley connected.")
        self.led.setChecked(False)


# noinspection PyUnresolvedReferences
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

        if self.params["sweep_type"] == "transfer":
            sweep_data = self.keithley.transferMeasurement(
                self.params["smu_gate"],
                self.params["smu_drain"],
                self.params["VgStart"],
                self.params["VgStop"],
                self.params["VgStep"],
                self.params["VdList"],
                self.params["tInt"],
                self.params["delay"],
                self.params["pulsed"],
            )
        elif self.params["sweep_type"] == "output":
            sweep_data = self.keithley.outputMeasurement(
                self.params["smu_gate"],
                self.params["smu_drain"],
                self.params["VdStart"],
                self.params["VdStop"],
                self.params["VdStep"],
                self.params["VgList"],
                self.params["tInt"],
                self.params["delay"],
                self.params["pulsed"],
            )

        elif self.params["sweep_type"] == "iv":
            direction = np.sign(self.params["VStop"] - self.params["VStart"])
            stp = direction * abs(self.params["VStep"])
            sweeplist = np.arange(
                self.params["VStart"], self.params["VStop"] + stp, stp
            )
            v, i = self.keithley.voltageSweepSingleSMU(
                self.params["smu_sweep"],
                sweeplist,
                self.params["tInt"],
                self.params["delay"],
                self.params["pulsed"],
            )

            self.keithley.beeper.beep(0.3, 2400)
            self.keithley.reset()

            params = {
                "sweep_type": "iv",
                "t_int": self.params["tInt"],
                "delay": self.params["delay"],
                "pulsed": self.params["pulsed"],
            }

            sweep_data = FETResultTable(
                ["Voltage", "Current"], ["V", "A"], np.array([v, i]).transpose(), params
            )

        self.finished_sig.emit(sweep_data)


def run():

    import sys
    import argparse
    from keithley2600 import log_to_screen

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    args = parser.parse_args()
    if args.verbose:
        log_to_screen()

    app = QtWidgets.QApplication(sys.argv)

    keithley_gui = KeithleyGuiApp()
    keithley_gui.show()
    app.exec()


if __name__ == "__main__":

    run()
