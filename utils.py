import redis

class PersistentSequenceGenerator(object):
    MIN_SEQUENCE = 0x00000001
    MAX_SEQUENCE = 0x7FFFFFFF
    PERSISTENCE_NAME = 'provider_sequences'

    def __init__(self):
        self.redis = redis.Redis(host='10.106.0.2', port=6379, db=2)
        actual_value = self.redis.get(self.PERSISTENCE_NAME)
        if actual_value:
            self._sequence = int(actual_value, 0)
        else:
            self._sequence = self.MIN_SEQUENCE
            self.redis.set(self.PERSISTENCE_NAME, self._sequence)

    def get_value(self):
        return self.redis.get(self.PERSISTENCE_NAME)

    @property
    def sequence(self):
        return int(self.redis.get(self.PERSISTENCE_NAME), 0)

    def next_sequence(self):
        next_value = int(self.get_value(), 0) + 1
        self.redis.set(self.PERSISTENCE_NAME, next_value)
        return next_value
