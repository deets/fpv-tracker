import os
import sys
import bisect

from PyQt5 import QtGui, QtSvg, QtWidgets, QtCore
from PyQt5.uic import loadUi

from .communication import SerialPortReader, SerialProtocol


class RSSIRenderer(QtCore.QObject):

    def __init__(self, protocol, view, color, selector, history_length=10, parent=None):
        super().__init__(parent)
        self._selector = selector
        protocol.status_message.connect(self._status_message)
        self._view = view
        self._history_length = history_length
        self._latest_timestamp = None
        self._messages = []

        self._scene = QtWidgets.QGraphicsScene(self._view)

        pen_width = self._view.width() * .9 / self._history_length

        path = QtGui.QPainterPath()
        path.moveTo(-10, 0)
        path.lineTo(0, 1023)
        pen = QtGui.QPen()
        pen.setWidth(2 / pen_width)
        pen.setColor(color)
        self._item = self._scene.addPath(path, pen)
        self._view.setScene(self._scene)
        self._view.installEventFilter(self)
        self._fit_view()


    def eventFilter(self, view, event):
        if event.type() == QtCore.QEvent.Resize:
            self._fit_view()
        return False


    def _fit_view(self):
        t = QtGui.QTransform()
        sx, sy = self._view.width() / self._history_length, -self._view.height() / 1024,
        t.scale(sx, sy)
        self._view.setTransform(t)


    def _status_message(self, message):
        ts, angle, left, right = message
        ts /= 1000.0
        self._latest_timestamp = ts
        cutoff = ts - self._history_length
        self._messages.append((ts, left, right))
        index = bisect.bisect_left(
            self._messages,
            (cutoff, -1, -1),
        )
        self._messages = self._messages[index:]


        if len(self._messages):
            path = QtGui.QPainterPath()
            s = self._messages[0]
            sel = self._selector

            path.moveTo(s[0] - ts, sel(s))

            for p in self._messages[1:]:
                x = p[0] - ts
                path.lineTo(x, sel(p))

            self._item.setPath(path)
            self._scene.update()


def main():
    app = QtWidgets.QApplication(sys.argv)

    protocol = SerialProtocol()
    reader = SerialPortReader.open_default_port(protocol)

    main_window = QtWidgets.QMainWindow()
    loadUi(os.path.join(os.path.dirname(__file__), "mainwindow.ui"), main_window)

    main_window.show()
    left_renderer = RSSIRenderer(
        protocol,
        main_window.left_rssi_view,
        QtGui.QColor(0, 255, 0),
        lambda message: message[1]
    )
    right_renderer = RSSIRenderer(
        protocol,
        main_window.right_rssi_view,
        QtGui.QColor(255, 0, 0),
        lambda message: message[2]
    )
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
