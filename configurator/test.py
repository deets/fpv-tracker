import sys
from PyQt5 import QtGui, QtSvg, QtWidgets, QtSerialPort, QtCore

class SerialPortReader(QtCore.QObject):

    TIMEOUT = 5000

    def __init__(self, port, parent=None):
        super().__init__(parent)
        self._port = port
        self._port.readyRead.connect(self._handle_ready_read)
        self._port.error.connect(self._handle_error)


    def _handle_ready_read(self):
        print(self._port.readAll())
        if not self._timer.isActive():
            self._timer.start(self.TIMEOUT)


    def _handle_error(self, error):
        print("error occured", error)


def main():
    app = QtWidgets.QApplication(sys.argv)
    port_info = [
        port for port in QtSerialPort.QSerialPortInfo.availablePorts()
        if "arduino" in port.manufacturer().lower()
        ][0]
    print(port_info.systemLocation())

    port = QtSerialPort.QSerialPort(port_info)
    port.open(QtCore.QIODevice.ReadWrite)

    reader = SerialPortReader(port)

    svgWidget = QtSvg.QSvgWidget('NASA_Logo.svg')
    svgWidget.setGeometry(50,50,759,668)
    svgWidget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
