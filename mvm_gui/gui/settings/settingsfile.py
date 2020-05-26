"""
Module to handle an external settings file and its checksum.
"""

import json
from hashlib import md5
from os import path as os_path


__all__ = ('SettingsFile',)


def _check_file(filename):
    """
    Checks whether the file exist on disk and has some content

    arguments:
    - filename:   the name of the file to be checked.
    """

    return os_path.exists(filename) and os_path.getsize(filename) > 0


class SettingsFile:
    """
    A class to handle writing to and reading from a JSON settings file.
    """

    def __init__(self, path):
        """
        Constructor

        arguments:
        - path    the path of the configuration file
        """

        self.path = path

    def _write_md5(self):
        """
        Store the md5 of the configuration file to a .md5 file
        """

        with open(self.path, "rb") as configfile:
            value = md5(configfile.read()).hexdigest()
        with open(self.path + ".md5", "w") as hashfile:
            hashfile.write(value + "\n")

    def _check_md5(self):
        """
        Check for config file validity

        returns: True if the md5 of the config file matches with the md5
                 file content, False otherwise.
        """

        md5_path = self.path + ".md5"

        if _check_file(self.path) and _check_file(md5_path):
            with open(md5_path, "r") as md5file:
                challenge = md5file.read().rstrip()
            with open(self.path, "rb") as configfile:
                value = md5(configfile.read()).hexdigest()
            return value == challenge
        return False

    def store(self, data):
        """
        Save the current configuration and update the md5 file.
        The file will contain only the provided data.

        arguments:
        - data          a JSON-convertible object to store

        returns: True if the store succeeded, False otherwise
        """

        try:
            with open(self.path, "w") as configfile:
                json.dump(data, configfile)
            self._write_md5()
            return True
        except: # pylint: disable=W0702
            return False

    def load(self):
        """
        Load the object contained in the config file if the md5 test
        succeeded.

        returns:        the deserialized content of the configuration file
                        if the md5 test succeeded, an empty dictionary if
                        failed.
        """

        if not self._check_md5():
            return {}

        with open(self.path) as configfile:
            return json.load(configfile)
