# -*- coding: utf-8 -*-
#
# Copyright © keithleygui Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

from __future__ import division, print_function, absolute_import
from qtpy import QtCore, QtWidgets


from keithleygui.utils.scientific_spinbox import ScienSpinBox, ScienDSpinBox
from keithleygui.utils.list_entry_widget import FloatListWidget
from keithleygui.config.main import CONF


class SettingsWidget(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setVerticalSpacing(5)

    def addDoubleField(self, name, value, unit=None, limits=None):

        label = QtWidgets.QLabel(self)
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        label.setText(name)

        spinbox = ScienDSpinBox(self)
        spinbox.setMinimumWidth(90)
        spinbox.setMaximumWidth(90)
        spinbox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        spinbox.setValue(value)
        if unit:
            spinbox.setSuffix(unit)
        if limits:
            spinbox.setRange(*limits)

        n_rows = self.gridLayout.rowCount()

        self.gridLayout.addWidget(label, n_rows, 0, 1, 1)
        self.gridLayout.addWidget(spinbox, n_rows, 1, 1, 1)

        return spinbox

    def addIntField(self, name, value, unit=None, limits=None):

        label = QtWidgets.QLabel(self)
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        label.setText(name)

        spinbox = ScienSpinBox(self)
        spinbox.setMinimumWidth(90)
        spinbox.setMaximumWidth(90)
        spinbox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        spinbox.setValue(value)
        if unit:
            spinbox.setSuffix(unit)
        if limits:
            spinbox.setRange(*limits)

        n_rows = self.gridLayout.rowCount()

        self.gridLayout.addWidget(label, n_rows, 0, 1, 1)
        self.gridLayout.addWidget(spinbox, n_rows, 1, 1, 1)

        return spinbox

    def addSelectionField(self, name, choices, index=0):

        label = QtWidgets.QLabel(self)
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        label.setText(name)

        combobox = QtWidgets.QComboBox(self)
        combobox.setMinimumWidth(150)
        combobox.setMaximumWidth(150)
        combobox.addItems(choices)
        combobox.setCurrentIndex(index)

        n_rows = self.gridLayout.rowCount()

        self.gridLayout.addWidget(label, n_rows, 0, 1, 1)
        self.gridLayout.addWidget(combobox, n_rows, 1, 1, 2)

        return combobox

    def addListField(self, name, value_list):

        label = QtWidgets.QLabel(self)
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        label.setText(name)

        list_field = FloatListWidget(self)
        list_field.setMinimumWidth(150)
        list_field.setMaximumWidth(150)
        list_field.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        list_field.setValue(value_list)

        n_rows = self.gridLayout.rowCount()

        self.gridLayout.addWidget(label, n_rows, 0, 1, 1)
        self.gridLayout.addWidget(list_field, n_rows, 1, 1, 2)

        return list_field


class SMUSettingsWidget(SettingsWidget):

    SENSE_LOCAL = 0
    SENSE_REMOTE = 1

    def __init__(self, smu_name):
        SettingsWidget.__init__(self)

        self.smu_name = smu_name

        self.sense_type = self.addSelectionField('Sense type:', ['local (2-wire)', 'remote (4-wire)'])
        self.limit_i = self.addDoubleField('Current limit:', 0.1, 'A', limits=[0, 100])
        self.limit_v = self.addDoubleField('Voltage limit:', 200, 'V', limits=[0, 200])

        self.load_defaults()

    def load_defaults(self):

        if CONF.get(self.smu_name, 'sense') == 'SENSE_LOCAL':
            self.sense_type.setCurrentIndex(self.SENSE_LOCAL)
        elif CONF.get(self.smu_name, 'sense') == 'SENSE_REMOTE':
            self.sense_type.setCurrentIndex(self.SENSE_REMOTE)

        self.limit_i.setValue(CONF.get(self.smu_name, 'limiti'))
        self.limit_v.setValue(CONF.get(self.smu_name, 'limitv'))

    def save_defaults(self):

        if self.sense_type.currentIndex() == self.SENSE_LOCAL:
            CONF.set(self.smu_name, 'sense', 'SENSE_LOCAL')
        elif self.sense_type.currentIndex() == self.SENSE_REMOTE:
            CONF.set(self.smu_name, 'sense', 'SENSE_REMOTE')

        CONF.set(self.smu_name, 'limiti', self.limit_i.value())
        CONF.set(self.smu_name, 'limitv', self.limit_v.value())


class SweepSettingsWidget(SettingsWidget):

    def __init__(self, keithley):
        SettingsWidget.__init__(self)

        self.keithley = keithley
        self.smu_list = list(self.keithley.SMU_LIST)

        while len(self.smu_list) < 2:
            self.smu_list.append('--')

        self.t_int = self.addDoubleField('Integration time:', 0.1, 's', [0.000016, 0.5])
        self.t_settling = self.addDoubleField('Settling time (auto = -1):', -1, 's', [-1, 100])
        self.sweep_type = self.addSelectionField('Sweep type:', ['Continuous', 'Pulsed'])
        self.smu_gate = self.addSelectionField('Gate SMU:', self.smu_list, 0)
        self.smu_drain = self.addSelectionField('Drain SMU:', self.smu_list, 1)

        self.load_defaults()

        self.smu_gate.currentIndexChanged.connect(self.on_smu_gate_changed)
        self.smu_drain.currentIndexChanged.connect(self.on_smu_drain_changed)

    def load_defaults(self):

        self.t_int.setValue(CONF.get('Sweep', 'tInt'))
        self.t_settling.setValue(CONF.get('Sweep', 'delay'))
        self.sweep_type.setCurrentIndex(int(CONF.get('Sweep', 'pulsed')))
        self.smu_gate.setCurrentText(CONF.get('Sweep', 'gate'))
        self.smu_drain.setCurrentText(CONF.get('Sweep', 'drain'))

    def save_defaults(self):
        CONF.set('Sweep', 'tInt', self.t_int.value())
        CONF.set('Sweep', 'delay', self.t_settling.value())
        CONF.set('Sweep', 'gate', self.smu_gate.currentText())
        CONF.set('Sweep', 'drain', self.smu_drain.currentText())

    @QtCore.Slot(int)
    def on_smu_gate_changed(self, int_smu):
        """Triggered when the user selects a different gate SMU. """

        if int_smu == 0 and len(self.smu_list) < 3:
            self.smu_drain.setCurrentIndex(1)
        elif int_smu == 1 and len(self.smu_list) < 3:
            self.smu_drain.setCurrentIndex(0)

    @QtCore.Slot(int)
    def on_smu_drain_changed(self, int_smu):
        """Triggered when the user selects a different drain SMU. """

        if int_smu == 0 and len(self.smu_list) < 3:
            self.smu_gate.setCurrentIndex(1)
        elif int_smu == 1 and len(self.smu_list) < 3:
            self.smu_gate.setCurrentIndex(0)


class TransferSweepSettingsWidget(SettingsWidget):

    def __init__(self):
        SettingsWidget.__init__(self)

        self.vg_start = self.addDoubleField('Vg start:', 0, 'V')
        self.vg_stop = self.addDoubleField('Vg stop:', 0, 'V')
        self.vg_step = self.addDoubleField('Vg step:', 0, 'V')
        self.vd_list = self.addListField('Drain voltages:', [-5, -60])
        self.vd_list.setAcceptedStrings(['trailing'])

        self.load_defaults()

    def load_defaults(self):

        self.vg_start.setValue(CONF.get('Sweep', 'VgStart'))
        self.vg_stop.setValue(CONF.get('Sweep', 'VgStop'))
        self.vg_step.setValue(CONF.get('Sweep', 'VgStep'))
        self.vd_list.setValue(CONF.get('Sweep', 'VdList'))

    def save_defaults(self):
        CONF.set('Sweep', 'VgStart', self.vg_start.value())
        CONF.set('Sweep', 'VgStop', self.vg_stop.value())
        CONF.set('Sweep', 'VgStep', self.vg_step.value())
        CONF.set('Sweep', 'VdList', self.vd_list.value())


class OutputSweepSettingsWidget(SettingsWidget):

    def __init__(self):
        SettingsWidget.__init__(self)

        self.vd_start = self.addDoubleField('Vd start:', 0, 'V')
        self.vd_stop = self.addDoubleField('Vd stop:', 0, 'V')
        self.vd_step = self.addDoubleField('Vd step:', 0, 'V')
        self.vg_list = self.addListField('Gate voltages:', [0, -20, -40, -60])

        self.load_defaults()

    def load_defaults(self):

        self.vd_start.setValue(CONF.get('Sweep', 'VdStart'))
        self.vd_stop.setValue(CONF.get('Sweep', 'VdStop'))
        self.vd_step.setValue(CONF.get('Sweep', 'VdStep'))
        self.vg_list.setValue(CONF.get('Sweep', 'VgList'))

    def save_defaults(self):
        CONF.set('Sweep', 'VdStart', self.vd_start.value())
        CONF.set('Sweep', 'VdStop', self.vd_stop.value())
        CONF.set('Sweep', 'VdStep', self.vd_step.value())
        CONF.set('Sweep', 'VgList', self.vg_list.value())


class IVSweepSettingsWidget(SettingsWidget):

    def __init__(self, smu_list):
        SettingsWidget.__init__(self)

        self.v_start = self.addDoubleField('Vd start:', 0, 'V')
        self.v_stop = self.addDoubleField('Vd stop:', 0, 'V')
        self.v_step = self.addDoubleField('Vd step:', 0, 'V')
        self.smu_sweep = self.addSelectionField('Sweep SMU:', smu_list, 0)

        self.load_defaults()

    def load_defaults(self):

        self.v_start.setValue(CONF.get('Sweep', 'VStart'))
        self.v_stop.setValue(CONF.get('Sweep', 'VStop'))
        self.v_step.setValue(CONF.get('Sweep', 'VStep'))
        self.smu_sweep.setCurrentText(CONF.get('Sweep', 'smu_sweep'))

    def save_defaults(self):
        CONF.set('Sweep', 'VStart', self.v_start.value())
        CONF.set('Sweep', 'VStop', self.v_stop.value())
        CONF.set('Sweep', 'VStep', self.v_step.value())
        CONF.set('Sweep', 'smu_sweep', self.smu_sweep.currentText())
