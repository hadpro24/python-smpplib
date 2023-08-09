import logging
import sys
from threading import Thread
from fastapi import FastAPI
import uvicorn

import smpplib.gsm
import smpplib.client
import smpplib.consts
from producer import publish
from utils import PersistentSequenceGenerator

# if you want to know what's happening
app = FastAPI()
logging.basicConfig(level='DEBUG')

def send_message_sm(pdu):
    sys.stdout.write('sent {} {} - {}\n'.format(pdu.sequence, pdu.message_id, pdu))
    print(pdu.message_id)
    publish('messageid_available', {'messageid': pdu.message_id.decode(), 'message_sequence': str(pdu.sequence)})

def handle_deliver_sm(pdu):
    sys.stdout.write('delivered {} - {}\n'.format(pdu.receipted_message_id, pdu.sequence))
    publish('webhook_delivery', {'messageid': pdu.receipted_message_id.decode(), 'message_sequence': str(pdu.sequence)})
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
    parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(message, encoding=smpplib.consts.SMPP_ENCODING_ISO10646)

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

if __name__ == '__main__':
    # start loop
    t = Thread(target=client.listen)
    t.start()
    uvicorn.run(app, host='0.0.0.0', port=8080)

