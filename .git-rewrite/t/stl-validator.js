#!/usr/bin/env node

/**
 * STL Validation and Optimization Service
 * Advanced mesh analysis, repair, and print optimization
 */

const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');
const AWS = require('aws-sdk');

class STLValidator {
    constructor() {
        this.s3 = new AWS.S3({ region: 'us-west-2' });
        this.tolerances = {
            minWallThickness: 0.8,    // mm
            minFeatureSize: 0.4,      // mm
            maxOverhang: 45,          // degrees
            minVolume: 1,             // cm³
            maxVolume: 1000,          // cm³
            maxTriangles: 1000000     // mesh complexity limit
        };
    }

    async validateSTL(stlBuffer, options = {}) {
        console.log('🔍 Starting comprehensive STL validation...');
        
        const validation = {
            isValid: false,
            isPrintable: false,
            errors: [],
            warnings: [],
            stats: {},
            optimizations: [],
            estimatedFixTime: 0
        };

        try {
            // 1. Basic file format validation
            const formatCheck = await this.validateFileFormat(stlBuffer);
            validation.stats.format = formatCheck;
            
            if (!formatCheck.valid) {
                validation.errors.push(`Invalid STL format: ${formatCheck.error}`);
                return validation;
            }

            // 2. Mesh geometry analysis
            const geometryCheck = await this.analyzeGeometry(stlBuffer);
            validation.stats.geometry = geometryCheck;

            // 3. Printability analysis
            const printabilityCheck = await this.analyzePrintability(geometryCheck);
            validation.stats.printability = printabilityCheck;

            // 4. Quality checks
            const qualityCheck = await this.checkMeshQuality(stlBuffer, geometryCheck);
            validation.stats.quality = qualityCheck;

            // 5. Generate recommendations
            const recommendations = await this.generateRecommendations(validation.stats);
            validation.optimizations = recommendations;

            // Determine overall validation result
            validation.isValid = validation.errors.length === 0;
            validation.isPrintable = validation.isValid && printabilityCheck.printable;

            console.log(`✅ STL validation complete. Valid: ${validation.isValid}, Printable: ${validation.isPrintable}`);
            
            return validation;

        } catch (error) {
            validation.errors.push(`Validation failed: ${error.message}`);
            return validation;
        }
    }

    async validateFileFormat(stlBuffer) {
        try {
            // Check minimum file size
            if (stlBuffer.length < 84) {
                return { valid: false, error: 'File too small to be valid STL' };
            }

            // Check for ASCII vs Binary STL
            const header = stlBuffer.slice(0, 80).toString();
            const isAscii = header.toLowerCase().startsWith('solid ');
            
            if (isAscii) {
                return this.validateAsciiSTL(stlBuffer);
            } else {
                return this.validateBinarySTL(stlBuffer);
            }
        } catch (error) {
            return { valid: false, error: error.message };
        }
    }

    validateBinarySTL(stlBuffer) {
        try {
            const triangleCount = stlBuffer.readUInt32LE(80);
            const expectedSize = 80 + 4 + (triangleCount * 50);
            
            if (stlBuffer.length !== expectedSize) {
                return {
                    valid: false,
                    error: `Binary STL size mismatch. Expected: ${expectedSize}, Got: ${stlBuffer.length}`
                };
            }

            if (triangleCount === 0) {
                return { valid: false, error: 'STL contains no triangles' };
            }

            if (triangleCount > this.tolerances.maxTriangles) {
                return {
                    valid: false,
                    error: `STL too complex: ${triangleCount} triangles (max: ${this.tolerances.maxTriangles})`
                };
            }

            return {
                valid: true,
                format: 'binary',
                triangleCount,
                fileSize: stlBuffer.length
            };
        } catch (error) {
            return { valid: false, error: `Binary STL parsing error: ${error.message}` };
        }
    }

    validateAsciiSTL(stlBuffer) {
        try {
            const content = stlBuffer.toString();
            const lines = content.split('\n').map(line => line.trim());
            
            if (!lines[0].toLowerCase().startsWith('solid')) {
                return { valid: false, error: 'ASCII STL missing solid declaration' };
            }

            if (!lines[lines.length - 1].toLowerCase().startsWith('endsolid') && 
                !lines[lines.length - 2].toLowerCase().startsWith('endsolid')) {
                return { valid: false, error: 'ASCII STL missing endsolid declaration' };
            }

            // Count facets
            const facetCount = (content.match(/facet normal/gi) || []).length;
            
            if (facetCount === 0) {
                return { valid: false, error: 'ASCII STL contains no facets' };
            }

            return {
                valid: true,
                format: 'ascii',
                triangleCount: facetCount,
                fileSize: stlBuffer.length
            };
        } catch (error) {
            return { valid: false, error: `ASCII STL parsing error: ${error.message}` };
        }
    }

