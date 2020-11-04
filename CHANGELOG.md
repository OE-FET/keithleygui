### v1.2.0

#### Changed:

- Don't make any assumptions about the number of available SMUs but adapt GUI after a
  Keithley has been connected.
- Adapted to work with v2.0.0 of the keithley2600 driver.
- Improved error messages.

### v1.1.8

#### Changed:

- Replaced deprecated `visa` import with `pyvisa`.

### v1.1.7

#### Added:

- Provide option for high capacitance mode.

#### Changed:

- Create our own keithley instance if none is provided.
- Depend on the newly released pyqtgraph 0.11.
  
#### Fixed:

- Fixed an issue where the color of legend labels would not update when switching to a
  dark UI.

### v1.1.6 (2020-03-06)

#### Changed:

- Depend on pyqtgraph 0.11.0rc0 instead of cx_pyqtgraph. All of our pull requests have
  been merged to upstream.
- Use Matlab palette for line colors. This provides 7 different colors which will be
  reused once exhausted.


### v1.1.5 (2019-12-13)

This version drops support for Python 2.7. Only Python 3.6 and higher are supported.

#### Changed:

- Depend on PyQt5 instead of qtpy.
- Resize connection dialog when hiding PyVisa backend textbox.
- Move connection dialog to submodule 'pyqt_labutils'.
- Update submodule 'pyqt_labutils'.

#### Removed:

- Support for Python 2.7.

### v1.1.4 (2019-10-09)

This release focuses on cosmetic improvements.

#### Changed:

- Depend on our own fork of PyQtGraph `cx_pyqtgraph`.

#### Added:

- Support for dark interface themes, such as the dark mode in macOS Mojave. This will
  require a version of PyQt / Qt which supports system themes, such as v5.12 for macOS.

### v1.1.3 (2019-07-17)

#### Changed:

- Moved utils to submodule `pyqt_labutils`.
- Updated requirements.

### v1.1.2 (2019-05-20)

#### Changed:

- Fixed a bug which caused `from keithleygui.config import CONF` to fail in Python 2.7.
- Fixed a critical error which would prevent IV sweeps from returning a dataset.

### v1.1.1 (2019-05-16)

#### Changed:

- Adaptations to driver changes.
- `KeithleyGuiApp` must now be explicitly imported from main.

### v1.1.0 (2019-05-01)

#### Changed:

- Unified and simplified code across all settings panels. This results in some GUI
  changes as well: All settings panels now have a two-column layout.

### v1.0.2 (2019-03-12)

#### Changed:

- Switched from matplotlib to PyQtGraph as plotting library.
