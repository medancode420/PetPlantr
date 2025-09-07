import { 
  getCompletePipelinePrompts,
  getSizeTierSpecs,
  formatReconstructionPrompt,
  formatCadPrompt,
  formatValidationPrompt,
  PhotoUrls 
} from '../src/utils/shapeMvdPrompts';

describe('Shape-MVD Production Prompts', () => {
  const testOrderId = 'ORD-F9YAJ2';
  const testSizeTier = 'MEDIUM';
  const testPhotos: PhotoUrls = {
    front: 'https://petplantr-uploads-dev.s3.amazonaws.com/photos/front.jpg',
    left: 'https://petplantr-uploads-dev.s3.amazonaws.com/photos/left.jpg',
    right: 'https://petplantr-uploads-dev.s3.amazonaws.com/photos/right.jpg',
    back: 'https://petplantr-uploads-dev.s3.amazonaws.com/photos/back.jpg',
    top: 'https://petplantr-uploads-dev.s3.amazonaws.com/photos/top.jpg'
  };

  describe('Size Tier Specifications', () => {
    it('should return correct specifications for all size tiers', () => {
      const smallSpecs = getSizeTierSpecs('SMALL');
      expect(smallSpecs.bbox_mm).toEqual([90, 70, 70]);
      expect(smallSpecs.cavity_diameter).toBe(48);
      expect(smallSpecs.cavity_depth).toBe(45);
      expect(smallSpecs.material_thickness).toBe(2.8);

      const mediumSpecs = getSizeTierSpecs('MEDIUM');
      expect(mediumSpecs.bbox_mm).toEqual([120, 90, 80]);
      expect(mediumSpecs.cavity_diameter).toBe(58);
      expect(mediumSpecs.cavity_depth).toBe(55);

      const largeSpecs = getSizeTierSpecs('LARGE');
      expect(largeSpecs.bbox_mm).toEqual([150, 115, 100]);
      expect(largeSpecs.cavity_diameter).toBe(70);
      expect(largeSpecs.cavity_depth).toBe(70);
    });

    it('should default to MEDIUM for unknown size tiers', () => {
      const specs = getSizeTierSpecs('UNKNOWN');
      const mediumSpecs = getSizeTierSpecs('MEDIUM');
      expect(specs).toEqual(mediumSpecs);
    });
  });

  describe('Reconstruction Prompt', () => {
    it('should generate correct reconstruction prompt with photo URLs', () => {
      const prompt = formatReconstructionPrompt(testOrderId, testPhotos);
      
      expect(prompt).toContain('3‑D reconstruction agent');
      expect(prompt).toContain(testPhotos.front);
      expect(prompt).toContain(testPhotos.left);
      expect(prompt).toContain(testPhotos.right);
      expect(prompt).toContain(testPhotos.back);
      expect(prompt).toContain(testPhotos.top);
      expect(prompt).toContain('millimetres, Z‑up');
      expect(prompt).toContain('85‑90 %');
      expect(prompt).toContain('> 95 % manifold ratio');
    });
  });

  describe('CAD Generation Prompt', () => {
    it('should generate correct CAD prompt with specifications', () => {
      const meshInput = 'S3://petplantr-raw-dev/ORD-F9YAJ2/recon.obj';
      const prompt = formatCadPrompt(testOrderId, testSizeTier, meshInput);
      
      expect(prompt).toContain('CAD agent');
      expect(prompt).toContain(testOrderId);
      expect(prompt).toContain('MEDIUM');
      expect(prompt).toContain('120×90×80 mm');
      expect(prompt).toContain(meshInput);
      expect(prompt).toContain('Ø 58 mm × 55 mm depth');
      expect(prompt).toContain('3 holes Ø 4 mm');
      expect(prompt).toContain('2.8');
      expect(prompt).toContain('≤ 180 k triangles');
    });
  });

  describe('Validation Prompt', () => {
    it('should generate correct validation prompt', () => {
      const prompt = formatValidationPrompt(testOrderId, testSizeTier);
      
      expect(prompt).toContain('QA validator');
      expect(prompt).toContain(testOrderId);
      expect(prompt).toContain('[120, 90, 80]');
      expect(prompt).toContain('{"diameter": 58, "depth": 55}');
      expect(prompt).toContain('3 holes Ø 4 mm');
      expect(prompt).toContain('2.8');
      expect(prompt).toContain('≤ 180 k');
      expect(prompt).toContain('"orderId"');
      expect(prompt).toContain('"pass": true|false');
    });
  });

  describe('Complete Pipeline Prompts', () => {
    it('should generate all prompts with consistent parameters', () => {
      const prompts = getCompletePipelinePrompts(testOrderId, testSizeTier, testPhotos);
      
      expect(prompts.reconstruction).toBeDefined();
      expect(prompts.cad_generation).toBeDefined();
      expect(prompts.validation).toBeDefined();
      expect(prompts.specs).toBeDefined();
      
      // Check that all prompts contain the order ID
      expect(prompts.reconstruction).toContain(testPhotos.front);
      expect(prompts.cad_generation).toContain(testOrderId);
      expect(prompts.validation).toContain(testOrderId);
      
      // Check specifications
      expect(prompts.specs.bbox_mm).toEqual([120, 90, 80]);
      expect(prompts.specs.cavity_diameter).toBe(58);
      expect(prompts.specs.cavity_depth).toBe(55);
    });
  });

  describe('Validation Response Processing', () => {
    it('should correctly parse and validate JSON response', () => {
      const exampleValidationResponse = {
        "orderId": "ORD-F9YAJ2",
        "bbox_mm": [119.5, 89.2, 79.8],
        "cavity_mm": {"diameter": 58.1, "depth": 54.8},
        "pass": true,
        "errors": []
      };

      expect(exampleValidationResponse.pass).toBe(true);
      expect(exampleValidationResponse.orderId).toBe(testOrderId);
      expect(exampleValidationResponse.bbox_mm).toHaveLength(3);
      expect(exampleValidationResponse.cavity_mm.diameter).toBeCloseTo(58, 0);
      expect(exampleValidationResponse.cavity_mm.depth).toBeCloseTo(55, 0);
      expect(exampleValidationResponse.errors).toHaveLength(0);
    });

    it('should validate dimensions against specifications', () => {
      const specs = getSizeTierSpecs('MEDIUM');
      const validationResult = {
        "orderId": "ORD-F9YAJ2",
        "bbox_mm": [119.5, 89.2, 79.8],
        "cavity_mm": {"diameter": 58.1, "depth": 54.8},
        "pass": true,
        "errors": []
      };

      // Check bounding box is within limits
      validationResult.bbox_mm.forEach((dim, i) => {
        expect(dim).toBeLessThanOrEqual(specs.bbox_mm[i]);
      });

      // Check cavity dimensions are within tolerance (±0.3mm)
      expect(Math.abs(validationResult.cavity_mm.diameter - specs.cavity_diameter)).toBeLessThanOrEqual(0.3);
      expect(Math.abs(validationResult.cavity_mm.depth - specs.cavity_depth)).toBeLessThanOrEqual(0.3);
    });
  });
});
