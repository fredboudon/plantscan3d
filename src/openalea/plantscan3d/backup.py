from copy import deepcopy

class BackupObject:
    def __init__(self, name, object, getmethod=getattr, setmethod=setattr, copymethod=deepcopy):
        self.name = name
        self.object = object
        self.setmethod = setmethod
        self.getmethod = getmethod
        self.copymethod = copymethod

    def copy(self):
        return self.copymethod(getattr(self.object, self.name))

    def getattribute(self):
        return self.getmethod(self.object, self.name)

    def setattribute(self, newobject):
        return self.setmethod(self.object, self.name, newobject)

class Backup:
    def __init__(self, maxbackup=4):
        self.backupdata = []
        self.redodata = []
        self.backupmetainfos = {}
        self.maxbackup = maxbackup
        pass

    def declare_backup(self, name, attributesnamelist, updatemethod=None):
        self.backupmetainfos[name] = {'backupobjects': attributesnamelist,
                                      'updatemethod': updatemethod}

    def copy_data(self, backupname):
        data = {}
        for backupobject in self.backupmetainfos[backupname]['backupobjects']:
            data[backupobject.name] = backupobject.copy()
        return data

    def get_data(self, backupname):
        data = {}
        for backupobject in self.backupmetainfos[backupname]['backupobjects']:
            data[backupobject.name] = backupobject.getattribute()
        return data

    def set_data(self, backupname, data):
        for backupobject in self.backupmetainfos[backupname]['backupobjects']:
            backupobject.setattribute(data[backupobject.name])

    def make_backup(self, name):
        self.backupdata.append({'type': name, 'data': self.copy_data(name)})
        self.redodata = []

    def restore_backup(self):
        if len(self.backupdata) > 0:
            print "ok1"
            data = self.backupdata.pop()
            print "ok2"
            self.redodata.append({'type': data['type'], 'data': self.get_data(data['type'])})
            print "ok3"
            self.set_data(data['type'], data['data'])
            print "ok4"
            if self.backupmetainfos[data['type']]['updatemethod'] is not None:
                self.backupmetainfos[data['type']]['updatemethod']()
            print "Undo " + data['type'] + " at " + str(id(data))
            return True
        return False

    def restore_redo(self):
        if len(self.redodata) > 0:
            print "ok1"
            data = self.redodata.pop()
            print "ok2"
            self.backupdata.append({'type': data['type'], 'data': self.get_data(data['type'])})
            print "ok3"
            self.set_data(data['type'], data['data'])
            print "ok4"
            if self.backupmetainfos[data['type']]['updatemethod'] is not None:
                self.backupmetainfos[data['type']]['updatemethod']()
            print "Redo " + data['type'] + " at " + str(id(data))
            return True
        return False
