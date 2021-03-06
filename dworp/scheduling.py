from abc import ABC, abstractmethod
from collections.abc import Iterator
import logging


class Time(Iterator):
    """Base class for time generation

    The simulation supports arbitrary time scales controlled by Time.
    The simulation iterates over the Time object to get the next time value.

    Can be used like so:
      time_gen = MyTime()
      for t in time_gen:
          print(t)
    """
    @abstractmethod
    def get_start_time(self):
        """Get the start time of the simulation

        Returns:
            int or float
        """
        pass


class BasicTime(Time):
    """Fixed step size and fixed num of steps

    BasicTime(5) will result in times of 1, 2, 3, 4, 5

    The start time is the time the simulation is initialized.
    The first time the agents' step() is called will be start + step_size.
    BasicTime(num_steps=3, start=10) will be 11, 12, 13

    Args:
        num_steps (int): Number of time steps in the simulation
        start (int or float, optional): Start time of the simulation
        step_size (int or float, optional): Time step size
    """
    def __init__(self, num_steps, start=0, step_size=1):
        self.start_time = start
        self.time = start
        self.num_steps = num_steps
        self.step_size = step_size
        self.step_count = 0

    def get_start_time(self):
        return self.start_time

    def __next__(self):
        self.step_count += 1
        if self.step_count > self.num_steps:
            raise StopIteration
        self.time += self.step_size
        return self.time


class InfiniteTime(Time):
    """Fixed step size and infinite num of steps

    The start time is the time the simulation is initialized.
    The first time the agents' step() is called will be start + step_size.
    InfiniteTime(start=10) will be 11, 12, 13, ...

    Args:
        start (int or float, optional): Start time of the simulation
        step_size (int or float, optional): Time step size
    """
    def __init__(self, start=0, step_size=1):
        self.start_time = start
        self.time = start
        self.step_size = step_size

    def get_start_time(self):
        return self.start_time

    def __next__(self):
        self.time += self.step_size
        return self.time


class Terminator(ABC):
    """Terminate the simulation when a convergence criteria is achieved"""
    @abstractmethod
    def test(self, time, agents, env):
        """
        Return True to stop the simulation

        Args:
            time: (int or float): current time of the simulation
            agents (list): list of Agent objects
            env: (Environment): environment object

        Returns: bool
        """
        pass


class NullTerminator(Terminator):
    """Never terminate!"""
    def test(self, time, agents, env):
        return False


class Scheduler(ABC):
    """Scheduling agents

    Determines which agents update for a particular time step.
    """
    logger = logging.getLogger(__name__)

    @abstractmethod
    def step(self, time, agents, env):
        """ Get the next step in schedule

        Args:
            time (int or float): current time of the simulation
            agents (list): list of Agent objects
            env (Environment): environment object

        Returns:
            list of agent indices or iterator over indices
        """
        pass


class BasicScheduler(Scheduler):
    """Schedules all agents in the order of the agents list"""
    def step(self, time, agents, env):
        return range(len(agents))


class RandomOrderScheduler(Scheduler):
    """Random permutation of all agents

    Args:
        rng (numpy.random.RandomState): numpy random generator
    """
    def __init__(self, rng):
        self.rng = rng

    def step(self, time, agents, env):
        return self.rng.permutation(len(agents))


class RandomSampleScheduler(Scheduler):
    """Uniformly sample from the list of agents

    Args:
        size (int): size of the sample
        rng (numpy.random.RandomState): numpy random generator
    """
    def __init__(self, size, rng):
        self.size = size
        self.rng = rng

    def step(self, time, agents, env):
        return self.rng.permutation(len(agents))[:self.size]
