try:
    import openalea.plantscan3d.py2exe_release

    py2exe_release = True
    print('Py2ExeRelease')
except ImportError:
    py2exe_release = False
    print('StdRelease')

if not py2exe_release:
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
    cui.check_ui_generation(os.path.join(ldir, 'database.ui'))
    cui.check_rc_generation(os.path.join(ldir, 'database.qrc'))

from . import database_ui
from . import database_item
from .server_manip import MongoDBManip, Based_filter, NonBased_filter
from .storage_connection import *


class DatabaseEditor(QDialog, database_ui.Ui_Dialog):
    openObjectRequested = pyqtSignal(str, str)
    saveObjectRequested = pyqtSignal(str)
    setCurrentObjectRequested = pyqtSignal(str)
    objectDeleted = pyqtSignal(str)

    def __init__(self, size_callback=None, make_thumbnail=None, parent=None):
        QDialog.__init__(self, parent)
        database_ui.Ui_Dialog.__init__(self)
        self.setupUi(self)
        self.size_callback = size_callback
        self.make_thumbnail = make_thumbnail

        self.trees_id = []
        self.current_opened_item = None
        self.register_id = {}
        self.current_thumbnail = None

        self.treeWidget.itemDoubleClicked.connect(self.item_double_clicked)
        self.treeWidget.currentItemChanged.connect(self.item_changed)

        self.thumbnailLabel.setBackgroundRole(QPalette.Base)
        self.thumbnailLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem('Key'))
        self.tableWidget.setHorizontalHeaderItem(1, QTableWidgetItem('Value'))

        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.openMenu)

    def openMenu(self, pos):
        item = self.treeWidget.itemAt(pos)
        if not hasattr(item, 'object_id'):
            return

        def on_delete():
            cb = QCheckBox('Do you want to delete the associated file ?')
            cb.setChecked(True)

            msgBox = QMessageBox()
            msgBox.setText('Are you sure to delete this data ? This action is not reversible.')
            msgBox.setStandardButtons(QMessageBox.Apply | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Cancel)
            msgBox.layout().addWidget(cb, 2, 1)

            if msgBox.exec_() == QMessageBox.Apply:
                self.delete_db(item.object_id, cb.isChecked())

        def on_modify():
            if QMessageBox.question(self, 'Update not recommended', 'Update an item is not recommended, you will erase the previous information. Are you sure to do that ?') != QMessageBox.Ok:
                return

            basedata = MongoDBManip.find_one({'_id': item.object_id}, Based_filter)
            nonebasedata = MongoDBManip.find_one({'_id': item.object_id}, NonBased_filter)
            thumbnail = QImage.fromData(basedata['thumbnail'])
            dbitemEditor = database_item.Database_Item(basedata, nonebasedata, thumbnail=thumbnail, parent=self)

            dbitemEditor.modified.connect(self.modify_db)
            dbitemEditor.exec_()

        delaction = QAction('Delete', self)
        modifaction = QAction('Modify', self)

        delaction.triggered.connect(on_delete)
        modifaction.triggered.connect(on_modify)

        menu = QMenu(self)
        menu.addAction(modifaction)
        menu.addAction(delaction)
        menu.exec_(self.treeWidget.mapToGlobal(pos))

    def resizeEvent(self, event):
        """

        :type event: QResizeEvent
        """
        if self.current_thumbnail is not None:
            w = self.thumbnailLabel.width()
            h = self.thumbnailLabel.height()
            self.thumbnailLabel.setPixmap(self.current_thumbnail.scaled(w, h, Qt.KeepAspectRatio))

    def file_manipulation(self, url, callback):
        protocol, url = str(url).split('://')
        connection = None  # type: StorageConnection
        if protocol == 'ftp':
            connection = FTPConnection(parent=self)

        connection.init_with_url(url)
        if connection.exec_():
            callback(connection)

    def modify_db(self, id, data):
        base_data = MongoDBManip.find_one({'_id': id}, {'name': 1, 'fileURL': 1})

        def callback(connection):
            connection.rename('', base_data['name'] + '.zip', data['$set']['name'] + '.zip')
            MongoDBManip.find_one_and_update({'_id': id}, data)
            self.get_trees()

        self.file_manipulation(str(base_data['fileURL']), callback)

    def insert_db(self, data):
        filename = data['name'] + '.zip'
        fname = str('/tmp/' + str(os.getpid()) + '/' + filename)
        self.saveObjectRequested.emit(fname)
        data['nbpoint'] = self.size_callback() if self.size_callback is not None else 0

        def callback(connection):
            connection.upload(filename, fname)
            data['filesize'] = connection.fileSize(filename)
            result = MongoDBManip.insert_one(data)
            self.current_opened_item = result.inserted_id
            self.setCurrentObjectRequested.emit(result.inserted_id.binary)
            self.get_trees()

        self.file_manipulation(str(data['fileURL']), callback)

    def delete_db(self, id, delete_file):
        data = MongoDBManip.find_one({'_id': id}, {'name': 1, 'fileURL': 1})

        def delete_in_bdd():
            MongoDBManip.delete_db_item(id)

            self.show()
            if self.current_opened_item == id:
                self.current_opened_item = None
                self.objectDeleted.emit(id)

        if delete_file:
            def callback(connection):
                connection.remove(data['name'] + '.zip')
                delete_in_bdd()
            self.file_manipulation(str(data['fileURL']), callback)
        else:
            delete_in_bdd()

    def get_trees(self):
        self.treeWidget.clear()
        self.trees_id = []

        parent_ref = {}  # type: dict[ObjectId, QTreeWidgetItem]
        tags_ref = {}  # type: dict[str, QTreeWidgetItem]

        for tags in MongoDBManip.get_tag_list():
            tags_table = tags.split('/')
            global_tag = tags_table[0]
            children_tags = tags_table[1:]

            if global_tag not in tags_ref:
                item = QTreeWidgetItem()
                item.setText(0, global_tag.strip())
                item.setIcon(0, QIcon(':/images/icons/folder.png'))
                tags_ref[global_tag] = item
                self.treeWidget.addTopLevelItem(item)

            index = 0
            for tag in children_tags:
                if tag.strip() != '':
                    tag_path = global_tag
                    for tp in children_tags[:index]:
                        tag_path += '/' + tp
                    if tag_path + '/' + tag not in tags_ref:
                        parent = tags_ref[tag_path]
                        item = QTreeWidgetItem()
                        item.setText(0, tag.strip())
                        item.setIcon(0, QIcon(':/images/icons/folder.png'))
                        tags_ref[tag_path + '/' + tag] = item
                        parent.addChild(item)
                index += 1

        allchecked = False
        while not allchecked:
            allchecked = True
            for tree in MongoDBManip.find({}, Based_filter):
                if tree['_id'] in parent_ref:
                    continue

                if tree['parent'] is None:
                    item = QTreeWidgetItem()
                    item.object_id = tree['_id']
                    item.setText(0, tree['name'])
                    item.setIcon(0, QIcon(':/images/icons/database.png'))
                    item.setText(1, tree['fileURL'])
                    item.setText(2, tree['date'].strftime('%Y/%m/%d %H:%M:%S'))
                    parent_ref[tree['_id']] = item
                else:
                    if tree['parent'] not in parent_ref:
                        allchecked = False
                        continue
                    parent = parent_ref[tree['parent']]
                    item = QTreeWidgetItem(parent)
                    item.object_id = tree['_id']
                    item.setText(0, tree['name'])
                    item.setIcon(0, QIcon(':/images/icons/database.png'))
                    item.setText(1, tree['fileURL'])
                    item.setText(2, tree['date'].strftime('%Y/%m/%d %H:%M:%S'))
                    parent.addChild(item)
                    parent_ref[tree['_id']] = item

        def clone_item(item):
            new_item = item.clone()
            children = []
            for i in range(item.childCount()):
                children.append(clone_item(item.child(i)))
            new_item.takeChildren()
            new_item.addChildren(children)
            new_item.object_id = item.object_id
            return new_item

        for tree in MongoDBManip.find({}, {'_id': 1}):
            info = MongoDBManip.get_tags_of_item(tree['_id'], {'parent': 1})

            added = False
            for t in info['tags']:
                tags_ref[t].addChild(clone_item(parent_ref[info['_id']]))
                added = True
            if not added and info['parent'] is None:
                self.treeWidget.addTopLevelItem(clone_item(parent_ref[info['_id']]))

    def show(self):
        self.get_trees()
        self.nameLabel.setText('')
        self.dateLabel.setText('')
        self.sizeLabel.setText('')
        self.thumbnailLabel.setText('')
        self.thumbnailLabel.setPixmap(QPixmap())
        self.current_thumbnail = None
        self.tableWidget.setRowCount(0)
        QDialog.show(self)

    def item_changed(self, item, column):
        """

        :type column: int
        :type item: QTreeWidgetItem
        """
        if not hasattr(item, 'object_id'):
            self.nameLabel.setText('')
            self.dateLabel.setText('')
            self.sizeLabel.setText('')
            self.thumbnailLabel.setText('')
            self.thumbnailLabel.setPixmap(QPixmap())
            self.current_thumbnail = None
            self.tableWidget.setRowCount(0)
            return

        data = MongoDBManip.find_one({'_id': item.object_id}, Based_filter)
        size_helper = ['o', 'Ko', 'Mo', 'Go', 'To']

        self.nameLabel.setText(data['name'])
        current_size = float(data['filesize'])
        size_helper_index = 0
        while current_size >= 1024:
            current_size /= 1024
            size_helper_index += 1
        self.sizeLabel.setText('%.1f' % (current_size) + ' ' + size_helper[size_helper_index])
        self.dateLabel.setText(data['date'].strftime('%c'))

        picture = QPixmap()
        picture.loadFromData(data['thumbnail'])
        w = self.thumbnailLabel.width()
        h = self.thumbnailLabel.height()
        self.current_thumbnail = picture
        self.thumbnailLabel.setPixmap(picture.scaled(w, h, Qt.KeepAspectRatio))

        data = MongoDBManip.find_one({'_id': item.object_id}, NonBased_filter)

        self.tableWidget.setRowCount(len(data))
        index = 0
        for d in data.items():
            key, value = d
            self.tableWidget.setItem(index, 0, QTableWidgetItem(str(key)))
            self.tableWidget.setItem(index, 1, QTableWidgetItem(str(value)))
            index += 1

    def item_double_clicked(self, item, column):
        """

        :type index: QModelIndex
        """
        if not hasattr(item, 'object_id'):
            return

        data = MongoDBManip.find_one({'_id': item.object_id}, {'name': 1, 'fileURL': 1})
        fname = str('/tmp/' + str(os.getpid()) + '/' + data['name'] + '.zip')

        def callback(connection):
            self.close()
            connection.download(data['name'] + '.zip', fname)
            self.openObjectRequested.emit(item.object_id.binary, fname)

        self.file_manipulation(str(data['fileURL']), callback)
        self.current_opened_item = item.object_id

    def insert_item(self):
        dbitemEditor = None  # type: database_item.Database_Item

        thumbnail = self.make_thumbnail() if self.make_thumbnail is not None else None

        if self.current_opened_item is not None:
            basedata = MongoDBManip.find_one({'_id': self.current_opened_item}, Based_filter)
            nonebasedata = MongoDBManip.find_one({'_id': self.current_opened_item}, NonBased_filter)
            version = MongoDBManip.count_documents({'parent': basedata['_id']}) + 1
            dbitemEditor = database_item.Database_Item(basedata, nonebasedata, version, thumbnail, self.size_callback(), self)
        else:
            dbitemEditor = database_item.Database_Item(thumbnail=thumbnail, nbpoint=self.size_callback(), parent=self)
        dbitemEditor.inserted.connect(self.insert_db)
        dbitemEditor.exec_()

    def update_current_item(self):
        if self.current_opened_item is None:
            return

        if QMessageBox.question(self, 'Update not recommended', 'Update an item is not recommended, you will erase the previous information. Are you sure to do that ?') != QMessageBox.Ok:
            return

        basedata = MongoDBManip.find_one({'_id': self.current_opened_item}, Based_filter)
        nonebasedata = MongoDBManip.find_one({'_id': self.current_opened_item}, NonBased_filter)
        thumbnail = QImage.fromData(basedata['thumbnail'])
        dbitemEditor = database_item.Database_Item(basedata, nonebasedata, thumbnail=thumbnail, parent=self)

        dbitemEditor.modified.connect(self.modify_db)
        dbitemEditor.exec_()