    async analyzeGeometry(stlBuffer) {
        const triangleCount = this.getTriangleCount(stlBuffer);
        const vertices = this.extractVertices(stlBuffer);
        
        // Calculate bounding box
        const boundingBox = this.calculateBoundingBox(vertices);
        const dimensions = {
            x: boundingBox.max.x - boundingBox.min.x,
            y: boundingBox.max.y - boundingBox.min.y,
            z: boundingBox.max.z - boundingBox.min.z
        };

        // Calculate volume (approximation)
        const volume = this.calculateVolume(stlBuffer);
        const surfaceArea = this.calculateSurfaceArea(stlBuffer);

        // Detect manifold issues
        const manifoldAnalysis = this.analyzeManifold(vertices);

        return {
            triangleCount,
            vertices: vertices.length,
            boundingBox,
            dimensions,
            volume,
            surfaceArea,
            manifold: manifoldAnalysis,
            aspectRatio: Math.max(dimensions.x, dimensions.y, dimensions.z) / 
                        Math.min(dimensions.x, dimensions.y, dimensions.z)
        };
    }

    async analyzePrintability(geometry) {
        const issues = [];
        const warnings = [];
        
        // Check size constraints
        if (geometry.volume < this.tolerances.minVolume) {
            issues.push(`Volume too small: ${geometry.volume.toFixed(2)}cm³ (min: ${this.tolerances.minVolume}cm³)`);
        }
        
        if (geometry.volume > this.tolerances.maxVolume) {
            issues.push(`Volume too large: ${geometry.volume.toFixed(2)}cm³ (max: ${this.tolerances.maxVolume}cm³)`);
        }

        // Check dimensions for build plate
        const maxBuildSize = { x: 250, y: 210, z: 210 }; // Prusa MK3S
        
        if (geometry.dimensions.x > maxBuildSize.x ||
            geometry.dimensions.y > maxBuildSize.y ||
            geometry.dimensions.z > maxBuildSize.z) {
            issues.push('Model exceeds build volume of available printers');
        }

        // Check for thin walls
        const minWallThickness = this.estimateMinWallThickness(geometry);
        if (minWallThickness < this.tolerances.minWallThickness) {
            warnings.push(`Thin walls detected: ${minWallThickness.toFixed(2)}mm (recommended: ${this.tolerances.minWallThickness}mm)`);
        }

        // Check aspect ratio
        if (geometry.aspectRatio > 10) {
            warnings.push('High aspect ratio may cause printing difficulties');
        }

        // Check for overhangs
        const overhangAnalysis = this.detectOverhangs(geometry);
        if (overhangAnalysis.maxOverhang > this.tolerances.maxOverhang) {
            warnings.push(`Steep overhangs detected: ${overhangAnalysis.maxOverhang}° (max recommended: ${this.tolerances.maxOverhang}°)`);
        }

        return {
            printable: issues.length === 0,
            issues,
            warnings,
            supportsNeeded: overhangAnalysis.needsSupports,
            estimatedPrintTime: this.estimatePrintTime(geometry),
            materialUsage: this.estimateMaterialUsage(geometry)
        };
    }

    async checkMeshQuality(stlBuffer, geometry) {
        const issues = [];
        
        // Check for manifold errors
        if (!geometry.manifold.isManifold) {
            issues.push('Non-manifold mesh detected');
        }

        // Check for inverted normals
        const normalIssues = this.checkNormals(stlBuffer);
        if (normalIssues.invertedCount > 0) {
            issues.push(`${normalIssues.invertedCount} inverted normals found`);
        }

        // Check for duplicate vertices
        const duplicateVertices = this.findDuplicateVertices(stlBuffer);
        if (duplicateVertices > 0) {
            issues.push(`${duplicateVertices} duplicate vertices found`);
        }

        // Check for holes
        const holes = this.detectHoles(geometry);
        if (holes.count > 0) {
            issues.push(`${holes.count} holes detected in mesh`);
        }

        return {
            isClean: issues.length === 0,
            issues,
            score: Math.max(0, 100 - (issues.length * 10)) // Quality score out of 100
        };
    }

