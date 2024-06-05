import paramiko
import json
import os
import time
import subprocess
import mw
from paramiko.client import SSHClient
from db import Sql
from plugins_api import plugins_api

SERVER_PATH = '/www/server'
PANEL_PATH = os.path.join(SERVER_PATH, 'panel')
CLASS_PATH = os.path.join(PANEL_PATH, 'class')
PYTHON_BIN_PATH = os.path.join(PANEL_PATH, 'pyenv/bin/python3')
DATA_PATH = os.path.join(PANEL_PATH, 'data')
DB_PATH = os.path.join(DATA_PATH, 'db')
REMOTE_STATUS_JSON = 'bt_migrate_remote.json'

def execute(client: SSHClient, command: str):
    _, stdout, _ = client.exec_command(command)
    output = stdout.read().decode()
    return output.strip()


def decrypt_pass(client: SSHClient, password: str):
    decrypt_python = f"import sys; sys.path.insert(0,'class/'); import PluginLoader; print(PluginLoader.db_decrypt('{password}')['msg'])"
    command = f"cd {CLASS_PATH} && {PYTHON_BIN_PATH} -c \"{decrypt_python}\""
    return execute(client, command)


def get_mysql_rootpass(client: SSHClient):
    get_mysql_rootpass = f"import password; print(password.password().get_mysql_root(None)['msg'])"
    command = f"cd {CLASS_PATH} && {PYTHON_BIN_PATH} -c \"{get_mysql_rootpass}\""
    return execute(client, command)


def check_status_nginx(client: SSHClient):
    vhost_path = os.path.join(PANEL_PATH, 'vhost')
    version_path = os.path.join(SERVER_PATH, 'nginx/version.pl')
    version = execute(client, f"cat {version_path}")
    site_db_path = os.path.join(DB_PATH, 'site.db')
    site_query = "SELECT id, name, path, ps FROM sites WHERE project_type = 'PHP';"
    result = {}
    if version:
        result = {
            'name': 'nginx',
            'version': version,
        }
        sites = []
        site_command = f"sqlite3 {site_db_path} \"{site_query}\""
        site_rows = execute(client, site_command).split('\n')
        for site_row in site_rows:
            if site_row:
                site_columns = site_row.split('|')
                site = {
                    'site_id': site_columns[0],
                    'site_name': site_columns[1],
                    'site_path': site_columns[2],
                    'site_ps': site_columns[3],
                    'rewrite_path': os.path.join(vhost_path, 'rewrite', site_columns[1] + '.conf'),
                    'ssl_path': os.path.join(vhost_path, 'ssl', site_columns[1]),
                    'cert_path': os.path.join(vhost_path, 'cert', site_columns[1]),
                    'config_path': os.path.join(vhost_path, 'nginx', site_columns[1] + '.conf'),
                    'well_known_path': os.path.join(vhost_path, 'nginx/well-known', site_columns[1] + '.conf'),
                    'domains': [],
                }

                domain_query = f"SELECT name, port FROM domain WHERE pid = {site_columns[0]};"
                domain_command = f"sqlite3 {site_db_path} \"{domain_query}\""
                domain_rows = execute(client, domain_command).split('\n')
                for domain_row in domain_rows:
                    domain_columns = domain_row.split('|')
                    domain = {
                        'domain_name': domain_columns[0],
                        'domain_port': domain_columns[1]
                    }
                    site['domains'].append(domain)

                sites.append(site)

        result['sites'] = sites

    return result

def check_status_mysql(client: SSHClient):
    version_path = os.path.join(SERVER_PATH, 'mysql/version.pl')
    version = execute(client, f"cat {version_path}")
    database_db_path = os.path.join(DB_PATH, 'database.db')
    database_query = 'SELECT pid, name, username, password, accept, ps FROM databases;'
    result = {}
    if version:
        result = {
            'name': 'mysql',
            'version': version,
            'root': 'root',
            'password': get_mysql_rootpass(client)
        }
        dbs = []
        command = f"sqlite3 {database_db_path} '{database_query}'"
        raw_dbs = execute(client, command)
        rows = raw_dbs.split('\n')
        for row in rows:
            if row:
                columns = row.split('|')
                dbs.append({
                    'site_id': columns[0],
                    'name': columns[1],
                    'username': columns[2],
                    'password': decrypt_pass(client, columns[3][6:]),
                    'accept': columns[4],
                    'ps': columns[5],
                })

        result['dbs'] = dbs

    return result


