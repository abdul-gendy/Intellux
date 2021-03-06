import os
import time
from pathlib import Path
import numpy as np
import RPi.GPIO as GPIO

#Naming convention Pi_MotorModel_DriverModel
class Pi_17HS4023_L298N:
    """Class for contolling the Nema-17 17HS4023 stepper motor model with L298N motor driver using Rasberry Pi"""
    def __init__(self, in1=13, in2=11, in3=15, in4=12, enable_a=18, enable_b=16, turning_direction=0):
        self.in1 = in1
        self.in2 = in2
        self.in3 = in3
        self.in4 = in4
        self.enable_a = enable_a
        self.enable_b = enable_b

        self.setup_motor_pins()
        self.motor_pins = [in1,in2,in3,in4]

        self.full_revolution_step_count = 400 #https://datasheetspdf.com/pdf-file/1328258/ETC/SM-17HS4023/1
        # careful lowering this, at some point you run into the mechanical limitation of how quick your motor can move
        self.step_sleep = 0.005 #5 milliseconds
        self.turning_direction = turning_direction
        
        # defining stepper motor sequence 
        self.step_sequence = [[1,0,0,0],
                            [1,1,0,0],
                            [0,1,0,0],
                            [0,1,1,0],
                            [0,0,1,0],
                            [0,0,1,1],
                            [0,0,0,1],
                            [1,0,0,1]]

        root = Path(os.path.abspath(__file__)).parents[0]
        index_files_directory = os.path.join(root,'stepper_position')
        self.motor_step_sequence_counter_file = os.path.join(index_files_directory, 'motor_step_sequence_counter.npy') # To Load the previous index
        self.motor_global_step_counter_file = os.path.join(index_files_directory, 'motor_global_step_counter.npy') # To Load the previous index

        if not os.path.isfile(self.motor_step_sequence_counter_file) or not os.path.isfile(self.motor_global_step_counter_file):   
            #UI Feedback
            raise ValueError("Current motor location cannot be found. Data maybe corrupted. Please recalibrate system")
        else:
            self.motor_step_sequence_counter = np.load(self.motor_step_sequence_counter_file)
            self.motor_global_step_counter = np.load(self.motor_global_step_counter_file)

    def setup_motor_pins(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM) #defines naming convention to be used for the pins

        # setting up
        GPIO.setup(self.in1, GPIO.OUT)
        GPIO.setup(self.in2, GPIO.OUT)
        GPIO.setup(self.in3, GPIO.OUT)
        GPIO.setup(self.in4, GPIO.OUT)
        GPIO.setup(self.enable_a, GPIO.OUT)
        GPIO.setup(self.enable_b, GPIO.OUT)
        
        # initializing
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.LOW)
        GPIO.output(self.in4, GPIO.LOW)
        GPIO.output(self.enable_a, GPIO.HIGH)
        GPIO.output(self.enable_b, GPIO.HIGH)

    def turn_CW(self, num_of_steps):
        for i in range(num_of_steps):
            self.motor_step_sequence_counter = (self.motor_step_sequence_counter - 1) % 8
            for pin in range(0, len(self.motor_pins)):
                GPIO.output( self.motor_pins[pin], self.step_sequence[self.motor_step_sequence_counter][pin] )
            time.sleep(self.step_sleep)
            if self.turning_direction == 0:
                self.motor_global_step_counter = self.motor_global_step_counter + 1
            else:
                self.motor_global_step_counter = self.motor_global_step_counter - 1

    def turn_CCW(self, num_of_steps):
        for i in range(num_of_steps):
            self.motor_step_sequence_counter = (self.motor_step_sequence_counter + 1) % 8
            for pin in range(0, len(self.motor_pins)):
                GPIO.output( self.motor_pins[pin], self.step_sequence[self.motor_step_sequence_counter][pin] )
            time.sleep(self.step_sleep)
            if self.turning_direction == 1:
                self.motor_global_step_counter = self.motor_global_step_counter + 1
            else:
                self.motor_global_step_counter = self.motor_global_step_counter - 1

    def move_to_required_stepper_position(self, required_stepper_position):
        steps_difference = required_stepper_position - self.motor_global_step_counter
        if steps_difference < 0:
            if self.turning_direction == 0:
                self.turn_CCW(abs(steps_difference))
            else:
                self.turn_CW(abs(steps_difference))
            assert(required_stepper_position == self.motor_global_step_counter)
            self.save_stepper_positions()
        elif steps_difference > 0:
            if self.turning_direction == 0:
                self.turn_CW(abs(steps_difference))
            else:
                self.turn_CCW(abs(steps_difference))
            assert(required_stepper_position == self.motor_global_step_counter)
            self.save_stepper_positions()
        else:
            self.save_stepper_positions()

    def save_stepper_positions(self):
        np.save(self.motor_step_sequence_counter_file, self.motor_step_sequence_counter)
        np.save(self.motor_global_step_counter_file, self.motor_global_step_counter)

    def reset_and_save_stepper_positions(self):
        np.save(self.motor_step_sequence_counter_file, 0)
        np.save(self.motor_global_step_counter_file, 0)

    def cleanup(self):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.LOW)
        GPIO.output(self.in4, GPIO.LOW)
        GPIO.output(self.enable_a, GPIO.LOW)
        GPIO.output(self.enable_b, GPIO.LOW)
        GPIO.cleanup()


#if __name__=='__main__':
    #GPIO.setmode(GPIO.BOARD)
    #x = Pi_17HS4023_L298N(in1=13, in2=11, in3=15, in4=12, enable_a=18, enable_b=16)
    #x.turn_CW(45)
    #x.cleanup()
