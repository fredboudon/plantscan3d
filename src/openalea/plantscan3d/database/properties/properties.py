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
    cui.check_ui_generation(os.path.join(ldir, 'create_property.ui'))
    cui.check_ui_generation(os.path.join(ldir, 'textprop.ui'))
    cui.check_ui_generation(os.path.join(ldir, 'dateprop.ui'))
    cui.check_ui_generation(os.path.join(ldir, 'floatvalueprop.ui'))

import create_property_ui
import textprop_ui
import dateprop_ui
import floatvalueprop_ui


class Property(QWidget):
    delete = pyqtSignal(str)

    def __init__(self, property_name, parent=None):
        QWidget.__init__(self, parent)
        self.property_name = property_name

        self.value = None

    def delete_property(self):
        self.delete.emit(self.property_name)

    def setValue(self, value):
        pass

    def getValue(self):
        pass


class TextProperty(Property, textprop_ui.Ui_Form):
    def __init__(self, property_name, parent=None):
        Property.__init__(self, property_name, parent)
        textprop_ui.Ui_Form.__init__(self)
        self.setupUi(self)

        QObject.connect(self.deleteButton, SIGNAL('clicked()'), self.delete_property)
        QObject.connect(self.propValue, SIGNAL('textChanged()'), self.valueChange)
        self.propNameLabel.setText(property_name)

    def setValue(self, value):
        self.propValue.setText(value)

    def valueChange(self):
        self.value = self.propValue.toPlainText()

    def getValue(self):
        return self.value


class DateProperty(Property, dateprop_ui.Ui_Form):
    def __init__(self, property_name, parent=None):
        Property.__init__(self, property_name, parent)
        dateprop_ui.Ui_Form.__init__(self)
        self.setupUi(self)

        QObject.connect(self.deleteButton, SIGNAL('clicked()'), self.delete_property)
        QObject.connect(self.propValue, SIGNAL('dateChanged(QDate)'), self.valueChange)
        self.propNameLabel.setText(property_name)

    def setValue(self, value):
        import datetime

        date = QDate()
        if isinstance(value, datetime.datetime):
            date = QDate(value.year, value.month, value.day)
        elif isinstance(value, QDate):
            date = value
        self.propValue.setDate(date)

    def valueChange(self, value):
        self.value = value

    def getValue(self):
        import datetime

        return datetime.datetime(self.value.year(), self.value.month(), self.value.day())


class FloatValueProperty(Property, floatvalueprop_ui.Ui_Form):
    def __init__(self, property_name, parent=None):
        Property.__init__(self, property_name, parent)
        floatvalueprop_ui.Ui_Form.__init__(self)
        self.setupUi(self)

        QObject.connect(self.deleteButton, SIGNAL('clicked()'), self.delete_property)
        QObject.connect(self.propValue, SIGNAL('valueChanged(double)'), self.valueChange)
        self.propNameLabel.setText(property_name)

    def setValue(self, value):
        self.propValue.setValue(value)

    def valueChange(self, value):
        self.value = value


class CreateProperty(QDialog, create_property_ui.Ui_Dialog):
    prop = None  # type: Property

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        create_property_ui.Ui_Dialog.__init__(self)
        self.setupUi(self)

        self.prop = None

        QObject.connect(self.buttonBox, SIGNAL('accepted()'), self.valid)

    def valid(self):
        if len(self.nameLineEdit.text()) == 0:
            return

        propname = str(self.nameLineEdit.text())

        if self.typeComboBox.currentText() == 'Date':
            self.prop = DateProperty(propname)
        elif self.typeComboBox.currentText() == 'Value':
            self.prop = FloatValueProperty(propname)
        elif self.typeComboBox.currentText() == 'Text':
            self.prop = TextProperty(propname)

        self.accept()
