import os
import json
import mw
from system_api import system_api
from plugins_api import plugins_api

def summary():
    system = system_api()
    local_summary = json.loads(system.getEnvInfoApi())['data']
    del local_summary['status']
    del local_summary['disk']
    local_summary['ftps'] = os.path.exists(os.path.join(mw.getServerDir(), 'pureftp', 'version.pl'))

    return local_summary

def get_mysql_password():
    result = plugins_api().run(name='mysql', func='get_db_list', args="\"{'page': 1, 'page_size': 10}\"")
    return json.loads(result[0])['info']['root_pwd']
