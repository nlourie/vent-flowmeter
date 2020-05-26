"""
Simulates a patient breath.

The pressure cycle looks like:

     /|
    / L_____
   /       |
__/        L____

1 2  3  4  5 6

1: Hold at baseline
2: Linear increase from baseline to max
3: Exponential decay to plateau
4: Hold at plateau
5: Exponential decay to baseline
6: Hold at baseline until start of next cycle
"""
import time
import os
import numpy as np
import yaml

class PEEP:
    """
    Settings are loaded from gui/communication/simulation.yaml.

    Class members:
    - phase_start: When each phase of the cycle starts, in seconds
    - peeps: Pressures in mbar
    - flows: Flow rates in lpm
    - decay_time_factor: Exponential decay tau, as a fraction of the linear rise time
    - resolution: Random fluctuation of returned values, as a fraction of (max-plateau).
        Same factor used for pressure and flow.
    - next_start_jitter: Random fluctuation for time between end of one cycle and start
        of next.
    - t_cycle_start: UNIX time of the start of the current cycle
    """
    def __init__(self):
        base_dir = os.path.dirname(__file__)
        settings_file = os.path.join(base_dir, 'simulation.yaml')

        with open(settings_file) as file:
            config = yaml.load(file, Loader=yaml.FullLoader)

        print('Simulator Config:', yaml.dump(config), sep='\n')

        self.phase_start = {}
        self.phase_start["lin_inc"] = float(config['t1'])
        self.phase_start["first_decay"] = self.phase_start["lin_inc"] + float(config['t2'])
        self.phase_start["plateau"] = self.phase_start["first_decay"] + float(config['t3'])
        self.phase_start["second_decay"] = self.phase_start["plateau"] + float(config['t4'])
        self.phase_start["restart"] = self.phase_start["second_decay"] + float(config['t5'])

        self.peeps = {}
        self.peeps["baseline"] = float(config['p0'])
        self.peeps["plateau"] = float(config['p1']) - self.peeps["baseline"]
        self.peeps["max"] = float(config['p2']) - self.peeps["baseline"]

        self.flows = {}
        self.flows["max"] = float(config['f1'])
        self.flows["plateau"] = float(config['f2'])
        self.flows["min"] = float(config['f3'])
        self.flows["baseline"] = float(config['f4'])

        self.decay_time_factor = float(config['decay_time'])
        self.resolution = float(config['resolution'])
        self.next_start_jitter = float(config['btiming_fluctuations'])

        self.t_cycle_start = time.time()

        print('PEEP timing   : {} {} {} {} {}'.format(self.phase_start["lin_inc"],
                                                      self.phase_start["first_decay"],
                                                      self.phase_start["plateau"],
                                                      self.phase_start["second_decay"],
                                                      self.phase_start["restart"]))
        print('PEEP pressures: {} {}'.format(self.peeps["plateau"], self.peeps["max"]))
        print('PEEP flow     : {} {} {} {}'.format(self.flows["max"],
                                                   self.flows["plateau"],
                                                   self.flows["min"],
                                                   self.flows["baseline"]))

    def pressure(self):
        """
        Get the current inspirarion pressure.

        Returns: pressure in mbar.
        """
        t_now = time.time() - self.t_cycle_start
        pressure = self.peeps["baseline"]

        if self.phase_start["lin_inc"] < t_now < self.phase_start["first_decay"]:
            # pressure linear increase
            rise_time = self.phase_start["first_decay"] - self.phase_start["lin_inc"]
            rate = self.peeps["max"] / rise_time
            offset = -rate * self.phase_start["lin_inc"]
            pressure += rate * t_now + offset
        elif self.phase_start["first_decay"] <= t_now < self.phase_start["plateau"]:
            # pressure reached its maximum and starts decreasing
            # exponentially
            fall_time = self.phase_start["plateau"] - self.phase_start["first_decay"]
            tau = fall_time * self.decay_time_factor
            amplitude = self.peeps["max"] - self.peeps["plateau"]
            pressure += self.peeps["plateau"]
            pressure += amplitude * np.exp(-(t_now - self.phase_start["first_decay"]) / tau)
        elif self.phase_start["plateau"] <= t_now < self.phase_start["second_decay"]:
            # pressure stay stable for a while
            pressure += self.peeps["plateau"]
        elif self.phase_start["second_decay"] <= t_now < self.phase_start["restart"]:
            # pressure drops exponentially
            fall_time = self.phase_start["plateau"] - self.phase_start["first_decay"]
            tau = fall_time * self.decay_time_factor
            amplitude = self.peeps["plateau"]
            pressure += amplitude * np.exp(-(t_now - self.phase_start["second_decay"]) / tau)
        elif t_now > self.phase_start["restart"]:
            # restart the cycle
            self.restart()

        # add some random fluctuations
        scale = (self.peeps["max"] - self.peeps["plateau"]) * self.resolution
        pressure += np.random.normal(scale=scale)

        return pressure

    def flow(self):
        """
        Get the current flow.

        Returns: flow in lpm.
        """
        t_now = time.time() - self.t_cycle_start
        flow = self.flows["min"]

        if self.phase_start["lin_inc"] < t_now < self.phase_start["first_decay"]:
            # flow decays exponentially after a fast grow
            # reaching an intermediate level
            fall_time = self.phase_start["first_decay"] - self.phase_start["lin_inc"]
            tau = fall_time * self.decay_time_factor
            amplitude = self.flows["max"]
            const = self.flows["plateau"]
            flow = amplitude - const * (1 - np.exp(-(t_now - self.phase_start["lin_inc"]) / tau))
        elif self.phase_start["first_decay"] <= t_now < self.phase_start["second_decay"]:
            # flow drops to low values, then increase
            # exponentially to zero
            fall_time = self.phase_start["first_decay"] - self.phase_start["lin_inc"]
            tau = fall_time * self.decay_time_factor
            amplitude = self.flows["min"]
            const = self.flows["baseline"]
            flow = amplitude - const * np.exp(-(t_now - self.phase_start["first_decay"]) / tau)
        elif t_now > self.phase_start["restart"]:
            # restart cycle
            self.restart()

        # add some random fluctuation
        scale = (self.flows["max"] - self.flows["plateau"]) * self.resolution
        flow += np.random.normal(scale=scale)
        return flow

    def restart(self):
        """
        Calculate the start time of the next cycle.
        """
        # the cycle restarts after a fixed +- random time
        self.t_cycle_start = time.time() + np.random.normal(scale=self.next_start_jitter)
