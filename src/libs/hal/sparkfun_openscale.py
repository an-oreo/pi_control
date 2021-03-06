#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
calibration and taring
python3.6 -m serial.tools.miniterm /dev/ttyUSB0

pi_control
sparkfun_openscale.py
Author: Danyal Ahsanullah
Date: 6/29/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: library for interfacing the Sparkfun OpenScale.
"""

import os
import yaml
import serial
from os.path import join as ospjoin
from typing import Tuple, Dict, Union
from libs.hal.constants import LOCK

CFG_FILE_PATH = ospjoin(os.environ.get('OPENSCALE_CFG_PATH', '../../CONFIGS/'), 'openscale_cfg.yml')


class OpenScale(serial.Serial):
    BAUDRATES = (1200, 1800, 2400, 4800, 9600, 19200, 38400, 57600,
                 115200, 230400, 460800, 500000, 576000, 921600, 1000000)
    # prompt for initial opening of config menu:
    #
    # Serial Load Cell Converter version 1.0
    # By SparkFun Electronics
    # No remote sensor found
    # System Configuration
    # 1) Tare scale to zero [8647409]
    # 2) Calibrate scale [262]
    # 3) Timestamp [On]
    # 4) Set report rate [953]
    # 5) Set baud rate [9600 bps]
    # 6) Change units of measure [kg]
    # 7) Decimals [4]
    # 8) Average amount [10]
    # 9) Local temp [On]
    # r) Remote temp [On]
    # s) Status LED [Off]
    # t) Serial trigger [On]
    # q) Raw reading [Off]
    # c) Trigger character: [48]
    # x) Exit
    # >

    # b'1) Tare scale to zero [\d+]\r\n'\
    # b'2) Calibrate scale[\d+]\r\n'\
    # b'3) Timestamp [On|Off]\r\n'\
    # b'4) Set report rate [\d+]\r\n'\
    # b'5) Set baud rate [\d+ bps]\r\n'\
    # b'6) Change units of measure [lbs|kg]\r\n'\
    # b'7) Decimals [\d+]\r\n'\
    # b'8) Average amount [\d+]\r\n'\
    # b'9) Local temp [On|Off]\r\n'\
    # b'r) Remote temp [On|Off]\r\n'\
    # b's) Status LED [Blink|Off]\r\n'\
    # b't) Serial trigger [On|Off]\r\n'\
    # b'q) Raw reading [On|Off]\r\n'\
    # b'c) Trigger character: [\d+]\r\n'\
    # b'x) Exit\r\n'\
    # b'>'

    prompt_indexes = (
        ('tare', 23),
        ('calibrate', 20),
        ('timestamp', 14),
        ('report_rate', 20),
        ('baud', 18),
        ('units', 28),
        ('decimal_places', 13),
        ('num_avg', 19),
        ('local_temp_enable', 15),
        ('remote_temp_enable', 16),
        ('status_led', 15),
        ('serial_trigger_enable', 19),
        ('raw_reading', 16),
        ('trigger_char', 23),
    )

    first_read = True

    def __init__(self, tare: int = 18304, cal_value: int = 0, timestamp_enable: bool = True, report_rate: int = 200,
                 units: str = 'kg', decimal_places: int = 4, num_avgs: int = 2, local_temp_enable: bool = False,
                 remote_temp_enable: bool = False, status_led: bool = True, serial_trigger_enable: bool = True,
                 raw_reading_enable: bool = False, trigger_char: bytes = b'0', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tare_val: int = tare
        self._tare_val_1: int = 0
        self._tare_val_2: int = 0
        self._cal_value: int = cal_value
        self._timestamp_enable: bool = timestamp_enable
        self._report_rate: int = report_rate
        self._units: str = units
        self._decimal_places: int = decimal_places
        self._num_avgs: int = num_avgs
        self._local_temp_enable: bool = local_temp_enable
        self._remote_temp_enable: bool = remote_temp_enable
        self._status_led: bool = status_led
        self._serial_trigger_enable: bool = serial_trigger_enable
        self._raw_reading_enable: bool = raw_reading_enable
        self._trigger_char: bytes = trigger_char
        # input command mapping
        self.cmds = {
            'open_menu': b'x',  # no eol
            'close_menu': b'x',  # no eol
            'tare': b'1',  # no eol
            'calibrate': b'2',  # no eol, leads to increment/decrement -> 'x' to close
            'increment': b'+',  # no eol, leads to increment/decrement -> 'x' to close
            'decrement': b'-',  # no eol, leads to increment/decrement -> 'x' to close
            'timestamp': b'3',  # no eol, toggles between enabled/disabled
            'report_rate': b'4',  # no eol, leads to increment/decrement -> 'x' to close
            'baud': b'5',  # requires EOL, enter a quantity
            'units': b'6',  # no eol, toggles between lbs and kg
            'decimals': b'7',  # no eol, leads to increment/decrement -> 'x' to close
            'avg_amt': b'8',  # no eol, leads to increment/decrement -> 'x' to close
            'local_temp': b'9',  # no eol, toggles between enabled/disabled
            'remote_temp': b'r',  # no eol, toggles between enabled/disabled
            'status_led': b's',  # no eol, toggles between enabled/disabled
            'serial_trigger': b't',  # no eol, toggles between enabled/disabled
            'raw_reading': b'q',  # no eol, toggles between enabled/disabled
            'trigger_char': b'c',  # no eol, next char entered is the new trigger char
        }
        self.write(b'x')
        # self.read_until(b'>')
        # self.load_config_from_device()

    def load_config_from_device(self):
        if not self.is_open:
            self.open()
        res = self.parse_menu_response()
        # noinspection SpellCheckingInspection
        self.baudrate = res['baud']
        self._tare_val = res['tare']
        self._timestamp_enable = res['timestamp']
        self._local_temp_enable = res['local_temp_enable']
        self._remote_temp_enable = res['remote_temp_enable']
        self._cal_value = res['calibrate']
        self._report_rate = res['report_rate']
        self._units = res['units']
        self._decimal_places = res['decimal_places']
        self._num_avgs = res['num_avg']
        self._status_led = res['status_led']
        self._serial_trigger_enable = res['serial_trigger_enable']
        self._raw_reading_enable = res['raw_reading']
        self._trigger_char = res['trigger_char']

        self.write(self.cmds['close_menu'])

    def parse_menu_response(self):
        """
        [
        '',
        'Serial Load Cell Converter version 1.0',
        'By SparkFun Electronics',
        'No remote sensor found',
        'System Configuration',
        '1) Tare scale to zero [8647409]',
        '2) Calibrate scale [262]',
        '3) Timestamp [On]',
        '4) Set report rate [953]',
        '5) Set baud rate [9600 bps]',
        '6) Change units of measure [kg]',
        '7) Decimals [4]',
        '8) Average amount [10]',
        '9) Local temp [On]',
        'r) Remote temp [On]',
        's) Status LED [Off]',
        't) Serial trigger [On]',
        'q) Raw reading [Off]',
        'c) Trigger character: [48]',
        'x) Exit',
        '>'
        ]
        """

        if not self.is_open:
            self.open()
        #     keep separate to help timings
        #
        # self.reset_output_buffer()
        self.reset_input_buffer()
        self.flush()
        self.write(self.cmds['open_menu'])  # wakes up device
        self.write(self.cmds['open_menu'])
        # from time import sleep; sleep(0.2)
        # self.flush()
        print('write query')
        # from time import sleep; sleep(0.5)
        # print(self.readline())
        # self.write(self.cmds['open_menu'])
        raw_res = self.read_until(b'>').decode('utf-8').split('\r\n')[5:-2]

        print(raw_res)
        res = {
            'tare': None,
            'calibrate': None,
            'timestamp': None,
            'report_rate': None,
            'baud': None,
            'units': None,
            'decimal_places': None,
            'num_avg': None,
            'local_temp_enable': None,
            'remote_temp_enable': None,
            'status_led': None,
            'serial_trigger_enable': None,
            'raw_reading': None,
            'trigger_char': None,
        }
        for line, index_tuple in zip(raw_res, self.prompt_indexes):
            res[index_tuple[0]] = line[index_tuple[1]:-1]
        res['trigger_char'] = chr(int(res['trigger_char'])).encode('utf-8')
        res['baud'] = int(res['baud'][:-4])
        for key in ('tare', 'calibrate', 'report_rate', 'decimal_places', 'num_avg'):
            res[key] = int(res[key])
        for key in ('timestamp', 'local_temp_enable', 'remote_temp_enable',
                    'status_led', 'serial_trigger_enable', 'raw_reading'):
            res[key] = False if res[key] == 'Off' else True

        self.write(self.cmds['close_menu'])
        return res

    def triggered_read(self):
        self.reset_input_buffer()
        self.write(self.trigger_char)
        self.reset_input_buffer()

    @property
    def timestamp_enable(self):
        return self._timestamp_enable

    @timestamp_enable.setter
    def timestamp_enable(self, enable: bool):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        if self._timestamp_enable != enable:
            self.write(self.cmds['timestamp'])
            self._timestamp_enable = enable
        self.write(self.cmds['close_menu'])

    @property
    def report_rate(self):
        return self._report_rate

    @report_rate.setter
    def report_rate(self, value: int):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        diff = self._report_rate - value
        if diff == 0:
            return
        elif diff > 0:  # decrement `diff` times
            self.write(self.cmds['report_rate'])
            for i in range(1, diff):
                self.write(self.cmds['decrement'])
            self.reset_input_buffer()
            self._report_rate = value
        elif diff < 0:  # increment `diff` times
            self.write(self.cmds['report_rate'])
            for i in range(1, diff):
                self.write(self.cmds['increment'])
            self.reset_input_buffer()
            self._report_rate = value
        self.write(self.cmds['close_menu'])

    @property
    def calibrate(self):
        return self._cal_value

    @calibrate.setter
    def calibrate(self, value: int):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        diff = self._cal_value - value
        if diff == 0:
            return
        elif diff > 0:  # decrement `diff` times
            self.write(self.cmds['calibrate'])
            for i in range(1, diff):
                self.write(self.cmds['decrement'])
                self.flush()
            self.reset_input_buffer()
        elif diff < 0:  # increment `diff` times
            self.write(self.cmds['calibrate'])
            for i in range(1, -diff):
                self.write(self.cmds['increment'])
                self.flush()
            self.reset_input_buffer()
        self.write(self.cmds['close_menu'])
        self._cal_value = value

    @property
    def trigger_char(self):
        return self._trigger_char

    @trigger_char.setter
    def trigger_char(self, char: (str, bytes)) -> None:
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        if len(char) != 1:
            raise ValueError('length of trigger char must be 1')
        self._trigger_char = bytes(char, 'utf-8')
        self.write(self.cmds['trigger_char'])
        self.write(self._trigger_char)

    @property
    def local_temp_enable(self):
        return self._local_temp_enable

    @local_temp_enable.setter
    def local_temp_enable(self, enable: bool):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        if self._local_temp_enable != enable:
            self.write(self.cmds['local_temp'])
            self._local_temp_enable = enable

        self.write(self.cmds['close_menu'])

    @property
    def remote_temp_enable(self):
        return self._remote_temp_enable

    @remote_temp_enable.setter
    def remote_temp_enable(self, enable: bool):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        if self._remote_temp_enable != enable:
            self.write(self.cmds['remote_temp'])
            self._remote_temp_enable = enable

        self.write(self.cmds['close_menu'])

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, unit: str):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        if self._units != unit:
            self.write(self.cmds['units'])
            self._units = unit
        self.write(self.cmds['close_menu'])

    @property
    def decimals(self):
        return self._decimal_places

    @decimals.setter
    def decimals(self, places: int):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        if self._decimal_places != places:
            self.write(self.cmds['decimals'])
            self._decimal_places = places
        self.write(self.cmds['close_menu'])

    @property
    def num_avgs(self):
        return self._num_avgs

    @num_avgs.setter
    def num_avgs(self, n_avgs: int):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        if self._num_avgs != n_avgs:
            self.write(self.cmds['avg_amt'])
            self.write(n_avgs)
            self._num_avgs = n_avgs

    @property
    def status_led(self):
        return self._status_led

    @status_led.setter
    def status_led(self, enable: bool):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        if self._status_led != enable:
            self.write(self.cmds['status_led'])
            self._status_led = enable
        self.write(self.cmds['close_menu'])

    @property
    def raw_reading_enable(self):
        return self._raw_reading_enable

    @raw_reading_enable.setter
    def raw_reading_enable(self, enable: bool):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        if self._raw_reading_enable != enable:
            self.write(self.cmds['raw_reading'])
            self._raw_reading_enable = enable
        self.write(self.cmds['close_menu'])

    @property
    def serial_trigger_enable(self):
        return self._serial_trigger_enable

    @serial_trigger_enable.setter
    def serial_trigger_enable(self, enable: bool):
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        if self._serial_trigger_enable != enable:
            self.write(self.cmds['serial_trigger'])
            self._serial_trigger_enable = enable
        self.write(self.cmds['close_menu'])

    @property
    def tare(self):
        return self._tare_val

    def tare_device(self) -> Tuple[int, int]:
        """tares scale and returns tare offset(s)"""
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        # self.reset_input_buffer()

        # b'\n\rTare point 1: [\d+]\r\n'\
        # b'\n\rTare point 2: [\d+]\r\n'
        self.write(self.cmds['tare'])
        self.read_until(b'Tare point 1: ')
        tare_val_1: int = int(self.read_until(b'\r\n').strip())
        self.read_until(b'Tare point 2: ')
        tare_val_2: int = int(self.read_until(b'\r\n').strip())
        self.write(self.cmds['close_menu'])
        return tare_val_1, tare_val_2

    def read_cal_info(self) -> Dict[str, Union[float, str, int]]:
        """Returns end result calibration value"""
        if not self.is_open:
            self.open()
            # keep separate to help timings
        self.reset_output_buffer()
        self.write(self.cmds['open_menu'])
        self.flush()
        self.reset_input_buffer()

        # b'Scale calibration\r\n'\
        # b'Remove all weight from scale\r\n'
        # b'After readings begin, place known weight on scale\r\n'\
        # b'Press + or a to increase calibration factor\r\n'\
        # b'Press - or z to decrease calibration factor\r\n'\
        # b'Press 0 to zero factor\r\n'\
        # b'Press x to exit\r\n'
        # b'Reading: [\d+.\d+ [lbs|kg]]   Calibration Factor: \d+\r\n'
        #
        # behaviour in loop:
        # -> b'+' | b'-' | b'0' | b'a' | b'z' => b'Reading: [\d+.\d+ [lbs|kg]]   Calibration Factor: \d+\r\n'
        # -> b'x' => <save_and_exit>
        self.write(self.cmds['calibrate'])
        self.read(240)  # initial spiel is 240 bytes
        response = self.read_until(b'\r\n').decode('utf-8').split()
        # index: contents
        # 0: b'Reading:'
        # 1: [ + string float reading in lbs|kg
        # 2: string for units + ]
        # 3: 'Calibration'
        # 4: 'Factor:'
        # 5: string reading of integer offset used internally
        res = {
            'reading': float(response[1][1:]),
            'units': str(response[2][:-1]),
            'cal_factor': int(response[5]),
        }
        self.write(self.cmds['close_menu'])
        return res

    def get_reading(self, to_force=True):
        # order is (if enabled) : comma separation, no whitespace:
        # timestamp -- toggleable -- int
        # calibrated_reading -- always printed -- float
        # units -- always printed -- str
        # raw_reading -- toggleable -- int
        # local_temp -- toggleable -- float
        # remote_temp -- toggleable -- float
        ret_map = {
            # order: ret       (timestamp,    cal_read, unit,       raw,       local,      remote)
            # order: ret       ( int (ms),       float,  str,     int24,       float,       float)
            0b01000: lambda x: [None, float(x[0]), x[1], None, None, None],
            0b01001: lambda x: [None, float(x[0]), x[1], None, None, float(x[2])],
            0b01010: lambda x: [None, float(x[0]), x[1], None, float(x[2]), None],
            0b01011: lambda x: [None, float(x[0]), x[1], None, float(x[2]), float(x[3])],
            0b01100: lambda x: [None, float(x[0]), x[1], int(x[2]), None, None],
            0b01101: lambda x: [None, float(x[0]), x[1], int(x[2]), None, float(x[3])],
            0b01110: lambda x: [None, float(x[0]), x[1], int(x[2]), float(x[3]), None],
            0b01111: lambda x: [None, float(x[0]), x[1], int(x[2]), float(x[3]), float(x[4])],
            0b11000: lambda x: [int(x[0]), float(x[1]), x[2], None, None, None],
            0b11001: lambda x: [int(x[0]), float(x[1]), x[2], None, None, float(x[3])],
            0b11010: lambda x: [int(x[0]), float(x[1]), x[2], None, float(x[3]), None],
            0b11011: lambda x: [int(x[0]), float(x[1]), x[2], None, float(x[3]), float(x[4])],
            0b11100: lambda x: [int(x[0]), float(x[1]), x[2], int(x[3]), None, None],
            0b11101: lambda x: [int(x[0]), float(x[1]), x[2], int(x[3]), None, float(x[4])],
            0b11110: lambda x: [int(x[0]), float(x[1]), x[2], int(x[3]), float(x[4]), None],
            0b11111: lambda x: [int(x[0]), float(x[1]), x[2], int(x[3]), float(x[4]), float(x[5])],
        }

        key = (self._timestamp_enable << 4) | 0b01000 | (self._raw_reading_enable << 2) | \
              (self._local_temp_enable << 1) | self._remote_temp_enable
        with LOCK:
            if self.first_read:
                self.triggered_read()
                res = self.read_until(b'\r\n')
                while not res.endswith(b'Readings:'):
                    res += self.read(1)
                self.readline()
                self.first_read = False
            self.write(self.cmds['trigger_char'])
            res = self.read_until(b'\r\n').decode('utf-8').split(',')

        res = [item for sublist in (r.split() for r in res) for item in sublist]
        data = ret_map[key](res)
        if to_force:
            data[1], data[2] = self.to_force(data[1], data[2])
        # todo: reorganize the ret_mapping to handle this
        if self.timestamp_enable:  # move timestamp to the end
            timestamp = data.pop(0)
            data.append(timestamp)
        return tuple(filter(None.__ne__, data))

    @staticmethod
    def to_force(reading, units):
        if units == 'kg':
            return reading * 9.80665, 'N'  # returns N
        else:
            return reading * 32.174049, 'lbf'  # returns lbf

    @property
    def configuration(self):
        return {
            'tare': self._tare_val,
            'calibrate': self._cal_value,
            'timestamp_enable': self._timestamp_enable,
            'report_rate': self._report_rate,
            'units': self._units,
            'decimal_places': self._decimal_places,
            'num_avgs': self._num_avgs,
            'local_temp_enable': self._local_temp_enable,
            'remote_temp_enable': self._remote_temp_enable,
            'status_led': self._status_led,
            'trigger_enable': self._serial_trigger_enable,
            'raw_read_enable': self._raw_reading_enable,
            'trigger_char': self._trigger_char,
        }

    def save_config(self):
        data = {
            'tare': self._tare_val,
            'calibrate': self._cal_value,
            'timestamp_enable': self._timestamp_enable,
            'report_rate': self._report_rate,
            'units': self._units,
            'decimal_places': self._decimal_places,
            'num_avgs': self._num_avgs,
            'local_temp_enable': self._local_temp_enable,
            'remote_temp_enable': self._remote_temp_enable,
            'status_led': self._status_led,
            'trigger_enable': self._serial_trigger_enable,
            'raw_read_enable': self._raw_reading_enable,
            'trigger_char': self._trigger_char,
        }
        with open(CFG_FILE_PATH, 'w') as file:
            file.write(yaml.dump(data))

    def load_config(self):
        with open(CFG_FILE_PATH, 'r') as file:
            data = yaml.dump(file.read())
        self._tare_val = data['tare']
        self._cal_value = data['calibrate']
        self._timestamp_enable = data['timestamp_enable']
        self._report_rate = data['report_rate']
        self._units = data['units']
        self._decimal_places = data['decimal_places']
        self._num_avgs = data['num_avgs']
        self._local_temp_enable = data['local_temp_enable']
        self._remote_temp_enable = data['remote_temp_enable']
        self._status_led = data['status_led']
        self._serial_trigger_enable = data['trigger_enable']
        self._raw_reading_enable = data['raw_read_enable']
        self._trigger_char = data['trigger_char']
