"""
MVM toggle helper.
An MVM toggle is a custom, big toggle button.
"""

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRect


class MVMToggle(QtWidgets.QPushButton):
    """
    This is custom QPushButton that renders as a toggle
    """

    def __init__(self, parent=None):
        """
        Constructor

        arguments:
        - parent: the parent widget
        """

        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumWidth(66)
        self.setMinimumHeight(22)

    def paintEvent(self, event):
        #pylint: disable=invalid-name
        #pylint: disable=unused-argument
        """
        Reimplement the QPushButton.paintEvent function

        arguments:
        - event: the event
        """

        label = "ON" if self.isChecked() else "OFF"
        if self.isEnabled():
            bg_color = Qt.green if self.isChecked() else Qt.red
        else:
            bg_color = Qt.gray

        radius = 18
        width = 60
        center = self.rect().center()

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(center)
        painter.setBrush(QtGui.QColor(0, 0, 0))

        pen = QtGui.QPen(Qt.black)
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRoundedRect(
            QRect(-width, -radius, 2 * width, 2 * radius), radius, radius)
        painter.setBrush(QtGui.QBrush(bg_color))
        sw_rect = QRect(-radius, -radius, width + radius, 2 * radius)
        if not self.isChecked():
            sw_rect.moveLeft(-width)
        painter.drawRoundedRect(sw_rect, radius, radius)
        painter.drawText(sw_rect, Qt.AlignCenter, label)

    def setValue(self, value):
        #pylint: disable=invalid-name
        '''
        Just calls setChecked().

        arguments:
        - value: (bool) the value to set
        '''
        return self.setChecked(value)

    def value(self):
        '''
        Just calls isChecked().
        '''
        return int(self.isChecked())
