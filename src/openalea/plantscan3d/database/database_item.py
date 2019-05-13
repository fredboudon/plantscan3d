try:
    import openalea.plantscan3d.py2exe_release

    py2exe_release = True
    print('Py2ExeRelease')
except ImportError:
    py2exe_release = False
    print('StdRelease')

if not py2exe_release:
    import openalea.plantgl.gui.qt
    from openalea.plantgl.gui.qt.QtCore import *
    from openalea.plantgl.gui.qt.QtGui import *

else:
    import sip

    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)

    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

import os

if not py2exe_release:
    import openalea.plantscan3d.compileUi as cui

    ldir = os.path.dirname(__file__)
    cui.check_ui_generation(os.path.join(ldir, 'database_item.ui'))

from . import database_item_ui
import datetime
from .properties.properties import *
from .server_manip import MongoDBManip, Binary, ObjectId, Already_used_key_db
from .tags_editor import TagsEditor

class Database_Item(QDialog, database_item_ui.Ui_Dialog):
    otherProperties = None  # type: dict[str, Property]
    MODIFY, INSERT, INSERT_CHILD = 1, 2, 4

    inserted = pyqtSignal(dict)
    modified = pyqtSignal(ObjectId, dict)

    def __init__(self, baseData=None, nonebaseData=None, version=None, thumbnail=None, nbpoint=0, parent=None):
        """

        :type baseData: dict[str, any]
        :type nonebaseData: dict[str, any]
        :type version: int
        :type thumbnail: QImage
        :type parent: QObject
        """
        QDialog.__init__(self, parent)
        database_item_ui.Ui_Dialog.__init__(self)
        self.setupUi(self)
        self.thumbnail = thumbnail
        self.nbpoint = nbpoint
        self.tags = []
        self.current_id = None

        self.thumbnailLabel.setBackgroundRole(QPalette.Base)
        if self.thumbnail is not None:
            pixmap = QPixmap()
            pixmap = pixmap.fromImage(self.thumbnail)
            self.thumbnailLabel.setPixmap(pixmap)

        self.dateTimeEdit.setDateTime(QDateTime.currentDateTime())
        self.pointNumberSpinBox.setValue(nbpoint)
        if baseData is not None:
            if version is not None:
                self.mode = self.INSERT_CHILD
            else:
                self.mode = self.MODIFY
                self.defaultName = baseData['name']

            self.current_id = baseData['_id']
            name_add_str = '-v' + str(version) if version is not None else ''
            self.nameEdit.setText(baseData['name'] + name_add_str)
            if self.mode == self.MODIFY:
                self.dateTimeEdit.setDateTime(QDateTime.fromString(baseData['date'].ctime()))
            protocol, url = str(baseData['fileURL']).split('://')
            server_address = str(url).split('/')[0]
            server_address_index = self.storageComboBox.findText(server_address)
            protocol_index = self.protocolComboBox.findText(protocol)

            self.protocolComboBox.setCurrentIndex(protocol_index)
            if server_address_index > -1:
                self.storageComboBox.setCurrentIndex(server_address_index)
            else:
                self.storageComboBox.setCurrentIndex(-1)
                self.storageComboBox.lineEdit().setText(server_address)

            if self.mode == self.MODIFY:
                self.storageComboBox.readonly = True
                self.protocolComboBox.readonly = True
                self.pointNumberSpinBox.setValue(baseData['nbpoint'])
                self.tags = MongoDBManip.get_tags_of_item(baseData['_id'])['tags']
                self.tag_editor = TagsEditor(self.current_id, parent=self)
            else:
                self.tag_editor = TagsEditor(None, parent=self)
        else:
            self.pointNumberSpinBox.setValue(nbpoint)
            self.mode = self.INSERT
            self.current_id = None
            self.tag_editor = TagsEditor(None, parent=self)

        self.otherProperties = {}
        self.usedname = list(Already_used_key_db)
        self.addedProperties = []
        self.deletedProperies = []

        if nonebaseData is not None:
            for data in nonebaseData.items():
                key, value = data
                prop = None  # type: Property
                if type(value) == datetime.datetime:
                    prop = DateProperty(key)
                elif type(value) == int or type(value) == float:
                    prop = FloatValueProperty(key)
                elif type(value) == str or type(value) == str:
                    prop = TextProperty(key)

                self.propertiesVLayout.addWidget(prop)
                self.usedname.append(key)
                self.otherProperties[key] = prop
                prop.delete.connect(self.deleteProperty)
                prop.setValue(value)
                prop.deleteButton.setIcon(QIcon(':/images/icons/delete.png'))

        self.buttonBox.accepted.connect(self.valid)
        self.addPropertiesButton.clicked.connect(self.addPropertiy)
        self.editTagsButton.clicked.connect(self.openTagsEditor)

    def openTagsEditor(self):
        if self.tag_editor.exec_():
            self.tags = self.tag_editor.get_tags()

    def addPropertiy(self):
        select_prop = CreateProperty(parent=self)

        while True:
            if select_prop.exec_():
                propname = select_prop.prop.property_name
                if propname in self.usedname:
                    QMessageBox.warning(self, 'Invalid key name', 'Cannot add property with the same name')
                    continue

                self.propertiesVLayout.addWidget(select_prop.prop)
                select_prop.prop.deleteButton.setIcon(QIcon(':/images/icons/delete.png'))

                self.usedname.append(propname)
                self.otherProperties[propname] = select_prop.prop

                select_prop.prop.delete.connect(self.deleteProperty)
                self.addedProperties.append(propname)
            break

    def deleteProperty(self, name):
        import sip
        self.usedname.remove(name)
        prop = self.otherProperties.pop(name)
        self.propertiesVLayout.removeWidget(prop)
        sip.delete(prop)
        prop = None

        if name in self.addedProperties:
            self.addedProperties.remove(name)
        else:
            self.deletedProperies.append(name)

    def valid(self):
        if self.nameEdit.text() == '':
            QMessageBox.warning(self, 'Invalid name', 'You have to set a name to the data')
            return
        if self.mode == self.MODIFY:
            if self.defaultName != self.nameEdit.text() and MongoDBManip.count_documents({'name': self.nameEdit.text()}) != 0:
                QMessageBox.warning(self, 'Invalid name', 'Connot have data with the same name')
                return

            from bson.binary import Binary

            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QIODevice.WriteOnly)
            self.thumbnail.save(buffer, 'PNG')

            thumbnail = Binary(ba.data())

            data = {
                '$set': {
                    'name': self.nameEdit.text(),
                    'tags': self.tags,
                    'fileURL': self.protocolComboBox.currentText() + '://' + self.storageComboBox.currentText() + '/' + self.nameEdit.text() + '.zip',
                    'date': datetime.datetime.now(),
                    'thumbnail': thumbnail
                }
            }
            for item in self.otherProperties.items():
                key, prop = item
                data['$set'][key] = prop.getValue()

            for deleted in self.deletedProperies:
                data['$unset'][deleted] = ''

            self.modified.emit(self.current_id, data)
        else:
            from bson.binary import Binary

            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QIODevice.WriteOnly)
            self.thumbnail.save(buffer, 'PNG')

            thumbnail = Binary(ba.data())

            if MongoDBManip.count_documents({'name': self.nameEdit.text()}) != 0:
                QMessageBox.warning(self, 'Invalid name', 'Connot have data with the same name')
                return
            data = {
                'name': self.nameEdit.text(),
                'parent': self.current_id if self.mode == self.INSERT_CHILD else None,
                'filesize': None,
                'fileURL': self.protocolComboBox.currentText() + '://' + self.storageComboBox.currentText() + '/' + self.nameEdit.text() + '.zip',
                'nbpoint': self.nbpoint,
                'thumbnail': thumbnail,
                'tags': self.tags,
                'date': datetime.datetime.now()
            }
            for item in self.otherProperties.items():
                key, prop = item
                data[key] = prop.getValue()

            self.inserted.emit(data)
        self.accept()
        self.close()
