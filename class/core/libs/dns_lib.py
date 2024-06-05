import uuid
import requests

TOKEN_API = 'http://23.224.167.180:5000'
DNS_API = 'http://23.224.167.180:8088'

def get_mac_address():
    return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])


def get_token(token_api: str):
    data = {
        'mac_address': get_mac_address()
    }

    return requests.post(token_api + '/get_token', json=data, timeout=10)
