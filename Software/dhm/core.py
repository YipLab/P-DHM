from pathlib import Path
from typing import Optional, Tuple
import os
import configparser
import numpy as np
import PIL
import matplotlib.pyplot as plt
import tifffile as tf
from skimage.restoration import unwrap_phase
from dhm import utils

# On Windows, install 'Microsoft's vcredist_x64.exe' to fix potential unwrap_phase dependency error
# ( https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)

source_path = Path(__file__).resolve()
source_dir = source_path.parent

class HoloGram:

    HOLO_LIST = []

    # States and Mutexs
    __back_loaded : bool = False
    __block :bool = False
    __dhm_mode : str = ""
    __config = None

    HOLOGRAM = np.ndarray(shape=(3000, 4000), dtype=np.uint8)
    BACKGROUND = np.ndarray(shape=(3000, 4000), dtype=np.uint8)
    BACKGROUND_PROCESSED = np.ndarray(shape=(400, 400), dtype=np.uint8)
    FOURIER_FILTER = np.ndarray(shape=(400, 400), dtype=np.uint8)

    HEIGHT_MAP = np.ndarray(shape=(400, 400), dtype=np.uint8)
    PHASE_MAP = np.ndarray(shape=(400, 400), dtype=np.uint8)
    WRAPPED_PHASE = np.ndarray(shape=(400, 400), dtype=np.uint8)
    REFOCUSED_VOLUME = np.ndarray(shape=(400, 400), dtype=np.uint8)
    INTENSITY_MAP = np.ndarray(shape=(400, 400), dtype=np.uint8)

    # File Paths
    _read_path_main : str = ''
    _read_path_back : str = ''
    _save_path_main : str = ''

    _load_config_path : str = ''

    # System Parameters
    _pixel_x_main : float # unit in micrometer
    _pixel_y_main : float # unit in micrometer
    _refractive_index_main : float
    _magnification_main : int
    _wavelength_main : float = 0.635  # unit in micrometer

    # Reconstruction Parameters
    _diffraction_distance : float = 0.0 # unit in micrometer
    _rec_start : float  = 0.0 # unit in micrometer
    _rec_end : float = 0.0
    _rec_zstack_qty : int = 0

    # Filter Parameters
    _filter_type_main : str = ''
    _filter_quadrant_main : str = ''
    _filter_rate_main : float = 0.0
    _apo_pad_size : int = 100
    __apo_k_factor : float = 1.5 # Golden Value

    # Save Flags
    _height_map_save: bool  = True
    _phase_map_save: bool  = True
    _wrapped_phase_save: bool  = True
    _inline_save: bool  = True

    # Processing Range Settings
    _process_range_start : int = 0
    _process_range_end : int = 0

    # ROI Setting
    _roi_enabled : bool = False
    _shape_x_main : int = 0
    _shape_y_main : int = 0

    def __init__(self) -> None:
        """Initialize ROI"""
        self.left = None; self.right = None; self.top = None; self.bot = None

    def set_background_img(self) -> Optional[int]:
        """Try loading background image, return false at Plt error due to unidentified format"""
        try:
            self.BACKGROUND = tf.imread(self._read_path_back)
            self.__back_loaded = True
            return 1
        except PIL.UnidentifiedImageError:
            return -1
        except FileNotFoundError:
            return -2

    def load_hologram_img(self, holo_num) -> Optional[int]:
        """Try loading hologram image, return false at Plt error due to unidentified format"""
        try:
            self.HOLOGRAM = tf.imread(f"{self._read_path_main}/{self.HOLO_LIST[holo_num]}")
            self._shape_x_main = self.HOLOGRAM.shape[0]
            self._shape_y_main = self.HOLOGRAM.shape[1]
            return 1
        except PIL.UnidentifiedImageError:
            return -1
        except FileNotFoundError:
            return -2

    def load_reconstruction_img(self, holo_num, recon_num) -> Optional[int]:
        """Try loading reconstruction image, return false at Plt error due to unidentified format"""
        try:
            self.REFOCUSED_VOLUME = tf.imread(f"{self._save_path_main}/{str(holo_num)}_inline_frame_{recon_num}.tiff")
            return 1
        except PIL.UnidentifiedImageError:
            return -1
        except FileNotFoundError:
            return -2

    def get_backloaded(self)-> Optional[bool]:
        """Asesss HoloGram backloaded status"""
        return self.__back_loaded

    def set_read_path(self, read_path: str) -> None:
        self._read_path_main = read_path

    def get_read_path(self) -> Optional[str]:
        return self._read_path_main

    def set_back_path(self, back_path: str) -> None:
        self._read_path_back = back_path

    def get_back_path(self) -> Optional[str]:
        return self._read_path_back

    def set_save_path(self, save_path: str) -> None:
        self._save_path_main = save_path
    
    def get_save_path(self) -> Optional[str]:
        return self._save_path_main

    def set_sys_param(self, pixel_x: float, pixel_y: float, refractive_index: float,
                      magnification: int, wavelength: float) -> None:
        """Set system param, wavelength converted from nm to um"""
        self._pixel_x_main = pixel_x
        self._pixel_y_main = pixel_y
        self._refractive_index_main = refractive_index
        self._magnification_main = magnification
        self._wavelength_main = wavelength / 1000
        self._delta = pixel_x / magnification
        self._vector = 2 * self._refractive_index_main * np.pi / self._wavelength_main
        self._height_factor = 2 * self._refractive_index_main * np.pi / self._wavelength_main

    def get_sys_param(self) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[int], Optional[float]]:
        return self._pixel_x_main, self._pixel_y_main, self._refractive_index_main, self._magnification_main, self._wavelength_main

    def set_filter_param(self, expansion: int, filter_type: str, filter_rate: int, filter_quadrant: str) -> None:
        """Set filtering param, apodization converted to int pixel sizes
        filter rate convert from percentage to ratio"""
        self._apo_pad_size = int(expansion)
        self._filter_type_main = filter_type
        self._filter_rate_main = float(filter_rate/100)
        self._filter_quadrant_main = filter_quadrant

    def get_filter_param(self) -> Tuple[Optional[str], Optional[int], Optional[str], Optional[int]]:
        return self._filter_type_main, self._filter_rate_main, self._filter_quadrant_main, self._apo_pad_size

    def set_roi_by_param(self, left: int, right: int, top: int, bottom: int) -> None:
        self.top = top; self.bot = bottom; self.left = left; self.right = right

    def set_roi_enable(self) -> None:
        self._roi_enabled = True

    def set_roi_disable(self) -> None:
        self._roi_enabled = False

    def set_recon_param(self, recstart: float, recend: float, zqty: int) -> None:
        self._rec_start = recstart
        self._rec_end = recend
        self._rec_zstack_qty = zqty

    def get_recon_param(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        return self._rec_start, self._rec_end, self._rec_zstack_qty

    def set_diffraction_dist(self, diff: float) -> None:
        self._diffraction_distance = diff
    
    def get_diffraction_dist(self) -> Optional[float]:
        return self._diffraction_distance

    def get_live_recon_dist(self, slice_num: int) -> float:
        """Return reconstruction distance by the reconstruction start + number of slices * per slice length"""
        return self._rec_start + slice_num * (self._rec_end - self._rec_start) / self._rec_zstack_qty

    def get_zstack_qty(self) -> Optional[int]:
        return self._rec_zstack_qty

    def set_save_flags(self, height_map: bool, phase_map: bool, wrapped_phase: bool, refocused_volume: bool) -> None:
        self._height_map_save = height_map
        self._phase_map_save = phase_map
        self._wrapped_phase_save = wrapped_phase
        self._inline_save = refocused_volume

    def get_save_flags(self) -> Tuple[Optional[bool], Optional[bool], Optional[bool], Optional[bool]]:
        return self._height_map_save, self._phase_map_save, self._wrapped_phase_save, self._inline_save

    def set_range_start(self, start : int  = 0) -> None:
        self._process_range_start = start

    def set_range_end(self, end : int  = 0) -> None:
        self._process_range_end = end

    def get_range_start(self) -> Optional[int]:
        return self._process_range_start

    def get_range_end(self) -> Optional[int]:
        return self._process_range_end

    def set_block(self) -> None:
        """Set Blocking Call"""
        self.__block = True
    
    def set_unblock(self) -> None:
        """Remove Blocking Call"""
        self.__block = False

    def get_block(self) -> bool:
        """Get Blocking Call Status"""
        return self.__block

    def set_dhm_mode(self, mode : str) -> None:
        """Set DHM operation mode"""
        self.__dhm_mode = mode

    def get_dhm_mode(self) -> Optional[bool]:
        """Get DHM operation mode"""
        return self.__dhm_mode

    def config_loaded(self) -> Optional[bool]:
        """Return config loaded state"""
        return True if self.__config != None else False

    def _filter_background_process(self) -> None:
        """Filtering Background, run fourier transform and shift, return background intensity"""
        holo_to_filter = self.HOLOGRAM[self.left:self.right, self.top:self.bot] if self._roi_enabled else self.HOLOGRAM
        back_to_filter = self.BACKGROUND[self.left:self.right, self.top:self.bot] if self._roi_enabled else self.BACKGROUND

        self.FOURIER_FILTER = utils.filter_fixed_point(hologram_raw=holo_to_filter, quad=self._filter_quadrant_main,
                                                    filter_rate=self._filter_rate_main, filter_type=self._filter_type_main)

        background_filtered = utils.fourier_process(back_to_filter, self.FOURIER_FILTER)
        self.BACKGROUND_PROCESSED = np.exp(complex(0, 1) * np.angle(np.conj(background_filtered)))

    def hologram_process(self, holo_num : int, stop : bool) -> Optional[int]:
        """Process Off-axis Hologram in the loop, using blocking call to terminate"""
        while True:
            self.load_hologram_img(holo_num)

            if self.get_block() == True:
                self.set_block()
                return -1

            self._filter_background_process()

            hologram = utils.fourier_process(self.HOLOGRAM[self.left:self.right, self.top:self.bot], self.FOURIER_FILTER)\
                if self._roi_enabled else utils.fourier_process(self.HOLOGRAM, self.FOURIER_FILTER)

            holo_cleared = hologram * self.BACKGROUND_PROCESSED
            holo_processed = utils.apodization_process(holo_cleared, self.__apo_k_factor, self._apo_pad_size)
            phase_reconed, intensity_reconed = self._reconstruction_offaxis(holo_processed, self._vector, self._delta, 
                                                                self._diffraction_distance, self._apo_pad_size)

            if self.get_block() == True:
                self.set_block()
                return -2

            self.WRAPPED_PHASE = phase_reconed
            self.INTENSITY_MAP = intensity_reconed            
            self.PHASE_MAP = unwrap_phase(self.WRAPPED_PHASE)
            self.HEIGHT_MAP = self.PHASE_MAP / self._height_factor

            if self.get_block() == True:
                self.set_block()
                return -3

            fname = os.path.splitext(self.HOLO_LIST[holo_num])[0]
            self._save_results(holo_num, fname)
            return

    def hologram_inline_process(self, holo_num : int, stop : bool) -> Optional[int]:
        """Process In-line Hologram in the loop, using blocking call to terminate"""
        while True:
            self.load_hologram_img(holo_num)

            if self.get_block() == True:
                self.set_block()
                return -1

            hologram = self.HOLOGRAM[self.left:self.right, self.top:self.bot] if self._roi_enabled else self.HOLOGRAM
            background = self.BACKGROUND[self.left:self.right, self.top:self.bot] if self._roi_enabled else self.BACKGROUND
            
            holo_cleared = (hologram - background) / background

            if self.get_block() == True:
                self.set_block()
                return -2

            fname = os.path.splitext(self.HOLO_LIST[holo_num])[0]
            self._reconstruction_inline(holo_cleared, holo_num, fname, self._rec_start,
                                            self._rec_end, self._rec_zstack_qty)
            return

    def _reconstruction_inline(self, image, num, name, recon_start, recon_end, slice_qty) -> None:
        """Inline reconstruction using angular spectrum method. Able to reconstruct a volume using
        the start & end distances as well as the the z stack slice quantities. Dump result in the save dir."""

        image_fft, kz, mask = utils.angular_mask(image, self._vector, self._delta)

        for z_step in range(1, slice_qty+1):
            diffract_dist = recon_start + z_step * (recon_end - recon_start) / slice_qty
            fft_core = np.where(mask, image_fft * np.exp(complex(0, 1) * kz * diffract_dist), 0)
            self._diffraction_distance = diffract_dist
            reconed_field = np.fft.ifft2(np.fft.ifftshift(fft_core))
            self.REFOCUSED_VOLUME = np.real(reconed_field * np.conjugate(reconed_field))
            if self._inline_save is True:
                f"Saving {num}_inline_frame_{z_step-1}.tiff..."
                tf.imwrite(f"{self._save_path_main}/{num}_inline_frame_{z_step-1}.tiff", self.REFOCUSED_VOLUME.astype('float32'))

    def _reconstruction_offaxis(self, image, vector, delta, diffrac_dist, pad_size) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """offaxis reconstruction using angular spectrum method. Able to reconstruct on one distance
        slice based on the set diffraction distance only."""

        if diffrac_dist == 0.0:
            reconed_field = image
        else:
            fft_img, kz, mask = utils.angular_mask(image, vector, delta)
            fft_core = np.where(mask, fft_img * np.exp(complex(0, 1) * kz * diffrac_dist), 0)
            reconed_field = np.fft.ifft2(np.fft.ifftshift(fft_core))

        if self._roi_enabled is True:
            reconed_field = reconed_field[pad_size: pad_size + self.right - self.left,
                pad_size: pad_size + self.bot - self.top,]
        else:
            reconed_field = reconed_field[pad_size: pad_size + self._shape_x_main,
                pad_size: pad_size + self._shape_y_main,]

        reconstructed_intensity = np.real(reconed_field * np.conjugate(reconed_field))
        reconstructed_phase = np.angle(reconed_field)
        return reconstructed_phase, reconstructed_intensity

    def _save_results(self, num, name) -> None:
        """Save Off-axis DHM images by saving flags"""
        if self._save_path_main == "":
            return
        if self._height_map_save is True:
            #f"Saving height map {num} at {self._save_path_main}..."
            tf.imwrite(f"{self._save_path_main}/{num}_height_map.tiff", self.HEIGHT_MAP.astype('float32'))
        if self._phase_map_save is True:
            #f"Saving phase map {num} at {self._save_path_main}..."
            tf.imwrite(f"{self._save_path_main}/{num}_phase_map.tiff", self.PHASE_MAP.astype('float32'))
        if self._wrapped_phase_save is True:
            #f"Saving wrapped phase {num} at {self._save_path_main}..."
            tf.imwrite(f"{self._save_path_main}/{num}_wrapped_phase.tiff", self.WRAPPED_PHASE.astype('float32'))

    def _dump_config_receipt(self, config_save_path) -> None:
        """Save Configuration Receipt .ini file to path"""

        config = configparser.ConfigParser()
        config['DHM_Mode'] = {'mode': ''}
        config['File_Paths'] = {'read_path_main': self._read_path_main,
                            'read_path_back': self._read_path_back,
                            'save_path_main': self._save_path_main}
        config['System_Parameters'] = {'pixel_x_main': self._pixel_x_main,
                            'pixel_y_main': self._pixel_y_main,
                            'refractive_index_main': self._refractive_index_main,
                            'magnification_main': self._magnification_main,
                            'wavelength_main': self._wavelength_main*1000}
        config['Reconstruction_Parameters'] = {'diffraction_distance': self._diffraction_distance,
                            'rec_start': self._rec_start,
                            'rec_end': self._rec_end,
                            'rec_zstack_qty': self._rec_zstack_qty}
        config['Filter_Parameters'] = {'filter_type_main': self._filter_type_main ,
                            'filter_quadrant_main': self._filter_quadrant_main,
                            'filter_rate_main': int(self._filter_rate_main*100),
                            'apo_pad_size': self._apo_pad_size}
        config['Save_Flags'] = {'height_map_save': self._height_map_save,
                            'phase_map_save': self._phase_map_save,
                            'wrapped_phase_save': self._wrapped_phase_save,
                            'inline_save': self._inline_save}
        config['Processing_Range'] = {'process_range_start': self._process_range_start+1,
                            'process_range_end': self._process_range_end+1}
        with open(f'{config_save_path}', 'w') as configfile:
            config.write(configfile)

    def get_config_path(self) -> Optional[str]:
        return self._load_config_path

    def read_config_receipt(self, config_read_path) -> None:
        """Read Configuration Receipt .ini file from path, parse into HoloGram"""

        self._load_config_path = config_read_path
        config = configparser.ConfigParser()
        config.read(config_read_path)
        self.set_sys_param( pixel_x = float(config['System_Parameters']['pixel_x_main']), 
                            pixel_y = float(config['System_Parameters']['pixel_y_main']), 
                            refractive_index = float(config['System_Parameters']['refractive_index_main']),
                            magnification = int(config['System_Parameters']['magnification_main']), 
                            wavelength = float(config['System_Parameters']['wavelength_main']))
                            
        self.set_read_path(config['File_Paths']['read_path_main'])
        self.set_back_path(config['File_Paths']['read_path_back'])
        self.set_save_path(config['File_Paths']['save_path_main'])

        self.set_diffraction_dist(float(config['Reconstruction_Parameters']['diffraction_distance']))
        self.set_recon_param(recstart = float(config['Reconstruction_Parameters']['rec_start']), 
                            recend = float(config['Reconstruction_Parameters']['rec_end']),
                            zqty = int(config['Reconstruction_Parameters']['rec_zstack_qty']))

        self.set_filter_param(expansion = int(config['Filter_Parameters']['apo_pad_size']), 
                        filter_type = config['Filter_Parameters']['filter_type_main'], 
                        filter_rate = float(config['Filter_Parameters']['filter_rate_main']),
                        filter_quadrant = config['Filter_Parameters']['filter_quadrant_main'])

        self.set_save_flags(height_map = config['Save_Flags'].getboolean('height_map_save'),
                            phase_map = config['Save_Flags'].getboolean('phase_map_save'),
                            wrapped_phase = config['Save_Flags'].getboolean('wrapped_phase_save'),
                            refocused_volume = config['Save_Flags'].getboolean('inline_save'))
        
        rng_start = int(config['Processing_Range']['process_range_start'])-1
        rng_end = int(config['Processing_Range']['process_range_end'])-1

        self.set_range_start(rng_start if rng_start > 0 else 0)
        self.set_range_end(rng_end if rng_end > 0 else 0)

        self.__config = config