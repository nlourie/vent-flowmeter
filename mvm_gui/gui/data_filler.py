'''
Module containing the DataFiller class,
which is responsible for filling data
to plots and monitors
'''
from copy import copy
from ast import literal_eval  # to convert a string to list
import numpy as np
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg


class DataFiller():
    #pylint: disable=too-many-instance-attributes
    '''
    This class fills the data for all the
    displayed plots on the screen, and
    updates the plots accordingly.
    It also passes data to the monitors.

    In "frozen" mode, we keep adding new data points to _data,
    but don't update the displayed graph. When we unfreeze, we
    then see the full recent data.

    Attributes:
        _qtgraphs           (dict) All PlotItems
        _plots              (dict) All PlotDataItems
        _data               (dict) The data for all plots
        _historic_data      (dict) The historic data for all plots
        _default_yrange     (dict) The default y ranges per plot
        _yrange             (dict) The current y ranges per plot
        _monitors           (dict) The monitors to which to send data
        _colors             (dict) The plot color
        _config             (dict) The config dict
        _n_samples          (int) The number of samples to plot
        _n_historic_samples (int) The number of samples to keep for historic data
        _sampling           (float) The time interval between samples
        _time_window        (float) The number of seconds shown
        _xdata              (array) The data along x
        _frozen             (bool) True we are in forzen state
        _first_plot         (PlotDataItem) Reference to the first drwan plot
        _looping            (bool) True displays looping plots
        _looping_data_idx   (int) The x index of the looping line
        _looping_lines      (dict) A dict of InfiniteLines
    '''

    def __init__(self, config):
        '''
        Constructor

        arguments:
        - config: the config dictionary
        '''
        self._qtgraphs = {}
        self._plots = {}
        self._data = {}
        self._historic_data = {}
        self._default_yrange = {}
        self._yrange = {}
        self._monitors = {}
        self._colors = {}
        self._config = config
        self._n_samples = self._config['nsamples']
        self._n_historic_samples = self._config.get('historic_nsamples',
                                                    200)
        self._sampling = self._config['sampling_interval']
        self._time_window = self._n_samples * self._sampling  # seconds
        self._xdata = np.linspace(-self._time_window, 0, self._n_samples)
        self._frozen = False
        self._first_plot = None
        self._looping = self._config['use_looping_plots']
        self._looping_data_idx = {}
        self._looping_lines = {}
        self._x_label = None

    def connect_plot(self, plotname, plot):
        '''
        Connects a plot to this class by
        storing it in a dictionary

        arguments:
        - plotname: the name of the plot
        - plot: the PlotItem from the ui file
        '''
        plot_config = self._config['plots'][plotname]
        name = plot_config['observable']

        # Link X axes if we've already seen a plot
        if self._first_plot:
            plot.setXLink(self._first_plot)
        else:
            self._first_plot = plot

        self._qtgraphs[name] = plot
        self._plots[name] = plot.plot()
        self._data[name] = np.linspace(0, 0, self._n_samples)
        self._historic_data[name] = np.linspace(0, 0, self._n_historic_samples)
        self._yrange[name] = None
        self._plots[name].setData(copy(self._xdata), copy(self._data[name]))
        self._colors[name] = plot_config['color']
        self._looping_data_idx[name] = 0

        # Set the Y axis
        y_axis_label = plot_config['name']
        y_axis_label += ' '
        y_axis_label += plot_config['units']
        plot.setLabel(axis='left', text=y_axis_label)

        # Set the X axis
        if self._config['show_x_axis_labels'] and 'bot' in plotname and not self._looping:
            self.add_x_axis_label(plot)

        # Remove x ticks, if selected
        if self._looping or not self._config['show_x_axis_ticks']:
            plot.getAxis('bottom').setTicks([])
            plot.getAxis('bottom').setStyle(tickTextOffset=0, tickTextHeight=0)

        # Customize the axis color
        color = self.parse_color(self._config['axis_line_color'])
        plot.getAxis('bottom').setPen(
            pg.mkPen(color, width=self._config['axis_line_width']))
        plot.getAxis('left').setPen(
            pg.mkPen(color, width=self._config['axis_line_width']))

        if self._looping:
            self.add_looping_lines(name, plot)

        # Fix the x axis range
        self.set_default_x_range(name)

        # Fix the y axis range
        value_min = plot_config['min']
        value_max = plot_config['max']
        ymin = value_min - (value_max - value_min) * 0.1
        ymax = value_max + (value_max - value_min) * 0.1
        self._default_yrange[name] = [ymin, ymax]
        self.set_default_y_range(name)

        # Remove mouse interaction with plots
        plot.setMouseEnabled(x=False, y=False)
        plot.setMenuEnabled(False)

        print('NORMAL: Connected plot',
              plot_config['name'], 'with variable', name)

    def set_default_y_range(self, name):
        '''
        Set the Y axis range of the plot to the defaults
        specified in the config file.

        arguments:
        - name: the plot name to set the y range
        '''
        if name not in self._qtgraphs:
            raise Exception('Cannot set y range for graph',
                            name, 'as it doesn\'t exist.')

        # Save the range for future use
        self._yrange[name] = (self._default_yrange[name]
                              [0], self._default_yrange[name][1])

        # Set the range to the graph
        self._qtgraphs[name].setYRange(*self._default_yrange[name])

        # Also set the width (space) on the left of the Y axis (for the label
        # and ticks)
        self._qtgraphs[name].getAxis('left').setWidth(
            self._config['left_ax_label_space'])

    def set_y_range(self, name):
        '''
        Set the Y axis range of the plot to the max and min
        from the historic data set.

        arguments:
        - name: the plot name to set the y range
        '''
        if name not in self._historic_data or name not in self._qtgraphs:
            raise Exception('Cannot set y range for graph',
                            name, 'as it doesn\'t exist.')

        # Calculate the max and min using the larger historical data sample
        ymax = np.max(self._historic_data[name])
        ymin = np.min(self._historic_data[name])

        if ymax == ymin:
            return
        span = ymax - ymin

        ymax += span * 0.1
        ymin -= span * 0.1

        # Save the range for future use
        self._yrange[name] = (ymin, ymax)

        # Set the range to the graph
        self._qtgraphs[name].setYRange(*self._yrange[name])

        self.updateTicks(name, ymax - ymin)

    def restore_y_range(self, name):
        '''
        Restores a previously set y range.
        If the y range was not previously set,
        this method calls set_y_range()

        arguments:
        - name: the plot name to restore the y range
        '''
        if self._yrange[name] is None:
            self.set_y_range(name)
            return

        self._qtgraphs[name].setYRange(*self._yrange[name])

    def updateTicks(self, name, yrange=None):
        #pylint: disable=invalid-name
        '''
        Updates the major and minor ticks
        in the graphs

        arguments:
        - name: the plot name to update tickes
        - yrange: (optinal) the yrange to use (otherwise Pyqtgraph default)
        '''

        if name not in self._qtgraphs:
            raise Exception('Cannot set ticks for graph',
                            name, 'as it doesn\'t exist.')

        ax = self._qtgraphs[name].getAxis('left')

        if yrange is None:
            ax.setTickSpacing()
        else:
            # Sligthly reduce the yrange so
            # the tick labels don't get
            # cropped on the top
            yrange -= yrange * 0.2

            major_step = yrange / (self._config['n_major_ticks'] - 1)
            minor_step = major_step / (self._config['n_minor_ticks'] - 1)

            if major_step == 0 or minor_step == 0:
                ax.setTickSpacing()
            else:
                ax.setTickSpacing(major=major_step, minor=minor_step)

    def set_default_x_range(self, name):
        '''
        Set the X axis range of the plot to the defaults
        specified in the config file.

        arguments:
        - name: the plot name to set the x range
        '''
        self._qtgraphs[name].setXRange(-self._time_window, 0)

    def add_x_axis_label(self, plot):
        #pylint: disable=invalid-name
        #pylint: disable=c-extension-no-member
        '''
        Adds the x axis label 'Time [s]' in the form
        of a QGraphicsTextItem. This is done because it
        is hard to customize the PyQtGraph label.

        arguments:
        - plot: the PlotDataItem to add the label
        '''
        self._x_label = QtGui.QGraphicsTextItem()
        self._x_label.setVisible(True)
        self._x_label.setHtml(
            '<p style="color: %s">Time [s]:</p>' %
            self._config["axis_line_color"])

        # Find the position of the label
        br = self._x_label.boundingRect()
        p = QtCore.QPointF(0, 0)
        # x = plot.size().width() / 2. - br.width() / 2.
        y = plot.size().height() - br.height()
        p.setX(0)  # Leave it on the left, so it doesn't cover labels.
        p.setY(y)
        self._x_label.setPos(p)
        plot.getAxis('bottom').scene().addItem(self._x_label)

    def add_looping_lines(self, name, plot):
        '''
        Add line corresponding to where the
        data is being updated when in "looping" mode.

        arguments:
        - name: the plot name to add the lines
        - plot: the PlotItem to add the lines
        '''

        self._looping_lines[name] = pg.InfiniteLine(
            pos=0,
            angle=90,
            movable=False,
            pen=pg.mkPen(
                cosmetic=False,
                width=self._time_window / 25,
                color='k',
                style=QtCore.Qt.SolidLine))

        plot.addItem(self._looping_lines[name])

    def connect_monitor(self, monitor):
        '''
        Connect a monitor to this class by
        storing it in a dictionary

        arguments:
        - monitor: the monitor to connect
        '''
        name = monitor.observable
        self._monitors[name] = monitor

        self._data[name] = np.linspace(0, 0, self._n_samples)

        self._looping_data_idx[name] = 0

        if name not in self._data:
            self._data[name] = np.linspace(0, 0, self._n_samples)

        print('NORMAL: Connected monitor',
              monitor.configname, 'with variable', name)

    def add_data_point(self, name, data_point):
        '''
        Adds a data point to the plot with
        name 'name'

        arguments:
        - name: the name of the plots (and monitor if available)
        - data_point: (float) the data point to add
        '''

        # print('NORMAL: Received data for monitor', name)

        if name in self._historic_data:
            # Save to the historic data dict
            self._historic_data[name][:-1] = self._historic_data[name][1:]
            self._historic_data[name][-1] = data_point

        if name in self._data:
            if self._looping:
                # Looping plots - update next value
                self._data[name][self._looping_data_idx[name]] = data_point

                self._looping_data_idx[name] += 1

                if self._looping_data_idx[name] == self._n_samples:
                    self._looping_data_idx[name] = 0
            else:
                # Scrolling plots - shift data 1 sample left
                self._data[name][:-1] = self._data[name][1:]

                # add the last data point
                self._data[name][-1] = data_point

        if name in self._plots:
            self.update_plot(name)

        if name in self._monitors:
            self.update_monitor(name)

    def update_plot(self, name):
        '''
        Send new data from self._data to the actual pyqtgraph plot.

        arguments:
        - name: the name of the plot to update
        '''

        if not self._frozen:
            # Update the displayed plot with current data.
            # In frozen mode, we don't update the display.
            color = self._colors[name]
            color = color.replace('rgb', '')
            color = literal_eval(color)
            self._plots[name].setData(
                copy(self._xdata),
                copy(self._data[name]),
                pen=pg.mkPen(color, width=self._config['line_width']))
            self.set_default_x_range(name)
            self.set_y_range(name)

            if self._looping:
                x_val = self._xdata[self._looping_data_idx[name]
                                    ] - self._sampling * 0.1
                self._looping_lines[name].setValue(x_val)

    def freeze(self):
        '''
        Enter "frozen" mode, where plots are not updated, and mouse/zoom
        interaction is enabled.
        '''
        self._frozen = True

        for plot in self._qtgraphs.values():
            plot.setMouseEnabled(x=True, y=True)

    def unfreeze(self):
        '''
        Leave "frozen" mode, resetting the zoom and showing self-updating
        plots.
        '''
        self._frozen = False

        for name in self._plots:
            self.update_plot(name)

        for plot in self._qtgraphs.values():
            plot.setMouseEnabled(x=False, y=False)

        self.reset_zoom()

    def reset_zoom(self):
        '''
        Revert to normal zoom range for each plot.
        autoRange() used to set X range, then
        custom values used for Y range.
        '''
        for name in self._qtgraphs:
            self.set_default_x_range(name)
            self.restore_y_range(name)

    def update_monitor(self, name):
        '''
        Updates the values in a monitor,
        if a monitor exists with this name

        arguments:
        - name: the name of the monitor to update
        '''

        if name in self._monitors:
            last_data_idx = self._looping_data_idx[name] - \
                1 if self._looping else -1
            self._monitors[name].update_value(self._data[name][last_data_idx])
        else:
            return

    def parse_color(self, rgb_string):
        #pylint: disable=no-self-use
        '''
        Given a color string in format
        'rgb(X,Y,Z)', it returns a list
        (X,Y,Z)

        arguments:
        - rgb_string: (str) the rgb string 'rgb(X,Y,Z)'
        '''

        color = rgb_string.replace('rgb', '')
        return literal_eval(color)
