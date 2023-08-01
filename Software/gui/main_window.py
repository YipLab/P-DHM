import os, sys
from typing import Any, Optional, Tuple

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QSpacerItem, QSizePolicy
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase, QIcon
from gui.spoiler_widgets import Spoiler

from gui import APP_NAME
from gui.gui_threading import Scheduler
import gui.dialog as dialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from dhm.core import HoloGram

from pathlib import Path
source_path = Path(__file__).resolve()
source_dir = source_path.parent

class Launcher(QMainWindow):
    """Lanuncher gives Application info as well as mode options for DHM"""
    launch_type = pyqtSignal(str)
    window_show = pyqtSignal()

    def __init__(self) -> None:
        super(Launcher, self).__init__()  # Call the inherited classes __init__ method
        uic.loadUi(f'{source_dir}/ui_files/launcher_window.ui', self)  # Load the .ui file

        self.off_axis_TDHM.clicked.connect(self._launch_tdhm_std)
        self.in_line_TDHM.clicked.connect(self._launch_in_line)
    
    def _launch_tdhm_std(self) -> None:
        self.hide()
        self.window_show.emit(); self.launch_type.emit("Offaxis")
    
    def _launch_in_line(self) -> None:
        self.hide()
        self.window_show.emit(); self.launch_type.emit("Inline")


class Window (QMainWindow):
    """The bases for the Main Window class"""
    plt.rcParams['svg.fonttype'] = 'none'
    plt.rcParams["font.family"] = "Helvetica, sans-serif"
    plt.rcParams["xtick.direction"] = "in"
    plt.rcParams["ytick.direction"] = "in"

    __scheduler: Optional[Scheduler] = None
    
    _dhm = HoloGram()
    _sp_list = []
    _name = ""
     
    sp_dict = {}
   
    def __init__(self) -> None:
        super(Window, self).__init__()
        uic.loadUi(f'{source_dir}/ui_files/main_window.ui', self)  # Load the .ui file

        self.text_info_show.setText("")
        self.setWindowTitle(APP_NAME)
        self.setBaseSize(1280, 800)
        self.img_canvas = FigureCanvas(plt.Figure())
        self.img_canvas.minimumWidth = 800
        self.img_canvas.minimumHeight = 600
        self.bar_layout.addWidget(NavigationToolbar(self.img_canvas, self))
        self.figure_layout.addWidget(self.img_canvas)
        self.image_figure = self.img_canvas.figure.subplots()
        # Maximize Canvas size on the GUI
        # self.set_figure_size(width = 8, height = 6)
        self.img_canvas.figure.subplots_adjust(left=0.052, bottom=0.056, right=0.957, top=0.966)
        self.image_figure_ax = self.img_canvas.figure.gca()

        self.progressBar.hide()
        self.pushButton_end_task.hide()
        self.pushButton_start_pause.hide()

        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        self.spinBox_select_img.setEnabled(False)
        self.pushButton_view_img.setEnabled(False)

    def get_canvas(self) -> FigureCanvas:
        return self.img_canvas

    def get_figure(self) -> Any:
        return self.img_canvas.figure
    
    def set_figure_size(self, width, height)-> None:
        self.img_canvas.figure.set_size_inches(width, height)

    def get_dhm(self) -> HoloGram:
        return self._dhm

    def get_name(self) -> str:
        return self._name
    
    def get_scheduler(self) -> Scheduler:
        """Get scheduler for threaded Tasks"""
        if self.__scheduler is None:
            self.__scheduler = Scheduler()
            self.__scheduler.daemon = True
            self.__scheduler.start()
        return self.__scheduler

    def _del_spoiler_list(self) -> None:
        """Deleting the spoilers from the spoiler loader list"""
        for idx, item in enumerate(self._sp_list):
            del self.sp_dict[type(item).__name__]
            del self._sp_list[idx]
        self._sp_list = []
        self.sp_dict = {}

    def _gen_spoiler_list(self, mode_type : str) -> None:
        """Generating the spoiler loader list for insertion into the dictionary. 
        Lists of spoilers for the various DHM modes are perserved and are able to be modified. 
        A dictionary loader instantiates the spoilers into a list. Some Spoilers such as the load_image can be reused. 
        Control of the SAME TYPE spoiler in different modes are handled by the visualizer class"""

        gen_list = {
            "Offaxis": [0, 2, 3, 4, 6],
            "Inline" : [1, 2, 3, 5, 7]
        }

        def set_param():
            return set_param_Spoiler(ui_path =f'{source_dir}/ui_files/spoiler_set_param_widget.ui')
        def set_param_inline():
            return set_param_Spoiler(ui_path =f'{source_dir}/ui_files/spoiler_set_param_inline_widget.ui')
        def load_img():
            return load_img_Spoiler(ui_path =f'{source_dir}/ui_files/spoiler_load_img_widget.ui')
        def set_roi():
            return set_roi_Spoiler(ui_path =f'{source_dir}/ui_files/spoiler_set_roi_widget.ui')
        def set_save():
            return set_save_Spoiler(ui_path =f'{source_dir}/ui_files/spoiler_set_save_widget.ui')
        def set_save_inline():
            return set_save_Spoiler(ui_path =f'{source_dir}/ui_files/spoiler_set_save_inline_widget.ui')
        def process_dhm():
            return process_dhm_Spoiler(ui_path =f'{source_dir}/ui_files/spoiler_process_dhm_widget.ui')
        def process_dhm_inline():
            return process_dhm_Spoiler(ui_path =f'{source_dir}/ui_files/spoiler_process_dhm_inline_widget.ui')
        
        gen_list_loader = {
            0: set_param,
            1: set_param_inline,
            2: load_img,
            3: set_roi,
            4: set_save,
            5: set_save_inline,
            6: process_dhm,
            7: process_dhm_inline
        }
        
        spoiler = None
        for proc_step in gen_list[mode_type]:
            spoiler = gen_list_loader[proc_step]()
            self._sp_list.append(spoiler)

    def gen_window_spoilers(self, mode_type : str) -> None:
        """Generating the spoiler dictionary from the list for access from the visualizer class.
        Connecting the 'go to next' signals. Add Spacers for UI consistency purpose"""
        self._gen_spoiler_list(mode_type)

        self.vbox.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        for idx, sp in enumerate(self._sp_list):
            self.sp_dict[type(sp).__name__] = self._sp_list[idx]
            if idx < len(self._sp_list) - 1:
                self._sp_list[idx].spoiler_next_step.connect(self._sp_list[idx + 1].open_spoiler)

            self.vbox.addWidget(self._sp_list[idx])
            self.vbox.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

