import logging
import sys
from threading import Thread
import requests
import uvicorn
from fastapi import FastAPI

import smpplib.gsm
import smpplib.client
import smpplib.consts

app = FastAPI()

# if you want to know what's happening
logging.basicConfig(level='DEBUG')
client = smpplib.client.Client('102.176.160.15', 7502)


def retry_with_backoff(retries=5, backoff_in_seconds=1):
    def rwb(f):
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return f(*args, **kwargs)
                except:
                    if x == retries:
                        raise
                    sleep = (backoff_in_seconds*2**x+random.uniform(0, 1))
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return rwb


@retry_with_backoff(retries=15)
def send_callback(URL, payload):
    response = requests.post(URL, json=playload)
    if response.status_code >= 400:
        raise Exception('Retry')
    return response.json()


def send_message(pdu):
    sys.stdout.write('sent {} {} \n'.format(pdu.sequence, pdu.message_id))


def handle_deliver_sm(pdu):
    sys.stdout.write('delivered {} \n'.format(pdu.receipted_message_id))
    key = "Ilc'pCm~!B/Dv)sD[J=9Y(>I;K'$qFzzQ;_.)/4E5ggSa#_].ATiLMCv:)MbSE"
    ULR = f'https://app.nimbasms.com/v1/webhook/provider/delivery-confirmation?key={key}'
    payload = {
        'messageid': pdu.receipted_message_id,
    }
    try:
        send_callback(URL, json=playload)
    except:
        pass
    return 0 # cmd status for deliver_sm_resp


@app.get("/")
async def home():
    return {'status': 'OK'}


@app.get('/send-message')
async def read_item(message:str, contact:str, sender_name:str):
    # Two parts, GSM default / UCS2, SMS with UDH
    parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(u'{}'.format(message))

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
    return {'messageid': pdu.sequence}


if __name__ == '__main__':
    # Print when obtain message_id
    client.set_message_sent_handler(lambda pdu: send_message(pdu))

    # Handle delivery receipts (and any MO SMS)
    client.set_message_received_handler(lambda pdu: handle_deliver_sm(pdu))

    client.connect()
    client.bind_transceiver(system_id='nimba', password='$re2@!23')

    # Enters a loop, waiting for incoming PDUs
    t = Thread(target=client.listen)
    t.start()
    # start app
    uvicorn.run(app, host='0.0.0.0', port=8080)
