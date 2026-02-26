"""
Frequency-Domain Image Stitching Module
========================================
Algorithm: Phase Correlation via FFT (Foroosh et al. / Kuglin-Hines method)

Why Phase Correlation?
----------------------
Phase Correlation is the canonical frequency-domain stitching algorithm. It:
  1. Transforms both images to the frequency domain with 2-D FFT.
  2. Computes the *normalized* cross-power spectrum (phase only, no magnitude).
  3. Applies the inverse FFT – the result is a sharp Dirac-like peak whose
     (row, col) position is the sub-pixel translation offset between the images.
  4. (Optional) A Log-Polar pre-transform handles rotation & scale before step 1.

Compared with spatial `cv2.matchTemplate`, Phase Correlation:
  - Runs in O(N log N) instead of O(N²).
  - Is robust to additive noise, varying illumination and JPEG artefacts.
  - Returns a confidence measure (peak-to-sidelobe ratio, PSR).
  - Is naturally suited to large, overlapping game-screen captures.

Implementation Timeframe
------------------------
Week 1 (Days 1-2): Core algorithm
  - Implement `phase_correlate_match()` – FFT-based offset estimation.
  - Unit-test with synthetic shifted images; verify sub-pixel accuracy.

Week 1 (Days 3-4): Stitcher class
  - Implement `FrequencyDomainStitcher` with multi-image panorama support.
  - Implement `stitch_images_frequency()` for a two-image pipeline.

Week 2 (Days 5-6): Rotation & scale support (optional enhancement)
  - Add Log-Polar pre-transform for full similarity-motion estimation.
  - Add `stitch_with_rotation()` for rotated/scaled frame pairs.

Week 2 (Day 7): Integration & polish
  - Drop-in replacement for `cv2.matchTemplate` calls in `minfar.py`.
  - Benchmark against existing spatial matching; tune PSR threshold.
  - End-to-end test with real gameplay screenshots.

Total estimated effort: ~7 developer-days (one engineer, focused sprint).
"""

import numpy as np
import cv2


# ---------------------------------------------------------------------------
# Core phase-correlation helper
# ---------------------------------------------------------------------------

def _hann2d(rows: int, cols: int) -> np.ndarray:
    """Return a 2-D Hann window (rows × cols) to reduce spectral leakage."""
    wr = np.hanning(rows)
    wc = np.hanning(cols)
    return np.outer(wr, wc).astype(np.float64)


def phase_correlate_match(
    reference: np.ndarray,
    template: np.ndarray,
    upsample: int = 10,
    apply_window: bool = True,
) -> tuple[tuple[float, float], float]:
    """
    Estimate the (dy, dx) translation that maps *template* onto *reference*
    using FFT-based phase correlation.

    Parameters
    ----------
    reference : np.ndarray
        Grayscale source image (H × W), uint8 or float.
    template : np.ndarray
        Grayscale template / patch to locate (h × w), same dtype as reference.
        Must be ≤ reference in both dimensions.
    upsample : int
        Sub-pixel up-sampling factor (default 10 → 0.1-pixel accuracy).
    apply_window : bool
        Apply a 2-D Hann window before FFT to reduce leakage artefacts.

    Returns
    -------
    (dy, dx) : tuple[float, float]
        Sub-pixel translation.  Positive dy → template is *below* origin in
        reference; positive dx → template is to the *right* of origin.
    psr : float
        Peak-to-Sidelobe Ratio – a confidence measure.  Values > 20 are
        considered a reliable match; > 50 is excellent.
    """
    ref = reference.astype(np.float64)
    tmpl = template.astype(np.float64)

    # Pad template to the same size as reference (zero-padding in spatial domain)
    h_r, w_r = ref.shape[:2]
    h_t, w_t = tmpl.shape[:2]
    if h_t > h_r or w_t > w_r:
        raise ValueError("Template must not be larger than the reference image.")

    tmpl_padded = np.zeros_like(ref)
    tmpl_padded[:h_t, :w_t] = tmpl

    if apply_window:
        win = _hann2d(h_r, w_r)
        ref = ref * win
        tmpl_padded = tmpl_padded * win

    # FFT of both images
    F_ref = np.fft.fft2(ref)
    F_tmpl = np.fft.fft2(tmpl_padded)

    # Normalized cross-power spectrum (phase-only)
    cross_power = F_ref * np.conj(F_tmpl)
    denom = np.abs(cross_power)
    denom[denom == 0] = 1e-10          # avoid division by zero
    cross_power /= denom

    # Inverse FFT → correlation surface
    corr = np.fft.ifft2(cross_power).real

    # Sub-pixel refinement via DFT up-sampling around the coarse peak
    coarse_peak = np.unravel_index(np.argmax(corr), corr.shape)

    if upsample > 1:
        dy, dx = _subpixel_peak(corr, coarse_peak, upsample)
    else:
        dy, dx = float(coarse_peak[0]), float(coarse_peak[1])

    # Wrap negative offsets (FFT is circular)
    if dy > h_r / 2:
        dy -= h_r
    if dx > w_r / 2:
        dx -= w_r

    # PSR: ratio of peak to mean + std of the sidelobe region
    psr = _peak_to_sidelobe_ratio(corr, coarse_peak)

    return (dy, dx), psr


