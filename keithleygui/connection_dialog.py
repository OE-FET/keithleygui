# -*- coding: utf-8 -*-
#
# Copyright © keithleygui Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

from __future__ import division, print_function, absolute_import
import os.path as osp
import pkg_resources as pkgr
import visa
import pyvisa
from qtpy import QtCore, QtWidgets, uic

# local imports
from keithleygui.config.main import CONF

CONNECTION_UI_PATH = pkgr.resource_filename('keithleygui', 'connection_dialog.ui')


class ConnectionDialog(QtWidgets.QDialog):

    def __init__(self, parent, instr):
        super(self.__class__, self).__init__(parent=parent)
        # load user interface layout from .ui file
        uic.loadUi(CONNECTION_UI_PATH, self)

        self.instr = instr

        # populate UI
        self.populate_ui_from_instr()

        # connect callbacks
        self.checkBoxAutoVisa.clicked.connect(self._on_auto_checked)
        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.populate_ui_from_instr)
        self.buttonBox.helpRequested.connect(self._on_help_clicked)
        self.pushButtonChoose.clicked.connect(self._on_choose_clicked)
        self.pushButtonSearch.clicked.connect(self._on_search_clicked)

    @QtCore.Slot()
    def populate_ui_from_instr(self):
        is_auto = self.instr.visa_library == ''
        self.checkBoxAutoVisa.setChecked(is_auto)
        self._on_auto_checked(is_auto)
        self._on_search_clicked()  # search for instrument addresses

    @QtCore.Slot(bool)
    def _on_auto_checked(self, checked):
        """Switch from automatic to manual visa library selection."""
        if checked:
            self.labelVisaLib.hide()
            self.lineEditLibrary.hide()
            self.pushButtonChoose.hide()
            self.lineEditLibrary.setText('')
        else:
            self.labelVisaLib.show()
            self.lineEditLibrary.show()
            self.pushButtonChoose.show()
            self.lineEditLibrary.setText(self.instr.visa_library)

    @QtCore.Slot()
    def _on_choose_clicked(self):
        """Select path to VISA library."""
        prompt = 'Please select a DLL.'
        filepath = QtWidgets.QFileDialog.getOpenFileName(self, prompt)
        if not osp.isfile(filepath[0]):
            return
        self.lineEditLibrary.setText(filepath[0])

    @QtCore.Slot()
    def _on_search_clicked(self):
        # set Address comboBox status
        self.comboBoxAddress.clear()
        self.comboBoxAddress.addItems([self.instr.visa_address])
        self.comboBoxAddress.addItems(self.instr.rm.list_resources())
        self.comboBoxAddress.setCurrentIndex(0)

    @QtCore.Slot()
    def _on_accept(self):
        """ Update connection settings, reconnect with new settings."""
        self.instr.visa_library = self.lineEditLibrary.text()
        self.instr.visa_address = self.comboBoxAddress.currentText()

        CONF.set('Connection', 'VISA_LIBRARY', self.instr.visa_library)
        CONF.set('Connection', 'VISA_ADDRESS', self.instr.visa_address)

        # reconnect with new address
        # close and reopen ResourceManager for visa_lib path change to take effect
        if self.instr.connected:
            self.instr.disconnect()

        self.instr.rm.close()

        try:
            self.instr.rm = visa.ResourceManager(self.instr.visa_library)

        except ValueError:
            msg = ('Could not find backend %s.\n' % self.lineEditLibrary.text() +
                   'Using default backend instead.')
            QtWidgets.QMessageBox.information(self, str('error'), msg)

            self.instr.visa_library = ''
            self.instr.rm = visa.ResourceManager()

            self.populate_ui_from_instr()

        self.instr.connect()

    @QtCore.Slot()
    def _on_help_clicked(self):
        """Show dialog box with help."""

        ni_visa_link = 'https://www.ni.com/visa/'

        msg = """
        <p><br/>If "%s" is selected, NI-VISA will be automatically detected and used. If
        NI-VISA is not installed, pyvisa-py will be used as a fallback. Alternatively, you
        may manually select the NI-VISA library path or select the pyvisa-py backend by
        entering "@py" in the path field.</p>

        <p>All detected visa instruments will be listed, but automatic detection may not
        work with instruments connected via Ethernet or on remote computers.</p>

        <p>You can get NI-VISA here: <a href="%s"> %s</a>.</p>

        <p><b>PyVisa detected the following setup:</b></p>
        """ % (self.checkBoxAutoVisa.text(), ni_visa_link, ni_visa_link)

        visa_info = pyvisa.util.get_debug_info(to_screen=False)
        visa_info = '<p style="white-space: pre-wrap;">' + visa_info + '\n </p>'

        text = ('<body style="margin-right:20px; margin-left:20px;">' +
                msg + visa_info + '</body>')

        self.helpText = QtWidgets.QTextBrowser()
        self.helpText.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.helpText.setHtml(text)
        self.helpText.setOpenExternalLinks(True)
        self.helpText.resize(500, 400)
        self.helpText.show()
