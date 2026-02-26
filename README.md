# KingshotAuto

Game automation script for Kingshot / Whiteout Survival using Python + OpenCV template matching.

---

## Frequency-Domain Image Stitching

### Algorithm: Phase Correlation (FFT)

The chosen stitching algorithm is **Phase Correlation via the 2-D FFT**
(Kuglin & Hines, 1975; extended by Foroosh et al., 2002).

#### How it works

1. **Convert to frequency domain** – apply `numpy.fft.fft2` to both images
   (optionally with a Hann window to reduce spectral leakage).
2. **Normalized cross-power spectrum** – multiply the FFT of image A by the
   complex conjugate of the FFT of image B, then divide element-wise by the
   magnitude.  This retains *only phase information* (hence the name).
3. **Inverse FFT** – the result is a correlation surface with a single, sharp
   Dirac-like peak at the (dy, dx) translation offset between the images.
4. **Sub-pixel refinement** – fit a parabola through the 3 × 3 neighbourhood
   of the coarse peak to get sub-pixel accuracy.
5. **Blend** – place both images on a canvas using the recovered offset, with a
   linear alpha ramp in the overlap zone.

An optional **Log-Polar pre-transform** (Fourier-Mellin) can handle rotation
and scale before step 1, enabling full similarity-motion estimation.

#### Why Phase Correlation?

| Property | Spatial `matchTemplate` | Phase Correlation (FFT) |
|---|---|---|
| Complexity | O(H·W·h·w) | O(N log N) |
| Sub-pixel accuracy | No | Yes (parabolic fit) |
| Noise robustness | Moderate | High (phase-only) |
| Illumination invariant | No | Mostly yes |
| Rotation / scale | No | Yes (+ Log-Polar) |
| Confidence metric | Raw score | PSR (peak-to-sidelobe) |

#### Implementation files

| File | Purpose |
|---|---|
| `frequency_stitch.py` | Core algorithm: `phase_correlate_match`, `stitch_images_frequency`, `FrequencyDomainStitcher` |
| `test_frequency_stitch.py` | 18 pytest unit tests covering all public functions |

#### Quick start

```python
import cv2
from frequency_stitch import FrequencyDomainStitcher

stitcher = FrequencyDomainStitcher(overlap_hint=200, blend_width=64)

# Stitch a list of horizontally ordered screenshots
frames = [cv2.imread(f"frame{i}.png") for i in range(4)]
panorama = stitcher.stitch(frames)
cv2.imwrite("panorama.png", panorama)

# Frequency-domain template match (drop-in for cv2.matchTemplate)
screen = cv2.imread("screen.png", cv2.IMREAD_GRAYSCALE)
template = cv2.imread("icon.png", cv2.IMREAD_GRAYSCALE)
pos, psr = stitcher.match_template(screen, template)
if pos is not None:
    print(f"Found at (dy={pos[0]:.1f}, dx={pos[1]:.1f}), PSR={psr:.1f}")
```

---

### Implementation Timeframe

| Phase | Days | Deliverables |
|---|---|---|
| **1 – Core algorithm** | Days 1-2 | `phase_correlate_match()`, Hann window, PSR metric, unit tests |
| **2 – Stitcher class** | Days 3-4 | `stitch_images_frequency()`, `FrequencyDomainStitcher`, alpha blending |
| **3 – Rotation & scale** | Days 5-6 | Log-Polar pre-transform, `stitch_with_rotation()`, extended tests |
| **4 – Integration** | Day 7 | Drop-in replacement for `cv2.matchTemplate` in `minfar.py`, benchmarks |

**Total: ~7 developer-days** (one engineer, focused sprint)

Phases 1-2 are already complete and tested.  Phases 3-4 are optional
enhancements that can be added incrementally without breaking the existing API.
