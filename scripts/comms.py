"""
Script to read logged data from plugged in teensy,
write it to `sensor-data.csv`, and then plot the
results using matplotlib

Probably requires Python >= 3.7, and for the `serial` and `matplotlib`
libraries to be installed
"""
from typing import List, NamedTuple
import csv
import serial
from serial.tools.list_ports import comports
import struct
import time


delay = 0.5 # increase if transmission is failing

TRANSCIEVER_PARAMS = {
    'baudrate': 9600,
    'stopbits': serial.STOPBITS_ONE,
    'parity': serial.PARITY_NONE,
    'bytesize': serial.EIGHTBITS,
    'timeout': 5
}

class HexapodRemote:
    def __init__(self):
        # find transciever
        print('connecting to transciever...', end='')
        from serial.tools.list_ports import comports
        devices = [dev for dev in comports() if dev.description == 'FT232R USB UART - FT232R USB UART']
        if len(devices) == 0:
            raise RuntimeError(f"Couldn't find transciever")
        elif len(devices) == 1:
            dev = devices[0]
        else:
            raise RuntimeError(f'Found more than one transciever: {devices}')
        print('Connected')

        with serial.Serial(dev.device, **TRANSCIEVER_PARAMS) as remote:
            # set baud rate
            packet = [0xA3, 0x3A, 0x02]
            remote.write(serial.to_bytes(packet))
            remote.read_until(serial.to_bytes([0xAA])) # wait for reciept confirmation

            # set channel
            packet = [0xA7, 0x7A, 0x01]
            remote.write(serial.to_bytes(packet))
            remote.read_until(serial.to_bytes([0xAA])) # wait for reciept confirmation

            # set ID
            packet = [0xA9, 0x9A, 0x01, 0x01]
            remote.write(serial.to_bytes(packet))
            remote.read_until(serial.to_bytes([0xAA])) # wait for reciept confirmation

            # set TX power
            packet = [0xAB, 0xBA, 0x0A]
            remote.write(serial.to_bytes(packet))
            remote.read_until(serial.to_bytes([0xAA])) # wait for reciept confirmation
            
            # check that configuration is correct
            packet = [0xA6, 0x6A]
            remote.write(serial.to_bytes(packet))

            header = [0xA6]
            remote.read_until(serial.to_bytes(header))
            data_bytes = remote.read(6)
            print([x for x in data_bytes])


if __name__ == '__main__':
    remote = HexapodRemote()
