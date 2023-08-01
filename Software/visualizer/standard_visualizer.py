from abc import abstractmethod
from gui.main_window import start_ui
from visualizer import activate, config_receipt, sop_control, save_settings, process_settings, threaded_task
from visualizer.abstract_visualizer import AbstractImageVisualizer
import re, datetime
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt

def show() -> None:
    """Creates a standard visualizer for an experiment."""
    launcher, window = start_ui()
    visualizer = StandardImageVisualizer(window)
    activate(visualizer)

class StandardImageVisualizer(AbstractImageVisualizer):
    """Containing all callback controls and as driver to dhm class methods"""

    def _link_sp_signals(self) -> None:
        """linking all pyqtsignals for spoilers at program start
        or at mode switch, and reset visualizer flags"""
        
        self.ROI_LIST.clear()
        self._current_viewer_event = "set_param"
        self._img_type_on_display = "hologram"
        self.load_canvas()
        self._window.text_info_show.setText("")
        self._window.action_dump_config.setEnabled(False)
        self._draw_all_roi()

        self._window.sp_dict["set_param_Spoiler"].pushButton_Confirm.clicked.connect(self._sop_check_param_set)

        self._window.sp_dict["load_img_Spoiler"].lineEdit_local_read.textChanged.connect(self._load_background)
        self._window.sp_dict["load_img_Spoiler"].lineEdit_read_add.textChanged.connect(self._load_2d_image_series)
        self._window.sp_dict["load_img_Spoiler"].pushButton_Confirm.clicked.connect(self._sop_check_load_img)
        
        self._window.sp_dict["set_roi_Spoiler"].checkBox_ROI_set.stateChanged.connect(self._roi_set)
        self._window.sp_dict["set_roi_Spoiler"].pushButton_add_new_roi.clicked.connect(self._roi_set_add_new)
        self._window.sp_dict["set_roi_Spoiler"].pushButton_discard_last_roi.clicked.connect(self._roi_set_discard_last)
        self._window.sp_dict["set_roi_Spoiler"].pushButton_Confirm.clicked.connect(self._sop_check_set_roi)

        self._window.sp_dict["set_save_Spoiler"].checkBox_save_image.stateChanged.connect(self._save_enable)
        self._window.sp_dict["set_save_Spoiler"].spinBox_range_from.textChanged.connect(self._signal_range_from)
        self._window.sp_dict["set_save_Spoiler"].spinBox_range_to.textChanged.connect(self._signal_range_to)
        self._window.sp_dict["set_save_Spoiler"].lineEdit_save_add.textChanged.connect(self._set_save_dir)
        self._window.sp_dict["set_save_Spoiler"].pushButton_Confirm.clicked.connect(self._sop_check_set_save)

        self._window.sp_dict["process_dhm_Spoiler"].pushButton_Confirm.clicked.connect(self._process_dhm)
        self._window.sp_dict["process_dhm_Spoiler"].pushButton_ImgSave.clicked.connect(self._save_live_view)
        self._window.sp_dict["process_dhm_Spoiler"].comboBox_imgshow.currentIndexChanged.connect(self._select_img_type)

    #################################################
    # Configuration File Operation Callbacks        #
    #################################################
    @abstractmethod
    def _load_config(self) -> None:
        """ Configuration Receipt loading,
            change Viewer event to load_config"""
        self._current_viewer_event = "load_config"
        config_receipt.load_config(self._window)

    @abstractmethod
    def _dump_config(self) -> None:
        """ Configuration Receipt dumping"""
        config_receipt.dump_config(self._window)

    ##################################################
    # Standard Operation Procedure Control Callbacks #
    ##################################################
    def _sop_check_param_set(self) -> None:
        """When comfirm button is clicked, check for all parameters"""
        sop_control.sop_check_param_set(self._window)

    def _sop_check_load_img(self) -> None:
        """When comfirm button is clicked, check for read path"""
        sop_control.sop_check_load_img(self._window)

    def _sop_check_set_roi(self) -> None:
        """When comfirm button is clicked, check if ROI has been saved"""
        sop_control.sop_check_set_roi(self._window, self.ROI_LIST == [])

    def _sop_check_set_save(self) -> None:
        """When comfirm button is clicked or configuration import is triggered,
            check for saving parameters and if saving address exist"""
        ret = sop_control.sop_check_set_save(self._window)
        if ret is not True:
            self._current_viewer_event = ""

    ####################################################################
    # ROI Setting Callbacks                                            #
    # (Threading and Abstraction to be implemented in future releases) #
    ####################################################################

    def _roi_set(self) -> None:
        """ Set ROI using Graphical RectangleSelector by matplotlib
        The range selector is adapted under GPL license from Matplotlib official documentation at:
        https://matplotlib.org/3.4.0/gallery/widgets/rectangle_selector.html """
        
        if self._dhm().config_loaded() is True:
            self._window.sp_dict["set_save_Spoiler"].lineEdit_save_add.setText(self._dhm().get_save_path())
        self._current_viewer_event = "set_roi"
        self._img_type_on_display = "hologram"
        self.load_canvas()
        
        _srs = self._window.sp_dict["set_roi_Spoiler"]
        self._roi_current = [0,0,0,0]

        def roi_set_line_select_callback(eclick, erelease) -> None:
            x0, y0 = int(eclick.xdata), int(eclick.ydata)
            x1, y1 = int(erelease.xdata), int(erelease.ydata)
            self._window.text_info_show.setText(f'New ROI at [{x0}, {y0}, {x1}, {y1}]. ' +
            'Click "Save Current ROI" in "Step 3" menu to save it.')
            self._roi_current = [x0, y0, x1, y1]
            
        def roi_rec_selector(event) -> None:
            ...
        
        roi_rec_selector.rs = RectangleSelector(self._ax, roi_set_line_select_callback,
            useblit=True, button=[1, 3], minspanx=5, minspany=5, spancoords='pixels', interactive=True)

        if _srs.checkBox_ROI_set.isChecked():
            self._window.text_info_show.setText(f"ROI Edit Mode Enabled...")
            _srs.pushButton_add_new_roi.setEnabled(True)
            _srs.pushButton_discard_last_roi.setEnabled(True)
            _srs.label_current_roi.setEnabled(True)
        else:
            _srs.pushButton_add_new_roi.setEnabled(False)
            _srs.pushButton_discard_last_roi.setEnabled(False)
            _srs.label_current_roi.setEnabled(False)
            return

        plt.connect('key_press_event', roi_rec_selector)
        self._window.text_info_show.setText(f"Click and Drag on the Image Canvas to select ROI...")
        self._window.sp_dict["set_roi_Spoiler"].label_current_roi.setEnabled(False)
        self._window.sp_dict["set_roi_Spoiler"].label_current_roi.setText("")
        self._draw_all_roi()

    def _roi_set_add_new(self) -> None:
        """Add ROI (as of current only support one ROI)"""
        if self._roi_current == [0,0,0,0]:
            return
        x0 = self._roi_current[0]; y0 = self._roi_current[1] 
        x1 = self._roi_current[2]; y1 = self._roi_current[3]
        self._window.text_info_show.setText(f"ROI Saved at [{x0},{y0},{x1},{y1}].")
        if len(self.ROI_LIST) == 0:
            self.ROI_LIST.append(self._roi_current)
        self._dhm().set_roi_by_param(y0, y1, x0, x1)
        self._dhm().set_roi_enable()
        self._roi_current = [0,0,0,0]
        self._window.sp_dict["set_roi_Spoiler"].label_current_roi.setEnabled(True)
        self._window.sp_dict["set_roi_Spoiler"].label_current_roi.setText(self.__gen_roi_label())
        self.draw_view()
        self._draw_all_roi()

    def _roi_set_discard_last(self) -> None:
        """Remove Last ROI (as of current only support one ROI)"""
        if len(self.ROI_LIST) > 0:
            self.ROI_LIST.pop()
        if len(self.ROI_LIST) == 0:
            self._dhm().set_roi_disable()
        self._window.sp_dict["set_roi_Spoiler"].label_current_roi.setText(self.__gen_roi_label())
        self._window.text_info_show.setText("Last ROI Removed")
        self._img_type_on_display = "hologram"
        self.load_canvas()

    def __gen_roi_label(self) -> str:
        """Generate ROI Label"""
        roip = ''
        for _, roi in enumerate(self.ROI_LIST):
            roip += f"ROI: {roi}\n" 
        return roip

    ##################################################
    # Save Setting Callbacks                         #
    ##################################################

    def _signal_range_from(self) -> None:
        """Upon slot trigger (peek from Spinbix), do save GUI tasks"""
        save_settings.signal_range_from(self._window)
        self._window.sp_dict["set_save_Spoiler"].pushButton_peek_start.clicked.connect(
                                                        self._update_canvas_range_start)
        
    def _signal_range_to(self) -> None:
        """Upon slot trigger (peek to Spinbox), do save GUI tasks"""
        save_settings.signal_range_to(self._window)
        self._window.sp_dict["set_save_Spoiler"].pushButton_peek_end.clicked.connect(
                                                        self._update_canvas_range_end)

    def _update_canvas_range_start(self) -> None:
        """Upon slot trigger (peek from Qbutton), load from image list and draw ROI"""
        holo_num = self._window.sp_dict["set_save_Spoiler"].spinBox_range_from.value()-1
        self._load_from_hololist(holo_num)
        self._dhm().set_range_start(holo_num)
        self._draw_all_roi()
        self._window.sp_dict["set_save_Spoiler"].pushButton_peek_start.setEnabled(False)

    def _update_canvas_range_end(self) -> None:
        """Upon slot trigger (peek to Qbutton), load from image list and draw ROI"""
        holo_num = self._window.sp_dict["set_save_Spoiler"].spinBox_range_to.value()-1
        self._load_from_hololist(holo_num)
        self._dhm().set_range_end(holo_num)
        self._draw_all_roi()
        self._window.sp_dict["set_save_Spoiler"].pushButton_peek_end.setEnabled(False)

    def _save_enable(self) -> None:
        """Upon slot trigger (save checkbox), Update GUI flags for saving"""
        if self._current_viewer_event != "load_config":
            self._current_viewer_event = "set_saving"
        save_settings.save_enable(self._window)

    def _set_save_dir(self) -> None:
        """Upon slot trigger (save lineEdit), check for valid saving address"""
        save_settings.set_save_dir(self._window)

    ##################################################
    # DHM Processing Callback                        #
    ##################################################

    def _process_dhm(self) -> None:
        """Upon slot trigger (Start Processing QButton), start processing images"""
        def set_recon_signal() -> None:
            pds = self._window.sp_dict["process_dhm_Spoiler"]
            pds.spinBox_recon_pos.textChanged.connect(self._signal_recon_to)

        def start_proc() -> None:
            self._estimate_proc_time(10.0)
            proc_start = self._dhm().get_range_start(); proc_end = self._dhm().get_range_end()
            self._img_idx_on_display = proc_start
            self._process_dhm_thread(proc_start, proc_end)

        self._current_viewer_event = "processing"
        self._window.pushButton_start_pause.clicked.connect(self._stop_processing_thread)
        self._window.pushButton_end_task.clicked.connect(self._end_processing_thread)
        process_settings.process_dhm(self._window, set_recon_signal, start_proc)

    def _stop_processing_thread(self) -> None:
        """Upon slot trigger (Stop QButton), stop or resume processing depending on program state"""
        ret = process_settings.stop_processing_thread(self._window, self._img_idx_on_display)
        if ret is True:
            proc_end = self._dhm().get_range_end()
            self._process_dhm_thread(self._img_idx_on_display, proc_end)

    def _end_processing_thread(self) -> None:
        """End processing by Blocking Running Call, Return to Set Saving Step"""
        process_settings.end_processing_thread(self._window)

    def _process_finished(self) -> None:
        """GUI cleanups after processing is finished"""
        process_settings.process_finished(self._window)
        self._text_info_show_misc = ''

    def _estimate_proc_time(self, loop_time) -> None:
        """Processing Time Estimation for TextInfoShow"""
        total_remain_time = round((self._dhm().get_range_end() - self._img_idx_on_display) * loop_time)
        self._text_info_show_misc = f"Estimated remaining time: {datetime.timedelta(seconds=total_remain_time)}."
    
    def _signal_recon_to(self) -> None:
        """Upon slot trigger (QSpinbox Reconstuction), enable peek button to view slice"""
        _pds = self._window.sp_dict["process_dhm_Spoiler"]
        _pds.pushButton_recon_peek.setEnabled(True)
        _pds.pushButton_recon_peek.clicked.connect(self._load_canvas_recon)

    def _progbar_signal_accept(self, value) -> None:
        """Update Progress Bar value during DHM Processing"""
        self._window.progressBar.setValue(value)
        if self._window.progressBar.value() == 99:
            self._window.progressBar.setValue(0)

    def _update_img_idx_on_display(self, value) -> None:
        """Update Image Index for TextInfoShow During DHM Processing"""
        self._img_idx_on_display = value
        self._window.spinBox_select_img.setValue(value+1)

    ##################################################
    # DHM Threaded Tasks Callback                    #
    ##################################################

    def _process_dhm_thread(self, proc_start, proc_end) -> None:
        """Spawn new thread for processing DHM images and saving the files.
        signals progressbar and display indeices, update canvas image"""
        if self._window.get_name() == "Inline":
            self._img_type_on_display = "refocused_volume"
        else:
            self._img_type_on_display = "height_map"

        def connect_signal(signal) -> None:
            """Connect SigHelper signals to Visualizer callbacks"""
            signal.idx.connect(self._progbar_signal_accept)
            signal.num.connect(self._update_img_idx_on_display)
            signal.show.connect(self.load_canvas)
            signal.time.connect(self._estimate_proc_time)
            signal.finished.connect(self._process_finished)

        threaded_task.process_dhm_thread(self._window, proc_start, proc_end, connect_signal)

    def _load_2d_image_series(self) -> None:
        """Spawn new thread for loading a 2d series from directory.
        check for IO correctness, sort the filename strings, update canvas image"""

        if self._current_viewer_event != "load_config":
            self._current_viewer_event = "load_sources"

        def connect_signal(signal) -> None:
            """Connect SigHelper signals to Visualizer callbacks"""
            signal.finished.connect(load_list)
        
        def load_list( _ ) -> None:
            """ Perform Human Sort with the file names, i.e.
                sort file list to [0.tiff, 1.tiff, 2.tiff, ..., 10.tiff, 11.tiff]
            Note: For RegEx expression generation of FLIR outputed images, use
            file = re.search("-\s*\K[^-]+$", file).group(0) """
            self._dhm().HOLO_LIST.sort(key=lambda f: int(re.sub('\D', '', f) or -1))
            self._total_img = len(self._dhm().HOLO_LIST)
            self._load_from_hololist(0)
            save_settings.config_spinbox(self._window, self._total_img, self._current_viewer_event == "load_config")
            if (self._dhm().get_back_path() != "") and (self._current_viewer_event == "load_config"):
                self._window.sp_dict["load_img_Spoiler"].lineEdit_local_read.setText(self._dhm().get_back_path())
            if self._dhm().config_loaded() is True:
                self._window.sp_dict["set_save_Spoiler"].lineEdit_save_add.setText(self._dhm().get_save_path()) 
        
        threaded_task.load_2d_image_series(self._window, connect_signal)

    def _load_background(self) -> None:
        """Spawn new thread for loading background image from the specified file path.
        check for IO correctness, load into HoloGram class, and update canvas image"""
        if self._current_viewer_event != "load_config":
            self._current_viewer_event = "load_sources"

        def connect_signal(signal) -> None:
            """Connect SigHelper signals to Visualizer callbacks"""
            signal.finished.connect(done_load_back)

        def done_load_back(cond : bool) -> None:
            self._img_type_on_display = "background"
            self.load_canvas()
            if (self._dhm().get_read_path() != "") and (self._current_viewer_event == "load_config"):
                self._window.sp_dict["load_img_Spoiler"].lineEdit_read_add.setText(self._dhm().get_read_path())
            if self._dhm().config_loaded() is True:
                self._window.sp_dict["set_save_Spoiler"].lineEdit_save_add.setText(self._dhm().get_save_path()) 

        threaded_task.load_background(self._window, connect_signal)

    def _load_from_hololist(self, holo_num) -> None:
        """Spawn new thread for loading one dhm image from HoloGram class 
        image list, then update canvas image"""
        self._img_type_on_display = "hologram"
        self._img_idx_on_display = holo_num

        def connect_signal(signal) -> None:
            """Connect SigHelper signals to Visualizer callbacks"""
            signal.finished.connect(self.load_canvas)

        threaded_task.load_from_hololist(self._window, holo_num, connect_signal)    

    def _load_canvas_recon(self) -> None:
        """Load Reconstructed Images from Inline mode, then update the Canvas"""
        self._img_type_on_display = "refocused_volume"
        recon_num = self._window.sp_dict["process_dhm_Spoiler"].spinBox_recon_pos.value()-1
        self._text_info_show_misc = f"Reconstruction distance is {round(self._dhm().get_live_recon_dist(recon_num), 3)}um."

        def connect_signal(signal) -> None:
            """Connect SigHelper signals to Visualizer callbacks"""
            signal.finished.connect(self.load_canvas)
        
        threaded_task.load_canvas_recon(self._window, self._img_idx_on_display, connect_signal)