class MainWindowStd(Window):
    relink_all = pyqtSignal()
    load_config = pyqtSignal()
    dump_config = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

    def _init_ui(self, window_name: str) -> None:
        """Set name, generating spoiler dictionary, linking signals"""
        self._name = window_name
        self._dhm.set_dhm_mode(self._name)
        self.gen_window_spoilers(self._name)
        self.relink_all.emit()
        self.action_off_axis.triggered.connect(self._name_tdhm_std)
        self.action_in_line.triggered.connect(self._name_in_line)
        self.action_load_config.triggered.connect(self._prompt_load_config)
        self.action_dump_config.setEnabled(False)
        self.action_dump_config.triggered.connect(self._prompt_dump_config)
        self._change_label()
        self._set_window_font(sys.platform)

    def _change_mode(self) -> None:
        """Change mode by instantiating a new HoloGram(), safely deleating all spoilers
        generating the new spoiler dictionary and relink all the pyqt signals"""
        self._dhm = HoloGram()
        self._dhm.set_dhm_mode(self._name)
        for i in reversed(range(self.vbox.count())): 
            item = self.vbox.itemAt(i)
            self.vbox.removeItem(item)
            if item.widget():
                item.widget().deleteLater()
        self._del_spoiler_list()
        self.gen_window_spoilers(self._name)
        self.relink_all.emit()
        self._change_label()
    
    def _change_label(self) -> None:
        """Reset Main window labelings and actions"""
        if self._name == "Offaxis":
            self.label_current_receipt.setText("Off-axis TDHM - Local Imaging")
            self.action_off_axis.setEnabled(False)
            self.action_in_line.setEnabled(True)
        else:
            self.label_current_receipt.setText("In-line TDHM - Local Imaging")
            self.action_off_axis.setEnabled(True)
            self.action_in_line.setEnabled(False)
    
    def _name_tdhm_std(self) -> None:
        """callback func for converting to offaxis mode"""
        self._name = "Offaxis"
        self._change_mode()

    def _name_in_line(self) -> None:
        """callback func for converting to inline mode"""
        self._name = "Inline"
        self._change_mode()

    def _prompt_load_config(self) -> None:
        """File Dialog-promping signal for loading configurations"""
        self.config_read_address = dialog.prompt_load_file("Select the configuration receipt", [
            (".ini configuration file", "*.ini")], default_dir=f"{source_dir}/../") if not None else ''
        self.load_config.emit()

    def _prompt_dump_config(self) -> None:
        """File Dialog-promping signal for dumping configurations"""
        self.config_save_address = dialog.prompt_save_file("Select the directory to save configuration receipt", [
            (".ini configuration file", "*.ini")], default_dir=f"{source_dir}/../") if not None else ''
        self.dump_config.emit()

    def _set_window_font(self, __sys) -> None:
        """Set Main Window Fonts sizes not covered in the application font for OSes"""
        font_name = ('Segoe UI' if __sys == 'win32' else 
                    'Lato' if __sys == 'linux' else 
                    'Helvetica Neue' if __sys == 'darwin' else 'Helvetica')
        self.label_current_receipt.setFont(QFont(font_name, 18 if __sys == 'darwin' else 15, 300))
        self.text_info_show.setFont(QFont(font_name, 13 if __sys == 'darwin' else 10, 300))
        self.pushButton_view_img.setFont(QFont(font_name, 13 if __sys == 'darwin' else 11, 300))
        self.spinBox_select_img.setFont(QFont(font_name, 13 if __sys == 'darwin' else 11, 300))
        self.pushButton_start_pause.setFont(QFont(font_name, 13 if __sys == 'darwin' else 11, 300))
        self.pushButton_end_task.setFont(QFont(font_name, 13 if __sys == 'darwin' else 11, 300))

