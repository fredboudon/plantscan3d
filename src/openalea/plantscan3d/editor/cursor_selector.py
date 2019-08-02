from openalea.plantgl.gui.qt.QtGui import *
import os

class CursorSelector:

    # Cursor list
    Normal = 1
    PointSelect = 2

    def __init__(self, editor):
        """
        :param editor: MTGEditor widget
        """
        self.editor = editor

        self.current = self.Normal
        self.pixmap = None
        self.isDisplayed = False
        self.isOver = False

        # Cursor pixmaps
        self.cursors = {}

        # We load the customs cursors
        self.__loadCursors([
            (self.PointSelect, 'select.png')
        ])

    def set(self, cursor: int):
        """
        Set the current cursor.
        :param cursor:
        :return: None
        """
        if cursor == self.Normal:
            # Default cursor
            self.restore()
        elif cursor != self.current and cursor in self.cursors:
            # Custom cursor
            self.current = cursor
            self.pixmap = self.cursors[cursor]

            # We display the new cursor, if the pointer is over the widget
            if self.isMouseOver():
                self.__display()

    def restore(self):
        """
        Restore the normal cursor.
        :return: None
        """
        if self.current != self.Normal:
            self.current = self.Normal
            self.pixmap = None
            self.__hide()

    def get(self) -> int:
        """
        Get the current cursor.
        :return: int
        """
        return self.current

    def setIsMouseOver(self, isOver=True):
        """
        Set the 'mouse over' state.
        :param isOver: Is the mouse over the widget?
        :return:
        """
        self.isOver = bool(isOver)

        if self.current == self.Normal:
            # No action needed for default cursor
            return

        if self.isMouseOver():
            # Over the widget, we display the custom cursor
            if not self.isDisplayed:
                self.__display()
        else:
            # Not over the widget, we display the default cursor
            if self.isDisplayed:
                self.__hide()

    def isMouseOver(self) -> bool:
        """
        Check whether the mouse is over the widget.
        :return: bool
        """
        return self.isOver

    def __display(self):
        """
        Apply the custom cursor.
        :return:
        """
        if self.pixmap is not None:
            cursor = QCursor(self.pixmap, 16, 16)
            QApplication.setOverrideCursor(cursor)

        self.isDisplayed = True

    def __hide(self):
        """
        Restore the default cursor.
        :return:
        """
        QApplication.restoreOverrideCursor()
        self.isDisplayed = False

    def __loadCursors(self, cursors: list):
        """
        Load the cursors passed as a parameter.
        :param cursors: The cursors to load.
        :return: None
        """
        currentDir = os.path.dirname(__file__)
        cursorsPath = os.path.join(currentDir, '..', 'images', 'cursors')

        for id, path in cursors:
            self.cursors[id] = QPixmap(os.path.join(cursorsPath, path))
