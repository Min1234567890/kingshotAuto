"""
Tests for the frequency_stitch module.

Run with:  python -m pytest test_frequency_stitch.py -v
"""

import numpy as np
import pytest

from frequency_stitch import (
    FrequencyDomainStitcher,
    phase_correlate_match,
    stitch_images_frequency,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _synthetic_pair(
    h: int = 128,
    w: int = 256,
    shift_y: int = 0,
    shift_x: int = 30,
    overlap: int = 60,
    noise_std: float = 0.0,
    rng_seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build a pair of uint8 grayscale images that overlap by *overlap* pixels
    horizontally and are offset vertically by *shift_y* rows.
    """
    rng = np.random.default_rng(rng_seed)
    # Create a wide reference pattern
    full_w = w + overlap
    full_h = h + abs(shift_y)
    pattern = (rng.random((full_h, full_w)) * 200 + 28).astype(np.uint8)

    img_l = pattern[:h, :w].copy()
    y0 = abs(shift_y) if shift_y < 0 else 0
    img_r = pattern[y0: y0 + h, w - overlap: w - overlap + w].copy()

    if noise_std > 0:
        noise = rng.normal(0, noise_std, img_r.shape)
        img_r = np.clip(img_r.astype(np.float64) + noise, 0, 255).astype(np.uint8)

    return img_l, img_r


# ---------------------------------------------------------------------------
# phase_correlate_match tests
# ---------------------------------------------------------------------------

class TestPhaseCorrelateMatch:
    def test_zero_shift(self):
        """Identical images → offset ≈ (0, 0) with high PSR."""
        rng = np.random.default_rng(0)
        img = (rng.random((128, 128)) * 255).astype(np.uint8)
        (dy, dx), psr = phase_correlate_match(img, img)
        assert abs(dy) < 0.6, f"dy={dy}"
        assert abs(dx) < 0.6, f"dx={dx}"
        assert psr > 20.0, f"PSR={psr}"

    def test_known_horizontal_shift(self):
        """Template shifted right by a known amount should be recovered."""
        rng = np.random.default_rng(1)
        ref = (rng.random((128, 256)) * 255).astype(np.uint8)
        shift = 40
        # Build a template that is the left region of ref shifted right
        tmpl = ref[:, shift: shift + 128].copy()
        # pad tmpl to ref size for the match
        (dy, dx), psr = phase_correlate_match(ref, tmpl)
        # The template appears at column `shift`, so dx ≈ shift
        assert abs(dx - shift) < 2.0, f"dx={dx} expected≈{shift}"
        assert psr > 10.0, f"PSR={psr}"

    def test_template_larger_than_reference_raises(self):
        ref = np.zeros((64, 64), dtype=np.uint8)
        tmpl = np.zeros((128, 128), dtype=np.uint8)
        with pytest.raises(ValueError, match="larger than the reference"):
            phase_correlate_match(ref, tmpl)

    def test_returns_float_offsets(self):
        rng = np.random.default_rng(2)
        img = (rng.random((64, 64)) * 255).astype(np.uint8)
        (dy, dx), psr = phase_correlate_match(img, img, upsample=1)
        assert isinstance(dy, float)
        assert isinstance(dx, float)
        assert isinstance(psr, float)

    def test_noisy_image_still_detects(self):
        """Phase correlation should handle moderate Gaussian noise."""
        rng = np.random.default_rng(3)
        ref = (rng.random((128, 128)) * 200 + 28).astype(np.uint8)
        noise = rng.normal(0, 15, ref.shape)
        noisy = np.clip(ref.astype(np.float64) + noise, 0, 255).astype(np.uint8)
        (dy, dx), psr = phase_correlate_match(ref, noisy)
        assert abs(dy) <= 2.0
        assert abs(dx) <= 2.0
        assert psr > 5.0, f"PSR={psr}"

    def test_window_flag(self):
        """Results with and without windowing should be close for aligned images."""
        rng = np.random.default_rng(4)
        img = (rng.random((128, 128)) * 255).astype(np.uint8)
        (dy_w, dx_w), _ = phase_correlate_match(img, img, apply_window=True)
        (dy_n, dx_n), _ = phase_correlate_match(img, img, apply_window=False)
        assert abs(dy_w - dy_n) < 1.0
        assert abs(dx_w - dx_n) < 1.0


# ---------------------------------------------------------------------------
# stitch_images_frequency tests
# ---------------------------------------------------------------------------

class TestStitchImagesFrequency:
    def test_output_wider_than_input(self):
        """Stitched panorama must be wider than a single input image."""
        img_l, img_r = _synthetic_pair(h=64, w=128, overlap=40)
        panorama, _, _ = stitch_images_frequency(img_l, img_r, overlap_hint=40)
        assert panorama.shape[1] > img_l.shape[1]

    def test_returns_tuple_with_psr(self):
        img_l, img_r = _synthetic_pair(h=64, w=128, overlap=40)
        result = stitch_images_frequency(img_l, img_r, overlap_hint=40)
        assert len(result) == 3
        panorama, (dy, dx), psr = result
        assert isinstance(panorama, np.ndarray)
        assert isinstance(dy, float)
        assert isinstance(dx, float)
        assert isinstance(psr, float)

    def test_color_image_stitching(self):
        """Stitching should work for 3-channel BGR images."""
        rng = np.random.default_rng(5)
        img_l = rng.integers(0, 255, (64, 128, 3), dtype=np.uint8)
        img_r = rng.integers(0, 255, (64, 128, 3), dtype=np.uint8)
        panorama, _, _ = stitch_images_frequency(img_l, img_r, overlap_hint=40)
        assert panorama.ndim == 3
        assert panorama.shape[2] == 3

    def test_grayscale_image_stitching(self):
        """Stitching should work for single-channel grayscale images."""
        img_l, img_r = _synthetic_pair(h=64, w=128, overlap=40)
        panorama, _, _ = stitch_images_frequency(img_l, img_r, overlap_hint=40)
        assert panorama.ndim == 2

    def test_output_dtype_uint8(self):
        """Canvas should remain uint8."""
        img_l, img_r = _synthetic_pair(h=64, w=128, overlap=40)
        panorama, _, _ = stitch_images_frequency(img_l, img_r, overlap_hint=40)
        assert panorama.dtype == np.uint8

    def test_no_overlap_hint(self):
        """None overlap_hint should fall back to half-width without crashing."""
        img_l, img_r = _synthetic_pair(h=64, w=128, overlap=64)
        panorama, _, _ = stitch_images_frequency(img_l, img_r, overlap_hint=None)
        assert panorama.shape[1] >= img_l.shape[1]


# ---------------------------------------------------------------------------
# FrequencyDomainStitcher tests
# ---------------------------------------------------------------------------

class TestFrequencyDomainStitcher:
    def test_single_image_returns_copy(self):
        img = np.zeros((64, 128), dtype=np.uint8)
        stitcher = FrequencyDomainStitcher()
        result = stitcher.stitch([img])
        np.testing.assert_array_equal(result, img)
        assert result is not img  # must be a copy

    def test_empty_list_raises(self):
        stitcher = FrequencyDomainStitcher()
        with pytest.raises(ValueError, match="empty"):
            stitcher.stitch([])

    def test_multi_image_stitch(self):
        """Three-image stitch should produce a wider panorama."""
        imgs = [_synthetic_pair(h=64, w=128, overlap=40)[0]] * 3
        stitcher = FrequencyDomainStitcher(overlap_hint=40)
        panorama = stitcher.stitch(imgs)
        assert panorama.shape[1] >= 128

    def test_match_template_below_threshold_returns_none(self):
        """A random template against a random screen should give low PSR → None."""
        rng = np.random.default_rng(7)
        screen = rng.integers(0, 255, (256, 256), dtype=np.uint8)
        template = rng.integers(0, 255, (64, 64), dtype=np.uint8)
        stitcher = FrequencyDomainStitcher(psr_threshold=1000.0)
        pos, psr = stitcher.match_template(screen, template)
        assert pos is None

    def test_match_template_above_threshold(self):
        """Identical images should easily pass threshold."""
        rng = np.random.default_rng(8)
        screen = (rng.random((128, 128)) * 255).astype(np.uint8)
        stitcher = FrequencyDomainStitcher(psr_threshold=5.0)
        pos, psr = stitcher.match_template(screen, screen)
        assert pos is not None
        assert psr > 5.0

    def test_psr_threshold_override(self):
        """Per-call psr_threshold should override the instance default."""
        rng = np.random.default_rng(9)
        screen = (rng.random((128, 128)) * 255).astype(np.uint8)
        stitcher = FrequencyDomainStitcher(psr_threshold=1000.0)
        # With a very low per-call threshold, identical images should match
        pos, psr = stitcher.match_template(screen, screen, psr_threshold=1.0)
        assert pos is not None
