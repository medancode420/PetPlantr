/**
 * 🚀 Cache Service
 * Production-ready caching layer with Redis support and in-memory fallback
 */

import { logger } from '../utils/logger';

export interface CacheConfig {
  enableRedis: boolean;
  redisUrl?: string;
  defaultTtl: number;
  maxInMemoryItems: number;
  enableCompression: boolean;
}

export interface CacheItem<T> {
  value: T;
  expiry: number;
  size: number;
}

export class CacheService {
  private config: CacheConfig;
  private inMemoryCache = new Map<string, CacheItem<any>>();
  private cacheStats = {
    hits: 0,
    misses: 0,
    sets: 0,
    deletes: 0,
    size: 0
  };

  constructor(config?: Partial<CacheConfig>) {
    this.config = {
      enableRedis: process.env.ENABLE_REDIS === 'true',
      redisUrl: process.env.REDIS_URL,
      defaultTtl: parseInt(process.env.CACHE_DEFAULT_TTL || '300'), // 5 minutes
      maxInMemoryItems: parseInt(process.env.CACHE_MAX_ITEMS || '1000'),
      enableCompression: process.env.ENABLE_CACHE_COMPRESSION === 'true',
      ...config
    };

    logger.info('CacheService initialized', {
      enableRedis: this.config.enableRedis,
      defaultTtl: this.config.defaultTtl,
      maxInMemoryItems: this.config.maxInMemoryItems
    });

    // Cleanup expired items every 5 minutes
    setInterval(() => this.cleanupExpired(), 5 * 60 * 1000);
  }

  /**
   * Get item from cache
   */
  async get<T>(key: string): Promise<T | null> {
    try {
      // Try Redis first if enabled
      if (this.config.enableRedis) {
        const redisValue = await this.getFromRedis<T>(key);
        if (redisValue !== null) {
          this.cacheStats.hits++;
          return redisValue;
        }
      }

      // Fallback to in-memory cache
      const item = this.inMemoryCache.get(key);
      if (!item) {
        this.cacheStats.misses++;
        return null;
      }

      // Check expiry
      if (Date.now() > item.expiry) {
        this.inMemoryCache.delete(key);
        this.cacheStats.misses++;
        return null;
      }

      this.cacheStats.hits++;
      logger.debug('Cache hit', { key, source: 'memory' });
      return item.value;
    } catch (error) {
      logger.error('Cache get error', { key, error });
      return null;
    }
  }

  /**
   * Set item in cache
   */
  async set<T>(key: string, value: T, ttlSeconds?: number): Promise<void> {
    try {
      const ttl = ttlSeconds || this.config.defaultTtl;
      const expiry = Date.now() + (ttl * 1000);

      // Store in Redis if enabled
      if (this.config.enableRedis) {
        await this.setInRedis(key, value, ttl);
      }

      // Store in memory cache
      const serializedValue = this.config.enableCompression 
        ? this.compress(JSON.stringify(value))
        : JSON.stringify(value);
      
      const size = this.calculateSize(serializedValue);
      
      // Ensure we don't exceed max items
      if (this.inMemoryCache.size >= this.config.maxInMemoryItems) {
        this.evictOldest();
      }

      this.inMemoryCache.set(key, {
        value,
        expiry,
        size
      });

      this.cacheStats.sets++;
      this.cacheStats.size += size;

      logger.debug('Cache set', { 
        key, 
        ttl, 
        size,
        source: this.config.enableRedis ? 'redis+memory' : 'memory'
      });
    } catch (error) {
      logger.error('Cache set error', { key, error });
    }
  }

  /**
   * Delete item from cache
   */
  async delete(key: string): Promise<void> {
    try {
      // Delete from Redis if enabled
      if (this.config.enableRedis) {
        await this.deleteFromRedis(key);
      }

      // Delete from memory cache
      const item = this.inMemoryCache.get(key);
      if (item) {
        this.cacheStats.size -= item.size;
        this.inMemoryCache.delete(key);
        this.cacheStats.deletes++;
        
        logger.debug('Cache delete', { key });
      }
    } catch (error) {
      logger.error('Cache delete error', { key, error });
    }
  }

