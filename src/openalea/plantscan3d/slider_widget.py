try:
    import openalea.plantscan3d.py2exe_release
    py2exe_release = True
    print('Py2ExeRelease')
except ImportError:
    py2exe_release = False
    print('StdRelease')

from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *

if not py2exe_release:
    # Qt UI Build
    from . import ui_compiler as cui
    ldir = os.path.dirname(__file__)
    cui.check_ui_generation(os.path.join(ldir, 'slider_widget.ui'))

from . import slider_widget_ui
import re

class SliderWidget(QWidget, slider_widget_ui.Ui_Slider):

    # Qt Signals
    valueChanged = pyqtSignal(int)
    valueFloatChanged = pyqtSignal(float)

    def __init__(self, parent=None):
        """
        :param parent: Parent window.
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)

        self.title = 'Value'
        self.value = 0
        self.floatValue = 0
        self.min = 0
        self.max = 100
        self.floats = False
        self.mousePressed = False
        self.enableSignal = True
        self.maxDecimals = 2

        # Handle
        self.handleImage.setPixmap(QPixmap("src/openalea/plantscan3d/images/slider.png"))

        # Events
        self.valueLineEdit.textEdited.connect(self.__onValueChanged)
        self.valueLineEdit.editingFinished.connect(self.__onValueEditFinished)

    def setup(self, title, minimum, maximum, value, maxDecimals=0):
        """
        Setup the differents parameters of the slider at once.
        :param title: The title.
        :param minimum: The minimum value.
        :param maximum: The maximum value.
        :param value: The current value.
        :param maxDecimals: Maximum number of decimals. 0 to use integers.
        :return: None
        """
        self.enableSignal = False
        try:
            if maxDecimals > 0:
                # Use floats
                self.setDecimals(maxDecimals)
                self.useFloats(True)

            self.setTitle(title)
            self.setBounds(minimum, maximum)
            self.setValue(value)
        finally:
            self.enableSignal = True

    def setValue(self, value):
        """
        Set the value of the slider.
        :param value: The new value.
        :return: None
        """
        value = float(value)

        if value > self.max:
            value = self.max
        elif value < self.min:
            value = self.min
        else:
            value = value

        self.floatValue = value
        self.value = self.__getValue(value)

        self.valueLineEdit.setText(self.__getTextValue())
        self.__computeHandlePosition()

        if self.enableSignal:
            # Emit Qt signals, if enabled
            self.valueChanged.emit(self.value)
            self.valueFloatChanged.emit(self.value)

    def getValue(self):
        """
        Get the value of the slider.
        :return: int|float
        """
        return self.value

    def setMaximum(self, maximum):
        """
        Set the maximum value of the slider.
        :param maximum: The new maximum value.
        :return: None
        """
        self.max = self.__getValue(maximum)

        if self.min > self.max:
            self.min = self.max

        self.setValue(self.value)

    def setMinimum(self, minimum):
        """
        Set the minimum value of the slider.
        :param minimum: The new minimum value.
        :return: None
        """
        self.min = self.__getValue(minimum)

        if self.max < self.min:
            self.max = self.min

        self.setValue(self.value)

    def maximum(self):
        """
        Get the maximum value of the slider.
        :return: int|float
        """
        return self.max

    def minimum(self):
        """
        Get the minimum value of the slider.
        :return: int|float
        """
        return self.min

    def setBounds(self, minimum, maximum):
        """
        Set the minimum and maximum values of the slider.
        :param minimum: The new minimum value.
        :param maximum: The new maximum value.
        :return: None
        """
        self.setMaximum(maximum)
        self.setMinimum(minimum)

    def isInBounds(self, value) -> bool:
        """
        Determine if the given value is in bounds.
        :param value: The value to test.
        :return: bool
        """
        value = self.__getValue(value)
        return self.min <= value <= self.max

    def useFloats(self, enable: bool=True):
        """
        Use floats instead of integers.
        :param enable: 'True' to use floats, 'False' to use integers.
        :return: None
        """
        enable = bool(enable)

        if enable != self.floats:
            self.floats = enable
            # We update the current values
            self.setValue(self.value)
            self.setBounds(self.min, self.max)

    def isUsingFloats(self) -> bool:
        """
        Return 'True' if floats are used, 'False' otherwise.
        :return: bool
        """
        return self.floats

    def setTitle(self, title: str):
        """
        Set the title of the slider.
        :param title: The new title.
        :return: None
        """
        self.title = str(title)
        self.titleLabel.setText(self.title + ' :')

    def title(self) -> str:
        """
        Get the title of the slider.
        :return: str
        """
        return self.title

    def setInputWidth(self, width: int):
        """
        Set the width of the input field.
        :param width: The new width.
        :return: None
        """
        self.valueLineEdit.setMinimumWidth(width)
        self.valueLineEdit.setMaximumWidth(width)

    def inputWidth(self) -> int:
        """
        Get the width of the input field
        :return: int
        """
        return self.valueLineEdit.minimumWidth()

    def setDecimals(self, decimals: int):
        """
        Set the maximum number of decimals.
        :param decimals: The maximum number of decimals.
        :return: None
        """
        self.maxDecimals = int(decimals)

    def decimals(self) -> int:
        """
        Get the maximum number of decimals.
        :return: int
        """
        return self.maxDecimals

    def mousePressEvent(self, event: QMouseEvent):
        """
        Mouse press event.
        :param event:
        :return: None
        """
        if event.button() == Qt.LeftButton and self.sliderLayout.geometry().contains(event.pos()):
            # The left mouse button is pressed and the handle is under
            # the mouse cursor
            self.mousePressed = True
            self.handleImage.setFocus()
            self.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Mouse release event
        :param event:
        :return: None
        """
        self.mousePressed = False

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Mouse move event.
        :param event:
        :return: None
        """
        if not self.mousePressed:
            return

        mousePos = event.pos()

        handleWidth = self.handleImage.geometry().width()
        areaWidth = self.handleLayout.geometry().width()

        if areaWidth <= 0:
            # Invalid area width
            return

        areaWidth -= handleWidth

        handleOffset = handleWidth / 2
        mouseOffset = mousePos.x() - handleOffset

        progress = mouseOffset / areaWidth
        range = self.max - self.min
        newValue = range * progress + self.min

        # We set the new value
        self.setValue(newValue)

    def showEvent(self, event: QShowEvent):
        """
        Show event.
        :param event:
        :return: None
        """
        self.__computeHandlePosition()

    def resizeEvent(self, event: QResizeEvent):
        """
        Resize event.
        :param event:
        :return: None
        """
        self.__computeHandlePosition()

    def __onValueChanged(self, value: str):
        """
        Event called when the text area value is changed.
        :param value: The new value.
        :return: None
        """
        # We remove invalid characters
        if self.floats:
            value = re.sub(r'[^0-9,.-]', '', value)
            value = value.replace(',', '.')

            # We remove excess points
            try:
                first = value.index('.') + 1
            except ValueError:
                pass
            else:
                value = value[:first] + value[first:].replace('.', '')
        else:
            value = re.sub(r'[^0-9-]', '', value)

        # We allow the '-' only at the beginning of the string
        value = re.sub(r'(?<!^)-', '', value)

        try:
            if len(value) != 0 and self.isInBounds(value):
                # We set the new value
                self.setValue(value)
                self.valueLineEdit.setText(self.__getTextValue())
        except:
            pass

    def __onValueEditFinished(self):
        """
        Event called when the edit of the text area is finished.
        :return: None
        """
        self.valueLineEdit.setText(self.__getTextValue())

    def __getTextValue(self) -> str:
        """
        Convert the value into string.
        :return: str
        """
        if self.floats:
            return ('{:.' + str(self.maxDecimals) + 'f}').format(self.value)
        else:
            return str(self.value)

    def __getValue(self, value):
        """
        Convert a numeric value to integer or float.
        :param value: The numeric value to convert.
        :return: int|float
        """
        return round(float(value), self.maxDecimals) if self.floats else int(round(float(value)))

    def __computeHandlePosition(self):
        """
        Compute the handle position.
        :return: None
        """
        imageWidth = self.handleImage.geometry().width()
        sliderWidth = self.handleLayout.geometry().width() - imageWidth

        if sliderWidth <= 0:
            # Invalid size
            return

        range = self.max - self.min
        value = self.floatValue - self.min
        spacerWidth = int(round(sliderWidth * (value / range)))

        spacer = self.handleLayout.itemAt(0).spacerItem()
        spacer.changeSize(spacerWidth, 0, QSizePolicy.Maximum, QSizePolicy.Minimum)

        self.handleLayout.invalidate()
