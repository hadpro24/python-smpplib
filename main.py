import logging
import sys
from threading import Thread
from fastapi import FastAPI
import uvicorn
import gsm0338

import smpplib.gsm
import smpplib.client
import smpplib.consts
from producer import publish
from utils import PersistentSequenceGenerator
from couter import SMSCounter

# if you want to know what's happening
app = FastAPI()
logging.basicConfig(level='DEBUG')

def get_encoding(message):
    m = SMSCounter.count(message)
    encode_m = {
        'GSM_7BIT': smpplib.consts.SMPP_ENCODING_DEFAULT,
        'GSM_7BIT_EX': smpplib.consts.SMPP_ENCODING_DEFAULT,
        'UTF16': smpplib.consts.SMPP_ENCODING_ISO10646,
    }
    return encode_m.get(m['encoding'], 'GSM_7BIT')

def send_message_sm(pdu):
    sys.stdout.write('sent {} {} - {}\n'.format(pdu.sequence, pdu.message_id, pdu))
    print(pdu.message_id)
    publish('messageid_available', {'messageid': pdu.message_id.decode(), 'message_sequence': str(pdu.sequence)})

def handle_deliver_sm(pdu):
    sys.stdout.write('delivered {} - {}\n'.format(pdu.receipted_message_id, pdu.sequence))
    #publish('webhook_delivery', {'messageid': pdu.receipted_message_id.decode(), 'message_sequence': str(pdu.sequence)})
    return 0 # cmd status for deliver_sm_resp

generator = PersistentSequenceGenerator()
client = smpplib.client.Client('102.176.160.15', 7502, sequence_generator=generator)

# Print when obtain message_id
client.set_message_sent_handler(lambda pdu: send_message_sm(pdu))

# Handle delivery receipts (and any MO SMS)
client.set_message_received_handler(lambda pdu: handle_deliver_sm(pdu))

client.connect()
client.bind_transceiver(system_id='nimba', password='$re2@!23')


@app.get("/")
async def home():
    return {'status': 'OK'}


@app.get('/send-message')
async def send_message_view(message:str, contact:str, sender_name:str):
    # Two parts, GSM default / UCS2, SMS with UDH
    parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(message, encoding=get_encoding(message))

    for part in parts:
        pdu = client.send_message(
            source_addr_ton=smpplib.consts.SMPP_TON_ALNUM,
            source_addr_npi=smpplib.consts.SMPP_NPI_UNK,
            # Make sure it is a byte string, not unicode:
            source_addr=sender_name,

            dest_addr_ton=smpplib.consts.SMPP_TON_INTL,
            dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
            # Make sure these two params are byte strings, not unicode:
            destination_addr=contact,
            short_message=part,

            data_coding=encoding_flag,
            esm_class=msg_type_flag,
            registered_delivery=True,
        )
        print(pdu.sequence)
    return {'message_sequence': pdu.sequence}


class PropagatingThread(Thread):
    def run(self):
        self.exc = None
        try:
            if hasattr(self, '_Thread__target'):
                # Thread uses name mangling prior to Python 3.
                self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
            else:
                self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        super(PropagatingThread, self).join(timeout)
        if self.exc:
            raise self.exc
        return self.ret

if __name__ == '__main__':
    # start loop
    t = PropagatingThread(target=client.listen)
    t.start()
    uvicorn.run(app, host='0.0.0.0', port=8080)
    t.join()
