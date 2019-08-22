from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *
from openalea.plantgl.gui.editablectrlpoint import *
import math

class PoleSelectionAlgorithm:

    def __init__(self, editor):
        """
        :param editor: MTGEditor widget
        """
        self.editor = editor
        self.enabled = False

    def start(self):
        """
        Enable the pole selection.
        :return: None
        """
        QMessageBox.information(self.editor, 'Pole Selection',
            'Please click on each pole you want to remove.\n'
            'Once you\'re done, press Espace to leave the selection mode.\n\n'
            'You should try to click on a clear area for each pole you want to select.')

        self.enabled = True
        self.editor.cursor.set(self.editor.cursor.PointSelect)

    def stop(self):
        """
        Disable the pole selection.
        :return: None
        """
        self.enabled = False
        self.editor.cursor.restore()

    def isEnabled(self) -> bool:
        """
        Check whether the pole selection is enabled.
        :return: bool
        """
        return self.enabled

    def select(self, point: QPoint, size: int = 2):
        """
        Try to select the clicked pole. A small selection area is created around
        the clicked point, then the nearest point of this selection is given to
        the pole selection algorithm.
        :param point: The cursor position.
        :param size: The size of the selection area.
        :return: None
        """
        assert size > 0
        assert size % 2 == 0

        self.editor.setSelectRegionWidth(size)
        self.editor.setSelectRegionHeight(size)

        self.editor.select(QPoint(int(point.x() - size / 2), int(point.y() - size / 2)))
        self.editor.rectangleSelect = None

    def execute(self, selection: list):
        """
        Execute the pole selection algorithm.
        :param selection: The list of selected points.
        :return: None
        """
        if selection is None or len(selection) == 0:
            # No point selected
            QMessageBox.warning(self.editor, 'Pole Selection', 'No point selected.')
            return

        # We select the nearest point
        nearestPoint = self.editor.getNearestSelectedPoint(selection)
        self.editor.displaySelectedPoint(nearestPoint)
        polePoints, score = select_pole_from_point(self.editor.points.pointList, nearestPoint, 10000, math.radians(15))

        if score > 0:
            # We display the selection
            self.editor.selectPoints(polePoints)
        else:
            # No pole found
            QMessageBox.warning(self.editor, 'Pole Selection', 'No pole found.')
