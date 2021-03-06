import time
import os
import numpy as np
import RPi.GPIO as GPIO
from pathlib import Path

from .Stepper_17HS4023_Driver_L298N import Pi_17HS4023_L298N

class calibrate_intellux:
    '''intellux calibration class with target of finding full range steps'''
    def __init__(self, turning_direction):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  # defines naming convention to be used for the pins
        self.stepper_motor = Pi_17HS4023_L298N(in1=27, in2=17, in3=22, in4=18, enable_a=24, enable_b=23, turning_direction=turning_direction)
        self.turning_direction = turning_direction

        root = Path(os.path.abspath(__file__)).parents[0]
        self.calibration_status_file = os.path.join(root, 'calibration_info', 'calibration_status.npy') 
        self.full_range_steps_file = os.path.join(root, 'calibration_info', 'full_range_steps.npy')  

    def start_calibration(self):
        # 0 - CW
        # 1 - CCW
        if self.turning_direction == 0:
            self.calibrate_CW()
        elif self.turning_direction == 1:
            self.calibrate_CCW()
        else:
            raise ValueError('Unknown turning direction, please input a binary value (0 or 1)')

    def calibrate_CW(self):
        calibration_file_last_update_time = os.path.getmtime(self.calibration_status_file)
        num_steps = 0
        while True:
            if os.path.getmtime(self.calibration_status_file) == calibration_file_last_update_time:
                #file was not updated, read right away
                calibration_status = np.load(self.calibration_status_file)
            else:
                time.sleep(1)
                print(calibration_file_last_update_time, os.path.getmtime(self.calibration_status_file))
                #file was updated, wait 1 second before reading
                calibration_status = np.load(self.calibration_status_file)

            if calibration_status == 1:
                self.stepper_motor.turn_CW(1)
                num_steps += 1
            else:   
                self.save_full_range_steps(num_steps)
                self.stepper_motor.turn_CCW(num_steps)
                self.stepper_motor.cleanup()
                break

    def calibrate_CCW(self):
        calibration_file_last_update_time = os.path.getmtime(self.calibration_status_file)
        num_steps = 0
        while True:
            if os.path.getmtime(self.calibration_status_file) == calibration_file_last_update_time:
                #file was not updated, read right away
                calibration_status = np.load(self.calibration_status_file)
            else:
                time.sleep(1)
                #file was updated, wait 1 second before reading
                calibration_status = np.load(self.calibration_status_file)

            if calibration_status == 1:
                self.stepper_motor.turn_CCW(1)
                num_steps += 1
            else:
                self.save_full_range_steps(num_steps)
                self.stepper_motor.turn_CW(num_steps)
                self.stepper_motor.cleanup()
                break

    def save_full_range_steps(self, num_steps):
        print("number of steps moved is", num_steps)
        with open(self.full_range_steps_file, 'wb') as f:
            np.save(f, num_steps)



