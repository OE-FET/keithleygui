from PyQt5 import QtWidgets
from keithleygui import KeithleyGuiApp

app = QtWidgets.QApplication([])

keithley_gui = KeithleyGuiApp()
keithley_gui.show()
app.exec()