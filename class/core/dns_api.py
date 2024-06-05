import requests
import mw
from libs.dns_lib import get_token, DNS_API, TOKEN_API

from flask import request


class dns_api:

    def __init__(self):
        self.token_api = TOKEN_API


    def getTokenApi(self):
        response = get_token(self.token_api)

        if response.status_code == 200:
            return mw.returnJson('OK', 'OK', data=response.json())
        else:
            raise Exception("Cannot get token")


    def addDomainApi(self):
        response = get_token(self.token_api)
        if response.status_code == 200:
            token = response.json()
        domain = request.form.get('domain', '')
        url = DNS_API + '/api/app/domain'
        params = {
            'act': 'add',
            'domain': domain,
            'tid': int(token['token_id']),
            'token': token['token'],
        }
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return mw.returnJson('OK', 'OK', data=response.json())
        return mw.returnJson('KO', 'KO', False)


    def getRecordsApi(self):
        response = get_token(self.token_api)
        if response.status_code == 200:
            token = response.json()
        domain = request.form.get('domain', '')
        url = DNS_API + '/api/app/record/list'
        params = {
            'page': 0,
            'pagesize': 10,
            'domain': domain,
            'tid': int(token['token_id']),
            'token': token['token'],
        }
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return mw.returnJson('OK', 'OK', data=response.json())
        return mw.returnJson('KO', 'KO', False)


    def manageRecord(self, act: str, token, form):
        record_id = form.get('id', '')
        domain = form.get('domain', '')
        host = form.get('host', '')
        ip = form.get('ip', '')
        qt = form.get('type', '')
        ttl = form.get('ttl', '')
        url = DNS_API + '/api/app/record'
        params = {
            'id': record_id,
            'act': act,
            'domain': domain,
            'host': host,
            'ip': ip,
            'qt': qt,
            'ttl': ttl,
            'tid': int(token['token_id']),
            'token': token['token'],
        }
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return mw.returnJson('OK', 'OK', data=response.json())
        return mw.returnJson('KO', 'KO', False)



    def deleteRecordApi(self):
        response = get_token(self.token_api)
        if response.status_code == 200:
            token = response.json()

        return self.manageRecord("del", token, request.form)
        


    def saveRecordApi(self):
        response = get_token(self.token_api)
        if response.status_code == 200:
            token = response.json()

        return self.manageRecord("add", token, request.form)