class set_param_Spoiler(Spoiler):
    def __init__(self, parent=None, ui_path = '', animationDuration=300):
        super(set_param_Spoiler, self).__init__(parent=parent, ui_path = ui_path, animationDuration=animationDuration)
        self.toggleButton.setEnabled(True)
        self.pushButton_Confirm.clicked.connect(self.toggleButton.click)

class load_img_Spoiler(Spoiler):
    def __init__(self, parent=None, ui_path = '', animationDuration=300):
        super(load_img_Spoiler, self).__init__(parent=parent, ui_path = ui_path, animationDuration=animationDuration)
        self.pushButton_Confirm.clicked.connect(self.toggleButton.click)

        self.read_path = ''
        self.background_read_address = ''
        self.pushButton_read_add.clicked.connect(self.add_holo_read)
        self.pushButton_background_read.clicked.connect(self.background_read)

    def background_read(self) -> None:
        self.background_read_address = dialog.prompt_load_file("Select the background image",
                [("Single TIF or TIF series", "*.tif*")], 
                default_dir=f"{source_dir}/../sample_images/background/") if not None else ''
        self.lineEdit_local_read.setText(self.background_read_address)

    def add_holo_read(self) -> None:
        self.read_path = dialog.prompt_load_dir("Select the directory to hologram(s)", 
                        default_dir=f"{source_dir}/../sample_images/images/") if not None else ''
        self.lineEdit_read_add.setText(self.read_path)

class set_roi_Spoiler(Spoiler):
    def __init__(self, parent=None, ui_path = '', animationDuration=300):
        super(set_roi_Spoiler, self).__init__(parent=parent, ui_path = ui_path, animationDuration=animationDuration)
        self.pushButton_Confirm.clicked.connect(self.toggleButton.click)

        self.pushButton_add_new_roi.setEnabled(False)
        self.pushButton_discard_last_roi.setEnabled(False)
        self.label_current_roi.setEnabled(False)

class set_save_Spoiler(Spoiler):
    def __init__(self, parent=None, ui_path = '', animationDuration=300):
        super(set_save_Spoiler, self).__init__(parent=parent, ui_path = ui_path, animationDuration=animationDuration)
        self.pushButton_Confirm.clicked.connect(self.toggleButton.click)
        self.save_path = ''
        self.background_save_address = ''
        self.spinBox_range_from.setEnabled(False)
        self.spinBox_range_to.setEnabled(False)
        self.pushButton_peek_start.setEnabled(False)
        self.pushButton_peek_end.setEnabled(False)

        self.pushButton_save_add.clicked.connect(self.add_holo_save)
        self.pushButton_save_add.setEnabled(False)
        self.lineEdit_save_add.setEnabled(False)

    def add_holo_save(self) -> None:
        self.save_path = dialog.prompt_load_dir("Select the directory to hologram(s)", 
                default_dir=f"{source_dir}/../sample_images/result/") if not None else ''
        self.lineEdit_save_add.setText(self.save_path) 

class process_dhm_Spoiler(Spoiler):
    def __init__(self, parent=None, ui_path = '', animationDuration=300):
        super(process_dhm_Spoiler, self).__init__(parent=parent, ui_path = ui_path, animationDuration=animationDuration)

def init_font(self) -> None:
    """Set Application-wide font scaling and type for the OSes"""
    self.fonts = [QFontDatabase.addApplicationFont(':/fonts/Helvetica.ttf'),
                QFontDatabase.addApplicationFont(':/fonts/Lato.ttf')]
    font_name = ('Trebuchet MS' if sys.platform == 'win32' else 
                'Lato' if sys.platform == 'linux' else 
                'Helvetica Neue' if sys.platform == 'darwin' else 'Helvetica')
    QApplication.setFont(QFont(font_name, 13 if sys.platform == 'darwin' else 10, 300))

def start_ui() -> Tuple[Launcher, Window]:
    """Instantiate the application, the lancher and the main window and some system parameters in addition"""
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    root = QApplication.instance()
    if not root:
        root = QApplication(sys.argv)

    root.setWindowIcon(QIcon(f'{source_dir}/icons/icon.png'))
    root.setApplicationName(APP_NAME)

    launcher = Launcher()
    init_font(launcher)
    main_window = MainWindowStd()
    launcher.window_show.connect(main_window.show)
    launcher.launch_type.connect(main_window._init_ui)
    launcher.show()

    return launcher, main_window

def mainloop() -> None:
    """Starts the main loop."""
    sys.exit(QApplication.instance().exec_())