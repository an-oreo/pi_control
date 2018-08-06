"""
pi_control
oscillate.py
Author: Danyal Ahsanullah
Date: 6/28/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

import sys
from libs.utils import INF
from libs.hal import actuator, hal_init
from time import perf_counter


def oscillate_force(interface=actuator, params=None):
    """
    Sets a minimum force. The moves back the prescribed displacement and back to a minimum force.
    The related keys are 'min_force', 'displacement' respectively.
    Movement speed is optionally defined in params dict with the 'speed' key.
    Frequency can be optionally defined in Hz with the 'freq' key. It will overwrite any value taken from the speed key.
    Adaptive controller is optionally specified with the 'controller' key.
    The ability to end oscillation at the closest threshold (low or high) is available with the 'reset_closest' key,
        which expects a boolean True or False value. If not specified, defaults to False
    Mutually exclusive number of oscillations and timeout are also optional params. if both are specified,
    it will stop at whatever comes first.
        - timeout is specified with the 'timeout' key and expects a float, defaults to inf
        - repetitions is specified with the 'repetitions' key and expects an int, defaults to inf

    depending on the conditions, four possible return values are possible plus an error condition:
        - 'timeout_stopped'  - broke on a timeout and left actuator where it was
        - 'repeats_stopped'  - broke on a repeat and left actuator where it was
        - 'timeout_reset'    - broke on a timeout and reset actuator to closest boundary point
        - 'repeats_reset'    - broke on a timeout and reset actuator to closest boundary point
        - 'error'            - triggers on any failure during oscillations
    """
    hal_init()
    condition = 'stopped'
    min_force = params['min_force']
    displacement = params['displacement']
    timeout = params.get('timeout', INF)
    repetitions = params.get('repetitions', INF)
    controller = params.get('controller', None)
    old_speed = interface.speed_controller.default_val
    speed = params.get('speed', interface.speed_controller.default_val)
    if params.get('freq', None) is not None:
        # calculate new speed for desired frequency
        pass
    interface.speed_controller.default_val = speed
    interface.mount_controller(controller)
    repeats = 0
    start = perf_counter()
    try:
        while (repeats < repetitions) and ((perf_counter() - start) < timeout):
            print('setting load...')
            high_pos = interface.set_load(min_force)
            low_pos = high_pos - displacement
            print('start oscillation', repeats, (perf_counter() - start))
            interface.set_position(low_pos)
            interface.set_position(high_pos)
            repeats += 1
            print('next oscillation')
        interface.speed_controller.default_val = old_speed
        return '_'.join(('timeout' if repeats < repetitions else 'repeats', condition))
    except Exception as e:
        interface.set_out_speed(interface.speed_controller.stop)
        interface.speed_controller.default_val = old_speed
        sys.stderr.write(str(e))
        sys.stderr.write('\n')
        sys.stderr.write(str(sys.exc_info()))
        sys.stderr.flush()
        return 'error'
