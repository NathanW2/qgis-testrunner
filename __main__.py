import sys
import json
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QProcess, pyqtSignal, QObject
from PyQt5 import uic
import subprocess

form, base = uic.loadUiType("ui\\runner.ui")

CTEST = r"C:\Program Files\CMake\bin\ctest.exe"



def runtest(test):
    args = [r"C:\Program Files\CMake\bin\ctest.exe", '-R', test, "-V"]
    print(args)
    output = subprocess.check_output(args, cwd=r"C:\Users\Nathan\dev\build-QGIS-QGIS_Qt5-ReleaseWithDebug").decode("utf-8")
    print(output)
    return output

class TestRunner(QObject):
    testFound = pyqtSignal(object)
    testOutput = pyqtSignal(object)
    testResult = pyqtSignal(object, bool)
    testStarted = pyqtSignal(object)

    def __init__(self):
        super(TestRunner, self).__init__()
        self.myProcess = QProcess()
        self.myProcess.setWorkingDirectory(r"C:\Users\Nathan\dev\build-QGIS-QGIS_Qt5-ReleaseWithDebug")
        #self.myProcess.readyReadStandardOutput.connect(self._parse_found_tests)
        self.myProcess.finished.connect(self._tests_loaded)

        self.testRunProcess = QProcess()
        self.testRunProcess.setWorkingDirectory(r"C:\Users\Nathan\dev\build-QGIS-QGIS_Qt5-ReleaseWithDebug")
        self.testRunProcess.readyReadStandardOutput.connect(self._parse_test_output)
        self.testRunProcess.finished.connect(self.done)
        self.buffer = ""
        self.pendingTests = []

    def done(self):
        self.run_next_test()

    def _parse_test_output(self):
        output = bytearray(self.testRunProcess.readAllStandardOutput())
        output = output.decode("utf-8")
        print(output)
        self.buffer += output
        if self.buffer.endswith("\r\n"):
            lines = self.buffer.splitlines()
            for line in lines:
                #print("Line: {}".format(line))
                ## TODO Regex this.
                if "Start" in line:
                    test = line.split(":")[1].strip()
                    self.testStarted.emit(test)
                if "Passed" in line:
                    test = line.split(":")[1].split(" ")[1].strip()
                    self.testResult.emit(test, True)
                if "***Failed" in line:
                    test = line.split(":")[1].split(" ")[1].strip()
                    self.testResult.emit(test, False)

            self.buffer = ""
            html = "<br>".join(lines)
            html = html.replace("Passed", '<b style="color:green">Passed</b>')
            html = html.replace("Failed", '<b style="color:red">Failed</b>')
            html += "<br>"
            self.testOutput.emit(html)

    def _tests_loaded(self):
        self._parse_found_tests()

    def run_tests(self, tests):
        self.pendingTests = tests
        self.run_next_test()
        # tests = "|".join(tests)
        # args = ["-R", tests, "--output-on-failure"]
        # self.testRunProcess.start(CTEST, args)

    def run_next_test(self):
        nexttest = self.pendingTests.pop()
        if not nexttest:
            return
        self.run_test(nexttest)

    def run_test(self, test):
        args = ["-R", test, "--output-on-failure"]
        self.testRunProcess.start(CTEST, args)

    def get_tests(self):
        self.myProcess.start(CTEST, ["-N"])
        # self.myProcess.waitForFinished()
        # self._parse_found_tests()

    def _parse_found_tests(self):
        output = bytearray(self.myProcess.readAllStandardOutput())
        output = output.decode("utf-8")
        tests = output.splitlines()
        tests = tests[1:-1]
        for test in tests:
            if not test:
                continue
            test = test.split(":")[1].strip()
            self.testFound.emit(test)

    def get_sub_tests(self, test):
        print("Get sub")
        def _parse_sub_tests():
            print("Parse")
            output = bytearray(myProcess.readAllStandardOutput())
            output = output.decode("utf-8")
            tests = output.splitlines()
            print(tests)

        self.subTestProcess = QProcess()
        self.subTestProcess.finished.connect(_parse_sub_tests)
        self.subTestProcess.waitForFinished()
        self.subTestProcess.setWorkingDirectory(r"C:\Users\Nathan\dev\build-QGIS-QGIS_Qt5-ReleaseWithDebug")
        self.subTestProcess.start(test, ["-functions"])



class RunnerUI(base, form):
    def __init__(self):
        super(RunnerUI,self).__init__()
        self.setupUi(self)
        self.actionRun_Selection.triggered.connect(self.run_selected)
        self.testRunner = TestRunner()
        self.testRunner.testFound.connect(self.load_test)
        self.testRunner.testOutput.connect(self.test_output)
        self.testRunner.testStarted.connect(self.test_started)
        self.testRunner.testResult.connect(self.test_result)
        self.nodes = {}

    def test_result(self, test, passed):
        testnode = self.nodes[test]
        PASSICON = QIcon(r"resources\success.png")
        FAILICON = QIcon(r"resources\error.png")
        if passed:
            testnode.setIcon(0, PASSICON)
        else:
            testnode.setIcon(0, FAILICON)
        print("Test: {} {}".format(test, passed))

    def test_started(self, test):
        print("test started {}".format(test))

    def test_output(self, output):
        self.mResultsText.insertHtml(output)

    def run_selected(self):
        self.mResultsText.clear()
        items = self.mTestTree.selectedItems()
        tests = [item.text(0) for item in items]
        self.testRunner.run_tests(tests)

    def load(self):
        self.nodes = {}
        self.mTestTree.clear()
        self.testRunner.get_tests()

    def load_test(self, test):
        if not test:
            return
        item = QTreeWidgetItem()
        item.setText(0, test)
        self.mTestTree.addTopLevelItem(item)
        self.nodes[test] = item
        self.testRunner.get_sub_tests(test)


app = QApplication(sys.argv)
runnerUI = RunnerUI()
from subprocess import Popen, PIPE
runnerUI.load()
runnerUI.show()
app.exec_()

