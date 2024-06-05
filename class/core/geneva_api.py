import os
import mw


class geneva_api:

    def __init__(self):
        self.http_service = 'geneva_http.service'
        self.https_service = 'geneva_https.service'


    def is_service_running(self) -> bool:
        http_output = mw.execShell(f"systemctl is-active {self.http_service}")
        https_output = mw.execShell(f"systemctl is-active {self.https_service}")
        return ('inactive' not in http_output[0]) and ('inactive' not in https_output[0])


    def startApi(self):
        mw.execShell(os.path.join(mw.getServerDir(), "mdserver-web/geneva/start.sh"))
        return mw.returnJson(self.is_service_running(), 'OK')


    def stopApi(self):
        mw.execShell(os.path.join(mw.getServerDir(), "mdserver-web/geneva/stop.sh"))
        return mw.returnJson(self.is_service_running(), 'OK')


    def getStatusApi(self):
        return mw.returnJson(self.is_service_running(), 'OK')

