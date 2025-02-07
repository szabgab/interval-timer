from typing import Optional
from time import sleep, perf_counter
from dataclasses import dataclass


@dataclass
class Interval:
    index: int
    period: float
    time_ready: float
    time: float

    def __repr__(self):
        return f'Interval(index={self.index}, time={self.time:.06f}, buffer={self.buffer}%)'

    @property
    def min(self) -> float:
        """
        The lower time limit of the interval.
        """
        return self.index * self.period

    @property
    def max(self) -> float:
        """
        The upper time limit of the interval.
        """
        return self.min + self.period

    @property
    def buffer(self) -> int:
        """
        The time at which the iteration occurred before the interval's maximum limit, as a percentage. Over 100%
        indicates that the iteration was requested before the time interval, under 100% indicates that there was some
        lag of the interval being requested relative to the start of the interval, and under 0% indicates that the
        interval was missed altogether.
        """
        return round((self.max - self.time_ready) / self.period * 100)

    @property
    def arrived(self) -> bool:
        """
        Indicates that this time interval has been reached.
        """
        return self.min <= self.time

    @property
    def missed(self) -> bool:
        """
        Indicates that the time interval was missed and the iteration was not synchronised to within the time interval.
        """
        return self.max <= self.time


class IntervalTimer:
    # Affects timer precision, but also prevents high CPU usage
    CPU_THROTTLE_S = 0.0001

    def _perf_counter_relative(self) -> float:
        return perf_counter() - self._zero_count

    def __init__(self, period: float, start: int = 0, stop: Optional[int] = None):
        """
        An interval timer iterator that synchronises iterations to within specific time intervals.

        The time taken for code execution within each iteration will not affect the interval timing, provided that the
        execution time is not longer than the interval period. The caller can check if this is the case by checking the
        `missed` attribute on the returned `Interval` instance.

        :param period: The interval period, in seconds.
        :param start: The number of iterations to delay starting by.
        :param stop: The number of iterations to automatically stop after.
        """
        self._period = period
        self._index = start
        self._stop = stop
        self._zero_count = perf_counter()

    def __iter__(self) -> 'IntervalTimer':
        return self

    def __next__(self) -> Interval:
        if self._stop == self._index:
            raise StopIteration()

        time = self._perf_counter_relative()
        interval = Interval(self._index, self._period, time, time)

        # Block this iteration until the interval is arrived at
        while not interval.arrived:
            interval.time = self._perf_counter_relative()
            sleep(self.CPU_THROTTLE_S)

        self._index += 1
        return interval
