# Copyright 2022 Cartesi Pte. Ltd.
#
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

from os import environ
import traceback
import logging
import requests
import json
import pickle
from eth_abi import decode, encode
from Order import Order
from OrderBook import OrderBook 

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]
logger.info(f"HTTP rollup_server url is {rollup_server}")

# Default header for ERC-20 transfers coming from the Portal, which corresponds
# to the Keccak256-encoded string "ERC20_Transfer", as defined at
# https://github.com/cartesi/rollups/blob/main/onchain/rollups/contracts/facets/ERC20PortalFacet.sol.
ERC20_TRANSFER_HEADER =  b'Y\xda*\x98N\x16Z\xe4H|\x99\xe5\xd1\xdc\xa7\xe0L\x8a\x990\x1b\xe6\xbc\t)2\xcb]\x7f\x03Cx'
# Function selector to be called during the execution of a voucher that transfers funds,
# which corresponds to the first 4 bytes of the Keccak256-encoded result of "transfer(address,uint256)"
TRANSFER_FUNCTION_SELECTOR = b'\xa9\x05\x9c\xbb'

def save_book(order_book):
    pickle_file = open("order_book", "wb")
    pickle.dump(order_book, pickle_file)
    pickle_file.close()

def load_book():
    pickle_file = open('order_book', 'rb')
    order_book = pickle.load(pickle_file)
    pickle_file.close()
    return order_book



def hex2str(hex):
    """
    Decodes a hex string into a regular string
    """
    return bytes.fromhex(hex[2:]).decode("utf-8")

def str2hex(str):
    """
    Encodes a string as a hex string
    """
    return "0x" + str.encode("utf-8").hex()

def handle_deposit_money(payload, sender, timestamp):
    print(f"Received deposit request {payload}")

    try:
        # Check whether an input was sent by the Portal,
        # which is where all deposits must come from
        if sender != rollup_address:
            result = {'error': 'Input does not come from the Portal'}
            save_notification(sender, NOTIFICATION_ACTIONS['SYSTEM'], {}, timestamp, result)
            return reject_input(json.dumps(result), payload)

        # Attempt to decode input as an ABI-encoded ERC20 deposit
        binary = bytes.fromhex(payload[2:])
        try:
            decoded = decode(['bytes32', 'address', 'address', 'uint256', 'bytes'], binary)
        except Exception as e:
            print(e)
            result = {'error': "Payload does not conform to ERC20 deposit ABI"}
            print(result)
            save_notification(sender, NOTIFICATION_ACTIONS['SYSTEM'], {}, timestamp, result)
            return reject_input(json.dumps(result), payload)

        # Check if the header matches the Keccak256-encoded string "ERC20_Transfer"
        input_header = decoded[0]
        if input_header != ERC20_TRANSFER_HEADER:
            result = {'error': 'Input header is not from an ERC20 transfer'}
            save_notification(sender, NOTIFICATION_ACTIONS['SYSTEM'], {}, timestamp, result)
            return reject_input(json.dumps(result), payload)

        user = decoded[1]
        erc20_contract = decoded[2]
        amount = decoded[3]

        result = {'message': f"Deposit received from: {user}; ERC-20: {erc20_contract}; Amount: {amount}"}
        print(f"Adding notice: {json.dumps(result)}")

        if not can_deposit_token(erc20_contract):
            print(f"Token is not acceptable, sending them back")
            handle_withdraw_money(user, amount, erc20_contract)
            result = {'error': "Token is not acceptable, we are sending them back to you as voucher!"}
            save_notification(
                user,
                NOTIFICATION_ACTIONS['DEPOSIT'],
                {'amount': amount, 'token': erc20_contract},
                timestamp,
                result
            )
            reject_input('Invalid token', json.dumps(result))
            return consts.ACCEPT_STATUS

        add_deposit_user(user, amount / BASE_AMOUNT, erc20_contract, timestamp)
        add_notice(json.dumps(result))
        save_notification(
            user,
            NOTIFICATION_ACTIONS['DEPOSIT'],
            {'amount': amount, 'token': erc20_contract},
            timestamp,
            result
        )
        return consts.ACCEPT_STATUS
    except Exception as e:
        print(e)
        return reject_input(f"Error processing data{payload}", payload)

def handle_withdraw_money(user, amount, token):
    # Encode a transfer function call that returns the amount back to the depositor
    print('return amount', amount)
    timestamp = int(datetime.datetime.now().timestamp())
    transfer_payload = \
        TRANSFER_FUNCTION_SELECTOR \
        + encode(['address', 'uint256', 'address', 'uint256'], [user, amount, token, timestamp])
    # Post voucher executing the transfer on the ERC-20 contract: "I don't want your money"!
    voucher = {"address": token, "payload": "0x" + transfer_payload.hex()}
    logger.info(f"Issuing voucher {voucher}")
    res = requests.post(rollup_server + "/voucher", json=voucher)
    logger.info(f"Received voucher status {res.status_code} body {res.content}")


def reject_input(msg, payload):
    print(f"Reject input {msg}")
    add_report(payload, consts.REJECT_STATUS)
    return consts.REJECT_STATUS



def handle_advance(data):
    logger.info(f"Received advance request data {data}")

    try:
        payload = bytes.fromhex(data["payload"][2:]).decode()
        print(payload)
    except Exception as e:
        print(e)
        return handle_deposit_money(data["payload"], data['metadata']['msg_sender'], timestamp)

    user = data['metadata']['msg_sender']

    try:
        payload = json.loads(payload)
        print("data json")
    except Exception as e:
        print("data not json", e)
        return "reject"

    order_book = load_book()
    
    print(payload)
    match payload['action']:
        case "add_order":
            # TODO: generate incremental id from orderBook structure
            order = Order(
                0,
                data['metadata']['msg_sender'], 
                payload['side'], 
                payload['price'],
                payload['quantity']
            )
            print("add order", order)
            order_book.add_order(order)
            print(order_book.view_book())
            result = "ok"
        case "cancel_order":
            print("cancel order")
            result = "ok"

    save_book(order_book)

    status = "accept"
    try:
        logger.info("Adding notice")
        response = requests.post(rollup_server + "/notice", json={"payload": data["payload"]})
        logger.info(f"Received notice status {response.status_code} body {response.content}")

    except Exception as e:
        status = "reject"
        msg = f"Error processing data {data}\n{traceback.format_exc()}"
        logger.error(msg)
        response = requests.post(rollup_server + "/report", json={"payload": str2hex(msg)})
        logger.info(f"Received report status {response.status_code} body {response.content}")

    return status

def handle_inspect(data):
    logger.info(f"Received inspect request data {data}")
    logger.info("Adding report")
    response = requests.post(rollup_server + "/report", json={"payload": data["payload"]})
    logger.info(f"Received report status {response.status_code}")
    return "accept"

handlers = {
    "advance_state": handle_advance,
    "inspect_state": handle_inspect,
}

finish = {"status": "accept"}
rollup_address = None

while True:
    logger.info("Sending finish")
    response = requests.post(rollup_server + "/finish", json=finish)
    logger.info(f"Received finish status {response.status_code}")
    if response.status_code == 202:
        logger.info("No pending rollup request, trying again")
    else:
        rollup_request = response.json()
        data = rollup_request["data"]
        if "metadata" in data:
            metadata = data["metadata"]
            if metadata["epoch_index"] == 0 and metadata["input_index"] == 0:
                rollup_address = metadata["msg_sender"]
                logger.info(f"Captured rollup address: {rollup_address}")
                continue
        handler = handlers[rollup_request["request_type"]]
        finish["status"] = handler(rollup_request["data"])