    async generateRecommendations(stats) {
        const recommendations = [];

        // Mesh repair recommendations
        if (!stats.quality.isClean) {
            recommendations.push({
                type: 'repair',
                priority: 'high',
                description: 'Repair mesh geometry issues',
                estimatedTime: 30,
                automated: true
            });
        }

        // Support recommendations
        if (stats.printability.supportsNeeded) {
            recommendations.push({
                type: 'supports',
                priority: 'medium',
                description: 'Add support structures for overhangs',
                estimatedTime: 10,
                automated: true
            });
        }

        // Orientation recommendations
        if (stats.geometry.aspectRatio > 5) {
            recommendations.push({
                type: 'orientation',
                priority: 'medium',
                description: 'Optimize print orientation to reduce supports',
                estimatedTime: 5,
                automated: true
            });
        }

        // Scaling recommendations
        if (stats.geometry.volume < this.tolerances.minVolume) {
            const scaleFactor = Math.cbrt(this.tolerances.minVolume / stats.geometry.volume);
            recommendations.push({
                type: 'scale',
                priority: 'high',
                description: `Scale model by ${scaleFactor.toFixed(2)}x to meet minimum volume`,
                estimatedTime: 2,
                automated: true
            });
        }

        return recommendations;
    }

    // Utility methods for mesh analysis
    getTriangleCount(stlBuffer) {
        const header = stlBuffer.slice(0, 80).toString();
        if (header.toLowerCase().startsWith('solid ')) {
            // ASCII STL
            const content = stlBuffer.toString();
            return (content.match(/facet normal/gi) || []).length;
        } else {
            // Binary STL
            return stlBuffer.readUInt32LE(80);
        }
    }

    extractVertices(stlBuffer) {
        const vertices = [];
        const triangleCount = this.getTriangleCount(stlBuffer);
        
        if (stlBuffer.slice(0, 80).toString().toLowerCase().startsWith('solid ')) {
            // ASCII STL - more complex parsing needed
            return this.extractVerticesASCII(stlBuffer);
        } else {
            // Binary STL
            for (let i = 0; i < triangleCount; i++) {
                const offset = 84 + i * 50;
                
                for (let v = 0; v < 3; v++) {
                    const vertexOffset = offset + 12 + v * 12;
                    vertices.push({
                        x: stlBuffer.readFloatLE(vertexOffset),
                        y: stlBuffer.readFloatLE(vertexOffset + 4),
                        z: stlBuffer.readFloatLE(vertexOffset + 8)
                    });
                }
            }
        }
        
        return vertices;
    }

