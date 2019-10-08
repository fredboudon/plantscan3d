from openalea.plantgl.gui.qt.QtCore import QSettings

class Settings(QSettings):

    def __init__(self):
        QSettings.__init__(self, QSettings.IniFormat, QSettings.UserScope, "OpenAlea", "PlantScan3D")
