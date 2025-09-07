/**
 * PetPlantr Shape-MVD Production Prompt Templates
 * High-quality 3D reconstruction and planter generation prompts
 */

export interface SizeTierSpec {
  bbox_mm: [number, number, number];
  cavity_diameter: number;
  cavity_depth: number;
  drain_holes: string;
  material_thickness: number;
}

export interface PhotoUrls {
  front: string;
  left: string;
  right: string;
  back: string;
  top: string;
}

export interface PipelinePrompts {
  reconstruction: string;
  cad_generation: string;
  validation: string;
  specs: SizeTierSpec;
}

// Size tier specifications
export const SIZE_TIER_SPECS: Record<string, SizeTierSpec> = {
  SMALL: {
    bbox_mm: [90, 70, 70],
    cavity_diameter: 48,
    cavity_depth: 45,
    drain_holes: "3 holes Ø 4 mm",
    material_thickness: 2.8
  },
  MEDIUM: {
    bbox_mm: [120, 90, 80],
    cavity_diameter: 58,
    cavity_depth: 55,
    drain_holes: "3 holes Ø 4 mm",
    material_thickness: 2.8
  },
  LARGE: {
    bbox_mm: [150, 115, 100],
    cavity_diameter: 70,
    cavity_depth: 70,
    drain_holes: "3 holes Ø 4 mm",
    material_thickness: 2.8
  }
};

// Part A - Pet Geometry Reconstruction Prompt
export const PET_RECONSTRUCTION_PROMPT = `You are a 3‑D reconstruction agent that converts 5 calibrated photos of a single
pet into a watertight, manifold triangular mesh.

Photos:
• Front:  {FRONT_IMG}
• Left:   {LEFT_IMG}
• Right:  {RIGHT_IMG}
• Back:   {BACK_IMG}
• Top:    {TOP_IMG}

OUTPUT requirements
-------------------
• Mesh units: millimetres, Z‑up.
• Pet head and muzzle must occupy 85‑90 % of the bounding box front‑to‑back.
• Ears, fur tufts and whiskers need at least 0.4 mm feature size.
• No self‑intersections; > 95 % manifold ratio.
Return ONLY the binary .obj content (base‑64) OR a signed S3 URL.`;

// Part B - Planter Cavity & Scaling Prompt
export const PLANTER_CAD_PROMPT = `You are a CAD agent that receives a high‑resolution pet mesh and turns it into a
functional planter.

Input mesh: {MESH_INPUT}
Requested size tier: {SIZE_TIER}  Target outer bounding box: {TARGET_BBOX}

TASKS
1. Scale the pet mesh so the longest dimension equals the bounding‑box limit.
2. Hollow the rear 40 % of the model with a **plant cavity**:
   – Internal cylinder {CAVITY_DIM} centred on Z‑axis.
   – Minimum wall thickness {MATERIAL_THK} everywhere.
3. Boolean‑subtract **{DRAIN_HOLES}** through the base.
4. Add a 2 mm chamfer on the rim for print cleanliness.
5. Ensure final mesh ≤ 180 k triangles and remains manifold.

Return \`petplantr_{ORDER_ID}.stl\` base‑64 OR presigned S3 url.`;

// Part C - Design Rule Validation Prompt
export const VALIDATION_PROMPT = `You are a QA validator.

Input: petplantr_{ORDER_ID}.stl
Checklist:
✔ Bounding box ≤ {TARGET_BBOX}
✔ Cavity exactly {CAVITY_DIM} ± 0.3 mm
✔ Wall thickness ≥ {MATERIAL_THK} everywhere
✔ Drain holes present: {DRAIN_HOLES}
✔ No non‑manifold edges
✔ Triangle count ≤ 180 k

Return JSON:
{
  "orderId": "{ORDER_ID}",
  "bbox_mm": [x,y,z],
  "cavity_mm": {"diameter": d, "depth": z},
  "pass": true|false,
  "errors": [...]
}`;

export function getSizeTierSpecs(sizeTier: string): SizeTierSpec {
  return SIZE_TIER_SPECS[sizeTier.toUpperCase()] || SIZE_TIER_SPECS.MEDIUM;
}

export function formatReconstructionPrompt(orderId: string, photoUrls: PhotoUrls): string {
  return PET_RECONSTRUCTION_PROMPT
    .replace('{ORDER_ID}', orderId)
    .replace('{FRONT_IMG}', photoUrls.front)
    .replace('{LEFT_IMG}', photoUrls.left)
    .replace('{RIGHT_IMG}', photoUrls.right)
    .replace('{BACK_IMG}', photoUrls.back)
    .replace('{TOP_IMG}', photoUrls.top);
}

export function formatCadPrompt(
  orderId: string, 
  sizeTier: string, 
  meshInput: string, 
  plantSpec: string = '2.5" nursery succulent pot'
): string {
  const specs = getSizeTierSpecs(sizeTier);
  
  return PLANTER_CAD_PROMPT
    .replace('{ORDER_ID}', orderId)
    .replace('{SIZE_TIER}', sizeTier.toUpperCase())
    .replace('{TARGET_BBOX}', `${specs.bbox_mm[0]}×${specs.bbox_mm[1]}×${specs.bbox_mm[2]} mm`)
    .replace('{MESH_INPUT}', meshInput)
    .replace('{PLANT_SPEC}', plantSpec)
    .replace('{CAVITY_DIM}', `Ø ${specs.cavity_diameter} mm × ${specs.cavity_depth} mm depth`)
    .replace('{DRAIN_HOLES}', specs.drain_holes)
    .replace('{MATERIAL_THK}', specs.material_thickness.toString());
}

export function formatValidationPrompt(orderId: string, sizeTier: string): string {
  const specs = getSizeTierSpecs(sizeTier);
  
  return VALIDATION_PROMPT
    .replace(/{ORDER_ID}/g, orderId)
    .replace('{TARGET_BBOX}', `[${specs.bbox_mm[0]}, ${specs.bbox_mm[1]}, ${specs.bbox_mm[2]}]`)
    .replace('{CAVITY_DIM}', `{"diameter": ${specs.cavity_diameter}, "depth": ${specs.cavity_depth}}`)
    .replace('{DRAIN_HOLES}', specs.drain_holes)
    .replace('{MATERIAL_THK}', specs.material_thickness.toString());
}

export function getCompletePipelinePrompts(
  orderId: string, 
  sizeTier: string, 
  photoUrls: PhotoUrls, 
  meshInput?: string
): PipelinePrompts {
  // If mesh_input is not provided, use S3 convention
  const actualMeshInput = meshInput || `S3://petplantr-raw-dev/${orderId}/recon.obj`;
  
  return {
    reconstruction: formatReconstructionPrompt(orderId, photoUrls),
    cad_generation: formatCadPrompt(orderId, sizeTier, actualMeshInput),
    validation: formatValidationPrompt(orderId, sizeTier),
    specs: getSizeTierSpecs(sizeTier)
  };
}