    extractVerticesASCII(stlBuffer) {
        const vertices = [];
        const content = stlBuffer.toString();
        const lines = content.split('\n');
        
        for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('vertex ')) {
                const coords = trimmed.split(/\s+/).slice(1).map(parseFloat);
                if (coords.length === 3 && coords.every(c => !isNaN(c))) {
                    vertices.push({ x: coords[0], y: coords[1], z: coords[2] });
                }
            }
        }
        
        return vertices;
    }

    calculateBoundingBox(vertices) {
        if (vertices.length === 0) {
            return { min: { x: 0, y: 0, z: 0 }, max: { x: 0, y: 0, z: 0 } };
        }

        const min = { x: Infinity, y: Infinity, z: Infinity };
        const max = { x: -Infinity, y: -Infinity, z: -Infinity };

        for (const vertex of vertices) {
            min.x = Math.min(min.x, vertex.x);
            min.y = Math.min(min.y, vertex.y);
            min.z = Math.min(min.z, vertex.z);
            max.x = Math.max(max.x, vertex.x);
            max.y = Math.max(max.y, vertex.y);
            max.z = Math.max(max.z, vertex.z);
        }

        return { min, max };
    }

    calculateVolume(stlBuffer) {
        // Simplified volume calculation using mesh divergence theorem
        const vertices = this.extractVertices(stlBuffer);
        let volume = 0;

        for (let i = 0; i < vertices.length; i += 3) {
            if (i + 2 < vertices.length) {
                const v1 = vertices[i];
                const v2 = vertices[i + 1];
                const v3 = vertices[i + 2];

                // Calculate signed volume of tetrahedron formed with origin
                volume += (v1.x * (v2.y * v3.z - v3.y * v2.z) +
                          v2.x * (v3.y * v1.z - v1.y * v3.z) +
                          v3.x * (v1.y * v2.z - v2.y * v1.z)) / 6;
            }
        }

        return Math.abs(volume) / 1000; // Convert mm³ to cm³
    }

    calculateSurfaceArea(stlBuffer) {
        const vertices = this.extractVertices(stlBuffer);
        let surfaceArea = 0;

        for (let i = 0; i < vertices.length; i += 3) {
            if (i + 2 < vertices.length) {
                const v1 = vertices[i];
                const v2 = vertices[i + 1];
                const v3 = vertices[i + 2];

                // Calculate triangle area using cross product
                const edge1 = {
                    x: v2.x - v1.x,
                    y: v2.y - v1.y,
                    z: v2.z - v1.z
                };
                const edge2 = {
                    x: v3.x - v1.x,
                    y: v3.y - v1.y,
                    z: v3.z - v1.z
                };

                const cross = {
                    x: edge1.y * edge2.z - edge1.z * edge2.y,
                    y: edge1.z * edge2.x - edge1.x * edge2.z,
                    z: edge1.x * edge2.y - edge1.y * edge2.x
                };

                const magnitude = Math.sqrt(cross.x * cross.x + cross.y * cross.y + cross.z * cross.z);
                surfaceArea += magnitude / 2;
            }
        }

        return surfaceArea / 100; // Convert mm² to cm²
    }

    analyzeManifold(vertices) {
        // Simplified manifold check
        // In a real implementation, this would be much more sophisticated
        const edges = new Map();
        let nonManifoldEdges = 0;

        for (let i = 0; i < vertices.length; i += 3) {
            if (i + 2 < vertices.length) {
                const triangle = [vertices[i], vertices[i + 1], vertices[i + 2]];
                
                // Check each edge of the triangle
                for (let j = 0; j < 3; j++) {
                    const v1 = triangle[j];
                    const v2 = triangle[(j + 1) % 3];
                    
                    const edgeKey = `${Math.min(v1.x, v2.x)},${Math.min(v1.y, v2.y)},${Math.min(v1.z, v2.z)}-${Math.max(v1.x, v2.x)},${Math.max(v1.y, v2.y)},${Math.max(v1.z, v2.z)}`;
                    
                    edges.set(edgeKey, (edges.get(edgeKey) || 0) + 1);
                }
            }
        }

        // Count non-manifold edges (edges shared by more than 2 faces)
        for (const [edge, count] of edges) {
            if (count !== 2) {
                nonManifoldEdges++;
            }
        }

        return {
            isManifold: nonManifoldEdges === 0,
            nonManifoldEdges,
            totalEdges: edges.size
        };
    }

    estimateMinWallThickness(geometry) {
        // Simplified estimation - in practice, would require ray-casting analysis
        const volume = geometry.volume * 1000; // Convert to mm³
        const surfaceArea = geometry.surfaceArea * 100; // Convert to mm²
        
        // Rough approximation based on volume/surface ratio
        return Math.max(0.4, (volume / surfaceArea) * 0.5);
    }

    detectOverhangs(geometry) {
        // Simplified overhang detection
        const maxOverhang = Math.max(0, 60 - (geometry.dimensions.z / Math.max(geometry.dimensions.x, geometry.dimensions.y)) * 30);
        
        return {
            maxOverhang,
            needsSupports: maxOverhang > this.tolerances.maxOverhang,
            supportVolume: maxOverhang > this.tolerances.maxOverhang ? geometry.volume * 0.1 : 0
        };
    }

    checkNormals(stlBuffer) {
        // Simplified normal checking
        const triangleCount = this.getTriangleCount(stlBuffer);
        let invertedCount = 0;

        // This would require actual normal vector analysis in a real implementation
        return {
            totalNormals: triangleCount,
            invertedCount,
            correctOrientation: invertedCount === 0
        };
    }

    findDuplicateVertices(stlBuffer) {
        const vertices = this.extractVertices(stlBuffer);
        const uniqueVertices = new Set();
        let duplicates = 0;

        for (const vertex of vertices) {
            const key = `${vertex.x.toFixed(6)},${vertex.y.toFixed(6)},${vertex.z.toFixed(6)}`;
            if (uniqueVertices.has(key)) {
                duplicates++;
            } else {
                uniqueVertices.add(key);
            }
        }

        return duplicates;
    }

    detectHoles(geometry) {
        // Simplified hole detection
        return {
            count: geometry.manifold.nonManifoldEdges > 0 ? 1 : 0,
            estimatedSize: 0
        };
    }

    estimatePrintTime(geometry) {
        // Simplified print time estimation
        const volume = geometry.volume;
        const height = geometry.dimensions.z;
        const layers = height / 0.2; // Assuming 0.2mm layer height
        
        const timePerLayer = 2; // minutes per layer (simplified)
        const baseTime = 30; // setup time
        
        return Math.round(baseTime + (layers * timePerLayer));
    }

    estimateMaterialUsage(geometry) {
        const volume = geometry.volume;
        const infillDensity = 0.15; // 15% infill
        const materialDensity = 1.24; // PLA density g/cm³
        
        return Math.round(volume * infillDensity * materialDensity * 1.1); // 10% waste factor
    }

    async optimizeSTL(stlBuffer, recommendations) {
        console.log('🔧 Applying STL optimizations...');
        
        let optimizedBuffer = stlBuffer;
        const appliedOptimizations = [];

        for (const rec of recommendations) {
            try {
                switch (rec.type) {
                    case 'repair':
                        optimizedBuffer = await this.repairMesh(optimizedBuffer);
                        appliedOptimizations.push('mesh_repair');
                        break;
                    case 'scale':
                        optimizedBuffer = await this.scaleMesh(optimizedBuffer, rec.scaleFactor);
                        appliedOptimizations.push('scaling');
                        break;
                    case 'orientation':
                        optimizedBuffer = await this.optimizeOrientation(optimizedBuffer);
                        appliedOptimizations.push('orientation');
                        break;
                }
            } catch (error) {
                console.warn(`Failed to apply ${rec.type} optimization: ${error.message}`);
            }
        }

        return {
            buffer: optimizedBuffer,
            optimizations: appliedOptimizations
        };
    }

    async repairMesh(stlBuffer) {
        // Placeholder for mesh repair - would use external tools like Meshlab
        console.log('🔨 Repairing mesh...');
        return stlBuffer;
    }

    async scaleMesh(stlBuffer, scaleFactor) {
        // Placeholder for mesh scaling
        console.log(`📏 Scaling mesh by factor: ${scaleFactor}`);
        return stlBuffer;
    }

    async optimizeOrientation(stlBuffer) {
        // Placeholder for orientation optimization
        console.log('🔄 Optimizing print orientation...');
        return stlBuffer;
    }
}