def check_status_php(client: SSHClient):
    versions_path = os.path.join(SERVER_PATH, 'php')
    versions = execute(client, f"ls {versions_path}").split('\n')
    extension_config_path = os.path.join(DATA_PATH, 'phplib.conf')
    extensions = json.loads(execute(client, f"cat {extension_config_path}"))
    result = []
    for version in versions:
        php_config_path = os.path.join(versions_path, version, 'etc/php.ini')
        php_config = execute(client, f"cat {php_config_path}")
        enabled_extensions = []
        for extension in extensions:
            if version in extension['versions'] and php_config.find(extension['check']) != -1:
                enabled_extensions.append(extension['name'])

        version_result = {
            'name': 'php',
            'version': version,
            'enabled_extensions': enabled_extensions
        }
        result.append(version_result)

    return result


def check_status_ftp(client: SSHClient):
    version_path = os.path.join(SERVER_PATH, 'pure-ftpd/version.pl')
    version = execute(client, f"cat {version_path}")
    ftp_db_path = os.path.join(DB_PATH, 'ftp.db')
    ftp_query = 'SELECT pid, name, password, path, status, ps FROM ftps;'
    result = {}
    if version:
        result = {
            'name': 'pure-ftpd',
            'version': version,
            
        }
        ftps = []
        command = f"sqlite3 {ftp_db_path} '{ftp_query}'"
        raw_ftps = execute(client, command)
        rows = raw_ftps.split('\n')
        for row in rows:
            if row:
                columns = row.split('|')
                ftps.append({
                    'site_id': columns[0],
                    'name': columns[1],
                    'password': decrypt_pass(client, columns[2][6:]),
                    'path': columns[3],
                    'status': columns[4],
                    'ps': columns[5],
                })

        result['ftps'] = ftps
    return result


def get_client(hostname: str, port: int, username: str, password: str) -> SSHClient:
    client = SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password)
    return client


def check(client: SSHClient, cache: bool = False) -> dict:
    if os.path.exists(REMOTE_STATUS_JSON) and cache:
        with open(REMOTE_STATUS_JSON, 'r', encoding='utf-8') as f:
            result = json.loads(f.read())
    else:
        result = {}
        result['webserver'] = check_status_nginx(client)
        result['database'] = check_status_mysql(client)
        result['php'] = check_status_php(client)
        result['ftp'] = check_status_ftp(client)
        if cache:
            with open(REMOTE_STATUS_JSON, 'w', encoding='utf-8') as f:
                f.write(json.dumps(result))
    return result


def summary(result: dict) -> dict:
    return {
        "webserver": result['webserver']['name'] if result['webserver']['version'] is not None else None,
        "php": [php['version'] for php in result['php']],
        "mysql": result['database']['version'] is not None,
        "ftps": result['ftp']['version'] is not None
    }


MIGRATE_PREPARE_PATH = "/tmp/bt_prepare"
MIGRATE_LOCAL_PATH = os.path.join(os.getcwd(), 'tmp', 'migration')
MIGRATE_LOCAL_PATH_DBS = os.path.join(MIGRATE_LOCAL_PATH, 'dbs')
MIGRATE_LOCAL_PATH_SITES = os.path.join(MIGRATE_LOCAL_PATH, 'sites')
MIGRATE_LOCAL_PATH_FTPS = os.path.join(MIGRATE_LOCAL_PATH, 'ftps')


def init(client):
    execute(client, f"mkdir -p {MIGRATE_PREPARE_PATH}")

    if not os.path.exists(MIGRATE_LOCAL_PATH):
        os.mkdir(MIGRATE_LOCAL_PATH)

    if not os.path.exists(MIGRATE_LOCAL_PATH_DBS):
        os.mkdir(MIGRATE_LOCAL_PATH_DBS)

    if not os.path.exists(MIGRATE_LOCAL_PATH_SITES):
        os.mkdir(MIGRATE_LOCAL_PATH_SITES)

    if not os.path.exists(MIGRATE_LOCAL_PATH_FTPS):
        os.mkdir(MIGRATE_LOCAL_PATH_FTPS)