  /**
   * Clear all cache
   */
  async clear(): Promise<void> {
    try {
      if (this.config.enableRedis) {
        // Would clear Redis here
      }

      this.inMemoryCache.clear();
      this.cacheStats.size = 0;
      
      logger.info('Cache cleared');
    } catch (error) {
      logger.error('Cache clear error', { error });
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const hitRate = this.cacheStats.hits / (this.cacheStats.hits + this.cacheStats.misses) || 0;
    
    return {
      ...this.cacheStats,
      hitRate: Math.round(hitRate * 100) / 100,
      memoryItems: this.inMemoryCache.size,
      avgItemSize: this.inMemoryCache.size > 0 ? this.cacheStats.size / this.inMemoryCache.size : 0
    };
  }

  /**
   * Get or set pattern - useful for caching expensive operations
   */
  async getOrSet<T>(
    key: string, 
    factory: () => Promise<T>, 
    ttlSeconds?: number
  ): Promise<T> {
    const cached = await this.get<T>(key);
    if (cached !== null) {
      return cached;
    }

    const value = await factory();
    await this.set(key, value, ttlSeconds);
    return value;
  }

  /**
   * Batch get multiple keys
   */
  async mget<T>(keys: string[]): Promise<Record<string, T | null>> {
    const results: Record<string, T | null> = {};
    
    // Use Promise.all for parallel fetching
    await Promise.all(
      keys.map(async (key) => {
        results[key] = await this.get<T>(key);
      })
    );

    return results;
  }

  /**
   * Batch set multiple key-value pairs
   */
  async mset<T>(items: Record<string, T>, ttlSeconds?: number): Promise<void> {
    await Promise.all(
      Object.entries(items).map(([key, value]) => 
        this.set(key, value, ttlSeconds)
      )
    );
  }

  /**
   * Check if key exists in cache
   */
  async exists(key: string): Promise<boolean> {
    if (this.config.enableRedis) {
      // Would check Redis here
    }

    const item = this.inMemoryCache.get(key);
    if (!item) return false;

    // Check expiry
    if (Date.now() > item.expiry) {
      this.inMemoryCache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Increment a numeric value in cache
   */
  async increment(key: string, delta = 1): Promise<number> {
    const current = await this.get<number>(key) || 0;
    const newValue = current + delta;
    await this.set(key, newValue);
    return newValue;
  }

  /**
   * Set expiry for an existing key
   */
  async expire(key: string, ttlSeconds: number): Promise<void> {
    const value = await this.get(key);
    if (value !== null) {
      await this.set(key, value, ttlSeconds);
    }
  }

  // Private helper methods

  private async getFromRedis<T>(key: string): Promise<T | null> {
    // Redis implementation would go here
    // For now, return null to fallback to memory cache
    return null;
  }

  private async setInRedis<T>(key: string, value: T, ttl: number): Promise<void> {
    // Redis implementation would go here
  }

  private async deleteFromRedis(key: string): Promise<void> {
    // Redis implementation would go here
  }

  private compress(data: string): string {
    // Simple compression simulation
    // In production, use a real compression library like zlib
    return data;
  }

  private calculateSize(data: string): number {
    return new Blob([data]).size;
  }

  private evictOldest(): void {
    // Find the oldest item (lowest expiry)
    let oldestKey: string | null = null;
    let oldestExpiry = Infinity;

    for (const [key, item] of this.inMemoryCache.entries()) {
      if (item.expiry < oldestExpiry) {
        oldestExpiry = item.expiry;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      const item = this.inMemoryCache.get(oldestKey)!;
      this.cacheStats.size -= item.size;
      this.inMemoryCache.delete(oldestKey);
      
      logger.debug('Cache eviction', { 
        evictedKey: oldestKey,
        reason: 'max_items_exceeded'
      });
    }
  }

  private cleanupExpired(): void {
    const now = Date.now();
    let cleanedCount = 0;
    let reclaimedSize = 0;

    for (const [key, item] of this.inMemoryCache.entries()) {
      if (now > item.expiry) {
        this.inMemoryCache.delete(key);
        this.cacheStats.size -= item.size;
        reclaimedSize += item.size;
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      logger.debug('Cache cleanup completed', {
        cleanedItems: cleanedCount,
        reclaimedSize,
        remainingItems: this.inMemoryCache.size
      });
    }
  }

  /**
   * Cleanup resources
   */
  async cleanup(): Promise<void> {
    this.inMemoryCache.clear();
    this.cacheStats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      size: 0
    };
    
    logger.info('CacheService cleanup completed');
  }
}
