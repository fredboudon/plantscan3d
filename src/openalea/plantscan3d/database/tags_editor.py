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
    import openalea.plantscan3d.ui_compiler as cui

    ldir = os.path.dirname(__file__)
    cui.check_ui_generation(os.path.join(ldir, 'tags_editor.ui'))

from . import tags_editor_ui
from .server_manip import MongoDBManip


class TagsEditor(QDialog, tags_editor_ui.Ui_Dialog):
    def __init__(self, item_id, parent=None):
        QDialog.__init__(self, parent)
        tags_editor_ui.Ui_Dialog.__init__(self)
        self.setupUi(self)
        self.tags_ref = {}
        self.item_id = item_id

        self.init_view()

        self.treeWidget.itemChanged.connect(self.item_changed)
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.open_menu)

    def item_changed(self, item, column):
        """

        :type item: QTreeWidgetItem
        """

        def update_uncheck(item):
            for i in range(item.childCount()):
                update_uncheck(item.child(i))
            item.setCheckState(0, Qt.Unchecked)

        def update_check(item):
            if item.parent() is not None:
                update_check(item.parent())
            item.setCheckState(0, Qt.Checked)

        if item.checkState(0) == Qt.Unchecked:
            update_uncheck(item)
        elif item.checkState(0) == Qt.Checked:
            update_check(item)

    def open_menu(self, pos):
        clicked_item = self.treeWidget.itemAt(pos)  # type: QTreeWidgetItem

        def on_add():
            tag_name, ok = QInputDialog.getText(self, 'Tag Name', 'Enter the name of the tag to create')
            if ok:
                tag_name = str(tag_name).strip()
                new_tag = ''
                if clicked_item is not None:
                    new_tag = self.get_tag_path(clicked_item) + '/' + tag_name
                else:
                    new_tag = tag_name

                if new_tag in self.tags_ref:
                    QMessageBox.warning(self, 'Tag Name', 'Cannot add a tag if already one exist with the same name')
                    return
                new_item = QTreeWidgetItem()
                new_item.setText(0, tag_name)
                new_item.setCheckState(0, Qt.Unchecked)
                self.tags_ref[str(new_tag)] = new_item
                if clicked_item is None:
                    self.treeWidget.addTopLevelItem(new_item)
                else:
                    clicked_item.addChild(new_item)

        def on_rename():
            tag_name, ok = QInputDialog.getText(self, 'Tag Name', 'Enter the new tag name')
            if ok:
                tag_name = str(tag_name).strip()
                new_tag = ''
                if clicked_item.parent() is not None:
                    new_tag = self.get_tag_path(clicked_item.parent()) + '/' + tag_name
                else:
                    new_tag = tag_name

                if str(new_tag) in self.tags_ref:
                    QMessageBox.warning(self, 'Tag Name', 'Cannot rename a tag if already one exist with the same name')
                    return

                MongoDBManip.rename_tag(self.get_tag_path(clicked_item), new_tag)
                self.tags_ref.pop(str(self.get_tag_path(clicked_item)))
                clicked_item.setText(0, tag_name)
                self.tags_ref[str(new_tag)] = clicked_item

        def on_delete():
            msgBox = QMessageBox()
            msgBox.setText('Are you sure to delete all tags of data ?')
            msgBox.setStandardButtons(QMessageBox.Apply | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Cancel)
            if msgBox.exec_() == QMessageBox.Apply:
                MongoDBManip.remove_tag(self.get_tag_path(clicked_item))
                self.tags_ref.pop(str(self.get_tag_path(clicked_item)))
                if clicked_item.parent() is None:
                    index = self.treeWidget.indexOfTopLevelItem(clicked_item)
                    self.treeWidget.takeTopLevelItem(index)
                else:
                    clicked_item.parent().removeChild(clicked_item)

        action_add = QAction('Add', self)
        action_rename = QAction('Rename', self)
        action_del = QAction('Delete', self)
        action_add.triggered.connect(on_add)
        action_rename.triggered.connect(on_rename)
        action_del.triggered.connect(on_delete)

        menu = QMenu(self)
        menu.addAction(action_add)
        if clicked_item is not None:
            menu.addAction(action_rename)
            menu.addAction(action_del)
        menu.exec_(self.treeWidget.mapToGlobal(pos))

    def init_view(self):
        self.tags_ref = {}
        for tags in MongoDBManip.get_tag_list():
            tags_table = tags.split('/')
            global_tag = tags_table[0]
            children_tags = tags_table[1:]

            if str(global_tag) not in self.tags_ref:
                item = QTreeWidgetItem()
                item.setText(0, global_tag.strip())
                item.setCheckState(0, Qt.Unchecked)
                self.tags_ref[str(global_tag)] = item
                self.treeWidget.addTopLevelItem(item)

            index = 0
            for tag in children_tags:
                if tag.strip() != '':
                    tag_path = global_tag
                    for tp in children_tags[:index]:
                        tag_path += '/' + tp
                    if str(tag_path + '/' + tag) not in self.tags_ref:
                        item = QTreeWidgetItem()
                        item.setText(0, tag.strip())
                        item.setCheckState(0, Qt.Unchecked)
                        self.tags_ref[str(tag_path + '/' + tag)] = item
                        self.tags_ref[str(tag_path)].addChild(item)
                index += 1

        if self.item_id is not None:
            tree = MongoDBManip.get_tags_of_item(self.item_id)
            for tag in tree['tags']:
                tags_table = tag.split('/')
                index = 0
                for tag in tags_table:
                    tag = tag.strip()
                    if tag != '':
                        tag_path = ''
                        for tp in tags_table[:index]:
                            tag_path += tp.strip() + '/'
                        self.tags_ref[str(tag_path + tag)].setCheckState(0, Qt.Checked)
                    index += 1

    def get_tag_path(self, item):
        def get_path(current_item):
            if current_item.parent() is not None:
                return get_path(current_item.parent()) + '/' + current_item.text(0)
            return current_item.text(0)

        tag_path = get_path(item)
        tag_path = tag_path[:len(tag_path)]
        return tag_path

    def get_tags(self):
        def get_path(parent_tag, item):
            isend = True
            tag = ''
            current_tag = parent_tag + str(item.text(0))
            for i in range(item.childCount()):
                if item.child(i).checkState(0) == Qt.Checked:
                    isend = False
                    tag += get_path(current_tag + '/', item.child(i))
            if isend:
                tag += current_tag + ';'
            return tag

        tags = []
        for i in range(self.treeWidget.topLevelItemCount()):
            if self.treeWidget.topLevelItem(i).checkState(0) == Qt.Checked:
                for t in get_path('', self.treeWidget.topLevelItem(i)).split(';'):
                    if t != '':
                        tags.append(t)
        return tags
