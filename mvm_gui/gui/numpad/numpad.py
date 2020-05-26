#!/usr/bin/env python3
'''
Module containing the NumPad class
'''
from PyQt5 import QtWidgets


class NumPad():
    '''
    Class defining a numeric pad
    '''
    def __init__(self, mainparent):
        #pylint: disable=cell-var-from-loop
        # See PyLint issue 3107
        """
        Creates the numpad menu.

        arguments:
        - mainparent: Reference to the main window.
        """
        self.mainparent = mainparent
        self.button_back = self.mainparent.findChild(
            QtWidgets.QPushButton, "numpad_back")

        # Only have every other button
        self.buttons_num = []
        for i in range(0, 10, 2):
            name = "numpad_" + str(i) + str(i + 1)
            button = self.mainparent.findChild(QtWidgets.QPushButton, name)
            # button.pressed.connect(lambda num=i: self.input_number(num))
            button.pressed.connect(lambda num=int(
                i / 2) + 1: self.input_number(num))
            self.buttons_num.append(button)

        self.assign_code("0000", None)

    def assign_code(self, code, func):
        """
        Assigns a code to the NumPad. When the correct cdoe is entered, the given function will be
        executed.

        arguments:
        - code: String code of digits.
        - func: Function to be executed when correct code is input.
        """
        # self.code = [int(int(d)/2)*2 for d in str(code) if d.isdigit()]
        self.code = [int(d) for d in str(code) if d.isdigit()]
        self.input_values = [-1] * len(self.code)
        self.func = func

    def input_number(self, num):
        """
        Add a number to the input values and compare with the assigned code.
        Input values are stored in a circular buffer so only the latest N digits (N = len(code))
        need to be correct for the code to be valid.

        arguments:
        - num: Number to be added to the input values
        """
        self.input_values[:-1] = self.input_values[1:]
        self.input_values[-1] = num
        self.check_code()

    def check_code(self):
        """
        Check the code against the input values.
        If they match, execute the assigned function reassign the code and function to reset.
        """
        if self.input_values == self.code:
            # Execute the code locked function
            if self.func is not None:
                print("**** Code accepted ****")
                self.func()
            # Reassign the code to reset
            self.assign_code(self.code, self.func)
