from openalea.plantgl.gui.qt.QtGui import *
from openalea.plantgl.gui.editablectrlpoint import *
import numpy

class WireSelectionAlgorithm:

    def __init__(self, editor):
        """
        :param editor: MTGEditor widget
        """
        self.editor = editor
        self.enabled = False
        self.wireStartPoints = []

    def start(self):
        """
        Enable the wire selection.
        :return: None
        """
        QMessageBox.information(self.editor, 'Wire Selection',
            'Please select one endpoint of the wire you want to select.\n\n'
            'Once you\'re done, press Enter to continue the selection process.\n\n'
            'Press Escape if you want to cancel.')

        self.enabled = True

    def stop(self):
        """
        Terminate the current wire selection process by cleaning up the
        selected endpoints and resetting the internal state.
        :return: None
        """
        self.wireStartPoints = []
        self.enabled = False

    def isEnabled(self) -> bool:
        """
        Check whether the wire selection is enabled.
        :return: bool
        """
        return self.enabled

    def useSelection(self):
        """
        Save the current selection for the wire selection algorithm.
        :return: None
        """
        if len(self.editor.pointinfo.selectedPoint) == 0:
            # No selection
            QMessageBox.warning(self.editor, 'Wire Selection', 'No point selected.')
            return

        self.wireStartPoints.append(self.editor.pointinfo.selectedPoint[0])
        self.editor.deselectPoints()
        self.__nextStep()

    def cancel(self):
        """
        Cancel the current wire selection process.
        :return: None
        """
        self.stop()
        QMessageBox.information(self.editor, 'Wire Selection', 'Wire selection cancelled.')

    def __nextStep(self):
        """
        Continue the wire selection process. If both endpoints have been
        selected, the wire selection algortihm is started. Otherwise, the user
        will be prompted to select the other endpoint.
        :return: None
        """
        if len(self.wireStartPoints) >= 2:
            # The two endpoints have been selected, we launch the wire
            # selection algorithm
            self.__setupAlgorithm()
            self.stop()
        else:
            # The other endpoint must now be selected
            QMessageBox.information(self.editor, 'Wire Selection',
                'You can now select the other endpoint of the wire.\n\n'
                'After that, press Enter to start the algorithm.')

    def __setupAlgorithm(self):
        """
        Ask the user to parameterize the wire selection algorithm, then
        execute it.
        :return:
        """
        # Parameters of the wire selection algorithm
        dialog = self.editor.createParamDialog('Parameterizing the Wire Selection Algorithm', [
            ('Barycenter radius value', float, 0.04),
            ('Get radii value', float, 0.05)
        ])

        if dialog.exec_():
            # We execute the wire selection algorithm
            self.editor.createBackup('points')
            bariRadius, radiiValue = dialog.getParams()
            self.__execute(bariRadius, radiiValue)

    def __execute(self, bariRadius: float, radiiValue: float):
        """
        Display the progress dialog then execute the wire selection algorithm.
        :param bariRadius: Radius of the baricenter
        :param radiiValue: Radii value
        :return: None
        """
        self.editor.progressdialog.setTaskCount(5)
        self.editor.progressdialog.setOneShot(True)

        try:
            wirePoints = self.__main(bariRadius, radiiValue)
            self.editor.selectPoints(wirePoints)
        except Exception as e:
            # Selection error
            QMessageBox.warning(self.editor, 'Wire Selection', str(e))
        finally:
            # We ensure the progress dialog is closed
            self.editor.progressdialog.disableMultitask()
            self.editor.progressdialog.hideDialog()

    def __main(self, bariRadius: float, radiiValue: float) -> Index:
        """
        Execute the wire selection algorithm.
        :param bariRadius: Radius of the baricenter
        :param radiiValue: Radii value
        :return: Index
        """
        kclosestWire = IndexArray(0)

        wirePath = get_shortest_path(self.editor.points.pointList, kclosestWire, self.wireStartPoints[0], self.wireStartPoints[1])
        newpoint, baricenters = add_baricenter_points_of_path(self.editor.points.pointList, kclosestWire, wirePath, bariRadius)

        self.editor.showProgress('Computing K-Closest points.', 0)
        kclosest = k_closest_points_from_ann(newpoint, 20, True)
        self.editor.showProgress('Computing K-Closest points.', 100)

        radii = get_radii_of_path(newpoint, kclosest, baricenters, radiiValue)

        if len(radii) == 0:
            # Pathfinding error
            raise Exception('No wire found.')

        radius = numpy.average(radii)
        wirePoints = select_wire_from_path(newpoint, baricenters, radius, radii)
        selectedPoints = Index([])

        for point in wirePoints:
            if point not in baricenters:
                selectedPoints.append(point)

        return selectedPoints
