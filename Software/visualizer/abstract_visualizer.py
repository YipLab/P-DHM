import numpy as np
from skimage import exposure
from matplotlib import patches

from gui.main_window import Window
from gui.dialog import popup_message
from visualizer import Visualizer

class AbstractImageVisualizer(Visualizer):
    """Some Abstractions of Standard image visualizer."""

    ROI_LIST = []
    _img_buf = np.ndarray(shape=(3000, 4000), dtype=np.uint16)
    _cmap = 'gist_gray'
    _text_info_show_misc = ""
    _total_img = 0
    # _viewer_events = {"set_param", "load_config", "load_sources", "set_roi", "set_saving", "processing"}
    _current_viewer_event = ""

    _img_type_str_mapper = {
        "Background" : "background",
        "Hologram" : "hologram",
        "Wrapped Phase" : "wrapped_phase",
        "FFT Filter" : "fft_filter",
        "Reconstructed Map" : "refocused_volume",
        "Phase map" : "phase_map",
        "Height map": "height_map",
        "Intensity map": "intensity_map"
    }

    def __init__(self, window: Window) -> None:
        """Initialize main window assets"""
        super().__init__(window)
        self._window.spinBox_select_img.textChanged.connect(self._signal_canvas_update)
        self._window.relink_all.connect(self._link_sp_signals)
        self._window.load_config.connect(self._load_config)
        self._window.dump_config.connect(self._dump_config)

    def load_canvas(self) -> None:
        """load image ndarray from HoloGram by copying onto a buffer,
        Update the viewer with intensity-scaled image buffer and draw ROI; 
        Update text infoshow """

        self._img_types = {
            "background":       lambda _: self._dhm().BACKGROUND,
            "hologram":         lambda _: self._dhm().HOLOGRAM,
            "wrapped_phase":    lambda _: self._dhm().WRAPPED_PHASE,
            "fft_filter" :      lambda _: self._dhm().FOURIER_FILTER,
            "refocused_volume": lambda _: self._dhm().REFOCUSED_VOLUME,
            "phase_map":        lambda _: self._dhm().PHASE_MAP,
            "height_map":       lambda _: self._dhm().HEIGHT_MAP,
            "intensity_map":    lambda _: self._dhm().INTENSITY_MAP
        }

        # _viewer_events = {"set_param", "load_config", "load_sources", "set_roi", "set_saving", "processing"}
        _current_viewer_event = ""
        if self._current_viewer_event == "set_param":
            self._window.text_info_show.setText("Start by clicking the drop down menu.")
        elif self._current_viewer_event in {"load_config", "load_sources", "set_roi", "set_saving"}:
            if len(self._dhm().HOLO_LIST) == 0:
                self._window.text_info_show.setText("Background image loaded.")
            else:
                self._window.text_info_show.setText(f"Viewing {self._img_idx_on_display+1}" +
                    f" out of {self._total_img} images. {self._text_info_show_misc}")
        elif self._current_viewer_event == "processing":
            proc_start = self._dhm().get_range_start(); proc_end = self._dhm().get_range_end()
            if self._img_idx_on_display < proc_start or self._img_idx_on_display > proc_end:
                self._window.text_info_show.setText(f"Viewing outside of processed series: " +
                    str([k for k,v in self._img_type_str_mapper.items() if v == self._img_type_on_display][0]) +
                    f", {self._img_idx_on_display+1} out of {self._total_img} from the folder. "+ ("" if self._text_info_show_misc == "" else "\n") +
                    f"{self._text_info_show_misc}")
            else:
                self._window.text_info_show.setText(f"Viewing {self._img_idx_on_display-proc_start+1}" +
                    f" out of {proc_end-proc_start+1} processed images: " + 
                    str([k for k,v in self._img_type_str_mapper.items() if v == self._img_type_on_display][0]) +
                    f", {self._img_idx_on_display+1} out of {self._total_img} from the folder. " + ("" if self._text_info_show_misc == "" else "\n") +
                    self._text_info_show_misc)
        
        self._img_buf = exposure.equalize_hist(self._img_types[self._img_type_on_display](1)) if self._img_type_on_display == "refocused_volume" else \
                        exposure.rescale_intensity(self._img_types[self._img_type_on_display](1))
        self._cmap = 'magma_r' if self._img_type_on_display == "height_map" else 'gist_heat_r' if self._img_type_on_display == "refocused_volume" else 'gist_gray'
        self.draw_view()
        if len(self.ROI_LIST) > 0:
            self._draw_all_roi()

    def _load_2d_image(self) -> None:
        self.draw_view()

    def draw_view(self) -> None:
        self._clear_axis()
        self._ax.set_facecolor((0.2, 0.2, 0.2))
        self._draw_image()
        self._fig.canvas.draw()

    def _draw_image(self) -> None:
        """Draw the whole image, or draw ROI with respective positioning"""
        if self._img_type_on_display != "background" and \
        self._img_type_on_display != "hologram" and (len(self.ROI_LIST) > 0):
            roi = self.ROI_LIST[0]
            x0 = roi[0]; y0 = roi[1]; x1 = roi[2]; y1 = roi[3]
            self._ax.imshow(self._img_buf,
                            aspect='auto',
                            origin='upper',
                            extent=[x1, x0, y0, y1],
                            cmap=self._cmap)
        else:
            self._ax.imshow(self._img_buf, cmap=self._cmap)

    def refresh_data(self) -> None:
        self._load_2d_image()  # Reload image, as image is a reconstruction of the data
        super().refresh_data()

    def refresh_all(self) -> None:
        self._load_2d_image()  # Reload image
        super().refresh_all()

    def _select_img_type(self) -> None:
        """Translate Image types strings on QcomboBox dropdown menus to program strings"""
        _pds = self._window.sp_dict["process_dhm_Spoiler"]
        _type = _pds.comboBox_imgshow.currentText()
        if self._window.get_name() == "inline" :
            if _type == "Reconstructed Map":
                _pds.label_recon_pos.setEnabled(True)
                _pds.label_recon_total.setEnabled(True)
                _pds.spinBox_recon_pos.setEnabled(True)
            else:
                _pds.label_recon_pos.setEnabled(False)
                _pds.label_recon_total.setEnabled(False)
                _pds.spinBox_recon_pos.setEnabled(False)

        self._img_type_on_display = self._img_type_str_mapper[_type]
        self.load_canvas()

    def _save_live_view(self) -> None:
        """Save live view for processing mode"""
        if self._dhm().get_save_path() == "":
            popup_message("Empty save path", f"Please set path to save images before proceeding.")
            self._window.sp_dict["process_dhm_Spoiler"].close_spoiler()
            self._window.sp_dict["set_save_Spoiler"].label_check.hide()
            self._window.sp_dict["set_save_Spoiler"].label_done_text.hide()
            self._window.sp_dict["set_save_Spoiler"].open_spoiler()
            return
        self._current_viewer_event = "processing"
        self._select_img_type()
        import tifffile as tf
        tf.imwrite(f"{self._dhm().get_save_path()}/live_save_" +
                    f"{self._img_idx_on_display}_{str(self._img_type_on_display)}.tiff",
                    self._img_buf)

    def _signal_canvas_update(self) -> None:
        """Upon slot trigger (viewer QSpinbox), enables update Qbutton"""
        self._window.pushButton_view_img.setEnabled(True)
        self._window.pushButton_view_img.clicked.connect(self._update_canvas_img)

    def _update_canvas_img(self) -> None:
        """Upon slot trigger (viewer Update image Qbutton), update canvas image"""
        holo_num = self._window.spinBox_select_img.value()-1
        self._load_from_hololist(holo_num)
        self._draw_all_roi()
        self._window.pushButton_view_img.setEnabled(False)

    def _draw_all_roi(self) -> None:
        """Drawing All ROIs in ROI_LIST on canvas"""
        for _, roi in enumerate(self.ROI_LIST):
            x0 = roi[0]; y0 = roi[1]; x1 = roi[2]; y1 = roi[3]
            self._ax.add_patch(patches.Rectangle((float(x0), float(y0)),
                        float(x1-x0), float(y1-y0), fc ='none', ec ='y', lw = 1.5))
            self._ax.text(float(x0), float(y0), f"ROI",
                verticalalignment='bottom', horizontalalignment='right',color='w')
        self._fig.canvas.draw()
