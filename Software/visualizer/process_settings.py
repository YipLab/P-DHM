from gui.main_window import Window

def process_dhm(window: Window, set_recon_signal, start_proc) -> None:
    """Preparatory UI actions for processing DHM"""
    window.progressBar.show()
    window.progressBar.setValue(0)
    window.progressBar.setMinimum(0)
    window.progressBar.setTextVisible(True)

    window.pushButton_start_pause.show()
    window.pushButton_start_pause.setText("Pause")
    window.pushButton_end_task.show()
    window.pushButton_start_pause.setEnabled(True)
    window.pushButton_end_task.setEnabled(True)

    _pds = window.sp_dict["process_dhm_Spoiler"]
    _ss = window.sp_dict["set_save_Spoiler"]
    _pds.pushButton_Confirm.setEnabled(False)

    if window.get_name() == "Inline" and _ss.checkBox_save_image.isChecked() == True and \
            _pds.comboBox_imgshow.currentText() == "Reconstructed Map":
        _pds.label_recon_pos.setEnabled(True)
        _pds.label_recon_total.setEnabled(True)
        _pds.spinBox_recon_pos.setEnabled(True)
        _pds.spinBox_recon_pos.setMinimum(1)
        _pds.spinBox_recon_pos.setMaximum(window.get_dhm().get_zstack_qty())
        _pds.spinBox_recon_pos.setValue(1)
        _pds.label_recon_total.setText(f"out of {window.get_dhm().get_zstack_qty()}")
        set_recon_signal()

    proc_start = window.get_dhm().get_range_start(); proc_end = window.get_dhm().get_range_end()
    window.progressBar.setMaximum(100)
    if window.get_dhm().get_block() == True:
        window.get_dhm().set_unblock()

    if proc_start == proc_end:
        window.text_info_show.setText(f"Processing hologram {proc_start+1} from Series...")
    else:
        window.text_info_show.setText(\
            f" Processing hologram from {proc_start+1} to {proc_end+1} in the Series...")
    start_proc()

def stop_processing_thread(window: Window, img_idx: int) -> bool:
    """Upon slot trigger (Stop QButton), stop or resume processing depending on program state"""
    if window.get_dhm().get_block() == False:
        window.get_dhm().set_block()
        window.pushButton_start_pause.setText("Resume")
        window.text_info_show.setText("Pausing process...")
        return False
    else:
        if window.get_dhm().get_block() == True:
            window.get_dhm().set_unblock()  
        window.pushButton_start_pause.setText("Pause")
        proc_end = window.get_dhm().get_range_end()
        window.text_info_show.setText(\
            f" Processing hologram from {img_idx+1} to {proc_end+1} from Series...")
        return True

def end_processing_thread(window: Window) -> None:
    """End processing by Blocking Running Call, Return to Set Saving Step"""
    window.get_dhm().set_block()
    window.text_info_show.setText("Processing Ending... Reset the saving range to start again.")
    window.pushButton_start_pause.hide()
    window.pushButton_end_task.hide()
    window.progressBar.hide()
    window.sp_dict["process_dhm_Spoiler"].close_spoiler()
    window.sp_dict["process_dhm_Spoiler"].toggleButton.setEnabled(False)
    window.sp_dict["set_save_Spoiler"].label_check.hide()
    window.sp_dict["set_save_Spoiler"].label_done_text.hide()
    window.sp_dict["process_dhm_Spoiler"].label_check.hide()
    window.sp_dict["process_dhm_Spoiler"].label_done_text.hide()
    window.sp_dict["process_dhm_Spoiler"].pushButton_Confirm.setEnabled(True)
    window.sp_dict["set_save_Spoiler"].open_spoiler()


def process_finished(window: Window) -> None:
    """GUI cleanups after processing is finished"""
    proc_start = window.get_dhm().get_range_start(); proc_end = window.get_dhm().get_range_end()
    window.sp_dict["process_dhm_Spoiler"].pushButton_Confirm.setEnabled(True)
    window.progressBar.setValue(0)
    window.progressBar.hide()
    window.pushButton_start_pause.hide()
    window.pushButton_end_task.hide()
    window.text_info_show.setText(\
            f" Finished exporting {proc_end-proc_start+1} images from Series.")