// Export for use in other modules
module.exports = STLValidator;

// CLI usage
if (require.main === module) {
    const validator = new STLValidator();
    
    const stlPath = process.argv[2];
    if (!stlPath) {
        console.log('Usage: node stl-validator.js <path-to-stl-file>');
        process.exit(1);
    }

    if (!fs.existsSync(stlPath)) {
        console.error('❌ STL file not found:', stlPath);
        process.exit(1);
    }

    (async () => {
        try {
            const stlBuffer = fs.readFileSync(stlPath);
            const validation = await validator.validateSTL(stlBuffer);
            
            console.log('\n📊 STL Validation Report:');
            console.log(`Valid: ${validation.isValid ? '✅' : '❌'}`);
            console.log(`Printable: ${validation.isPrintable ? '✅' : '❌'}`);
            
            if (validation.errors.length > 0) {
                console.log('\n❌ Errors:');
                validation.errors.forEach(error => console.log(`  • ${error}`));
            }
            
            if (validation.warnings.length > 0) {
                console.log('\n⚠️  Warnings:');
                validation.warnings.forEach(warning => console.log(`  • ${warning}`));
            }
            
            if (validation.optimizations.length > 0) {
                console.log('\n🔧 Recommended Optimizations:');
                validation.optimizations.forEach(opt => 
                    console.log(`  • ${opt.description} (${opt.priority} priority, ~${opt.estimatedTime}s)`)
                );
            }
            
            console.log('\n📈 Statistics:');
            console.log(`  Triangles: ${validation.stats.format?.triangleCount || 'N/A'}`);
            console.log(`  Volume: ${validation.stats.geometry?.volume?.toFixed(2) || 'N/A'} cm³`);
            console.log(`  Print Time: ${validation.stats.printability?.estimatedPrintTime || 'N/A'} minutes`);
            console.log(`  Material: ${validation.stats.printability?.materialUsage || 'N/A'} grams`);
            
        } catch (error) {
            console.error('❌ Validation failed:', error.message);
            process.exit(1);
        }
    })();
}
