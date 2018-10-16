# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
keithleygui configuration options.
"""

# Local import
from config.user import UserConfig

PACKAGE_NAME = 'keithleygui'
SUBFOLDER = '.%s' % PACKAGE_NAME


# =============================================================================
#  Defaults
# =============================================================================
DEFAULTS = [
            ('Connection',
             {
              'KEITHLEY_ADDRESS': 'TCPIP0::192.168.2.121::INSTR'
              }),
            ('Sweep',
             {
              'VgStart': 10,
              'VgStop': -60,
              'VgStep': 1,
              'VdList': [-5, -60],
              'VdStart': 0,
              'VdStop': -60,
              'VdStep': 1,
              'VgList': [0, -20, -40, -60],
              'tInt': 0.1,
              'pulsed': False,
              'delay': -1,
              'gate': 'smua',
              'drain': 'smub'
             })
            ]


# =============================================================================
# Config instance
# =============================================================================
# IMPORTANT NOTES:
# 1. If you want to *change* the default value of a current option, you need to
#    do a MINOR update in config version, e.g. from 3.0.0 to 3.1.0
# 2. If you want to *remove* options that are no longer needed in our codebase,
#    or if you want to *rename* options, then you need to do a MAJOR update in
#    version, e.g. from 3.0.0 to 4.0.0
# 3. You don't need to touch this value if you're just adding a new option
CONF_VERSION = '1.0.0'

# Main configuration instance
try:
    CONF = UserConfig(PACKAGE_NAME, defaults=DEFAULTS, load=True,
                      version=CONF_VERSION, subfolder=SUBFOLDER, backup=True,
                      raw_mode=True)
except Exception:
    CONF = UserConfig(PACKAGE_NAME, defaults=DEFAULTS, load=False,
                      version=CONF_VERSION, subfolder=SUBFOLDER, backup=True,
                      raw_mode=True)
