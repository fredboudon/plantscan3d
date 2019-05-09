from PyQt5.QtCore import QSettings

class PSSettings(QSettings):
    def __init__(self):
        QSettings.__init__(self,QSettings.IniFormat,QSettings.UserScope,"OpenAlea","PlantScan3D")