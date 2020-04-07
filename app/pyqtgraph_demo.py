# -*- coding: utf-8 -*-
"""
This example demonstrates many of the 2D plotting capabilities
in pyqtgraph. All of the plots may be panned/scaled by dragging with 
the left/right mouse buttons. Right click on any plot to show a context menu.
"""

#import initExample ## Add path to library (just for examples; you do not need this)


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

win = pg.GraphicsWindow(title="Basic plotting examples")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph example: Plotting')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

p1 = win.addPlot(title="Updating plot")
curve1 = p1.plot(pen='y')
data1 = np.random.normal(size=(10,1000))
ptr1 = 0
def update1():
    global curve1, data1, ptr1, p1
    curve1.setData(data1[ptr1%10])
    if ptr1 == 0:
        p1.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    ptr1 += 1
timer1 = QtCore.QTimer()
timer1.timeout.connect(update1)
timer1.start(50)




win.nextRow()



p2 = win.addPlot(title="Updating plot")
curve2 = p2.plot(pen='y')
data2 = np.random.normal(size=(10,1000))
ptr2 = 0
def update2():
    global curve2, data2, ptr2, p2
    curve2.setData(data2[ptr2%10])
    if ptr2 == 0:
        p2.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    ptr2 += 1
timer2 = QtCore.QTimer()
timer2.timeout.connect(update2)
timer2.start(50)


win.nextRow()

p3 = win.addPlot(title="Updating plot")
curve3 = p3.plot(pen='y')
data3 = np.random.normal(size=(10,1000))
ptr3 = 0
def update3():
    global curve3, data3, ptr3, p3
    curve3.setData(data3[ptr3%10])
    if ptr3 == 0:
        p3.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    ptr3 += 1
timer3 = QtCore.QTimer()
timer3.timeout.connect(update3)
timer3.start(50)



## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
