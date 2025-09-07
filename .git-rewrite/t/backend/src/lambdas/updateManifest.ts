/**
 * Lambda 2: Update Manifest
 * Updates training dataset manifest with new photos
 */

import { Context } from 'aws-lambda';
import AWS from 'aws-sdk';

const s3 = new AWS.S3();

interface UpdateManifestEvent {
  totalPhotos: number;
  validPhotos: number;
  s3Keys: string[];
  batchId: string;
  timestamp: string;
}

interface ManifestEntry {
  s3Key: string;
  orderId: string;
  petName: string;
  qualityScore: number;
  addedAt: string;
  batchId: string;
}

interface TrainingManifest {
  version: string;
  lastUpdated: string;
  totalImages: number;
  batches: {
    [batchId: string]: {
      addedAt: string;
      imageCount: number;
      s3Keys: string[];
    };
  };
  images: ManifestEntry[];
}

export const handler = async (
  event: UpdateManifestEvent,
  context: Context
) => {
  console.log('Updating training manifest:', JSON.stringify(event, null, 2));
  
  const { s3Keys, batchId, timestamp, validPhotos } = event;
  
  try {
    // 1. Load existing manifest
    const manifest = await loadManifest();
    
    // 2. Add new photos to manifest
    const newEntries = await createManifestEntries(s3Keys, batchId);
    
    // 3. Update manifest
    const updatedManifest = updateManifest(manifest, newEntries, batchId, timestamp);
    
    // 4. Save updated manifest
    await saveManifest(updatedManifest);
    
    // 5. Generate training statistics
    const stats = generateTrainingStats(updatedManifest);
    
    const result = {
      manifestVersion: updatedManifest.version,
      newImagesAdded: newEntries.length,
      totalImages: updatedManifest.totalImages,
      batchId,
      trainingStats: stats,
      nextAction: 'kickFineTuneJob'
    };
    
    console.log('Manifest update result:', result);
    return result;
    
  } catch (error) {
    console.error('Failed to update manifest:', error);
    throw new Error(
      (error instanceof Error ? error.message : String(error)) || 'Manifest update failed'
    );
  }
};

async function loadManifest(): Promise<TrainingManifest> {
  const bucketName = process.env.S3_DATASET_BUCKET!;
  const manifestKey = 'training-manifest.json';
  
  try {
    const result = await s3.getObject({
      Bucket: bucketName,
      Key: manifestKey
    }).promise();
    
    if (result.Body) {
      return JSON.parse(result.Body.toString());
    }
  } catch (error) {
    console.log('No existing manifest found, creating new one');
  }
  
  // Return default manifest if none exists
  return {
    version: '1.0.0',
    lastUpdated: new Date().toISOString(),
    totalImages: 0,
    batches: {},
    images: []
  };
}

async function createManifestEntries(
  s3Keys: string[],
  batchId: string
): Promise<ManifestEntry[]> {
  const bucketName = process.env.S3_DATASET_BUCKET!;
  const entries: ManifestEntry[] = [];
  
  for (const s3Key of s3Keys) {
    try {
      // Get metadata from S3 object
      const headResult = await s3.headObject({
        Bucket: bucketName,
        Key: s3Key
      }).promise();
      
      const metadata = headResult.Metadata || {};
      
      entries.push({
        s3Key,
        orderId: metadata['original-order-id'] || 'unknown',
        petName: metadata['pet-name'] || 'unknown',
        qualityScore: parseFloat(metadata['quality-score'] || '0'),
        addedAt: new Date().toISOString(),
        batchId
      });
      
    } catch (error) {
      console.error(`Failed to get metadata for ${s3Key}:`, error);
    }
  }
  
  return entries;
}

function updateManifest(
  manifest: TrainingManifest,
  newEntries: ManifestEntry[],
  batchId: string,
  timestamp: string
): TrainingManifest {
  return {
    ...manifest,
    version: incrementVersion(manifest.version),
    lastUpdated: timestamp,
    totalImages: manifest.totalImages + newEntries.length,
    batches: {
      ...manifest.batches,
      [batchId]: {
        addedAt: timestamp,
        imageCount: newEntries.length,
        s3Keys: newEntries.map(entry => entry.s3Key)
      }
    },
    images: [...manifest.images, ...newEntries]
  };
}

async function saveManifest(manifest: TrainingManifest): Promise<void> {
  const bucketName = process.env.S3_DATASET_BUCKET!;
  const manifestKey = 'training-manifest.json';
  
  await s3.upload({
    Bucket: bucketName,
    Key: manifestKey,
    Body: JSON.stringify(manifest, null, 2),
    ContentType: 'application/json',
    Metadata: {
      'version': manifest.version,
      'total-images': manifest.totalImages.toString(),
      'last-updated': manifest.lastUpdated
    }
  }).promise();
  
  // Also save a versioned copy
  const versionedKey = `manifests/training-manifest-${manifest.version}.json`;
  await s3.upload({
    Bucket: bucketName,
    Key: versionedKey,
    Body: JSON.stringify(manifest, null, 2),
    ContentType: 'application/json'
  }).promise();
}

function generateTrainingStats(manifest: TrainingManifest): Record<string, any> {
  const stats = {
    totalImages: manifest.totalImages,
    recentBatches: Object.keys(manifest.batches).length,
    averageQuality: 0,
    qualityDistribution: {
      high: 0,    // > 0.8
      medium: 0,  // 0.5 - 0.8
      low: 0      // < 0.5
    },
    petNameDistribution: {} as Record<string, number>
  };
  
  // Calculate quality stats
  let totalQuality = 0;
  for (const image of manifest.images) {
    totalQuality += image.qualityScore;
    
    if (image.qualityScore > 0.8) {
      stats.qualityDistribution.high++;
    } else if (image.qualityScore > 0.5) {
      stats.qualityDistribution.medium++;
    } else {
      stats.qualityDistribution.low++;
    }
    
    // Track pet name distribution (anonymized)
    const anonymizedName = image.petName.charAt(0) + '***';
    stats.petNameDistribution[anonymizedName] = 
      (stats.petNameDistribution[anonymizedName] || 0) + 1;
  }
  
  stats.averageQuality = manifest.totalImages > 0 
    ? totalQuality / manifest.totalImages 
    : 0;
  
  return stats;
}

function incrementVersion(version: string): string {
  const parts = version.split('.');
  const patch = parseInt(parts[2] || '0', 10) + 1;
  return `${parts[0]}.${parts[1]}.${patch}`;
}
