"""
  License: GPL
  Top level classes and bolierplates licensed from https://github.com/jvzonlab/OrganoidTracker/ 
"""

from typing import Optional, Union, Dict, Any, List, Callable
import os.path
from matplotlib.backend_bases import MouseEvent
from matplotlib.figure import Figure, Axes

from dhm import UserError
from dhm.core import HoloGram
from gui.main_window import Window
from gui.gui_threading import Task

class Visualizer:
    """A complete application for visualization of an experiment"""
    _window: Window
    _fig: Figure
    _ax: Axes
    _axes: List[Axes]

    _img_idx_on_display = 0
    _img_types = {}
    _img_type_on_display = ""

    def __init__(self, window: Window):
        self._window = window
        self._fig = window.get_figure()

        subplots_config = self._get_subplots_config()
        self._fig.clear()
        self._fig.subplots(**subplots_config)
        self._axes = self._fig.axes
        self._ax = self._axes[0]
        
        self._img_type_on_display = "background"

    def _get_subplots_config(self) -> Dict[str, Any]:
        """Gets the configuration, passed to figure.subplots. Make sure to at least specify nrows and ncols."""
        return {
            "nrows": 1,
            "ncols": 1
        }

    def _dhm(self) -> HoloGram:
        try:
            return self._window.get_dhm()
        except UserError:
            return HoloGram()

    def _clear_axis(self):
        """Clears the axis, except that zoom settings are preserved"""
        for ax in self._axes:
            for image in ax.images:
                colorbar = image.colorbar
                if colorbar is not None:
                    colorbar.remove_connection()
            for text in self._fig.texts:
                text.remove_connection()

            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            ax.clear()
            if xlim[1] - xlim[0] > 2:
                # Only preserve scale if some sensible value was recorded
                ylim = [max(ylim), min(ylim)]  # Make sure y-axis is inverted
                ax.set_xlim(*xlim)
                ax.set_ylim(*ylim)
                ax.set_autoscale_on(False)

    def run_async(self, runnable: Callable[[], Any], result_handler: Callable[[Any], None]):
        """Creates a callable that runs the given runnable on a worker thread."""
        class MyTask(Task):
            def compute(self):
                return runnable()

            def on_finished(self, result: Any):
                result_handler(result)

        self._window.get_scheduler().add_task(MyTask())

    def draw_view(self):
        """Draws the view."""
        raise NotImplementedError()

    def refresh_data(self):
        """Redraws the view."""
        self.draw_view()

    def refresh_all(self):
        """Redraws the view after loading the images."""
        self.draw_view()

    def update_status(self, text: Union[str, bytes], redraw=True):
        """Updates the status of the window."""
        self._window.set_status(str(text))

    def _on_command(self, text: str) -> bool:
        return False

    def _on_mouse_click(self, event: MouseEvent):
        pass

    def _on_scroll(self, event: MouseEvent):
        """Called when scrolling. event.button will be "up" or "down"."""
        pass

    def _get_window_title(self) -> Optional[str]:
        """Called to query what the window title should be. This will be prefixed with the name of the program."""
        return None

    def get_extra_menu_options(self) -> Dict[str, Any]:
        return {}

    def _get_must_show_plugin_menus(self) -> bool:
        """Returns whether the plugin-added menu options must be shown in this visualizer."""
        return False

    def get_default_status(self) -> str:
        """Gets the status normally used when moving between time points or between different visualizers. Use
        update_status to set a special status."""
        return str(self.__doc__)

    def get_window(self) -> Window:
        return self._window

    def isReadableFile(self, file_path):
        try:
            if not os.path.isfile(file_path):
                return False
            elif not os.access(file_path, os.R_OK):
                return False
            else:
                return True
        except IOError as ex:
            print ("I/O error({0}): {1}".format(ex.errno, ex.strerror))
            return False
        except TypeError:
            return False

    def isReadablePath(self, file_path):
        try:
            if not os.path.exists(file_path):
                return False
            elif not os.access(file_path, os.R_OK):
                return False
            else:
                return True
        except IOError as ex:
            print ("I/O error({0}): {1}".format(ex.errno, ex.strerror))
            return False
        except TypeError:
            return False


__active_visualizer = None # Reference to prevent event handler from being garbage collected


def activate(visualizer: Visualizer) -> None:
    if visualizer.get_window().get_scheduler().has_active_tasks():
        raise UserError("Running a task", "Please wait until the current task has been finished before switching"
                                               " to another window.")
    global __active_visualizer

    __active_visualizer = visualizer
    __active_visualizer.refresh_all()

