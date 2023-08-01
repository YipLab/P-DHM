from typing import Optional
from gui.main_window import Window

def config_spinbox(window: Window, total_img: int, load_config_true: bool) -> None:
    """Configure QSpinbox in set_save spoiler by the qty of images in the series"""
    window.spinBox_select_img.setMaximum(total_img)
    window.spinBox_select_img.setValue(1)

    _ss = window.sp_dict["set_save_Spoiler"]
    _ss.label_total_img.setText(f"out of {total_img}")
    _ss.label_total_img_2.setText(f"out of {total_img}")
    _ss.spinBox_range_from.setMaximum(total_img)
    # Changing the spinbox value to activates pyqtsignal for UI updates 
    if not load_config_true:
        _ss.spinBox_range_from.setValue(2)
        _ss.spinBox_range_from.setValue(1)
        _ss.spinBox_range_to.setMaximum(total_img)
        _ss.spinBox_range_to.setValue(total_img)
    else:
        _ss.spinBox_range_from.setEnabled(True)
        _ss.spinBox_range_to.setEnabled(True)
        _ss.spinBox_range_to.setMaximum(total_img)
    window.spinBox_select_img.setEnabled(True)

def signal_range_from(window: Window) -> None:
    """Upon slot trigger (peek from Qbutton), do save GUI tasks"""
    _ss = window.sp_dict["set_save_Spoiler"]
    _ss.spinBox_range_from.setEnabled(True)
    _ss.pushButton_peek_start.setEnabled(True)
    num = _ss.spinBox_range_from.value()-1
    window.get_dhm().set_range_start(num)

def signal_range_to(window: Window) -> None:
    """Upon slot trigger (peek to Qbutton), do save GUI tasks"""
    _ss = window.sp_dict["set_save_Spoiler"]
    _ss.spinBox_range_to.setEnabled(True)
    _ss.pushButton_peek_end.setEnabled(True)
    _ss.spinBox_range_to.setMinimum(_ss.spinBox_range_from.value())
    num = _ss.spinBox_range_to.value()-1
    window.get_dhm().set_range_end(num)

def save_enable(window: Window) -> None:
    """Upon slot trigger (save checkbox), Update GUI flags for saving"""
    _ss = window.sp_dict["set_save_Spoiler"]
    _pds = window.sp_dict["process_dhm_Spoiler"]

    if _ss.checkBox_save_image.isChecked():
        if window.get_name() == "Offaxis":
            _ss.checkBox_height.setEnabled(True)
            _ss.checkBox_phase.setEnabled(True)
            _ss.checkBox_wrapped_phase.setEnabled(True)
        _ss.pushButton_save_add.setEnabled(True)
        _ss.lineEdit_save_add.setEnabled(True)
    else:
        if window.get_name() == "Offaxis":
            _ss.checkBox_height.setEnabled(False)
            _ss.checkBox_phase.setEnabled(False)
            _ss.checkBox_wrapped_phase.setEnabled(False)
        if window.get_name() == "Inline":
            _pds.label_recon_pos.setEnabled(False)
            _pds.label_recon_total.setEnabled(False)
            _pds.spinBox_recon_pos.setEnabled(False)
            _pds.pushButton_recon_peek.setEnabled(False)
        _ss.pushButton_save_add.setEnabled(False)
        _ss.lineEdit_save_add.setEnabled(False)
    return

def set_save_options(window: Window) -> None:
    """Upon slot trigger, set HoloGram class save flags"""
    _ss = window.sp_dict["set_save_Spoiler"]
    if window.get_name() == "Offaxis":
        window.get_dhm().set_save_flags(height_map=_ss.checkBox_height.isChecked(),
                            phase_map=_ss.checkBox_phase.isChecked(),
                            wrapped_phase=_ss.checkBox_wrapped_phase.isChecked(),
                            refocused_volume=False)
    else:
        window.get_dhm().set_save_flags(height_map= False, phase_map=False, wrapped_phase=False,
                            refocused_volume=_ss.checkBox_save_image.isChecked())

def set_save_dir(window: Window) -> None:
    """Check Save Path validity, set save option based on imaging mode for configuration loading"""
    from visualizer.threaded_task import isReadablePath, SigHelper, ImageTask
    _ss = window.sp_dict["set_save_Spoiler"]
    save_path = _ss.lineEdit_save_add.text()
    _ss.spinBox_range_from.setValue(window.get_dhm().get_range_start()+1)
    _ss.spinBox_range_to.setValue(window.get_dhm().get_range_end()+1)

    h_map, p_map, warp_ph, inl_sv = window.get_dhm().get_save_flags()
    if window.get_name() == "Offaxis":
        _tenery_save_t = (h_map == True or p_map == True or warp_ph == True)
        _ss.checkBox_save_image.setChecked(True) if _tenery_save_t else _ss.checkBox_save_image.setChecked(False)
        _ss.checkBox_height.setChecked(True) if h_map == True else _ss.checkBox_height.setChecked(False)
        _ss.checkBox_phase.setChecked(True) if p_map == True else _ss.checkBox_height.setChecked(False)
        _ss.checkBox_wrapped_phase.setChecked(True) if warp_ph == True else _ss.checkBox_height.setChecked(False)   
    if window.get_name() == "Inline":
        if inl_sv == True:
            _ss.checkBox_save_image.setChecked(True) if inl_sv == True else _ss.checkBox_save_image.setChecked(False)

    def set_dhm_save_path(cond : bool):
        if cond == True:
            window.get_dhm().set_save_path(save_path)

    class SetSaveTask(ImageTask):
        def compute(self) -> Optional[bool]:
            return isReadablePath(save_path)

    signal = SigHelper()
    file_io_task = SetSaveTask(signal)
    signal.finished.connect(set_dhm_save_path)
    window.get_scheduler().add_task(file_io_task)