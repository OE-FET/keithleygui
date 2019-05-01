# -*- coding: utf-8 -*-
#
# Copyright © keithleygui Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

from __future__ import division, absolute_import, print_function
import sys
from qtpy import QtGui, QtCore, QtWidgets


PY2 = sys.version[0] == '2'

if not PY2:
    basestring = str  # in Python 3


class ListValidator(QtGui.QValidator):
    """
    This is a validator for a list float values.
    """

    accepted_strings = []

    def validate(self, string, position):
        """
        This is the actual validator. It checks whether the current user input is a valid string
        every time the user types a character. There are 3 states that are possible.
        1) Invalid: The current input string is invalid. The user input will not accept the last
                    typed character.
        2) Acceptable: The user input in conform with the regular expression and will be accepted.
        3) Intermediate: The user input is not a valid string yet but on the right track. Use this
                         return value to allow the user to type fill-characters needed in order to
                         complete an expression (i.e. the decimal point of a float value).
        :param string: The current input string (from a QLineEdit for example)
        :param position: The current position of the text cursor
        :return: enum QValidator::State: the returned validator state,
                 str: the input string, int: the cursor position
        """

        string_list = string.split(',')
        validated_list = [self.validate_string(x) for x in string_list]

        if self.Invalid in validated_list:
            return self.Invalid, string, position
        elif self.Intermediate in validated_list:
            return self.Intermediate, string, position
        else:
            return self.Acceptable, string, position

    def validate_string(self, text):

        text = text.strip()
        text = text.rstrip()

        try:
            float(text)
            return self.Acceptable
        except ValueError:

            if text in ['', '-', '+']:
                return self.Intermediate

            for string in self.accepted_strings:
                if string == text:
                    return self.Acceptable
                elif string.startswith(text):
                    return self.Intermediate

            return self.Invalid


class FloatListWidget(QtWidgets.QLineEdit):

    _accepted_strings = []

    def __init__(self, *args, **kwargs):
        super(FloatListWidget, self).__init__(*args, **kwargs)

        self.validator_ = ListValidator()
        self.validator_.accepted_strings = self._accepted_strings
        self.setValidator(self.validator_)

    def value(self):

        text = self.text()
        string_list = text.split(',')

        return [self._string_to_value(x) for x in string_list]

    def setValue(self, value_list):

        string_list = []

        for value in value_list:
            if value in self._accepted_strings:
                string_list.append(value)
            elif isinstance(value, float) and value.is_integer():
                string_list.append(str(int(value)))
            else:
                string_list.append(str(value))

        string = ', '.join(string_list)

        string = string.replace('  ', ' ')
        string = string.strip()

        self.setText(string)

    def setAcceptedStrings(self, string_list):

        if not all([isinstance(x, basestring) for x in string_list]):
            raise ValueError('Input must be a list of strings.')

        self._accepted_strings = string_list
        self.validator_.accepted_strings = string_list

    def acceptedStrings(self):
        return self._accepted_strings

    def _string_to_value(self, string):
        try:
            return float(string)
        except ValueError:
            if string in self._accepted_strings:
                return string
            else:
                raise ValueError('Invalid drain voltage.')
