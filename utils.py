import http.client
import json
import redis


def send_delivery_sm(messageid, message_status, id_smsc):
    conn = http.client.HTTPSConnection("app.test.nimbasms.com/v1")

    headers = {
        "content-type": "application/json"
    }
    payload = {
        'messageid': messageid,
        'message_status': message_status,
        'id_smsc': id_smsc,
        # 'subdate': request.POST.get('subdate'),
        # 'donedate': request.POST.get('donedate'),
    }
    conn.request("GET", "/webhooks/default-provider-confirmation/",
                 body=json.dumps(payload), headers=headers)
    res = conn.getresponse()
    data = res.read()
    return data.decode('utf-8')


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

    def get_value(self, key):
        return self.redis.get(key)

    def delete_key(self, key):
        self.redis.delete(key)

    def set_value_with_expiry(self, key, value, expiry_seconds=86400):
        return self.redis.setex(key, expiry_seconds, value)

    @property
    def sequence(self):
        return int(self.redis.get(self.PERSISTENCE_NAME), 0)

    def next_sequence(self):
        next_value = int(self.get_value(self.PERSISTENCE_NAME), 0) + 1
        self.redis.set(self.PERSISTENCE_NAME, next_value)
        return next_value
