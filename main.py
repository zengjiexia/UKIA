import sys
import os

import PySide6
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QProgressDialog
from PySide6.QtCore import QFile, QIODevice, Slot, Qt, QThread, Signal
from PySide6.QtUiTools import QUiLoader
import pyqtgraph as pg
import toolbox
from logics import SimPullAnalysis
import imagej


class DiffractionLimitAnalysis_UI(QMainWindow):

    def __init__(self):
        super(DiffractionLimitAnalysis_UI, self).__init__()
        self.loadUI()

    def loadUI(self):

        path = os.path.join(os.path.dirname(__file__), "form.ui")
        ui_file = QFile(path)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
            sys.exit(-1)

        class UiLoader(QUiLoader): # Enable promotion to custom widgets
            def createWidget(self, className, parent=None, name=""):
                if className == "PlotWidget":
                    return pg.PlotWidget(parent=parent) # promote to pyqtgraph.PlotWidget
                if className == "LogTextEdit":
                    return toolbox.LogTextEdit(parent=parent) # promote to self defined LogTextEdit(QPlainTextEdit)
                return super().createWidget(className, parent, name)

        loader = UiLoader()
        self.window = loader.load(ui_file, self)

        # main window widgets
        self.window.main_runButton.clicked.connect(self.clickMainWindowRun)

        ui_file.close()
        if not self.window:
            print(loader.errorString())
            sys.exit(-1)
        self.window.show()
        sys.exit(app.exec_())       

    def updateLog(self, message):
        self.window.main_logBar.insertPlainText(message + '\n')
        self.window.main_logBar.verticalScrollBar().setValue(
            self.window.main_logBar.verticalScrollBar().maximum())
        # auto scroll down to the newest message


    def initialiseProgress(self, work, workload):
        self.window.progressBar.setMaximum(workload)
        self.window.progressBar.setValue(0)
        self.window.progressBarLabel.setText(work)


    def updateProgress(self, progress):
        self.window.progressBar.setValue(progress)


    def restProgress(self):
        self.window.progressBarLabel.setText('No work in process.')
        self.window.progressBar.reset()


    def showMessage(self, msg_type, message):
        msgBox = QMessageBox(self.window)
        if msg_type == 'c':
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setWindowTitle('Critical Error')
        elif msg_type == 'w':
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle('Warning')
        msgBox.setText(message)
        returnValue = msgBox.exec_()


    def clickMainWindowRun(self):
        guard = self._checkParameters()
        if guard == 1:
            #guard == self._runAnalysis()
            guard == self._generateReports()
        else:
            self.showMessage('w', 'Failed to locate particles using ComDet. Please see help.')


    def _checkParameters(self):
        #Check if data path exists
        data_path = self.window.main_pathEntry.text()
        if os.path.isdir(data_path) == False:
            self.showMessage('w', 'Error: Path to folder not found.')
            return 0
        else:
            self.data_path = data_path
            self.window.main_pathEntry.setText(self.data_path)
            self.updateLog('Data path set to '+data_path)

        #Check input: threshold
        try:
            self.threshold = int(self.window.main_thresholdEntry.text())
            self.window.main_thresholdEntry.setText(str(self.threshold))
        except ValueError:
            self.showMessage('c', 'Please input a number for threshold.')
            return 0
        if self.threshold <= 2 or self.threshold >= 20:
            self.updateLog('Threshold set as '+str(self.threshold)+' SD. Suggested range would be 3-20 SD.')
        else:
            self.updateLog('Threshold set at '+str(self.threshold)+' SD.')

        #Check input: estimated size
        try:
            self.size = int(self.window.main_sizeEntry.text())
            self.window.main_sizeEntry.setText(str(self.size))
        except ValueError:
            self.showMessage('c', 'Please input a number for estimated particle size.')
            return 0
        if self.size >= 15:
            self.updateLog('Estimated particle size set as '+str(self.size)+' pixels which is quite high. Pariticles close to each other might be considered as one.')
        else:
            self.updateLog('Estimated particle size set as '+str(self.size)+' pixels.')

        self.project = SimPullAnalysis(self.data_path) # Creat SimPullAnalysis object
        return 1


    def _runAnalysis(self):

        path_fiji = os.path.join(os.path.dirname(__file__), 'Fiji.app')

        try:
            self.updateLog('Initiating Fiji...')
            self.IJ = imagej.init(path_fiji, headless=False) # Initiate fiji
            #self.IJ.ui().showUI()
        except TypeError:
            self.showMessage('c', 'Fiji initiation failed. Please restart program.')
            return 0

        # Create a QThread object
        self.fijiThread = QThread()
        # Create a worker object
        self.fijiWorker = toolbox.FijiWorker(self.IJ, self.project, self.size, self.threshold)

        # Connect signals and slots
        self.fijiThread.started.connect(self.fijiWorker.run)
        self.fijiWorker.finished.connect(self.fijiThread.quit)
        self.fijiWorker.finished.connect(self.fijiWorker.deleteLater)
        self.fijiThread.finished.connect(self.fijiThread.deleteLater)
        # Move worker to the thread
        self.fijiWorker.moveToThread(self.fijiThread)
        # Connect progress signal to GUI
        self.fijiWorker.work_info.connect(self.initialiseProgress)
        self.fijiWorker.progress.connect(self.updateProgress)
        # Start the thread
        self.fijiThread.start()
        self.updateLog('Start to locate particles...')
        
        # UI response
        self.window.main_runButton.setEnabled(False) # Block 'Run' button
        self.fijiThread.finished.connect(
            lambda: self.window.main_runButton.setEnabled(True) # Reset 'Run' button
            )
        self.fijiThread.finished.connect(
            lambda: self.updateLog('Particles in images are located.')
            )
        self.fijiThread.finished.connect(
            lambda: self.IJ.getContext().dispose()
            ) # Close fiji
        self.fijiThread.finished.connect(
            lambda: self.restProgress()
            ) # Reset progress bar to rest
        self.fijiThread.finished.connect(
            lambda: self._generateReports()
            )


    def _generateReports(self):
        # Generate sample summaries, Summary.csv and QC.csv
        self.reportThread = QThread()
        self.reportwriter = toolbox.ReportWriter(self.project)

        self.reportThread.started.connect(self.reportwriter.run)
        self.reportwriter.finished.connect(self.reportThread.quit)
        self.reportwriter.finished.connect(self.reportwriter.deleteLater)
        self.reportThread.finished.connect(self.reportThread.deleteLater)


        self.reportwriter.moveToThread(self.reportThread)

        self.reportwriter.work_info.connect(self.initialiseProgress)
        self.reportwriter.progress.connect(self.updateProgress)

        self.reportThread.start()
        self.updateLog('Start to generate reports...')

        self.window.main_runButton.setEnabled(False) # Block 'Run' button
        self.reportThread.finished.connect(
            lambda: self.window.main_runButton.setEnabled(True) # Reset 'Run' button
            )
        self.reportThread.finished.connect(
            lambda: self.updateLog('Reports generated at: ' + self.project.path_result_main)
            )
        self.reportThread.finished.connect(
            lambda: self.restProgress()
            ) # Reset progress bar to rest


if __name__ == "__main__":

    app = QApplication([])
    #app.setQuitOnLastWindowClosed(False)
    widget = DiffractionLimitAnalysis_UI()
    widget.show()
    sys.exit(app.exec_())