def migrate_site(client: SSHClient, site: dict, msg: list, progress: float):
    site_name = site['site_name']
    site_folder = site['site_path']
    site_ssl_folder = site['ssl_path']
    site_cert_folder = site['cert_path']
    site_folder_archive_file = f"site_{site_name}.tar.gz"
    site_ssl_folder_archive_file = f"site_ssl_{site_name}.tar.gz"
    site_cert_folder_archive_file = f"site_cert_{site_name}.tar.gz"

    site_rewrite_file_path = site['rewrite_path']
    site_rewrite_file_name = os.path.basename(site_rewrite_file_path)
    site_config_file_path = site['config_path']
    site_config_file_name = os.path.basename(site_config_file_path)
    site_well_known_file_path = site['well_known_path']
    site_well_known_file_name = os.path.basename(site_well_known_file_path)

    msg_title = f"[站点][{site_name}]"

    msg.append(f"{msg_title} 开始迁移\n")
    mw.writeMigrationProgress(True, progress, msg)

    site_folder_backup_command = f"cd {MIGRATE_PREPARE_PATH} && tar -czvf {site_folder_archive_file} -C {site_folder} ."
    execute(client, site_folder_backup_command)
    msg.append(f"{msg_title} 完成文件归档\n")
    mw.writeMigrationProgress(True, progress, msg)
    site_ssl_folder_backup_command = f"cd {MIGRATE_PREPARE_PATH} && tar -czvf {site_ssl_folder_archive_file} -C {site_ssl_folder} ."
    execute(client, site_ssl_folder_backup_command)
    msg.append(f"{msg_title} 完成ssl归档\n")
    mw.writeMigrationProgress(True, progress, msg)
    site_cert_folder_backup_command = f"cd {MIGRATE_PREPARE_PATH} && tar -czvf {site_cert_folder_archive_file} -C {site_cert_folder} ."
    execute(client, site_cert_folder_backup_command)
    msg.append(f"{msg_title} 完成cert归档\n")
    mw.writeMigrationProgress(True, progress, msg)

    site_path = os.path.join(MIGRATE_LOCAL_PATH_SITES, site_name)
    if not os.path.exists(site_path):
        os.mkdir(site_path)
        msg.append(f"{msg_title} 创建本地迁移文件夹\n")
        mw.writeMigrationProgress(True, progress, msg)

    with client.open_sftp() as sftp:
        local_site_folder_archive_file = os.path.join(site_path, site_folder_archive_file)
        sftp.get(os.path.join(MIGRATE_PREPARE_PATH, site_folder_archive_file), local_site_folder_archive_file)
        msg.append(f"{msg_title} 下载远程归档\n")
        mw.writeMigrationProgress(True, progress, msg)

        if os.path.exists(site_folder):
            subprocess.run(['rm', '-rf', site_folder], check=True)
        subprocess.run(['mkdir', '-p', site_folder], check=True)
        subprocess.run(['tar', '-xzf', local_site_folder_archive_file, '-C', site_folder], check=True)
        msg.append(f"{msg_title} 解压文件夹, 并复制到目标文件夹\n")
        mw.writeMigrationProgress(True, progress, msg)

        # ssl migrate
        local_site_ssl_folder_archive_file = os.path.join(site_path, site_ssl_folder_archive_file)
        sftp.get(os.path.join(MIGRATE_PREPARE_PATH, site_ssl_folder_archive_file), local_site_ssl_folder_archive_file)
        msg.append(f"{msg_title} 下载远程ssl归档\n")
        mw.writeMigrationProgress(True, progress, msg)

        dest_site_ssl_folder = os.path.join("/www/server/web_conf/ssl", os.path.basename(site_ssl_folder))
        if os.path.exists(dest_site_ssl_folder):
            subprocess.run(['rm', '-rf', dest_site_ssl_folder], check=True)
        subprocess.run(['mkdir', '-p', dest_site_ssl_folder], check=True)
        subprocess.run(['tar', '-xzf', local_site_ssl_folder_archive_file, '-C', dest_site_ssl_folder], check=True)
        msg.append(f"{msg_title} 解压文件夹, 并复制到目标文件夹\n")
        mw.writeMigrationProgress(True, progress, msg)

        # cert migrate
        local_site_cert_folder_archive_file = os.path.join(site_path, site_cert_folder_archive_file)
        sftp.get(os.path.join(MIGRATE_PREPARE_PATH, site_cert_folder_archive_file), local_site_cert_folder_archive_file)
        msg.append(f"{msg_title} 下载远程cert归档\n")
        mw.writeMigrationProgress(True, progress, msg)

        os.makedirs("/www/server/panel/vhost/cert", exist_ok=True)
        dest_site_cert_folder = os.path.join("/www/server/panel/vhost/cert", os.path.basename(site_cert_folder))
        if os.path.exists(dest_site_cert_folder):
            subprocess.run(['rm', '-rf', dest_site_cert_folder], check=True)
        subprocess.run(['mkdir', '-p', dest_site_cert_folder], check=True)
        subprocess.run(['tar', '-xzf', local_site_cert_folder_archive_file, '-C', dest_site_cert_folder], check=True)
        msg.append(f"{msg_title} 解压文件夹, 并复制到目标文件夹\n")
        mw.writeMigrationProgress(True, progress, msg)

        dest_site_config_file = os.path.join("/www/server/web_conf/nginx/vhost", site_config_file_name)
        try:
            sftp.get(site_config_file_path, dest_site_config_file)
            msg.append(f"{msg_title} 下载远程配置\n")
            mw.writeMigrationProgress(True, progress, msg)
        except FileNotFoundError:
            msg.append(f"{msg_title} 远程配置未找到, {site_config_file_path}\n")
            mw.writeMigrationProgress(True, progress, msg)

        os.makedirs("/www/server/panel/vhost/rewrite", exist_ok=True)
        dest_site_rewrite_file = os.path.join("/www/server/panel/vhost/rewrite", site_rewrite_file_name)
        try:
            msg.append(f"{msg_title} 下载远程伪静态\n")
            mw.writeMigrationProgress(True, progress, msg)
            sftp.get(site_rewrite_file_path, dest_site_rewrite_file)
        except FileNotFoundError:
            msg.append(f"{msg_title} 远程伪静态未找到, {site_rewrite_file_path}\n")
            mw.writeMigrationProgress(True, progress, msg)

        os.makedirs("/www/server/panel/vhost/nginx/well-known", exist_ok=True)
        dest_site_well_known_file = os.path.join("/www/server/panel/vhost/nginx/well-known", site_well_known_file_name)
        try:
            sftp.get(site_well_known_file_path, dest_site_well_known_file)
            msg.append(f"{msg_title} 下载远程well_known\n")
            mw.writeMigrationProgress(True, progress, msg)
        except FileNotFoundError:
            msg.append(f"{msg_title} 远程well_known未找到, {site_well_known_file_path}\n")
            mw.writeMigrationProgress(True, progress, msg)

        php_folder = os.path.join(SERVER_PATH, 'php')
        php_conf_folder = '/www/server/web_conf/php/conf/'
        replace_php = f" {php_conf_folder}enable-php-"

        is_apt = False
        if not os.path.exists(php_folder):
            php_folder = os.path.join(SERVER_PATH, 'php-apt')
            replace_php = f" {php_conf_folder}enable-php-apt"
            if not os.path.exists(php_folder):
                replace_php = f' {php_conf_folder}enable-php-yum'
            else:
                is_apt = True

        with open(dest_site_config_file, 'r', encoding='utf-8') as config_file:
            file_contents = config_file.read()
            replaced_file_content = ''

            original_php = "enable-php-00"
            if original_php in file_contents:
                replaced_file_content = file_contents.replace(original_php, f"{php_conf_folder}{original_php}")
            elif is_apt:
                for version in ["56", "70", "71", "72", "73", "74", "80", "81", "82", "83"]:
                    original_php = f"enable-php-{version}"
                    if original_php in file_contents:
                        replaced_file_content = file_contents.replace(original_php, f"{replace_php}{version[0]}.{version[1]}")
            elif 'enable-php-' in file_contents:
                replaced_file_content = file_contents.replace('enable-php-', replace_php)

            if replaced_file_content:
                with open(dest_site_config_file, 'w', encoding='utf-8') as config_file:
                    config_file.write(replaced_file_content)

    msg.append(f"{msg_title} 配置 PHP\n")
    mw.writeMigrationProgress(True, progress, msg)

    sql = Sql().dbfile("default")
    add_time = time.strftime('%Y-%m-%d %X', time.localtime())
    e_date = '0000-00-00'
    found_site = sql.table('sites').field('id').where('name=?', (site_name,)).find()
    if found_site:
        site_id = found_site['id']
        sql.table('sites').where('name=?', (site_name,)).update({
            'path': site['site_path'],
            'status': 1,
            'type_id': 0,
            'ps': site['site_ps'],
            'edate': e_date,
            'addtime': add_time
        })
    else:
        site_id = sql.table('sites').add('name, path, status, type_id, ps, edate, addtime', (site_name, site['site_path'], 1, 0, site['site_ps'], e_date, add_time))

    for domain in site['domains']:
        found_domain = sql.table('domain').field('id').where('pid=? AND name=?', (site_id, domain['domain_name'])).find()
        if found_domain:
            sql.table('domain').where('id=?', (found_domain['id'],)).update({
                'port': domain['domain_port']
            })
        else:
            sql.table('domain').add('pid, name, port, addtime', (site_id, domain['domain_name'], domain['domain_port'], add_time))

    msg.append(f"{msg_title} 导入数据库\n")
    mw.writeMigrationProgress(True, progress, msg)