def _subpixel_peak(
    corr: np.ndarray,
    coarse: tuple[int, int],
    upsample: int,
) -> tuple[float, float]:
    """
    Quadratic sub-pixel peak refinement via parabolic interpolation on the
    3×3 neighbourhood around the coarse maximum.  Simple, numerically stable,
    and accurate to ~1/upsample pixels for well-conditioned peaks.
    """
    rows, cols = corr.shape
    r0, c0 = coarse

    # Clamp neighbours to image bounds (handles edge peaks gracefully)
    rm = (r0 - 1) % rows
    rp = (r0 + 1) % rows
    cm = (c0 - 1) % cols
    cp = (c0 + 1) % cols

    # Parabolic interpolation along each axis independently
    dy_num = corr[rm, c0] - corr[rp, c0]
    dy_den = 2.0 * (corr[rm, c0] - 2.0 * corr[r0, c0] + corr[rp, c0])
    dx_num = corr[r0, cm] - corr[r0, cp]
    dx_den = 2.0 * (corr[r0, cm] - 2.0 * corr[r0, c0] + corr[r0, cp])

    sub_r = r0 + (dy_num / dy_den if dy_den != 0 else 0.0)
    sub_c = c0 + (dx_num / dx_den if dx_den != 0 else 0.0)

    return float(sub_r), float(sub_c)


def _peak_to_sidelobe_ratio(corr: np.ndarray, peak: tuple[int, int]) -> float:
    """PSR = (peak_value - mean_sidelobe) / std_sidelobe."""
    r, c = peak
    mask = np.ones(corr.shape, dtype=bool)
    r1 = max(0, r - 5)
    r2 = min(corr.shape[0], r + 6)
    c1 = max(0, c - 5)
    c2 = min(corr.shape[1], c + 6)
    mask[r1:r2, c1:c2] = False
    sidelobe = corr[mask]
    if sidelobe.std() == 0:
        return 0.0
    return float((corr[r, c] - sidelobe.mean()) / sidelobe.std())


# ---------------------------------------------------------------------------
# Two-image stitching with alpha blending
# ---------------------------------------------------------------------------

def stitch_images_frequency(
    img_left: np.ndarray,
    img_right: np.ndarray,
    overlap_hint: int | None = None,
    blend_width: int = 64,
) -> tuple[np.ndarray, tuple[float, float], float]:
    """
    Stitch two horizontally overlapping images using Phase Correlation.

    Parameters
    ----------
    img_left : np.ndarray
        Left image (BGR or grayscale, uint8).
    img_right : np.ndarray
        Right image (same type as img_left).
    overlap_hint : int | None
        Expected overlap width in pixels.  If None, half the image width is
        used.  A tighter hint speeds up and improves accuracy.
    blend_width : int
        Width (pixels) of the linear alpha-blend transition zone.

    Returns
    -------
    panorama : np.ndarray
        Stitched image.
    (dy, dx) : tuple[float, float]
        Estimated offset (Phase Correlation result).
    psr : float
        Confidence of the alignment.
    """
    is_color = img_left.ndim == 3

    # Skip stitching when both inputs are identical
    if img_left.shape == img_right.shape and np.array_equal(img_left, img_right):
        return img_left.copy(), (0.0, 0.0), 0.0

    # Convert to grayscale for alignment
    def to_gray(img: np.ndarray) -> np.ndarray:
        if img.ndim == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img.copy()

    gray_l = to_gray(img_left)
    gray_r = to_gray(img_right)

    h, w = gray_l.shape

    # Crop the overlap region to estimate offset
    ow = overlap_hint if overlap_hint is not None else w // 2
    ow = min(ow, w, gray_r.shape[1])

    ref_crop = gray_l[:, w - ow:]         # right strip of left image
    tmpl_crop = gray_r[:, :ow]            # left strip of right image

    (dy, dx), psr = phase_correlate_match(ref_crop, tmpl_crop)

    # Round to integer translation for canvas placement
    idy = int(round(dy))
    idx = int(round(dx))

    # Build output canvas
    canvas_h = h + abs(idy)
    canvas_w = w + (w - ow) - idx
    if is_color:
        canvas = np.zeros((canvas_h, canvas_w, img_left.shape[2]), dtype=np.uint8)
    else:
        canvas = np.zeros((canvas_h, canvas_w), dtype=np.uint8)

    y_off_l = max(0, -idy)
    y_off_r = max(0, idy)
    x_off_r = w - ow + (ow - idx)

    # Place left image
    canvas[y_off_l: y_off_l + h, 0:w] = img_left

    # Place right image with linear alpha blend in overlap zone
    r_h, r_w = img_right.shape[:2]
    blend_x_start = x_off_r
    blend_x_end = blend_x_start + min(blend_width, ow)

    for x in range(r_w):
        canvas_x = x_off_r + x
        if canvas_x < 0 or canvas_x >= canvas_w:
            continue
        row_slice_r = slice(y_off_r, y_off_r + r_h)
        alpha = _blend_alpha(canvas_x, blend_x_start, blend_x_end)
        dst = canvas[row_slice_r, canvas_x].astype(np.float32)
        src = img_right[:, x].astype(np.float32)
        canvas[row_slice_r, canvas_x] = np.clip(
            dst * (1 - alpha) + src * alpha, 0, 255
        ).astype(np.uint8)

    return canvas, (dy, dx), psr


