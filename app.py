import logging
import sys

import smpplib.gsm
import smpplib.client
import smpplib.consts

# if you want to know what's happening
logging.basicConfig(level='DEBUG')

def send_message(pdu):
    sys.stdout.write('sent {} {} - {}\n'.format(pdu.sequence, pdu.message_id, pdu))

def handle_deliver_sm(pdu):
        sys.stdout.write('delivered {} - {} {}\n'.format(pdu.receipted_message_id, pdu.payload_type, pdu.message_state))
        return 0 # cmd status for deliver_sm_resp

# Two parts, GSM default / UCS2, SMS with UDH
parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(u'Hello World €$£')

client = smpplib.client.Client('102.176.160.15', 7502)

# Print when obtain message_id
client.set_message_sent_handler(lambda pdu: send_message(pdu))

# Handle delivery receipts (and any MO SMS)
client.set_message_received_handler(lambda pdu: handle_deliver_sm(pdu))

client.connect()
client.bind_transceiver(system_id='nimba', password='$re2@!23')

for part in parts:
    pdu = client.send_message(
        source_addr_ton=smpplib.consts.SMPP_TON_ALNUM,
        source_addr_npi=smpplib.consts.SMPP_NPI_UNK,
        # Make sure it is a byte string, not unicode:
        source_addr='Nimba',

        dest_addr_ton=smpplib.consts.SMPP_TON_INTL,
        dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
        # Make sure these two params are byte strings, not unicode:
        destination_addr='224623273737',
        short_message=part,

        data_coding=encoding_flag,
        esm_class=msg_type_flag,
        registered_delivery=True,
    )
    print(pdu.sequence)

# Enters a loop, waiting for incoming PDUs
client.listen()
