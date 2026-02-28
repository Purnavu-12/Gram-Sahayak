/**
 * Centralized Cache Manager
 * Implements caching strategies for performance optimization
 */

export interface CacheConfig {
  ttl: number; // Time to live in seconds
  maxSize: number; // Maximum cache size
  strategy: 'lru' | 'lfu' | 'fifo';
}

export interface CacheEntry<T> {
  value: T;
  timestamp: number;
  accessCount: number;
  size: number;
}

export class CacheManager<T> {
  private cache: Map<string, CacheEntry<T>>;
  protected config: CacheConfig;
  private currentSize: number;
  private hits: number;
  private misses: number;

  constructor(config: Partial<CacheConfig> = {}) {
    this.cache = new Map();
    this.config = {
      ttl: config.ttl || 3600, // 1 hour default
      maxSize: config.maxSize || 1000,
      strategy: config.strategy || 'lru',
    };
    this.currentSize = 0;
    this.hits = 0;
    this.misses = 0;
  }

  async get(key: string): Promise<T | null> {
    const entry = this.cache.get(key);

    if (!entry) {
      this.misses++;
      return null;
    }

    // Check if entry has expired
    const now = Date.now();
    if (now - entry.timestamp > this.config.ttl * 1000) {
      this.cache.delete(key);
      this.currentSize -= entry.size;
      this.misses++;
      return null;
    }

    // Update access count for LFU strategy
    entry.accessCount++;
    this.hits++;

    return entry.value;
  }

  async set(key: string, value: T, size: number = 1): Promise<void> {
    // Check if we need to evict entries
    while (this.currentSize + size > this.config.maxSize && this.cache.size > 0) {
      this.evict();
    }

    const entry: CacheEntry<T> = {
      value,
      timestamp: Date.now(),
      accessCount: 1,
      size,
    };

    // Remove old entry if exists
    const oldEntry = this.cache.get(key);
    if (oldEntry) {
      this.currentSize -= oldEntry.size;
    }

    this.cache.set(key, entry);
    this.currentSize += size;
  }

  async delete(key: string): Promise<boolean> {
    const entry = this.cache.get(key);
    if (entry) {
      this.currentSize -= entry.size;
      return this.cache.delete(key);
    }
    return false;
  }

  async clear(): Promise<void> {
    this.cache.clear();
    this.currentSize = 0;
    this.hits = 0;
    this.misses = 0;
  }

  getStats(): {
    size: number;
    hits: number;
    misses: number;
    hitRate: number;
    currentSize: number;
    maxSize: number;
  } {
    const total = this.hits + this.misses;
    return {
      size: this.cache.size,
      hits: this.hits,
      misses: this.misses,
      hitRate: total > 0 ? this.hits / total : 0,
      currentSize: this.currentSize,
      maxSize: this.config.maxSize,
    };
  }

  private evict(): void {
    let keyToEvict: string | null = null;

    switch (this.config.strategy) {
      case 'lru':
        keyToEvict = this.evictLRU();
        break;
      case 'lfu':
        keyToEvict = this.evictLFU();
        break;
      case 'fifo':
        keyToEvict = this.evictFIFO();
        break;
    }

    if (keyToEvict) {
      const entry = this.cache.get(keyToEvict);
      if (entry) {
        this.currentSize -= entry.size;
      }
      this.cache.delete(keyToEvict);
    }
  }

  private evictLRU(): string | null {
    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      if (entry.timestamp < oldestTime) {
        oldestTime = entry.timestamp;
        oldestKey = key;
      }
    }

    return oldestKey;
  }

  private evictLFU(): string | null {
    let leastUsedKey: string | null = null;
    let leastCount = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      if (entry.accessCount < leastCount) {
        leastCount = entry.accessCount;
        leastUsedKey = key;
      }
    }

    return leastUsedKey;
  }

  private evictFIFO(): string | null {
    // Get first entry (oldest insertion)
    const firstKey = this.cache.keys().next().value;
    return firstKey || null;
  }
}

// Specialized cache for scheme data
export class SchemeCacheManager extends CacheManager<any> {
  constructor() {
    super({
      ttl: 86400, // 24 hours for scheme data
      maxSize: 5000,
      strategy: 'lru',
    });
  }

  async getScheme(schemeId: string): Promise<any | null> {
    return this.get(`scheme:${schemeId}`);
  }

  async setScheme(schemeId: string, scheme: any): Promise<void> {
    return this.set(`scheme:${schemeId}`, scheme, 1);
  }

  async getEligibilityResult(userId: string, schemeId: string): Promise<any | null> {
    return this.get(`eligibility:${userId}:${schemeId}`);
  }

  async setEligibilityResult(userId: string, schemeId: string, result: any): Promise<void> {
    // Shorter TTL for eligibility results
    const oldTtl = this.config.ttl;
    this.config.ttl = 3600; // 1 hour
    await this.set(`eligibility:${userId}:${schemeId}`, result, 1);
    this.config.ttl = oldTtl;
  }
}

// Specialized cache for user profiles
export class UserProfileCacheManager extends CacheManager<any> {
  constructor() {
    super({
      ttl: 1800, // 30 minutes for user profiles
      maxSize: 10000,
      strategy: 'lru',
    });
  }

  async getUserProfile(userId: string): Promise<any | null> {
    return this.get(`profile:${userId}`);
  }

  async setUserProfile(userId: string, profile: any): Promise<void> {
    return this.set(`profile:${userId}`, profile, 1);
  }

  async invalidateUserProfile(userId: string): Promise<boolean> {
    return this.delete(`profile:${userId}`);
  }
}

// Global cache instances
export const schemeCache = new SchemeCacheManager();
export const userProfileCache = new UserProfileCacheManager();
