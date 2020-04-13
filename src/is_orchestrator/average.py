class MovingAverage(object):
    def __init__(self, length: int = 5):
        self._buffer = list()
        self._length = length
    
    def calculate (self, value: float):
        if len(self._buffer) < self._length:
            self._buffer.append(value)
        else:
            self._buffer.pop(0)
            self._buffer.append(value)
        return sum(self._buffer)/self._length
