[![PyPi Release](https://img.shields.io/pypi/v/keithleygui.svg?style=flat)](https://pypi.org/project/keithleygui/)
[![Downloads](https://pepy.tech/badge/keithleygui)](https://pepy.tech/project/keithleygui)
[![Build Status](https://travis-ci.com/OE-FET/keithleygui.svg?branch=master)](https://travis-ci.com/OE-FET/keithleygui)

**Warning:** Keithleygui v1.1.4 will be the last release that is developed and tested for
Python 2.7. Future releases will only support Python 3.6 and higher.

# keithleygui
A high-level user interface for Keithley 2600 series instruments which allows
the user to configure, record and save voltage sweeps such as transfer and
output measurements. Since there typically is no need to provide a live stream
of readings from the Keithley, the data from an IV-curve is buffered locally on
the instrument and only transferred to CustomXepr after completion of a
measurement.

![Screenshot of the user interface](screenshots/KeithleyGUI.png)

## Installation
Install the stable version from PyPI by running
```console
$ pip install keithleygui
```
Or install the latest development version from GitHub:
```console
$ pip install git+https://github.com/OE-FET/keithleygui
```

## System requirements

- Linux or macOS
- Python 3.6 or higher

## Acknowledgements
- Config modules are based on the implementation from [Spyder](https://github.com/spyder-ide).
- Scientific spin boxes are taken from [qudi](https://github.com/Ulm-IQO/qudi).
