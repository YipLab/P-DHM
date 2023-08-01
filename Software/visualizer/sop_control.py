from typing import Optional
from gui.main_window import Window
from gui.dialog import popup_message

def sop_check_param_set(window: Window) -> None:
    """When comfirm button is clicked, check for all parameters"""
    _param_set_confirm(window)
    window.sp_dict["load_img_Spoiler"].toggleButton.setEnabled(True)
    window.sp_dict["set_param_Spoiler"].spoiler_next_step.emit()
    _set_mode_specific_UI_elements(window)

def _param_set_confirm(window: Window) -> None:
    """Set the system params for the given DHM mode"""
    _sps = window.sp_dict["set_param_Spoiler"]
    window.get_dhm().set_sys_param(pixel_x=_sps.pixel_size.value(),
                        pixel_y=_sps.pixel_size.value(),
                        refractive_index=_sps.refractive_index.value(),
                        magnification=_sps.magnification.value(),
                        wavelength=_sps.wave_length.value())

    if window.get_name() == "Offaxis":
        window.get_dhm().set_filter_param(expansion=_sps.expansion.value(),
                        filter_type=_sps.comboBox_FilterType.currentText(),
                        filter_rate=_sps.SpinBox_rate.value(),
                        filter_quadrant=_sps.comboBox_quadrant.currentText())
        window.get_dhm().set_diffraction_dist(diff=_sps.SpinBox_diffract_dist.value())
    
    if window.get_name() == "Inline":
        window.get_dhm().set_recon_param(recstart=_sps.SpinBox_start_recon.value(),
                        recend=_sps.SpinBox_end_recon.value(),
                        zqty=_sps.spinBox_slice_qty.value())

def _set_mode_specific_UI_elements(window: Window) -> None:
    """ Since we are unable to set mode-specific spoiler setting in initialization
        We specify mode setting in a function triggered by callback """
    if window.get_name() == "Offaxis":
        _ss = window.sp_dict["set_save_Spoiler"]
        _ss.checkBox_height.setEnabled(False)
        _ss.checkBox_phase.setEnabled(False)
        _ss.checkBox_wrapped_phase.setEnabled(False)
        # _ss.checkBox_refocus_volume.setEnabled(False)
    if window.get_name() == "Inline":
        _pds = window.sp_dict["process_dhm_Spoiler"]
        _pds.label_recon_pos.setEnabled(False)
        _pds.label_recon_total.setEnabled(False)
        _pds.spinBox_recon_pos.setEnabled(False)
        _pds.pushButton_recon_peek.setEnabled(False)

def sop_check_load_img(window: Window) -> None:
    """When comfirm button is clicked, check for read path"""
    if window.get_dhm().get_read_path() == "" or window.get_dhm().get_backloaded == False:
        popup_message("Empty read path", f"Please set path to read images before proceeding.")
        window.sp_dict["load_img_Spoiler"].label_check.hide()
        window.sp_dict["load_img_Spoiler"].label_done_text.hide()
        window.sp_dict["load_img_Spoiler"].open_spoiler()
    else:
        window.sp_dict["set_roi_Spoiler"].toggleButton.setEnabled(True)
        window.sp_dict["load_img_Spoiler"].spoiler_next_step.emit()

def sop_check_set_roi(window: Window, list_empty: bool) -> None:
    """When comfirm button is clicked, check if ROI has been saved"""
    if window.sp_dict["set_roi_Spoiler"].checkBox_ROI_set.isChecked() and list_empty:
        popup_message("No ROI Set", f"Please set ROI or uncheck 'Edit ROI' before proceeding.")
        window.sp_dict["set_roi_Spoiler"].open_spoiler()
    else:
        window.sp_dict["set_save_Spoiler"].toggleButton.setEnabled(True)
        window.sp_dict["set_roi_Spoiler"].spoiler_next_step.emit()

def sop_check_set_save(window: Window) -> Optional[bool]:
    """When comfirm button is clicked or configuration import is triggered,
        check for valid saving address and saving parameters"""
    ss = window.sp_dict["set_save_Spoiler"]
    if ss.checkBox_save_image.isChecked() is True:
        if window.get_dhm().get_save_path() == "":
            popup_message("Empty save path", f"Please set path to save images before proceeding.")
            ss.label_check.hide()
            ss.label_done_text.hide()
            ss.open_spoiler()
            return False
        else:
            if window.get_name() == "Offaxis" and ss.checkBox_height.isChecked() == False and \
                    ss.checkBox_phase.isChecked() == False and ss.checkBox_wrapped_phase.isChecked() == False:
                popup_message("No Saving Selection", f"Please Select saving image type or uncheck 'Save images'.")
                ss.open_spoiler()
                return
            from visualizer.save_settings import set_save_options, set_save_dir
            set_save_options(window)
            set_save_dir(window)
            window.sp_dict["process_dhm_Spoiler"].toggleButton.setEnabled(True)
            ss.spoiler_next_step.emit()
            window.action_dump_config.setEnabled(True)
            return True
    else:
        window.get_dhm().set_save_flags(height_map=False, phase_map=False, wrapped_phase=False, refocused_volume=False)
        window.sp_dict["process_dhm_Spoiler"].toggleButton.setEnabled(True)
        window.sp_dict["set_save_Spoiler"].spoiler_next_step.emit()
        window.action_dump_config.setEnabled(True)