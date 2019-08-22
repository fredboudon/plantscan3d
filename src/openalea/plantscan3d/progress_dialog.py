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
    cui.check_ui_generation(os.path.join(ldir, 'progress_dialog.ui'))

from . import progress_dialog_ui

class ProgressDialog(QDialog, progress_dialog_ui.Ui_ProgressDialog):

    def __init__(self, parent=None):
        """
        :param parent: Parent window.
        """
        QDialog.__init__(self, parent)
        progress_dialog_ui.Ui_ProgressDialog.__init__(self)

        self.setupUi(self)
        # Remove 'Help' and 'Close' buttons
        self.setWindowFlags((self.windowFlags() & ~Qt.WindowContextHelpButtonHint) & ~Qt.WindowCloseButtonHint)

        self.currentProgress = 0
        self.isComplete = False
        self.isAutoCloseEnabled = True
        self.isAutoResetEnabled = True
        self.isCloseButtonDisplayed = False
        self.minimumDuration = 2
        self.displayTimer = None
        self.oneShot = False

        # Multitask data
        self.isMultiTask = False
        self.taskCount = 1
        self.currentTask = 1
        self.isWaitingTaskUpdate = False

        self.__displayCancelButton()
        self.hideDialog()

        # Signals and slots
        self.canceled = pyqtSignal()
        self.closeButton.clicked.connect(self.hideDialog)
        self.cancelButton.clicked.connect(self.__cancelDialog)

    def setProgress(self, progress):
        """
        Update the current progress.
        :param progress: The progress value, in range [0; 100].
        :return:
        """
        progress = float(progress)
        self.__startDialogDisplayTimer()

        if progress >= 100:
            # Complete
            self.currentProgress = 100
            self.__handleCompletion()
        else:
            if progress <= 0:
                self.currentProgress = 0
            else:
                self.currentProgress = progress

            # In progress
            self.isComplete = False
            self.__handleProgress()

            if self.isWaitingTaskUpdate:
                self.__displayMainTitle()

        self.__refreshDialog()

    def setLabelText(self, text):
        """
        Update the text of the main label.
        :param text: The new text value.
        :return:
        """
        self.descLabel.setText(str(text))

    def setMinimumDuration(self, duration):
        """
        Update the minimum task duration to display this dialog.
        :param duration: The duration, in seconds.
        :return:
        """
        self.minimumDuration = float(duration)

    def setOneShot(self, oneShot=True):
        """
        Set the next display to be made without delay.
        :param oneShot: Enable or disable.
        :return:
        """
        self.oneShot = bool(oneShot)

    def setTaskCount(self, taskCount):
        """
        Enable the multitask display. If 'taskCount' is lower than 2, the
        multitask display will be disabled.
        :param taskCount: The total number of tasks.
        :return:
        """
        self.disableMultitask()

        if taskCount < 2:
            # Less than two tasks, we do not enable the multitask display
            return

        self.isMultiTask = True
        self.taskCount = taskCount
        self.setCurrentTask(1)

    def nextTask(self):
        """
        Switch to the next task, if any.
        :return:
        """
        self.setCurrentTask(self.currentTask + 1)

    def setCurrentTask(self, task):
        """
        Set the current task number.
        :param task: The task number, within interval [1; taskCount]
        :return:
        """
        if self.isMultiTask and 1 <= task <= self.taskCount:
            self.currentTask = task

            if not self.isComplete:
                self.__displayMainTitle()
            else:
                self.isWaitingTaskUpdate = True

    def disableMultitask(self):
        """
        Disable the multitask display.
        :return:
        """
        if not self.isMultiTask:
            # Multitask display is not enabled
            return

        self.isMultiTask = False
        self.__displayMainTitle()

    def setAutoCloseEnabled(self, enable=True):
        """
        Enable or disable the auto-close of the dialog.
        :param enable: Enable or disable.
        :return:
        """
        self.isAutoCloseEnabled = bool(enable)

    def setAutoResetEnabled(self, enable=True):
        """
        Enable or disable the auto-reset when the progress is complete.
        :param enable: Enable or disable.
        :return:
        """
        self.isAutoResetEnabled = bool(enable)

    def setCancelButtonEnabled(self, enable=True):
        """
        Enable or disable the 'Cancel' button.
        :param enable: Enable or disable.
        :return:
        """
        self.cancelButton.setEnabled(bool(enable))

    def displayDialog(self):
        """
        Display the dialog, then clear the display timer, if any.
        :return:
        """
        self.show()
        self.__cancelDialogDisplayTimer()
        self.__refreshDialog()

    def hideDialog(self):
        """
        Hide the dialog, then clear the display timer, if any.
        :return:
        """
        self.hide()
        self.__cancelDialogDisplayTimer()
        self.__refreshDialog()

    def __startDialogDisplayTimer(self):
        """
        Start the dialog display timer. If the timer duration is zero or lower,
        the dialog is displayed instantly.
        :return:
        """
        if not self.isHidden() or self.displayTimer is not None:
            # Already displayed, or the timer is already running
            return

        if self.minimumDuration <= 0 or self.oneShot:
            self.oneShot = False
            self.displayDialog()
            return

        self.displayTimer = QTimer(self)
        self.displayTimer.timeout.connect(self.displayDialog)
        self.displayTimer.setSingleShot(True)
        self.displayTimer.start(int(self.minimumDuration * 1000))

    def __cancelDialogDisplayTimer(self):
        """
        Cancel the display timer, if any.
        :return:
        """
        if self.displayTimer is not None:
            self.displayTimer.stop()
            self.displayTimer = None

    def __refreshDialog(self):
        """
        Prevent the dialog from freezing.
        :return:
        """
        QApplication.processEvents()

    def __cancelDialog(self):
        """
        Cancel the dialog.
        :return:
        """
        self.canceled.emit()

    def __handleProgress(self):
        """
        Function called when the progress is updated.
        :return:
        """
        if self.isCloseButtonDisplayed:
            self.__displayCancelButton()

        self.progressBar.setValue(int(self.currentProgress * 100))
        self.progressLabel.setText("%.2f%%" % self.currentProgress)

    def __handleCompletion(self):
        """
        Function called when the progress is complete.
        :return:
        """
        if self.isComplete:
            # Already completed
            self.__cancelDialogDisplayTimer()
            return

        self.isComplete = True
        self.__handleProgress()

        if self.__isLastTask():
            if self.isAutoResetEnabled:
                if self.isAutoCloseEnabled:
                    # If required, we automatically close the dialog
                    self.hideDialog()

                # Reset progress to zero
                self.currentProgress = 0
                self.__handleProgress()

            elif not self.isCloseButtonDisplayed:
                # We display the 'Close' buton instead of the 'Cancel' button
                self.__displayCloseButton()

            self.disableMultitask()
        else:
            self.nextTask()

    def __displayCloseButton(self):
        """
        Display the 'Close' button instead of the 'Cancel' button.
        :return:
        """
        self.cancelButton.setVisible(False)
        self.closeButton.setVisible(True)
        self.isCloseButtonDisplayed = True
        self.__displayMainTitle()

    def __displayCancelButton(self):
        """
        Display the 'Cancel' button instead of the 'Close' button.
        :return:
        """
        self.closeButton.setVisible(False)
        self.cancelButton.setVisible(True)
        self.isCloseButtonDisplayed = False
        self.__displayMainTitle()

    def __displayMainTitle(self):
        """
        Set the main title of the dialog.
        :return:
        """
        if self.isCloseButtonDisplayed:
            # Task completed
            self.titeLabel.setText("Completed!")
        elif self.isMultiTask:
            # Mutlitask progress
            self.titeLabel.setText("Processing... (Task {} of {})".format(self.currentTask, self.taskCount))
            self.isWaitingTaskUpdate = False
        else:
            self.titeLabel.setText("Processing...")

    def __isLastTask(self):
        """
        Check whether the current task is the last one.
        :return:
        """
        return not self.isMultiTask or self.currentTask >= self.taskCount
