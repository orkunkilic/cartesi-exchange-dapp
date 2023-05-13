import requests, json
from os import environ

rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]

def to_hex(value):
    return "0x" + value.encode().hex()

def add_report(payload):
    print("Adding report")
    response_data = requests.post(rollup_server + "/report", json={"payload": to_hex(json.dumps(payload))})
    return response_data.status_code
