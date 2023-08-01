import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import Qt, pyqtSignal, QParallelAnimationGroup, QPropertyAnimation, QAbstractAnimation


class Spoiler(QWidget):
    """The base class of a spoiler (drop down menu) unit. 
    Licensed under GPL and Adapted from: 
    https://stackoverflow.com/a/37927256/386398 """

    spoiler_next_step = pyqtSignal()
    _sp_opened : bool = False
    
    def __init__(self, parent=None, ui_path = '', animationDuration=300):
        super(Spoiler, self).__init__(parent=parent)
        # Load Spoiler-specific controls by imporitng the .ui file
        uic.loadUi(ui_path, self)  

        self.label_check.hide()
        self.label_done_text.hide()

        self.animationDuration = animationDuration
        self.toggleAnimation = QParallelAnimationGroup()

        self.toggleButton.setStyleSheet("QToolButton { border: none; }")
        self.__set_spoiler_font(sys.platform)

        self.toggleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(Qt.RightArrow)
        self.toggleButton.setCheckable(True)
        self.toggleButton.setChecked(False)
        self.toggleButton.setEnabled(False)

        self.contentArea.setStyleSheet("QScrollArea { background-color: white; border: none; }")
        self.contentArea.setMaximumHeight(0)
        self.contentArea.setMinimumHeight(0)

        self.toggleAnimation.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        self.toggleAnimation.addAnimation(QPropertyAnimation(self, b"maximumHeight"))
        self.toggleAnimation.addAnimation(QPropertyAnimation(self.contentArea, b"maximumHeight"))
        
        self.mainLayout.setVerticalSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.toggleButton, 0, 0, 1, 1, Qt.AlignLeft)
        self.setLayout(self.mainLayout)

        def start_animation(checked):
            """Open or Close spoiler at event"""
            arrow_type = Qt.DownArrow if checked else Qt.RightArrow
            direction = QAbstractAnimation.Forward if checked else QAbstractAnimation.Backward
            self.toggleButton.setArrowType(arrow_type)
            self.toggleAnimation.setDirection(direction)
            self.toggleAnimation.start()
            self._sp_opened = self.toggleButton.isChecked()

        self.toggleButton.clicked.connect(start_animation)
        self.spoiler_next_step.connect(self.label_check.show)
        self.spoiler_next_step.connect(self.label_done_text.show)
        self.setContentLayout(self.contentLayout)

    def open_spoiler(self):
        if self._sp_opened == False:
            self.toggleButton.click()

    def close_spoiler(self):
        if self._sp_opened == True:
            self.toggleButton.click()

    def setContentLayout(self, contentLayout):
        """Display Spoiler content in QFrame"""
        self.contentArea.destroy()
        self.contentArea.setLayout(contentLayout)
        collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
        contentHeight = contentLayout.sizeHint().height()

        for i in range(self.toggleAnimation.animationCount()-1):
            spoilerAnimation = self.toggleAnimation.animationAt(i)
            spoilerAnimation.setDuration(self.animationDuration)
            spoilerAnimation.setStartValue(collapsedHeight)
            spoilerAnimation.setEndValue(collapsedHeight + contentHeight)

        contentAnimation = self.toggleAnimation.animationAt(self.toggleAnimation.animationCount() - 1)
        contentAnimation.setDuration(self.animationDuration)
        contentAnimation.setStartValue(0)
        contentAnimation.setEndValue(contentHeight)

    def __set_spoiler_font(self, __sys):
        """Set font scaling and type of the toggle and the labels for the OSes"""
        font_name = ('Segoe UI' if __sys == 'win32' else 
                    'Lato' if __sys == 'linux' else 
                    'Helvetica Neue' if __sys == 'darwin' else 'Helvetica')
        toggle_font = QFont(font_name, 16 if __sys == 'darwin' else 13, 300)
        label_check_font = QFont(font_name, 20 if __sys == 'darwin' else 15, 300)
        label_done_font = QFont(font_name, 13 if __sys == 'darwin' else 10, 300)
        toggle_font.setBold(True); label_done_font.setBold(True)
        self.toggleButton.setFont(toggle_font)
        self.label_check.setFont(label_check_font)
        self.label_done_text.setFont(label_done_font)
