from openalea.plantgl.gui.editablectrlpoint import *

class SoilSelectionAlgorithm:

    def __init__(self, editor):
        """
        :param editor: MTGEditor widget
        """
        self.editor = editor

    def select(self):
        """
        Select the soil.
        :return: None
        """
        centerZ = self.editor.points.pointList.getCenter().z
        minZIndex = self.editor.points.pointList.getZMinIndex()
        minZ = self.editor.points.pointList[minZIndex].z

        maxHeight = minZ + (centerZ - minZ) * 0.5

        dialog = self.editor.createParamDialog('Parameterizing the Soil Selection Algorithm', [
            ('Top height percent', int, 10, {'range': (0, 100)}),
            ('Bottom threshold', float, maxHeight)
        ])

        if dialog.exec_():
            # We execute the soil selection algorithm
            topPercent, bottomThreshold = dialog.getParams()
            self.editor.createBackup('points')
            soilPoints = select_soil(self.editor.points.pointList, IndexArray(0), topPercent, bottomThreshold)
            self.editor.selectPoints(soilPoints)
