import time
import machine

class Servo:

    def __init__(self, pin):
        servo_pin = machine.Pin(4, machine.Pin.OUT)
        self._servo = machine.PWM(servo_pin)
        self._servo.freq(50) # servos run with 50Hz
        self.angle = 90

    @property
    def angle(self):
        return self._angle


    @angle.setter
    def angle(self, value):
        v = 0.002 / 180.0 * value + .0005
        v = int(1024 / 0.02 * v)
        self._servo.duty(v)
