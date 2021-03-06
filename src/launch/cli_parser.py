#! /usr/bin/env python3
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
cli_parser.py
Author: Danyal Ahsanullah
Date: 6/11/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: parser definition for launching elastocaloric control script.
             yaml data structures definitions.
Usage:
    from cli_parser import parser, cmds, actions
       or
    from cli_parser import *
    ...
    args = parser.parse_args()
    if args['cmd'] = cmds['cmd_key_here']:
        ...
"""

from argparse import ArgumentParser

from orchestration.actions import action_map
from launch.command_map import cmds
from version import version as __version__
from libs.hal import adc, actuator

parser = ArgumentParser()  # 'elastocaloric testing'
subparsers = parser.add_subparsers(help='Action to take', dest='cmd')
parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('-t', '--timeout', type=int, default=5, help='set timeout for loop')
parser.add_argument('-r', '--sample_rate', type=int, choices=sorted(adc.accepted_sample_rates),
                    default=adc.sample_rate, help='Sample rate for adc (sps)')
parser.add_argument('-o', '--outfile', type=str, default=None, help='optional file to save results to')
parser.add_argument('--config', type=str, default=None, help='optional configuration file')
parser.add_argument('-u', '--unit', type=str, default='raw', choices={'raw', 'in', 'mm'},
                    help='unit to have final results in.')
# parser.add_argument('-g', '--gain', type=float, choices={2/3, 1, 2, 3, 8, 16}, default=1,
#                     help='adc input polarity (1, -1)')
# parser.add_argument('-c', '--channel', type=int, choices={1, 2, 3, 4}, help='adc input channel',
#                     default=ADC_CHANNEL)
# parser.add_argument('-a', '--alert_pin', type=int, default=21, help='RPI gpio pin number (eg: gpio27 -> "-a 27")')
# parser.add_argument('-v', '--verbose', action='count', default=0, help='verbosity')
# parser.add_argument('--help', action='help')

test_adc_parser = subparsers.add_parser(cmds['TEST_ADC'], help='test adc functionality')
test_dac_parser = subparsers.add_parser(cmds['TEST_DAC'], help='test dac functionality')
test_cal_parser = subparsers.add_parser(cmds['TEST_CAL'], help='test calibration routines')

test_positioning_parser = subparsers.add_parser(cmds['TEST_POS'], add_help=False, help='test controllable positing')
test_positioning_parser.add_argument('-L', '--low_min', type=int, default=actuator.pos_limit_low)
test_positioning_parser.add_argument('-l', '--low_threshold', type=int, default=actuator.pos_limit_low)
test_positioning_parser.add_argument('-h', '--high_threshold', type=int, default=actuator.pos_limit_high)
test_positioning_parser.add_argument('-H', '--high_max', type=int, default=actuator.pos_limit_high)
test_positioning_parser.add_argument('--help', action='help', help='print help')

pos_subparsers = test_positioning_parser.add_subparsers(help='specific position action to take', dest='action')
pos_subparsers.add_parser(action_map['RESET_MIN'], help='reset to minimum extension')
pos_subparsers.add_parser(action_map['RESET_MAX'], help='reset to max extension')

goto_parser = pos_subparsers.add_parser('goto_pos', help='go to desired position')
goto_parser.add_argument('position', type=int, default=adc.levels >> 1,
                         help='position value between 0 and {}'.format(adc.max_level))

monitor_parser = subparsers.add_parser(cmds['RUN_ACQ'], add_help=False, help='run acquisition')
monitor_parser.add_argument('-L', '--low_min', type=int, default=actuator.pos_limit_low)
monitor_parser.add_argument('-l', '--low_threshold', type=int, default=actuator.pos_limit_low)
monitor_parser.add_argument('-h', '--high_threshold', type=int, default=actuator.pos_limit_high)
monitor_parser.add_argument('-H', '--high_max', type=int, default=actuator.pos_limit_high)
monitor_parser.add_argument('--help', action='help', help='print help')


if __name__ == '__main__':
    parser.print_help()
