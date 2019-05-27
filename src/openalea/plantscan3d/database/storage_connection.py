try:
    import openalea.plantscan3d.py2exe_release

    py2exe_release = True
    print('Py2ExeRelease')
except ImportError:
    py2exe_release = False
    print('StdRelease')

from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *

import os

if not py2exe_release:
    import openalea.plantscan3d.compileUi as cui

    ldir = os.path.dirname(__file__)
    cui.check_ui_generation(os.path.join(ldir, 'connection.ui'))

from . import connection_ui
import ftplib
from .server_manip import server_info

class StorageConnection(QDialog, connection_ui.Ui_Dialog):
    def __init__(self, server_address='', server_port=0, parent=None):
        QDialog.__init__(self, parent)
        connection_ui.Ui_Dialog.__init__(self)
        self.setupUi(self)

        self.server_address = server_address
        self.server_port = server_port

        self.username = 'anonymous'
        self.password = 'anonymous'

        self.usernameLineEdit.textChanged.connect(self.set_username)
        self.passwordLineEdit.textChanged.connect(self.set_password)
        self.buttonBox.accepted.connect(self.test_connection)

        if self.server_address in server_info.register_id:
            self.username, self.password = server_info.register_id[self.server_address]

        self.connected = False

    def exec_(self):
        if not self.try_to_connect():
            return QDialog.exec_(self)
        return True

    def set_username(self, text):
        self.username = str(text)

    def set_password(self, text):
        self.password = str(text)

    def init_with_url(self, url):
        url = str(url).split('/')[0]
        port = 0
        if ':' in url:
            url, port = str(url).split(':')
            port = int(port)
        self.server_address = url
        self.server_port = port

        if self.server_address in server_info.register_id:
            self.username, self.password = server_info.register_id[self.server_address]

    def test_connection(self):
        if self.try_to_connect():
            self.accept()
            self.close()

    def try_to_connect(self):
        if self.checkBox.isChecked() and self.server_address not in server_info.register_id:
            server_info.register_id[self.server_address] = (self.username, self.password)
        return True

    def download(self, server_path, local_path):
        pass

    def upload(self, local_path, server_path):
        pass

    def fileSize(self, server_path):
        pass

    def rename(self, server_path, old_name, new_name):
        pass

    def remove(self, server_path):
        pass

class FTPConnection(StorageConnection):
    def __init__(self, server_address='', server_port=0, parent=None):
        StorageConnection.__init__(self, server_address, server_port, parent)

    def try_to_connect(self):
        try:
            ftp = self.get_instance()
            # QMessageBox.information(self.parent(), 'Connection Success', 'Success to connect to ftp server: ' + self.server_address)
            ftp.quit()
            self.connected = True
            return StorageConnection.try_to_connect(self)
        except ftplib.error_perm:
            QMessageBox.warning(self.parent(), 'Connection Fail', 'Fail to connect to ftp server: ' + self.server_address)
            self.connected = False
            return False

    def download(self, server_path, local_path):
        if not self.connected:
            return

        ftp = self.get_instance()

        try:
            os.makedirs(os.path.split(local_path)[0])
        except:
            pass

        f = open(local_path, 'wb')
        ftp.retrbinary('RETR ' + server_path, f.write)
        f.close()
        ftp.quit()

    def upload(self, server_path, local_path):
        if not self.connected or not os.path.exists(local_path):
            return

        ftp = self.get_instance()

        f = open(local_path, 'rb')
        ftp.storbinary('STOR ' + server_path, f)
        f.close()
        ftp.quit()

    def fileSize(self, server_path):
        if not self.connected:
            return -1

        ftp = self.get_instance()

        size = ftp.size(server_path)
        ftp.quit()
        return size

    def rename(self, server_path, old_name, new_name):
        if not self.connected:
            return

        ftp = self.get_instance()

        ftp.cwd(server_path)
        ftp.rename(old_name, new_name)
        ftp.quit()

    def remove(self, server_path):
        if not self.connected:
            return
        ftp = self.get_instance()

        ftp.delete(server_path)
        ftp.quit()

    def get_instance(self):
        ftp = ftplib.FTP()
        ftp.connect(self.server_address, self.server_port)
        ftp.login(self.username, self.password)
        return ftp
