"""
Procedural Dog Planter generator (lightweight, no external deps)

Generates a watertight, parametric planter as ASCII STL. Parameters allow
size, wall thickness, and drainage options. Breed hint is used to vary
subtle geometry (segments and taper) for fun differentiation.
"""
from __future__ import annotations

import os
import time
import math
import hashlib
import logging
from typing import Optional, Dict, Any, Iterable, Tuple, List, Callable

logger = logging.getLogger(__name__)


def _hash_seed(text: str) -> int:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _normal(a: Tuple[float, float, float], b: Tuple[float, float, float], c: Tuple[float, float, float]) -> Tuple[float, float, float]:
    # Compute triangle normal using cross product (unnormalized is acceptable for STL)
    ux, uy, uz = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    vx, vy, vz = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    # Avoid zero normals
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / length, ny / length, nz / length)


def _ring(radius: float, z: float, segments: int, phase: float = 0.0) -> List[Tuple[float, float, float]]:
    pts: List[Tuple[float, float, float]] = []
    for i in range(segments):
        ang = 2.0 * math.pi * (i / segments) + phase
        pts.append((radius * math.cos(ang), radius * math.sin(ang), z))
    return pts


def _ring_modulated(
    base_radius: float,
    z: float,
    segments: int,
    phase: float,
    delta_fn: Optional[Callable[[float], float]],
) -> List[Tuple[float, float, float]]:
    pts: List[Tuple[float, float, float]] = []
    for i in range(segments):
        ang = 2.0 * math.pi * (i / segments) + phase
        delta = delta_fn(ang) if delta_fn else 0.0
        r = max(1e-3, base_radius + delta)
        pts.append((r * math.cos(ang), r * math.sin(ang), z))
    return pts


def _write_facet(f, a, b, c):
    nx, ny, nz = _normal(a, b, c)
    f.write(f"  facet normal {nx:.6f} {ny:.6f} {nz:.6f}\n")
    f.write("    outer loop\n")
    f.write(f"      vertex {a[0]:.6f} {a[1]:.6f} {a[2]:.6f}\n")
    f.write(f"      vertex {b[0]:.6f} {b[1]:.6f} {b[2]:.6f}\n")
    f.write(f"      vertex {c[0]:.6f} {c[1]:.6f} {c[2]:.6f}\n")
    f.write("    endloop\n")
    f.write("  endfacet\n")


def _stitch_quads(f, lower: List[Tuple[float, float, float]], upper: List[Tuple[float, float, float]]):
    # Assumes same length arrays, wraps around
    n = len(lower)
    for i in range(n):
        j = (i + 1) % n
        a = lower[i]
        b = lower[j]
        c = upper[j]
        d = upper[i]
        # Two triangles: a-b-c and a-c-d
        _write_facet(f, a, b, c)
        _write_facet(f, a, c, d)


