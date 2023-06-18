#!/usr/bin/env python
"""
An example of using the backend
"""
import sys
from pathlib import Path

import numpy as np
from matplotlib_backend_qtquick.backend_qtquick import (
    NavigationToolbar2QtQuick)
from matplotlib_backend_qtquick.backend_qtquickagg import (
    FigureCanvasQtQuickAgg)
from matplotlib_backend_qtquick.qt_compat import QtGui, QtQml, QtCore,QtWidgets
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

class DisplayBridge(QtCore.QObject):
    """ A bridge class to interact with the plot in python
    """
    coordinatesChanged = QtCore.pyqtSignal(str)
    canvasConnected = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # The figure and toolbar
        self.canvas = None
        self.figure = None
        self.toolbar = None

        self._axes = None
        # this is used to display the coordinates of the mouse in the window
        self._coordinates = ""
        self.canvasConnected.connect(self.updateCanvas)


    @QtCore.pyqtSlot(FigureCanvasQtQuickAgg)
    def connectCanvas(self, canvas: FigureCanvasQtQuickAgg):
        """ initialize with the canvas for the figure
        """
        self.canvas = canvas
        self.figure = self.canvas.figure
        self.toolbar = NavigationToolbar2QtQuick(canvas=self.canvas)
        
        # connect for displaying the coordinates
        self.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvasConnected.emit()

    @QtCore.pyqtProperty(Axes)
    def axes(self):
        return self.figure.add_subplot(111) if self._axes is None else self._axes
        

    @QtCore.pyqtSlot()
    def updateCanvas(self):
        self.canvas.draw_idle()
 
    @QtCore.pyqtProperty(str, notify=coordinatesChanged)
    def coordinates(self):
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates):
        self._coordinates = coordinates
        self.coordinatesChanged.emit(self._coordinates)
    

    # The toolbar commands
    @QtCore.Slot()
    def pan(self, *args):
        """Activate the pan tool."""
        self.toolbar.pan(*args)

    @QtCore.Slot()
    def zoom(self, *args):
        """activate zoom tool."""
        self.toolbar.zoom(*args)

    @QtCore.Slot()
    def home(self, *args):
        self.toolbar.home(*args)

    @QtCore.Slot()
    def back(self, *args):
        self.toolbar.back(*args)

    @QtCore.Slot()
    def forward(self, *args):
        self.toolbar.forward(*args)

    def on_motion(self, event):
        """
        Update the coordinates on the display
        """
        if event.inaxes == self.axes:
            self.coordinates = f"({event.xdata:.2f}, {event.ydata:.2f})"

def shutdown():
    # https://bugreports.qt.io/browse/QTBUG-81247
    # ensures that the qml engine is destroyed before the python objects,
    del globals()["engine"]

if __name__ == "__main__":
    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication (sys.argv)
    engine = QtQml.QQmlApplicationEngine()

    # instantate the display bridge
    displayBridge = DisplayBridge()


    # Expose the Python object to QML
    context = engine.rootContext()
    context.setContextProperty("displayBridge", displayBridge)

    # matplotlib stuff
    QtQml.qmlRegisterType(FigureCanvasQtQuickAgg, "Backend", 1, 0, "FigureCanvas")

    # Load the QML file
    qmlFile = Path(Path.cwd(), Path(__file__).parent, "main.qml")
    engine.load(QtCore.QUrl.fromLocalFile(str(qmlFile)))

    fig, ax = plt.subplots()
    x = np.linspace(0, 2*np.pi, 100)
    y = np.sin(x)
    ax.plot(x, y)
    displayBridge.setAxes(ax)

    # win = engine.rootObjects()[0]
    # displayBridge.updateWithCanvas(win.findChild(QtCore.QObject, "figure"))

    app.aboutToQuit.connect(shutdown)
    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


