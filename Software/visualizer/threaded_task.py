import os, time
from gui.dialog import popup_message
from typing import Optional, Any
from PyQt5.QtCore import pyqtSignal, QObject
from gui.gui_threading import Task
from gui.main_window import Window

class SigHelper(QObject):
    finished = pyqtSignal(bool)

class ImageTask(Task):
    """A Runnable Task Implementation with pyqtSignal integration"""

    def __init__(self, SigHelper) -> None:
        self._sig = SigHelper

    def compute(self) -> Optional[bool]:
        return 1

    def on_finished(self, result: Any) -> None:
        self._sig.finished.emit(result)

def isReadableFile(file_path) -> bool:
    """Verify if the specified file is readable"""
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

def isReadablePath(file_path) -> bool:
    """Verify if the specified path is readable"""
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

def process_dhm_thread(window:Window, proc_start: int, proc_end: int, connect_signal) -> None:
    """Spawn new thread for processing DHM images and saving the files.
        signals progressbar and display indeices, update canvas image"""
    holo_proc = window.get_dhm()

    class SigHelper(QObject):
        finished = pyqtSignal()
        idx = pyqtSignal(int)
        time = pyqtSignal(float)
        num = pyqtSignal(int)
        show = pyqtSignal()

    class ProcessDHMTask(ImageTask):
        def compute(self) -> Optional[Any]:
            for holo_num in range(proc_start,proc_end+1):
                if holo_proc.get_block() == True:
                    return holo_num
                t = time.time()
                f"image {holo_num}"
                if holo_proc.get_dhm_mode() == "Offaxis":
                    holo_proc.hologram_process(holo_num, False)
                else:
                    holo_proc.hologram_inline_process(holo_num, False)
                    diffract_dist = holo_proc.get_diffraction_dist()
                idx = int((holo_num-proc_start)/(proc_end-proc_start)*100) if proc_end>proc_start else 1.0
                if holo_proc.get_block() == False:
                    self._sig.time.emit(time.time()-t)
                self._sig.idx.emit(idx)
                self._sig.num.emit(holo_num)
                self._sig.show.emit()

            return holo_proc.get_save_path() if holo_proc.get_block() == False else holo_num

        def on_finished(self, result: Any) -> None:
            if holo_proc.get_block() == True:
                popup_message("Program Stopped", f"Program Stopped at image {result} of the queue.")
            else:
                self._sig.finished.emit()
                if holo_proc.get_save_flags() == (False, False, False, False):
                    popup_message("DHM Saved", f"Done! The movie is finished processing.")
                else:
                    popup_message("DHM Saved", f"Done! The movie is now saved at {result}.")

    signal = SigHelper()
    connect_signal(signal)
    img_task = ProcessDHMTask(signal)
    window.get_scheduler().add_task(img_task) 


def load_2d_image_series(window: Window, connect_signal) -> None:
    """Spawn new thread for loading a 2d series from directory.
    check for IO correctness, sort the filename strings, update canvas image"""

    read_path = window.sp_dict["load_img_Spoiler"].lineEdit_read_add.text()
    holo_load = window.get_dhm()
    filelist = []
   
    class FileSeriesTask(ImageTask):

        def compute(self) -> Optional[bool]:
            return isReadablePath(read_path)

        def on_finished(self, result: Any) -> None:
            """Load the filenames into the HoloGram Class HOLO_LIST"""
            # if directory not readable, return
            if not result:
                return
            window.text_info_show.setText(f"Loading DHM List...")
            for (_, _, filenames) in os.walk(read_path):
                filelist.extend(filenames)
                break
            holo_load.set_read_path(read_path)
            holo_load.HOLO_LIST.clear()
            for file in filelist:
                holo_load.HOLO_LIST.append(file) if file.lower().endswith(".tif")\
                or file.lower().endswith(".tiff") else file
            # if does not contain tiff files, return
            if len(holo_load.HOLO_LIST) == 0:
                window.text_info_show.setText(f"Please Navigate to directory containing hologram images...")
                return
            self._sig.finished.emit(result)

    signal = SigHelper()
    connect_signal(signal)
    file_io_task = FileSeriesTask(signal)
    window.get_scheduler().add_task(file_io_task)


def load_background(window: Window, connect_signal) -> None:
    """Spawn new thread for loading background image from the specified file path.
    check for IO correctness, load into HoloGram class, and update canvas image"""

    back_path = window.sp_dict["load_img_Spoiler"].lineEdit_local_read.text()
    holo_load = window.get_dhm()

    class FileIOTask(ImageTask):

        def compute(self) -> Optional[int]:
            if not isReadableFile(back_path):
                return -4 # return at an incomplete path
            if os.path.splitext(back_path)[1] != (".tiff" or ".tif"):
                return -3
            holo_load.set_back_path(back_path)
            return holo_load.set_background_img()

        def on_finished(self, result: Any) -> None:
            if result == 1:
                window.text_info_show.setText(f"Loading background from {back_path}...")
                self._sig.finished.emit(result)
            elif result == -1: 
                popup_message("File Reading Error", "The loaded file can not be identified as an image.")
            elif result == -2:
                popup_message("File Not Found", "The previously imported file is nolonger found in the directory.")
            elif result == -3:
                popup_message("File is not an image", f"Please select a .tiff of .tif file.")
            elif result == -4:
                ...

    signal = SigHelper()
    connect_signal(signal)
    file_io_task = FileIOTask(signal)
    window.get_scheduler().add_task(file_io_task)


def load_from_hololist(window: Window, holo_num: int, connect_signal) -> None:
    """Spawn new thread for loading one dhm image from HoloGram class 
    image list, then update canvas image"""

    window.text_info_show.setText(f"Loading Image {holo_num+1}...")
    holo_load = window.get_dhm()

    class LoadListTask(ImageTask):
        def compute(self) -> bool:
            return holo_load.load_hologram_img(holo_num)

        def on_finished(self, result: Any):
            if result == -1:
                popup_message("File Reading Error", "The loaded file can not be identified as an image.")
                return
            elif result == -2:
                popup_message("File Not Found", "The previously imported file is nolonger found in the directory.")
                return
            self._sig.finished.emit(result)

    signal = SigHelper()
    connect_signal(signal)
    img_task = LoadListTask(signal)
    window.get_scheduler().add_task(img_task)


def load_canvas_recon(window : Window, holo_num: int, connect_signal) -> None:
    """Load Reconstructed Images from Inline mode, then update the Canvas"""
    holo_load = window.get_dhm()
    if holo_num < holo_load.get_range_start() or holo_num > holo_load.get_range_end():
        window.text_info_show.setText(f"Reconstruction slice not computed at the distance specified.")
        return

    recon_num = window.sp_dict["process_dhm_Spoiler"].spinBox_recon_pos.value()-1
    window.text_info_show.setText(f"Loading Reconstruction Slice {recon_num+1}...")

    class LoadReconTask(ImageTask):

        def compute(self) -> Optional[bool]:
            return holo_load.load_reconstruction_img(holo_num, recon_num)

        def on_finished(self, result: Any):
            if result == -1:
                popup_message("File Reading Error", "The loaded file can not be identified as an image.")
                return
            elif result == -2:
                popup_message("File Not Found", "The previously imported file is nolonger found in the directory.")
                return
            self._sig.finished.emit(result)

    signal = SigHelper()
    img_task = LoadReconTask(signal)
    connect_signal(signal)
    window.get_scheduler().add_task(img_task)
    window.sp_dict["process_dhm_Spoiler"].pushButton_recon_peek.setEnabled(False)