def migrate_ftp(client: SSHClient, ftp: dict, msg: list, progress: float):
    ftp_name = ftp['name']
    msg_title = f"[FTP][{ftp_name}]"
    msg.append(f"{msg_title} 开始迁移\n")
    mw.writeMigrationProgress(True, progress, msg)

    ftp_folder = ftp['path']
    ftp_archive_file = f"ftp_{ftp_name}.tar.gz"
    ftp_backup_command = f"cd {MIGRATE_PREPARE_PATH} && tar -czvf {ftp_archive_file} {ftp_folder}"
    if ftp_folder not in execute(client, ftp_backup_command):
        return False
    msg.append(f"{msg_title} 完成文件归档\n")
    mw.writeMigrationProgress(True, progress, msg)

    ftp_path = os.path.join(MIGRATE_LOCAL_PATH_FTPS, ftp_name)
    if not os.path.exists(ftp_path):
        os.mkdir(ftp_path)
        msg.append(f"{msg_title} 创建本地迁移文件夹\n")
        mw.writeMigrationProgress(True, progress, msg)

    with client.open_sftp() as sftp:
        local_ftp_archive_file_path = os.path.join(ftp_path, ftp_archive_file)
        sftp.get(os.path.join(MIGRATE_PREPARE_PATH, ftp_archive_file), local_ftp_archive_file_path)
        subprocess.run(['tar', '-xzf', local_ftp_archive_file_path, '-C', "/"], check=True)
        msg.append(f"{msg_title} 下载远程文件归档, 解压文件夹\n")
        mw.writeMigrationProgress(True, progress, msg)
        
    sql = Sql().dbPos("/www/server/pureftp", "ftps")
    add_time = time.strftime('%Y-%m-%d %X', time.localtime())
    if sql.table('ftps').field('name').where('name=?',(ftp['name'],)).find():
        sql.table('ftps').where('name=?',(ftp['name'],)).update({
            'password': ftp['password'],
            'path': ftp['path'],
            'status': ftp['status'],
            'ps': ftp['ps'],
            'addtime': add_time
        })
    else:
        sql.table('ftps').add('name, password, path, status, ps, addtime', (ftp['name'], ftp['password'], ftp['path'], ftp['status'], ftp['ps'], add_time))

    pure_pw = os.path.join(mw.getServerDir(), "pureftp/bin/pure-pw")
    pure_pw_db = os.path.join(mw.getServerDir(), "pureftp/etc/pureftpd.pdb")
    setup_user = f"""
#!/bin/bash
if {pure_pw} show {ftp['name']} > /dev/null 2>&1; then
    {pure_pw} passwd {ftp['name']} <<EOF \n{ftp['password']}\n{ftp['password']}\nEOF
else
    {pure_pw} useradd {ftp['name']} -u www -d {ftp['path']} <<EOF \n{ftp['password']}\n{ftp['password']}\nEOF
fi
{pure_pw} mkdb {pure_pw_db}
"""
    mw.execShell(setup_user)

    msg.append(f"{msg_title} 导入数据库\n")
    mw.writeMigrationProgress(True, progress, msg)


