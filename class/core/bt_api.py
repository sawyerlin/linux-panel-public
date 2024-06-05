import json
import threading
import mw
import bt_migrate_local
import bt_migrate_remote

from typing import Tuple
from flask import request
import traceback

ssh_client = None

class bt_api:

    def __init__(self):
        ...

    
    def _compare_env(self, remote_summary: dict, local_summary: dict) -> Tuple[bool, str]:
        remote_webserver = remote_summary['webserver']
        local_webserver = local_summary['webserver']
        if remote_webserver == 'nginx':
            if local_webserver != 'OpenResty':
                return False, f"【Web服务器】【本地】不支持 {local_webserver}"
        else:
            return False, f"【Web服务器】【远程】不支持 {remote_webserver}"

        remote_phps = remote_summary['php']
        local_phps = local_summary['php']

        for remote_php in remote_phps:
            if remote_php not in local_phps:
                return False, f"【PHP】【本地】{remote_php} 未安装"

        remote_mysql = remote_summary['mysql']
        local_mysql = local_summary['mysql']

        if remote_mysql and not local_mysql:
            return False, "【MySQL】【本地】未安装"

        if remote_summary['ftps'] and not local_summary['ftps']:
            return False, "【PureFtp】【本地】未安装"

        return True, ""


    def getSummaryApi(self):
        domain_ip = request.form.get('domain_ip')
        port = request.form.get('port')
        username = request.form.get('username')
        password = request.form.get('password')

        global ssh_client
        ssh_client = bt_migrate_remote.get_client(domain_ip, port, username, password)
        remote_result = bt_migrate_remote.check(ssh_client)
        remote_summary = bt_migrate_remote.summary(remote_result)
        local_summary = bt_migrate_local.summary()
        is_matching, matching_msg = self._compare_env(remote_summary, local_summary)
        return mw.returnJson('OK', 'OK', {
            'local_summary': local_summary,
            'remote_summary': remote_summary,
            'remote_result': remote_result,
            'is_matching': is_matching,
            'matching_msg': matching_msg
        })

    def migrateApi(self):
        global ssh_client
        migrate_data = json.loads(request.form.get('migrate_data'))
        thread = threading.Thread(target=self.migrate, args=(ssh_client, migrate_data,))
        thread.start()
        print(mw.writeMigrationProgress(True, 0, list('')))

        return mw.returnJson('OK', '', {
            "progress": 0.0,
            "migration_started": True,
        })

  
    def getProgressApi(self):
        migration_progress = json.loads(mw.getMigrationProgress())
        return mw.returnJson('OK', migration_progress["progress_msg"], {
            "progress": f"{migration_progress['progress']:.2f}",
            "migration_started": migration_progress["migration_started"],
        })


    def migrate(self, ssh_client, migrate_data):
        progress = 0
        progress_msg = list('')
        try:
            bt_migrate_remote.init(ssh_client)
            total_count = len(migrate_data['sites']) + len(migrate_data['databases']) + len(migrate_data['ftps'])
            current_count = 0.0
            local_mysql_password = bt_migrate_local.get_mysql_password()
            for site in migrate_data['sites']:
                current_count = current_count + 1
                bt_migrate_remote.migrate_site(ssh_client, site, progress_msg, progress)
                progress = current_count / total_count * 100
            for database in migrate_data['databases']:
                current_count = current_count + 1
                bt_migrate_remote.migrate_db(ssh_client, migrate_data['username'], migrate_data['password'], local_mysql_password, database, progress_msg, progress)
                progress = current_count / total_count * 100
            for ftp in migrate_data['ftps']:
                current_count = current_count + 1
                bt_migrate_remote.migrate_ftp(ssh_client, ftp, progress_msg, progress)
                progress = current_count / total_count * 100
        except Exception as ex:
            traceback.print_exc()
            progress_msg.append(str(ex))
        finally:
            mw.writeMigrationProgress(False, progress, progress_msg)
