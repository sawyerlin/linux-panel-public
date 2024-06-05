"""
lib for getting remote plugins
"""
from urllib.parse import urljoin
import requests
import json
import mw

URL = 'https://ceshi.tingwen777.com/linux-panel-plugins/'
INDEX_URL = 'https://ceshi.tingwen777.com/index.json'

def get_plugins(os_name: str) -> list:
    """
    get plugins
    """
    with open(mw.getPanelDataDir() + "/plugins.json") as json_file:
        result = []
        for data in json.load(json_file):
            if data.get('disable', False):
                continue
            plugin_os_name = data.get('os', None)
            if plugin_os_name == 'debian':
                if os_name in ('debian', 'ubuntu'):
                    result.append(data)
            elif plugin_os_name == 'rhel':
                if os_name in ('centos', 'rhel'):
                    result.append(data)
            else:
                result.append(data)
        return result


def get_plugin_info(name: str, os_name: str):
    """
    get plugin info
    """
    plugins = get_plugins(os_name)
    for plugin in plugins:
        if plugin["name"] == name:
            return plugin
    return None


def get_plugin_remote_url(name: str):
    """
    get plugin remote url
    """
    return urljoin(URL, name)
