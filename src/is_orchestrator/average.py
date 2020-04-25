class MovingAverage(object):
    def __init__(self, length: int = 5):
        self._buffer = list()
        self._length = length
    
    def calculate (self, value: float) -> float: 
        if len(self._buffer) < self._length:
            self._buffer.append(value)
        elif len(self._buffer) == self._length:
            self._buffer.pop(0)
            self._buffer.append(value)
        elif len(self._buffer) > self._length:
            while len(self._buffer) > self._length:
                self._buffer.pop(0)
            self._buffer.pop(0)
            self._buffer.append(value)

        return float(sum(self._buffer)/self._length)
    
    @property
    def length(self):
        return self._length
    
    @length.setter
    def length(self, length):
        self._length = length

    @property
    def buffer(self):
        return self._buffer

    @buffer.setter
    def buffer(self, buffer):
        self._buffer = buffer