class ImprovedNeuralDogPlanter:
    """Procedural planter generator.

    Creates a parametric cylindrical planter with optional taper and drainage hole.
    Units: millimeters (1 unit = 1 mm in STL).
    """

    def __init__(self) -> None:
        logger.info("ImprovedNeuralDogPlanter initialized (procedural mode)")

    def generate_dog_planter(
        self,
        input_image_path: str,
        output_stl_path: str,
        breed_hint: Optional[str] = None,
        *,
        planter_diameter_mm: float = 120.0,
        height_mm: float = 100.0,
        wall_thickness_mm: float = 3.0,
        base_thickness_mm: float = 3.0,
        include_drainage: bool = True,
        drainage_hole_mm: float = 6.0,
        segments: Optional[int] = None,
        rim_lip_mm: float = 1.5,
        taper_ratio: Optional[float] = None,  # 0.0 (straight) to 0.3 (noticeable taper)
        # Advanced shaping options
        pattern: str = "smooth",  # smooth | fluted | faceted | breed
        pattern_amplitude_mm: float = 1.2,
        pattern_frequency: int = 8,
        twist_turns: float = 0.25,  # number of full twists along height
        include_ear_tabs: bool = False,
        ear_size_mm: float = 4.0,
        ear_width_deg: float = 30.0,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(output_stl_path) or ".", exist_ok=True)

        # Derive deterministic style from breed hint (segments/taper)
        seed = _hash_seed(breed_hint) if breed_hint else 0xA5A5A5A5
        if segments is None:
            segments = 24 + (seed % 17)  # 24..40
        if taper_ratio is None:
            taper_ratio = 0.05 + ((seed >> 8) % 21) / 100.0  # 0.05..0.25

        # Breed-influenced defaults when pattern='breed'
        if pattern == "breed" and breed_hint:
            bh = breed_hint.lower()
            if any(k in bh for k in ["greyhound", "whippet", "doberman", "husky", "shiba"]):
                pattern = "fluted"; pattern_frequency = 12; pattern_amplitude_mm = 1.0; twist_turns = 0.35
            elif any(k in bh for k in ["bulldog", "pug", "mastiff", "boxer"]):
                pattern = "faceted"; segments = max(20, segments - 4); pattern_frequency = 8; pattern_amplitude_mm = 1.6; twist_turns = 0.1
            elif any(k in bh for k in ["retriever", "labrador", "collie", "beagle"]):
                pattern = "fluted"; pattern_frequency = 10; pattern_amplitude_mm = 1.2; twist_turns = 0.2
            else:
                pattern = "fluted"; pattern_frequency = 9; pattern_amplitude_mm = 1.1; twist_turns = 0.2

        outer_r_bottom = max(10.0, planter_diameter_mm * 0.5)
        outer_r_top = max(8.0, outer_r_bottom * (1.0 - taper_ratio))
        inner_r_bottom = max(1.0, outer_r_bottom - wall_thickness_mm)
        inner_r_top = max(1.0, outer_r_top - wall_thickness_mm)

        # Drainage hole radius (in base). Ensure it's smaller than inner radius
        drain_r = min(max(0.0, drainage_hole_mm * 0.5), inner_r_bottom - 1.0) if include_drainage else 0.0

        start = time.time()
        with open(output_stl_path, "w") as f:
            f.write("solid PetPlantrProcedural\n")

            # Bottom ring (base_thickness), with optional central drainage hole (ring fill)
            z0 = 0.0
            z1 = base_thickness_mm

            # Prepare modulation function (same delta applied to outer/inner to keep thickness roughly constant)
            amp = max(0.0, float(pattern_amplitude_mm))
            freq = max(0, int(pattern_frequency))
            ear_sigma = max(1e-3, math.radians(ear_width_deg) / 2.355)

            def delta_fn(theta: float) -> float:
                d = 0.0
                if pattern == "fluted" and freq > 0 and amp > 0.0:
                    d += amp * math.sin(freq * theta)
                elif pattern == "faceted" and freq > 0 and amp > 0.0:
                    d += amp * (2.0 / math.pi) * math.asin(math.sin(freq * theta))
                if include_ear_tabs and ear_size_mm > 0.0:
                    def gauss(center: float) -> float:
                        x = min(abs(((theta - center + math.pi) % (2 * math.pi)) - math.pi), math.pi)
                        return math.exp(-0.5 * (x / ear_sigma) ** 2)
                    d += ear_size_mm * (gauss(0.0) + gauss(math.pi))
                return d

            def phase_at(zv: float) -> float:
                if height_mm <= 0:
                    return 0.0
                return 2.0 * math.pi * twist_turns * ((zv - z0) / max(1e-6, height_mm))

            outer0 = _ring_modulated(outer_r_bottom, z0, segments, phase_at(z0), delta_fn if pattern != "smooth" or include_ear_tabs else None)
            outer1 = _ring_modulated(outer_r_bottom, z1, segments, phase_at(z1), delta_fn if pattern != "smooth" or include_ear_tabs else None)
            inner0 = _ring_modulated(inner_r_bottom, z0, segments, phase_at(z0), delta_fn if pattern != "smooth" or include_ear_tabs else None)
            inner1 = _ring_modulated(inner_r_bottom, z1, segments, phase_at(z1), delta_fn if pattern != "smooth" or include_ear_tabs else None)

            # If no drainage, bottom is a full disc from center to outer; else a ring
            if drain_r <= 0.0:
                center0 = (0.0, 0.0, z0)
                for i in range(segments):
                    j = (i + 1) % segments
                    _write_facet(f, center0, outer0[j], outer0[i])
                center1 = (0.0, 0.0, z1)
                for i in range(segments):
                    j = (i + 1) % segments
                    _write_facet(f, outer1[i], outer1[j], center1)
            else:
                drain0 = _ring(drain_r, z0, segments)
                drain1 = _ring(drain_r, z1, segments)
                for i in range(segments):
                    j = (i + 1) % segments
                    _write_facet(f, drain0[i], outer0[j], outer0[i])
                    _write_facet(f, drain0[i], drain0[j], outer0[j])
                    _write_facet(f, outer1[i], drain1[i], outer1[j])
                    _write_facet(f, outer1[j], drain1[i], drain1[j])
                _stitch_quads(f, drain0, drain1)

            # Base side walls
            _stitch_quads(f, outer0, outer1)
            _stitch_quads(f, inner1, inner0)

            # Vertical walls up to height_mm with taper
            z2 = height_mm
            outer_top = _ring_modulated(outer_r_top, z2, segments, phase_at(z2), delta_fn if pattern != "smooth" or include_ear_tabs else None)
            inner_top = _ring_modulated(inner_r_top, z2, segments, phase_at(z2), delta_fn if pattern != "smooth" or include_ear_tabs else None)
            _stitch_quads(f, outer1, outer_top)
            _stitch_quads(f, inner_top, inner1)

            if rim_lip_mm > 0.0:
                lip_outer = _ring_modulated(outer_r_top + rim_lip_mm, z2, segments, phase_at(z2), delta_fn if pattern != "smooth" or include_ear_tabs else None)
                _stitch_quads(f, outer_top, lip_outer)
                for i in range(segments):
                    j = (i + 1) % segments
                    _write_facet(f, inner_top[i], lip_outer[j], lip_outer[i])
                    _write_facet(f, inner_top[i], inner_top[j], lip_outer[j])

            f.write("endsolid PetPlantrProcedural\n")

        dur = time.time() - start
        complexity = (1 if pattern == "smooth" else 2) + (1 if include_ear_tabs else 0) + (1 if twist_turns else 0)
        quality_score = min(99.0, 60.0 + (segments - 20) * 0.8 + wall_thickness_mm * 3.0 + taper_ratio * 20.0 + complexity * 2.0)

        # Rough internal volume estimate (ml): treat as frustum ignoring modulation
        r1 = inner_r_bottom
        r2 = inner_r_top
        h = max(0.0, height_mm - base_thickness_mm)
        volume_mm3 = (math.pi * h * (r1 * r1 + r1 * r2 + r2 * r2) / 3.0)
        soil_ml = round(volume_mm3 / 1000.0, 1)

        logger.info(
            "Generated procedural planter at %s in %.2fs | Ø=%.1fmm, H=%.1fmm, wall=%.1fmm, seg=%d, taper=%.2f, drainage=%s(%.1fmm)",
            output_stl_path,
            dur,
            outer_r_bottom * 2.0,
            height_mm,
            wall_thickness_mm,
            segments,
            taper_ratio,
            "yes" if drain_r > 0.0 else "no",
            drainage_hole_mm,
        )

        return {
            "quality_score": round(quality_score, 2),
            "duration": round(dur, 3),
            "output_path": output_stl_path,
            "params": {
                "diameter_mm": round(outer_r_bottom * 2.0, 2),
                "height_mm": height_mm,
                "wall_thickness_mm": wall_thickness_mm,
                "base_thickness_mm": base_thickness_mm,
                "segments": segments,
                "taper_ratio": round(taper_ratio, 3),
                "include_drainage": include_drainage,
                "drainage_hole_mm": drainage_hole_mm,
                "breed_hint": breed_hint or "",
                "pattern": pattern,
                "pattern_amplitude_mm": pattern_amplitude_mm,
                "pattern_frequency": pattern_frequency,
                "twist_turns": twist_turns,
                "include_ear_tabs": include_ear_tabs,
                "ear_size_mm": ear_size_mm,
                "ear_width_deg": ear_width_deg,
            },
            "estimates": {
                "soil_capacity_ml": soil_ml
            },
        }

    def generate_planter(
        self,
        input_image_path: str,
        output_stl_path: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # Alias to generate_dog_planter for compatibility
        return self.generate_dog_planter(input_image_path, output_stl_path, **kwargs)
