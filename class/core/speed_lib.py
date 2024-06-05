import json
import time
import random
import mw
import db
import requests

def http_request2(url, data=''):
    options = {
        'headers': {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        'verify': False,
        'timeout': 10000
    }

    if data:
        options['data'] = data

    response = requests.post(url, **options)
    return response.text


MAX_RETRIES = 3
def http_check(host):
    print(f"check domain speed: {host}")
    retires = 0
    while retires < MAX_RETRIES:
        try:
            url = mw.getSpeedTestServer()
            data = {'host': host}
            return json.loads(http_request2(url, data=data))
        except ValueError as e:
            print(f"Error fetching data from {url}: {e}")
            if retires < MAX_RETRIES:
                delay = random.uniform(3, 5)
                print(f"Retrying ({retires}/{MAX_RETRIES}) in {delay} seconds ...")
                time.sleep(delay)
            else:
                print(f"Failed to fetch valid JSON from {url} after {MAX_RETRIES} attempts.")
                return {'code': -1}


def speed_check_task():
    sql = db.Sql().dbfile('system')
    csql = mw.readFile('data/sql/system.sql')
    csql_list = csql.split(';')
    for csql_item in csql_list:
        sql.execute(csql_item, ())

    sites = mw.M('sites').field('id,name,path,status,ps,addtime,edate,type_id').select()
    for site in sites:
        domains = mw.M('domain').field('id,name').where('pid=?', (site['id'],)).select()
        for domain in domains:
            time.sleep(random.uniform(3, 5))

            name = domain.get('name')
            result = http_check(name)
            if result['code'] == -1:
                success_rate = -1
            else:
                details = []
                success_count = 0
                for data in result["data"]["all_data"]:
                    if data['type'] == 'success' and 200 <= data['http_code'] < 400:
                        success_count += 1
                    details.append({
                        "name": data['name'],
                        "code": data['http_code'],
                        "speed_time": data['all_time'],
                        "ip": data['ip'],
                    })
                success_rate = success_count / len(details) * 100
            find_domains = sql.table('domain_speed').field('id').where('domain_id=?', (domain['id'],)).select()
            if find_domains:
                domain_speed_id = find_domains[0]['id']
                sql.table('domain_speed').where('id=?', (domain_speed_id,)).update({
                    'success_rate': success_rate,
                    'addtime': int(time.time())
                })
            else:
                domain_speed_id = sql.table('domain_speed').add('domain_id, success_rate, addtime', (domain["id"], success_rate, int(time.time())))
            sql.table('domain_speed_detail').where('domain_speed_id=?', (domain_speed_id,)).delete()
            for detail in details:
                sql.table('domain_speed_detail').add('domain_speed_id, name, code, speed_time, ip', (domain_speed_id, detail['name'], detail['code'], detail['speed_time'], detail['ip']))

