[![PyPi Release](https://img.shields.io/pypi/v/keithleygui.svg?style=flat)](https://pypi.org/project/keithleygui/)
[![Build Status](https://travis-ci.com/OE-FET/keithleygui.svg?branch=master)](https://travis-ci.com/OE-FET/keithleygui)

# keithleygui
A high-level user interface for Keithley 2600 series instruments which allows
the user to configure, record and save voltage sweeps such as transfer and
output measurements. Since there typically is no need to provide a live stream
of readings from the Keithley, the data from an IV-curve is buffered locally on
the instrument and only transferred to CustomXepr after completion of a
measurement.

![Screenshot of the user interface](https://github.com/OE-FET/keithleygui/blob/master/screenshots/KeithleyGUI.png?raw=true)

## System requirements
*Required*:

- Linux or macOS
- Python 2.7 or 3.x

## Installation
Download or clone the repository. Install the package by running 
```console
$ pip install git+https://github.com/OE-FET/keithleygui
```

## Acknowledgements
- Config modules are based on the implementation from [Spyder](https://github.com/spyder-ide).
- Scientific spin boxes are taken from [qudi](https://github.com/Ulm-IQO/qudi).
