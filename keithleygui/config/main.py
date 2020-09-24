# -*- coding: utf-8 -*-
#
# Copyright © keithleygui Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)

"""
keithleygui configuration options.
"""

# Local import
from keithleygui.config.user import UserConfig
from keithley2600 import Keithley2600

PACKAGE_NAME = "keithleygui"
SUBFOLDER = ".%s" % PACKAGE_NAME


# =============================================================================
#  Defaults
# =============================================================================
DEFAULTS = [
    (
        "Window",
        {
            "x": 0,
            "y": 0,
            "width": 1200,
            "height": 733,
        },
    ),
    (
        "Connection",
        {"VISA_ADDRESS": "TCPIP0::192.168.1.121::INSTR", "VISA_LIBRARY": ""},
    ),
    (
        "Sweep",
        {
            "VgStart": 10.0,
            "VgStop": -60.0,
            "VgStep": 1.0,
            "VdList": [-5, -60],
            "VdStart": 0.0,
            "VdStop": -60.0,
            "VdStep": 1.0,
            "VgList": [0, -20, -40, -60],
            "VStart": -10.0,
            "VStop": 10.0,
            "VStep": 1.0,
            "smu_sweep": Keithley2600.SMU_LIST[0],
            "tInt": 0.1,
            "pulsed": False,
            "delay": -1.0,
            "gate": Keithley2600.SMU_LIST[0],
            "drain": Keithley2600.SMU_LIST[1],
        },
    ),
]


for smu in Keithley2600.SMU_LIST:
    smu_settings = (
        smu,
        {
            "sense": "SENSE_LOCAL",
            "limitv": 200.0,
            "limiti": 0.1,
            "highc": False,
        },
    )
    DEFAULTS.append(smu_settings)

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
CONF_VERSION = "4.0.0"

# Main configuration instance
try:
    CONF = UserConfig(
        PACKAGE_NAME,
        defaults=DEFAULTS,
        load=True,
        version=CONF_VERSION,
        subfolder=SUBFOLDER,
        backup=True,
        raw_mode=True,
    )
except Exception:
    CONF = UserConfig(
        PACKAGE_NAME,
        defaults=DEFAULTS,
        load=False,
        version=CONF_VERSION,
        subfolder=SUBFOLDER,
        backup=True,
        raw_mode=True,
    )
