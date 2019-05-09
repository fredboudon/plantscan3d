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

import pymongo as pm
import ftplib
from bson.objectid import *
from bson import Binary


class ServerInformation:
    def __init__(self):
        self.mongodb_uri = None
        self.mongodb_database = 'PlantScan3D'
        self.mongodb_collection = 'AppleTrees'

        self.register_id = {}
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, "OpenAlea", "PlantScan3D")

        self.settings.beginGroup('FileTransferIds')
        if self.settings.contains('Ids'):
            ids = self.settings.value('Ids')

            for id in str(ids).split(';'):
                address, username, password = id.split(':')
                self.register_id[address] = (username, password)
        self.settings.endGroup()

    def save_register_ids(self):
        self.settings.beginGroup('FileTransferIds')
        ids = ''
        index = 0
        for rid in self.register_id.items():
            address, id = rid
            username, password = id
            ids += address + ':' + username + ':' + password
            index += 1
            if index < len(self.register_id):
                ids += ';'
        self.settings.setValue('Ids', ids)
        self.settings.endGroup()

    def get_mongodb_instance(self):
        client = pm.MongoClient(self.mongodb_uri)
        db = client[self.mongodb_database]
        return client, db, db[self.mongodb_collection]


server_info = ServerInformation()
Already_used_key_db = ['name', '_id', 'date', 'nbpoint', 'filesize', 'fileURL', 'tags', 'parent', 'thumbnail']
Based_filter = {key: 1 for key in Already_used_key_db}
NonBased_filter = {key: 0 for key in Already_used_key_db}


class MongoDBManip:
    @staticmethod
    def find(filter=None, projection=None, sort=None):
        client, db, collection = server_info.get_mongodb_instance()

        res = collection.find(filter=filter, projection=projection, sort=sort)
        client.close()
        return res

    @staticmethod
    def count_documents(query):
        client, db, collection = server_info.get_mongodb_instance()

        res = collection.count_documents(query)
        client.close()
        return res

    @staticmethod
    def find_one(filter=None, projection=None, sort=None):
        client, db, collection = server_info.get_mongodb_instance()

        res = collection.find_one(filter=filter, projection=projection, sort=sort)
        client.close()
        return res

    @staticmethod
    def find_one_and_update(filter, update, projection=None):
        client, db, collection = server_info.get_mongodb_instance()

        res = collection.find_one_and_update(filter=filter, update=update, projection=projection)
        client.close()
        return res

    @staticmethod
    def find_one_and_delete(filter):
        client, db, collection = server_info.get_mongodb_instance()

        res = collection.find_one_and_delete(filter=filter)
        client.close()
        return res

    @staticmethod
    def insert_one(document):
        client, db, collection = server_info.get_mongodb_instance()

        res = collection.insert_one(document=document)
        client.close()
        return res

    @staticmethod
    def get_tag_list():
        trees = MongoDBManip.find({}, {'tags': 1, '_id': 0})
        tags_list = []
        for tree in trees:
            tags = tree['tags']
            if type(tags) == str or type(tags) == str:
                if str(tags).strip() != '':
                    separator = ' ; '
                    for t in str(tags).split(separator):
                        t = t.strip()
                        if t != '' and t not in tags_list:
                            tags_list.append(t)
            elif type(tags) == list:
                for t in tags:
                    t = t.strip()
                    if t != '' and t not in tags_list:
                        tags_list.append(t)
        return tags_list

    @staticmethod
    def get_tags_of_item(id, projection=None):
        if projection is None:
            projection = {}
        projection['tags'] = 1

        tree = MongoDBManip.find_one({'_id': id}, projection=projection)

        tags_list = []
        tags = tree['tags']
        if type(tags) == str or type(tags) == str:
            if str(tags).strip() != '':
                separator = ' ; '
                for t in str(tags).split(separator):
                    t = t.strip()
                    if t != '' and t not in tags_list:
                        tags_list.append(t)
        elif type(tags) == list:
            for t in tags:
                t = t.strip()
                if t != '' and t not in tags_list:
                    tags_list.append(t)

        tree['tags'] = tags_list
        return tree

    @staticmethod
    def remove_tag(tag):
        trees = MongoDBManip.find({}, {'tags': 1})
        for tree in trees:
            tags = tree['tags']
            if type(tags) == str or type(tags) == str:
                separator = ' ; '
                new_tag = ''
                tags_list = str(tags).split(separator)
                for t in tags_list:
                    t = t.strip()
                    if not t.startswith(tag):
                        new_tag += t + separator
                new_tag = new_tag[:new_tag.rfind(separator)]
                MongoDBManip.find_one_and_update({'_id': tree['_id']}, {'$set': {'tags': new_tag}})
            elif type(tags) == list:
                MongoDBManip.find_one_and_update({'_id': tree['_id']}, {
                    '$pull': {
                        'tags': {
                            '$regex': tag + '.*'
                        }
                    }
                })

    @staticmethod
    def rename_tag(tag_name, new_tag_name):
        trees = MongoDBManip.find({}, {'tags': 1})
        for tree in trees:
            tags = tree['tags']
            if type(tags) == str or type(tags) == str:
                separator = ' ; '
                new_tag = ''
                tags_list = str(tags).split(separator)
                for t in tags_list:
                    t = t.strip()
                    if tag_name in t:
                        t = t.replace(tag_name, new_tag_name)
                    new_tag += t + separator
                new_tag = new_tag[:new_tag.rfind(separator)]
                MongoDBManip.find_one_and_update({'_id': tree['_id']}, {'$set': {'tags': new_tag}})
            elif type(tags) == list:
                new_tag = []
                for t in tags:
                    if tag_name in t:
                        t = t.replace(tag_name, new_tag_name)
                    new_tag.append(t)
                MongoDBManip.find_one_and_update({'_id': tree['_id']}, {'$set': {'tags': new_tag}})

    @staticmethod
    def delete_db_item(id):
        data = MongoDBManip.find_one_and_delete({'_id': id})
        children = MongoDBManip.find({'parent': id}, {'_id': 1, 'tags': 1})
        separator = ' ; '

        for c in children:
            new_tags = None
            if c['tags'] is not None:
                if type(c['tags']) == list:
                    new_tags = c['tags']
                    if type(data['tags']) == list:
                        new_tags += data['tags']
                    elif type(data['tags']) == str or type(data['tags']) == str:
                        for t in str(data['tags']).split(';'):
                            if t.strip() != '':
                                new_tags.append(t)
                elif type(c['tags']) == str or type(c['tags']) == str:
                    new_tags = str(c['tags'])
                    if type(data['tags']) == list:
                        for t in data['tags']:
                            new_tags += str(t) + separator
                        new_tags = new_tags[:new_tags.rfind(separator)]
                    elif type(data['tags']) == str or type(data['tags']) == str:
                        if len(new_tags) > 0:
                            new_tags += separator + data['tags']
                        else:
                            new_tags = data['tags']
            else:
                new_tags = data['tags']

            MongoDBManip.find_one_and_update({'_id': c['_id']}, {
                '$set': {
                    'parent': data['parent'],
                    'tags': new_tags
                }
            })

class WorkerTestConnection(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(bool)

    def __init__(self):
        QObject.__init__(self)

    def run(self):
        try:
            client = pm.MongoClient(server_info.mongodb_uri)
            # The ismaster command is cheap and does not require auth.
            client.admin.command('ismaster')
            print("Database connection to " + server_info.mongodb_uri + " successful")
            self.result.emit(True)
        except pm.errors.ConnectionFailure:
            print("Database connection to " + server_info.mongodb_uri + " failed")
            self.result.emit(False)
        self.finished.emit()
