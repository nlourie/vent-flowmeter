'''
Module containg the MessageBox which
handles pop up messages
'''
from functools import reduce
from PyQt5.QtWidgets import QMessageBox


class MessageBox(QMessageBox):
    '''
    Class that displaes a QT message box, with callbacks
    attached to each button.

    Example usage:

    ```
    from messagebox import MessageBox

    callbacks = {QMessageBox.Retry: your_retry_callback_function,
                 QMessageBox.Abort: lambda: sys.exit(-1)}

    MessageBox().critical("short message", "long message", "details",
                          "Window title", callbacks)
    ```
    '''

    def _wrapper(self, text, long_text, detail_text, title,
                 icon, callbacks, do_not_block=False):
        #pylint: disable=too-many-arguments
        """
        Wrapper function to implement the message box

        arguments:
        - text          the short message
        - long_text     the long message
        - detail_text   the text to be shown in the optional text box
                        (None for none)
        - title         the window title
        - icon          one in:
                            MessageBox.Question, MessageBox.Information,
                            MessageBox.Warning, and MessageBox.Critical
        - callbacks     dictionary: keys are one in:
                            MessageBox.Ok, MessageBox.Open, MessageBox.Save,
                            MessageBox.Cancel, MessageBox.Close,
                            MessageBox.Yes, MessageBox.No, MessageBox.Abort,
                            MessageBox.Retry, and MessageBox.Ignore
                        value is a user-defined function object
        - do_not_block  bool: By default, a QMessage blocks further
                        actions until the QMessage is closed. If you don't
                        want to block further actions, set this to True

        returns the function object corresponding to the clicked button.
        """

        text = "<big>%s</big>" % text
        long_text = "<big>%s</big>" % long_text
        bitmask = reduce(lambda o, x: o | x, callbacks)
        button_style = """
        QPushButton {
            border: 1px solid #8f8f91;
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #f6f7fa, stop: 1 #dadbde);
            min-width: 60px;
            min-height: 40px;
            font-weight: bold;
        }

        QPushButton:pressed {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #dadbde, stop: 1 #f6f7fa);
        }

        QPushButton:flat {
            border: none;
        }

        QPushButton:default {
            border: 2px solid navy;
        }"""

        self.setIcon(icon)
        self.setWindowTitle(title)
        self.setText(text)
        self.setInformativeText(long_text)
        self.setDetailedText(detail_text)
        self.setStyleSheet(button_style)
        self.setStandardButtons(bitmask)

        if do_not_block:
            # Connect buttons to the appropriate callbacks in this case
            for btn, callback in callbacks.items():
                self.button(btn).clicked.connect(callback)
            return True

        return callbacks[self.exec()]

    def question(self, text, long_text, detail_text,
                 title, callbacks, do_not_block=False):
        #pylint: disable=too-many-arguments
        """
        Display a question message window

        arguments:
        - text          the short message
        - long_text     the long message
        - detail_text   the text to be shown in the optional text box
                        (None for none)
        - title         the window title
        - callbacks     dictionary: keys are one in:
                            MessageBox.Ok, MessageBox.Open, MessageBox.Save,
                            MessageBox.Cancel, MessageBox.Close,
                            MessageBox.Yes, MessageBox.No, MessageBox.Abort,
                            MessageBox.Retry, and MessageBox.Ignore
                        value is a user-defined function object
        - do_not_block  bool: By default, a QMessageBox blocks further
                        actions until the QMessageBox is closed. If you don't
                        want to block further actions, set this to True

        returns the function object corresponding to the clicked button.
        """
        return self._wrapper(text, long_text, detail_text, title,
                             self.Question, callbacks, do_not_block)

    def critical(self, text, long_text, detail_text,
                 title, callbacks, do_not_block=False):
        #pylint: disable=too-many-arguments
        """
        Display a critical error window

        arguments:
        - text          the short message
        - long_text     the long message
        - detail_text   the text to be shown in the optional text box
                        (None for none)
        - title         the window title
        - callbacks     dictionary: keys are one in:
                            MessageBox.Ok, MessageBox.Open, MessageBox.Save,
                            MessageBox.Cancel, MessageBox.Close,
                            MessageBox.Yes, MessageBox.No, MessageBox.Abort,
                            MessageBox.Retry, and MessageBox.Ignore
                        value is a user-defined function object
        - do_not_block  bool: By default, a QMessageBox blocks further
                        actions until the QMessageBox is closed. If you don't
                        want to block further actions, set this to True

        returns the function object corresponding to the clicked button.
        """

        text = "<font color='#ff0000'>%s</font>" % text
        return self._wrapper(text, long_text, detail_text, title,
                             self.Critical, callbacks, do_not_block)

    def warning(self, text, long_text, detail_text,
                title, callbacks, do_not_block=False):
        #pylint: disable=too-many-arguments
        """
        Display a warning message window

        arguments:
        - text          the short message
        - long_text     the long message
        - detail_text   the text to be shown in the optional text box
                        (None for none)
        - title         the window title
        - callbacks     dictionary: keys are one in:
                            MessageBox.Ok, MessageBox.Open, MessageBox.Save,
                            MessageBox.Cancel, MessageBox.Close,
                            MessageBox.Yes, MessageBox.No, MessageBox.Abort,
                            MessageBox.Retry, and MessageBox.Ignore
                        value is a user-defined function object
        - do_not_block  bool: By default, a QMessageBox blocks further
                        actions until the QMessageBox is closed. If you don't
                        want to block further actions, set this to True

        returns the function object corresponding to the clicked button.
        """

        return self._wrapper(text, long_text, detail_text, title,
                             self.Warning, callbacks, do_not_block)
