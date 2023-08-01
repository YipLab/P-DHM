import os
from gui.dialog import popup_message
from typing import Optional
from gui.main_window import Window
from visualizer.threaded_task import ImageTask, SigHelper, isReadableFile

def load_config(window: Window) -> None:
    """ Configuration Receipt loading"""
    config_path = window.config_read_address
    
    def load_config_success(cond : bool):
        """Upon loading success, load GUI params and all images"""
        if cond == True:
            if os.path.splitext(config_path)[1] != ".ini":
                popup_message("File is not a config file", f"Please select a .ini file.")
                return
            if window.get_dhm().get_config_path() == config_path:
                window.text_info_show.setText(f"Config Receipt Unchanged.")
                return
            window.get_dhm().read_config_receipt(config_path)
            window.text_info_show.setText(f"Config Receipt Loaded.")

            #load Params onto the GUI
            _sps = window.sp_dict["set_param_Spoiler"]
            pixel_x, _, ref_idx, mag, wvlen = window.get_dhm().get_sys_param()
            start, end, z_qty = window.get_dhm().get_recon_param()
            _sps.pixel_size.setValue(pixel_x)
            _sps.refractive_index.setValue(ref_idx)
            _sps.magnification.setValue(mag)
            _sps.wave_length.setValue(wvlen*1000)

            if window.get_name() == "Offaxis":
                f_type, f_rate, f_quad, apd_size = window.get_dhm().get_filter_param()
                _sps.comboBox_FilterType.setCurrentText(f_type)
                _sps.expansion.setValue(apd_size)
                _sps.SpinBox_rate.setValue(int(f_rate*100))
                _sps.comboBox_quadrant.setCurrentText(f_quad)
                _sps.SpinBox_diffract_dist.setValue(window.get_dhm().get_diffraction_dist())

            if window.get_name() == "Inline":
                _sps.SpinBox_start_recon.setValue(start)
                _sps.SpinBox_end_recon.setValue(end)
                _sps.spinBox_slice_qty.setValue(z_qty)
            
            #load all read and save paths onto the GUI
            _pds = window.sp_dict["process_dhm_Spoiler"]
            _ss = window.sp_dict["set_save_Spoiler"]
            _pds.close_spoiler()
            _ss.close_spoiler()
            _ss.label_check.hide()
            _ss.label_done_text.hide()
            _pds.label_check.hide()
            _pds.label_done_text.hide()
            _pds.toggleButton.setEnabled(False)
            _ss.toggleButton.setEnabled(False)
            _sps.open_spoiler()
            _sps.pushButton_Confirm.click()

            # Load one of the two source targets first to avoid thread mutex contention
            # then load the other following the first
            if window.get_dhm().get_back_path() != "":
                window.sp_dict["load_img_Spoiler"].lineEdit_local_read.setText(window.get_dhm().get_back_path())
            elif window.get_dhm().get_back_path() != "":
                window.sp_dict["load_img_Spoiler"].lineEdit_read_add.setText(window.get_dhm().get_read_path())
            window.sp_dict["load_img_Spoiler"].pushButton_Confirm.click()

    class ConfigTask(ImageTask):
        def compute(self) -> Optional[bool]:
            return isReadableFile(config_path)

    signal = SigHelper()
    file_io_task = ConfigTask(signal)
    signal.finished.connect(load_config_success)
    window.get_scheduler().add_task(file_io_task)

def dump_config(window: Window) -> None:
    """ Configuration Receipt dumping"""
    config_path = window.config_save_address
    if os.path.splitext(config_path)[1] != ".ini":
        popup_message("File is not a config file", f"Please specify a .ini file.")
        return
    window.get_dhm()._dump_config_receipt(config_path)
    window.text_info_show.setText(f"Config Receipt Saved!")