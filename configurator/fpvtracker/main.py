import sys
import bisect

from PyQt5 import QtGui, QtSvg, QtWidgets, QtCore

from .communication import SerialPortReader, SerialProtocol


class RSSIRenderer(QtCore.QObject):

    def __init__(self, protocol, view, history_length=10, parent=None):
        super().__init__(parent)
        protocol.status_message.connect(self._status_message)
        self._view = view
        self._history_length = history_length
        self._latest_timestamp = None
        self._messages = []

        self._scene = QtWidgets.QGraphicsScene(self._view)

        path = QtGui.QPainterPath()
        path.moveTo(-10, 0)
        path.lineTo(0, 1023)
        pen = QtGui.QPen()
        pen.setWidth(2 / 60)
        pen.setColor(QtGui.QColor(0, 255, 0))
        self._right_item = self._scene.addPath(path, pen)

        pen = QtGui.QPen()
        pen.setWidth(2 / 60)
        pen.setColor(QtGui.QColor(255, 0, 0))
        self._left_item = self._scene.addPath(QtGui.QPainterPath(), pen)

        self._view.setScene(self._scene)

        t = QtGui.QTransform()
        t.scale(
            self._view.width() * .9 / history_length,
            -self._view.height() * .9 / 1024,
        )
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
            left_path, right_path = QtGui.QPainterPath(), QtGui.QPainterPath()
            s = self._messages[0]

            left_path.moveTo(s[0] - ts, s[1])
            right_path.moveTo(s[0] - ts, s[2])

            h = []
            for p in self._messages[1:]:
                x = p[0] - ts
                h.append(x)
                left_path.lineTo(x, p[1])
                right_path.lineTo(x, p[2])
            #print(left_path.boundingRect())

            self._left_item.setPath(left_path)
            self._right_item.setPath(right_path)
            self._scene.update()


def main():
    app = QtWidgets.QApplication(sys.argv)

    protocol = SerialProtocol()
    reader = SerialPortReader.open_default_port(protocol)

    # svgWidget = QtSvg.QSvgWidget('NASA_Logo.svg')
    # svgWidget.setGeometry(50,50,759,668)
    # svgWidget.show()
    gv = QtWidgets.QGraphicsView()
    gv.setGeometry(50,50,700,600)
    gv.show()
    renderer = RSSIRenderer(protocol, gv)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
