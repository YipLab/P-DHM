"""
  License: GPL
  All classes and bolierplates adapted and licensed from https://github.com/jvzonlab/OrganoidTracker/ 
"""

import traceback as _traceback
from dhm import UserError
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QWidget, QMessageBox
from typing import Tuple, List, Optional

def _window() -> QWidget:
    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, QMainWindow):
            return widget
    return QApplication.topLevelWidgets()[0]

def prompt_save_file(title: str, file_types: List[Tuple[str, str]], default_dir: str) -> Optional[str]:
    """Shows a prompt that asks the user to save a file. Example:

        prompt_save_file("Save as...", [("PNG file", "*.png"), ("JPEG file", "*.jpg")])

    If the user does not write a file extension, then the file extension will be added automatically.
    """
    file_types_str = ";;".join((name + "(" + extension + ")" for name, extension in file_types))
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    file_name, _ = QFileDialog.getSaveFileName(_window(), title, default_dir, file_types_str)
    if not file_name:
        return None
    return file_name

def prompt_load_file(title: str, file_types: List[Tuple[str, str]], default_dir: str) -> Optional[str]:
    """Shows a prompt that asks the user to open a file. Example:

        prompt_load_file("Choose an image", [("PNG file", "*.png"), ("JPEG file", "*.jpg")])

    Returns None if the user pressed Cancel. This function automatically adds an "All supported files" option.
    """
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    file_name, _ = QFileDialog.getOpenFileName(_window(), title, default_dir, _to_file_types_str(file_types))
    if not file_name:
        return None
    return file_name

def prompt_load_dir(title: str, default_dir: str) -> Optional[str]:
    """Shows a prompt that asks the user to open a file. Example:

        prompt_load_file("Choose an image", [("PNG file", "*.png"), ("JPEG file", "*.jpg")])

    Returns None if the user pressed Cancel. This function automatically adds an "All supported files" option.
    """
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    file_name = QFileDialog.getExistingDirectory(_window(), title, default_dir)
    if not file_name:
        return None
    return file_name

def prompt_load_multiple_files(title: str, file_types: List[Tuple[str, str]], default_dir: str) -> List[str]:
    """Shows a prompt that asks the user to open multiple files. Example:

        prompt_load_files("Choose images", [("PNG file", "*.png"), ("JPEG file", "*.jpg")])

    Returns an empty list if the user pressed Cancel. This function automatically adds an "All supported files" option.
    """
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    file_names, _ = QFileDialog.getOpenFileNames(_window(), title, default_dir, _to_file_types_str(file_types))
    if not file_names:
        return []
    return file_names

def _to_file_types_str(file_types: List[Tuple[str, str]]) -> str:
    if len(file_types) > 1:
        # Create option "All supported file types"
        extensions = set()
        for name, extension in file_types:
            extensions.add(extension)
        file_types = [("All supported file types", ";".join(extensions))] + file_types
    return ";;".join((name + "("+extension+ ")" for name, extension in file_types))

def popup_error(title: str, message: str):
    QMessageBox.critical(_window(), title, message, QMessageBox.Ok, QMessageBox.Ok)

def popup_exception(exception: BaseException):
    if isinstance(exception, UserError):
        popup_error(exception.title, exception.body)
        return
    _traceback.print_exception(type(exception), exception, exception.__traceback__)
    popup_error("Internal error", "An error occured.\n" + str(exception) + "\nSee console for technical details.")

def popup_message(title: str, message: str):
    QMessageBox.information(_window(), title, message, QMessageBox.Ok, QMessageBox.Ok)