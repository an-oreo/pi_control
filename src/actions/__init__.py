#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
actions/__init__.py
Author: Danyal Ahsanullah
Date: 6/25/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description:
"""
# prototype action function signature:
#
# def some_action(interface: obj, params: dict, nxt: dict) -> Callable:
#     """
#     Action description
#     ...
#     :param interface: base interface abstraction layer that is performing an action.
#     :param params: dictionary of the form
#     	{'param0':<val>, 'param1':<val>, ..., 'paramN':<val>}
#     :param nxt: dictionary of state transitions in the form
#     	{<condition>:<action_func>, <condition>:<action_func>, None:<action_func>}
#     """
#     condition = None
#     # stuff happens here -- eval and assign the desired value for condition
#     ...
#     return next[condition]
#

from .calibrate import calibrate
from .reset_max import reset_max
from .reset_min import reset_min

actions = {'RESET_MIN': 'reset_min',
           'RESET_MAX': 'reset_max',
           'GOTO_POS': 'set_pos',
           'CLEANUP': 'cleanup',
           }
