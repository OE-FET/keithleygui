#### v1.1.4 (2019-10-09)

This release focuses on cosmetic improvements.

##### Changed:

- Depend on our own fork of PyQtGraph `cx_pyqtgraph`.

##### Added:

- Support for dark interface themes, such as the dark mode in macOS Mojave. This will
  require a version of PyQt / Qt which supports system themes, such as v5.12 for macOS.

#### v1.1.3 (2019-07-17)

##### Changed:

- Moved utils to submodule `pyqt_labutils`.
- Updated requirements.

#### v1.1.2 (2019-05-20)

##### Changed:

- Fixed a bug which caused `from keithleygui.config import CONF` to fail in Python 2.7.
- Fixed a critical error which would prevent IV sweeps from returning a dataset.

#### v1.1.1 (2019-05-16)

##### Changed:

- Adaptations to driver changes.
- `KeithleyGuiApp` must now be explicitly imported from main.

#### v1.1.0 (2019-05-01)

##### Changed:

- Unified and simplified code across all settings panels. This results in some GUI
  changes as well: All settings panels now have a two-column layout.

#### v1.0.2 (2019-03-12)

##### Changed:

- Switched from matplotlib to PyQtGraph as plotting library.
