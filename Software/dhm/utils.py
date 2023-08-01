"""Utilities Functions for DHM Processing"""

import numpy as np
import warnings
from typing import Tuple
from skimage.filters import gaussian

def _hanning_filter(sh_x, sh_y, cent_x, cent_y, r) -> np.ndarray:
    """Returning a hanning filter based on the radius and relative position in the quadrant."""
    hann = np.sqrt(np.outer(np.hanning(r * 2), np.hanning(r * 2)))
    hann = np.pad(hann, ((int(cent_x - r), int(sh_x - cent_x - r)), (int(cent_y - r), int(sh_y - cent_y - r))), 'constant')
    return hann

def _flat_window(l_end, l_begin, a, b, k_fac) -> np.ndarray:
    """Return a flat window filter by its dimensions"""
    line = np.linspace(1, l_end, l_end)

    interval0 = [1 if (i < (int(l_end - l_begin) / 2)) else 0 for i in line]
    interval1 = [1 if ((((l_end - l_begin) / 2) <= i) and (i <= int(l_end + l_begin) / 2)) else 0 for i in line]
    interval2 = [1 if (i > ((l_end + l_begin) / 2)) else 0 for i in line]

    w1 = np.power(np.cos(a * ((2 * line) / int(l_end - l_begin) - 1)), k_fac) * interval0
    w1[np.isnan(w1)] = 0
    w2 = interval1
    w3 = np.power(np.cos(b * ((2 * line) / (l_end + l_begin + 2) - 1)), k_fac) * interval2
    w3[np.isnan(w3)] = 0

    window = w1 + w2 + w3
    return window

def fourier_process(img_pre, filter_pre) -> np.ndarray:
    """FFT and Shift the Hologram."""
    fourier_pre = np.fft.fft2(img_pre)
    fourier_selected = np.fft.ifftshift(np.fft.fftshift(fourier_pre) * filter_pre)
    fourier_selected = np.fft.ifft2(fourier_selected)
    return fourier_selected

def apodization_process(img, k_factor, pad_size) -> np.ndarray:
    """Apodize the hologram image by padding the sides."""
    l0x, l0y = img.shape
    l0x = l0x - (pad_size * 3)
    l0y = l0y - (pad_size * 3)

    holo = np.pad(img, pad_width=pad_size, mode='edge')
    lx, ly = holo.shape

    ax = - (np.pi / 2) * (lx - l0x) / (l0x - lx + 2)
    bx = (np.pi / 2) * (lx + l0x + 2) / (lx - l0x - 2)
    ay = - (np.pi / 2) * (ly - l0y) / (l0y - ly + 2)
    by = (np.pi / 2) * (ly + l0y + 2) / (ly - l0y - 2)

    # Suppressing RuntimeWarning caused by complex values for np.power
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wx = _flat_window(lx, l0x, ax, bx, k_factor)
        wy = _flat_window(ly, l0y, ay, by, k_factor)

    x, y = np.meshgrid(wy, wx)
    window = x * y
    img_processed = holo * window

    return img_processed

def angular_mask(image, vector, delta) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Angular mask creation for the angular spectrum method."""

    image_fft = np.fft.fftshift(np.fft.fft2(image))
    n_x, m_y = image_fft.shape
    extent_x = m_y * delta
    extent_y = n_x * delta
    kx = np.linspace(-np.pi * m_y // 2 / (extent_x / 2), np.pi * m_y // 2 / (extent_x / 2), m_y)
    ky = np.linspace(-np.pi * n_x // 2 / (extent_y / 2), np.pi * n_x // 2 / (extent_y / 2), n_x)
    kx, ky = np.meshgrid(kx, ky)

    # Suppressing RuntimeWarning caused by complex values for np.sqrt
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kz = np.sqrt(vector ** 2 - kx ** 2 - ky ** 2)

    mask = (vector ** 2 - kx ** 2 - ky ** 2) > 0
    return image_fft, kz, mask

def background_unit(img) -> np.ndarray:
    """Smoothing the final image."""

    img = img - gaussian(img, sigma=150)
    histogram, bin_edges = np.histogram(img, bins=256)
    max_histogram = bin_edges[np.argmax(histogram)]
    image_back = img - max_histogram
    return image_back

def filter_fixed_point(hologram_raw, quad: str, filter_rate: float, filter_type: str) -> np.ndarray:
    """Filter the hologram with an optimized adn maximized region selection in a given quadrant, 
        either with Flat or Hanning Method."""
    
    frequency = np.fft.fftshift(np.fft.fft2(hologram_raw))
    shape_x, shape_y = np.shape(frequency)
    center_x = None; center_y = None
    v_pad = int(np.floor(shape_x / 2)); h_pad = int(np.floor(shape_y / 2))

    quad_filt = frequency[  1        if quad == ('1' or '2') else (v_pad + 30):
                        (v_pad - 30) if quad == ('1' or '2') else (shape_x - 30),
                            1        if quad == ('2' or '3') else (h_pad + 30):
                        (h_pad - 30) if quad == ('2' or '3') else (shape_y - 30)]

    indices = np.where(quad_filt == np.amax(quad_filt))
    center_x = indices[0] + ((v_pad + 30) if quad == ('3' or '4') else 0)
    center_y = indices[1] + ((h_pad + 30) if quad == ('1' or '4') else 0)

    distance = np.sqrt(np.power(np.abs(center_x - int(shape_x / 2)), 2)
                    + np.power(np.abs(int(shape_y / 2) - center_y), 2))
    radius = int((distance / 3) * filter_rate)

    mesh_m, mesh_n = np.meshgrid(np.arange(0, shape_y), np.arange(0, shape_x))
    region = np.sqrt((mesh_n - float(center_x)) ** 2 + (mesh_m - float(center_y)) ** 2)
    circle_window = np.array(region <= radius)

    if filter_type == "Hann":
        filter_hann = _hanning_filter(shape_x, shape_y, center_x, center_y, radius)
        circle_window = circle_window * filter_hann
    return circle_window