"""
Script to read logged data from plugged in teensy,
write it to `sensor-data.csv`, and then plot the
results using matplotlib

Probably requires Python >= 3.7, and for the `serial` and `matplotlib`
libraries to be installed

TODO:
* automatically detect which port the teensy is on
  https://alknemeyer.github.io/embedded-comms-with-python
* add proper command line args (output filename, whether to plot)
  using the argparse module
"""
from typing import List, NamedTuple
import csv
import serial
import struct
import time


class Packet(NamedTuple):
    time: float
    height_m: float
    boom_encoder_val: int
    accel_x_mss: float
    accel_y_mss: float
    accel_z_mss: float
    gyro_x_rads: float
    gyro_y_rads: float
    gyro_z_rads: float
    mag_x_uT: float
    mag_y_uT: float
    mag_z_uT: float


HEADER = bytes([0xAA, 0x55])
DATAFMT = '<if9f'


def _fmt(s: str):
    return [s.format(ax) for ax in 'xyz']


PACKET_HEADER = ['time', 'height [m]', 'boom pos [encoder val]'] + \
    _fmt('accel {} [m/s^2]') + \
    _fmt('gyro {} [rad/s]') + \
    _fmt('mag {} [uT]')


class TeensyLogger:
    def __init__(self, port: str):
        print('connecting to teensy... ', end='')
        self.ser = serial.Serial(port, 250_000)
        print('done')

    def read(self) -> Packet:
        self.ser.reset_input_buffer()
        self.ser.read_until(HEADER)

        data_bytes = self.ser.read(struct.calcsize(DATAFMT))
        boom_pos, height, *imudata = struct.unpack(
            DATAFMT, data_bytes,
        )

        return Packet(time.time(), height/1000, boom_pos, *imudata)

    def read_and_log_until_ctrl_c(self, display: bool = True) -> List[Packet]:
        data: List[Packet] = []

        while True:
            try:
                packet = self.read()

                if display is True:
                    print(f'height = {packet.height_m*1000:3.0f} mm, '
                          f'boom pos = {packet.boom_encoder_val:4.3f}, '
                          f'imu acceleration = '
                          f'{packet.accel_x_mss:3.1f} '
                          f'{packet.accel_y_mss:3.1f} '
                          f'{packet.accel_z_mss:3.1f}')

                data.append(packet)

            except KeyboardInterrupt:
                break

        return data


if __name__ == '__main__':
    data = TeensyLogger(port='/dev/ttyACM0').read_and_log_until_ctrl_c()

    if len(data) == 0:
        print('Got no data!')
        quit()

    ##
    print('Writing file...')
    with open('sensor-data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PACKET_HEADER)
        writer.writerows(data)

    ##
    print('Plotting...')
    import matplotlib.pyplot as plt
    plt.style.use('seaborn')
    sampletimes = [d.time - data[0].time for d in data]

    fig, (ax0, ax1, ax2) = plt.subplots(3, 1)

    dt = data[-1].time-data[0].time
    ax0.set_title(f'{len(data)} packets in {dt:.2f} seconds.\n'
                  f'Avg sample time = {1000*dt/len(data):.2f} ms/sample')

    ax0.plot(sampletimes, [d.height_m for d in data], label='height [m]')
    ax0.legend()

    ax1.plot(sampletimes, [d.boom_encoder_val
                           for d in data], label='encoder count')
    ax1.legend()

    ax2.plot(sampletimes, [d.accel_x_mss for d in data], label='accel-x')
    ax2.plot(sampletimes, [d.accel_y_mss for d in data], label='accel-y')
    ax2.plot(sampletimes, [d.accel_z_mss for d in data], label='accel-z')
    ax2.legend()
    plt.show()
