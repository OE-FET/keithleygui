#### v1.1.3 (2019-07-17):

_Changed:_

- Moved utils to submodule `pyqt_labutils`.
- Updated requirements.

#### v1.1.2 (2019-05-20):

_Changed:_

- Fixed a bug which caused `from keithleygui.config import CONF` to fail in Python 2.7.
- Fixed a critical error which would prevent IV sweeps from returning a dataset.

#### v1.1.1 (2019-05-16):

_Changed:_

- Adaptations to driver changes.
- `KeithleyGuiApp` must now be explicitly imported from main.

#### v1.1.0 (2019-05-01):

_Changed:_

- Unified and simplified code across all settings panels. This results in some GUI
  changes as well: All settings panels now have a two-column layout.

#### v1.0.2 (2019-03-12):

_Changed:_

- Switched from Matplotlib to PyQtGraph as plotting library.
