#!/usr/bin/env python3
"""
A "tool settings" widget shows the current value of a setting, plus a slider representing
how that value relates to the minimum/maximum allowed values of the parameter.

This widget does not allow the value to be changed - it is just informational.
"""

from PyQt5 import QtWidgets, uic
from PyQt5 import QtGui

class ToolSettings(QtWidgets.QWidget):
    """
    Class members:
    - labels: QLabels for various elements
        - name: For the parameter name
        - value: For the current value
        - min: For the minimum allowed value
        - max: For the maximum allowed value
        - units: For the units of the parameter
    - slider_value: QProgressBar for the current value
    - show_fraction: bool for whether to show the value as 1:X rather than X
    - min: Minimum allowed value
    - max: Maximum allowed value
    - step: Minimum increment of value
    - _config: Loaded YAML settings
    """
    def __init__(self, *args):
        """
        Initializes the ToolSettings widget.

        Grabs child widgets and and connects slider value to text value.
        """
        super(ToolSettings, self).__init__(*args)
        uic.loadUi("toolsettings/toolsettings.ui", self)

        self.labels = {}
        self.labels["name"] = self.findChild(QtWidgets.QLabel, "label_name")
        self.labels["value"] = self.findChild(QtWidgets.QLabel, "label_value")
        self.labels["min"] = self.findChild(QtWidgets.QLabel, "label_min")
        self.labels["max"] = self.findChild(QtWidgets.QLabel, "label_max")
        self.labels["units"] = self.findChild(QtWidgets.QLabel, "label_units")

        self.slider_value = self.findChild(QtWidgets.QProgressBar, "slider_value")

        self.show_fraction = False
        self.min = 0
        self.max = 0
        self.step = 0
        self._config = None

        # Set background color
        palette = self.palette()
        role = self.backgroundRole()
        palette.setColor(role, QtGui.QColor("#eeeeee"))
        self.setPalette(palette)

    def setup(self, name, setrange=(0, 0, 100), units=None, step=0.1,
              show_fraction=False):
        #pylint: disable=too-many-arguments
        """
        Sets up main values for the ToolSettings widget, including the name and the values for the
        range as (minimum, initial, maximum).

        Arguments:
        - name: The name to be displayed.
        - setrange: Tuple (min, current, max) for the allowed min/max values and current value.
        - units: String value for the units to be displayed.
        - step: sets the granularity of a single step of the parameter
        - show_fraction: If True, will display fractional values instead of decimal
        """
        self.labels["name"].setText(name)

        # unpack and assign slider min, current, and max
        (low, val, high) = setrange
        self.update_range(valuerange=(low, high), step=step)
        self.labels["min"].setText(str(low))
        self.labels["max"].setText(str(high))

        self.show_fraction = show_fraction

        # Handle optional units
        if units is not None:
            self.labels["units"].setText(str(units))
        else:
            self.labels["units"].setText("")

        self.update(val)

    def load_presets(self, name="default"):
        """
        Configure this widget by loading values from the configuration file.

        Arguments:
        - name: The attribute to look for in the YAML file. If the attribute is not
            found, default values will be loaded instead (no warning/exception).
        """
        toolsettings_default = {
            "name": "Param",
            "default": 50,
            "min": 0,
            "max": 100,
            "current": None,
            "units": "-",
            "step": 1,
            "show_fraction": False}
        entry = self._config.get(name, toolsettings_default)
        self.setup(
            entry.get("name", toolsettings_default["name"]),
            setrange=(
                entry.get("min", toolsettings_default["min"]),
                entry.get("default", toolsettings_default["default"]),
                entry.get("max", toolsettings_default["max"])),
            units=entry.get("units", toolsettings_default["units"]),
            step=entry.get("step", toolsettings_default["step"]),
            show_fraction=entry.get("show_fraction", toolsettings_default["show_fraction"]))

    def connect_config(self, config):
        """
        Tell this class about the current configuration.

        Arguments:
        - config: Loaded YAML settings.
        """
        self._config = config

    def update_range(self, valuerange=(0, 1), step=0.1):
        """
        Updates the range of the progress bar widget.

        Arguments:
        - valuerange: (min, max) for the parameter
        - step: sets the granularity of a single step of the parameter
        """
        self.min = valuerange[0]
        self.max = valuerange[1]
        self.step = step

        # set the max for exactly the number of steps we need
        self.slider_value.setMinimum(0)
        self.slider_value.setMaximum((self.max - self.min) / self.step)

        self.labels["min"].setText(str(valuerange[0]))
        self.labels["max"].setText(str(valuerange[1]))

    def update(self, value):
        """
        Updates the slider position and text value to a provided value (min < value < max).
        Displays a fractional value instead of a decimal, if floating point is given.

        value: The value that the setting will display.
        fraction: If true, display fractional values instead of decimal
        """
        if self.show_fraction:
            # Display fraction
            disp_value = "1:%.2g" % value
        else:
            # Display decimal/integer
            disp_value = "%g" % (round(value / self.step) * self.step)

        slider_value = int((value - self.min) / self.step)
        self.slider_value.setValue(slider_value)
        self.labels["value"].setText(disp_value)