def migrate_db(client: SSHClient, username: str, password: str, local_password: str, db: dict, msg: list, progress: float) -> bool:
    db_name = db['name']
    msg_title = f"[DB][{db_name}]"
    msg.append(f"{msg_title} 开始迁移\n")
    mw.writeMigrationProgress(True, progress, msg)

    db_sql_file = f"{db_name}.sql"
    db_archive_file = f"db_{db_name}.tar.gz"
    db_backup_command = f"cd {MIGRATE_PREPARE_PATH} && mysqldump -u {username} --password='{password}' {db_name} > {db_sql_file} && tar -czvf {db_archive_file} {db_sql_file}"
    if execute(client, db_backup_command) != db_sql_file:
        return False
    msg.append(f"{msg_title} 完成文件归档\n")
    mw.writeMigrationProgress(True, progress, msg)

    db_path = os.path.join(MIGRATE_LOCAL_PATH_DBS, db_name)
    if not os.path.exists(db_path):
        os.mkdir(db_path)
        msg.append(f"{msg_title} 创建本地迁移文件夹\n")
        mw.writeMigrationProgress(True, progress, msg)

    with client.open_sftp() as sftp:
        local_db_archive_file_path = os.path.join(db_path, db_archive_file)
        sftp.get(os.path.join(MIGRATE_PREPARE_PATH, db_archive_file), local_db_archive_file_path)
        subprocess.run(['tar', '-xzf', local_db_archive_file_path, '-C', db_path], check=True)
        msg.append(f"{msg_title} 下载远程文件归档, 解压文件夹\n")
        mw.writeMigrationProgress(True, progress, msg)

    with open(os.path.join(db_path, 'db.json'), 'w', encoding='utf-8') as db_file:
        db_file.write(json.dumps(db))
        msg.append(f"{msg_title} 编写配置文件\n")
        mw.writeMigrationProgress(True, progress, msg)

    mysql_path = '/www/server/mysql'
    mysql_bin = 'bin/mysql'
    if not os.path.exists(mysql_path):
        mysql_bin = 'bin/usr/bin/mysql'
        mysql_path = '/www/server/mysql-apt'
        if not os.path.exists(mysql_path):
            mysql_path = '/www/server/mysql-yum'

    mysql_bin_path = os.path.join(mysql_path, mysql_bin)
    mysql_sock_path = os.path.join(mysql_path, 'mysql.sock')

    subprocess.run(f"{mysql_bin_path} -u root -p{local_password} -S {mysql_sock_path} -e \"CREATE DATABASE IF NOT EXISTS {db['name']}\"", shell=True, check=True)
    subprocess.run(f"{mysql_bin_path} -u root -p{local_password} -S {mysql_sock_path} {db['name']} < {os.path.join(db_path, db_sql_file)}", shell=True, check=False)
    msg.append(f"{msg_title} 创建数据库并导入备份\n")
    mw.writeMigrationProgress(True, progress, msg)

    sql = Sql().dbPos(mysql_path, "mysql")
    add_time = time.strftime('%Y-%m-%d %X', time.localtime())
    if sql.table('databases').field('name').where('name=?',(db['name'],)).find():
        sql.table('databases').where('name=?', (db['name'],)).update({
            'username': db['username'],
            'password': db['password'],
            'accept': db['accept'],
            'ps': db['ps'],
            'addtime': add_time
        })
    else:
        sql.table('databases').add('name, username, password, accept, ps, addtime', (db['name'], db['username'], db['password'], db['accept'], db['ps'], add_time))
    msg.append(f"{msg_title} 导入数据库\n")

    username = db['username']
    access = db['accept']
    args = f"{{'username':'{username}','access':'{access}'}}"
    result = plugins_api().run(name='mysql', func='set_db_access', args=args)
    msg.append(f"{msg_title} {result}\n")
    mw.writeMigrationProgress(True, progress, msg)