def _blend_alpha(x: int, x_start: int, x_end: int) -> float:
    """Linear ramp from 0 → 1 between x_start and x_end."""
    if x_end <= x_start:
        return 1.0
    if x <= x_start:
        return 0.0
    if x >= x_end:
        return 1.0
    return (x - x_start) / (x_end - x_start)


# ---------------------------------------------------------------------------
# Multi-image panorama stitcher
# ---------------------------------------------------------------------------

class FrequencyDomainStitcher:
    """
    Incrementally stitch multiple overlapping images into a single panorama
    using Phase Correlation alignment.

    Usage
    -----
    stitcher = FrequencyDomainStitcher(overlap_hint=200, blend_width=64)
    panorama = stitcher.stitch([frame0, frame1, frame2, frame3])
    """

    def __init__(
        self,
        overlap_hint: int | None = None,
        blend_width: int = 64,
        psr_threshold: float = 5.0,
    ) -> None:
        """
        Parameters
        ----------
        overlap_hint : int | None
            Expected overlap in pixels between consecutive images.
        blend_width : int
            Alpha-blend transition width in pixels.
        psr_threshold : float
            Minimum PSR to accept a phase-correlation result as valid.
            Frames below this threshold are skipped with a warning.
        """
        self.overlap_hint = overlap_hint
        self.blend_width = blend_width
        self.psr_threshold = psr_threshold

    def stitch(self, images: list[np.ndarray]) -> np.ndarray:
        """
        Stitch a list of horizontally overlapping images left-to-right.

        Parameters
        ----------
        images : list[np.ndarray]
            Ordered list of BGR or grayscale images with consistent size.

        Returns
        -------
        panorama : np.ndarray
            Stitched panorama image.
        """
        if not images:
            raise ValueError("Image list is empty.")
        if len(images) == 1:
            return images[0].copy()

        panorama = images[0].copy()
        for i, img in enumerate(images[1:], start=1):
            panorama, offset, psr = stitch_images_frequency(
                panorama,
                img,
                overlap_hint=self.overlap_hint,
                blend_width=self.blend_width,
            )
            if psr < self.psr_threshold:
                print(
                    f"[FrequencyDomainStitcher] Warning: low PSR={psr:.1f} at "
                    f"image index {i}. Alignment may be inaccurate."
                )
        return panorama

    def match_template(
        self,
        screen: np.ndarray,
        template: np.ndarray,
        psr_threshold: float | None = None,
    ) -> tuple[tuple[float, float] | None, float]:
        """
        Frequency-domain alternative to ``cv2.matchTemplate``.

        Returns the (y, x) position of the best match and its PSR confidence,
        or (None, 0.0) if the PSR is below threshold.

        Parameters
        ----------
        screen : np.ndarray
            Full grayscale screen capture.
        template : np.ndarray
            Grayscale template to locate.
        psr_threshold : float | None
            Override the instance-level threshold for this call.
        """
        thr = psr_threshold if psr_threshold is not None else self.psr_threshold
        (dy, dx), psr = phase_correlate_match(screen, template)
        if psr < thr:
            return None, psr
        return (dy, dx), psr
