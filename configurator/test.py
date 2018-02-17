import sys
import struct

from PyQt5 import QtGui, QtSvg, QtWidgets, QtSerialPort, QtCore

class SerialPortReader(QtCore.QObject):

    TIMEOUT = 5000

    def __init__(self, protocol, port, parent=None):
        super().__init__(parent)
        self._port = port
        self._port.readyRead.connect(self._handle_ready_read)
        self._port.error.connect(self._handle_error)
        self._protocol = protocol


    def _handle_ready_read(self):
        self._protocol.feed(self._port.readAll())


    def _handle_error(self, error):
        print("error occured", error)


class SerialProtocol:
    PAYLOAD = "IfHH"
    LAYOUT =  PAYLOAD + "B"

    def __init__(self):
        self._buffer = b""


    def feed(self, data):
        self._buffer += bytes(data)
        while self._buffer:
            pos = self._buffer.index(b"{")
            end = pos + struct.calcsize(self.LAYOUT) + 1
            try:
                right_boundary = chr(self._buffer[end])
            except IndexError:
                # we don't have yet enough data, just
                # break
                break
            else:
                if right_boundary == '}':
                    self._parse_message(self._buffer[pos+1:end])
                    self._buffer = self._buffer[end+1:]
                else:
                    # we didn't arrive at a correct boundary,
                    # lets throw away the data in question
                    self._buffer = self._buffer[pos+1:]


    def _parse_message(self, message):
        crc = message[-1]
        h = 0
        for c in message[:-1]:
            h += c
        h = h & 0xff
        if h == crc:
            # successfully decoded a message
            print(struct.unpack(self.PAYLOAD, message[:-1]))


def main():
    app = QtWidgets.QApplication(sys.argv)
    port_info = [
        port for port in QtSerialPort.QSerialPortInfo.availablePorts()
        if "arduino" in port.manufacturer().lower()
        ][0]
    print(port_info.systemLocation())

    port = QtSerialPort.QSerialPort(port_info)
    port.open(QtCore.QIODevice.ReadWrite)

    protocol = SerialProtocol()
    reader = SerialPortReader(protocol, port)

    svgWidget = QtSvg.QSvgWidget('NASA_Logo.svg')
    svgWidget.setGeometry(50,50,759,668)
    svgWidget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
