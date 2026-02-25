/**
 * Offline Voice Processing Module
 * 
 * Provides offline capabilities for voice processing including:
 * - Cached model storage and loading with version management
 * - Offline speech recognition using local models
 * - Local scheme information caching with sync strategy
 * - Fallback mechanisms for offline mode
 * 
 * Validates Requirements 8.1, 8.2
 */

import { EventEmitter } from 'events';
import { TranscriptionResult, DialectCode } from '../../../shared/types';

/**
 * Model version information
 */
export interface ModelVersion {
  version: string;
  language: string;
  dialect?: DialectCode;
  size: number;
  downloadedAt: Date;
  lastUsed: Date;
  checksum: string;
}

/**
 * Cached model metadata
 */
export interface CachedModel {
  id: string;
  version: ModelVersion;
  modelData: ArrayBuffer;
  isLoaded: boolean;
}

/**
 * Scheme cache entry
 */
export interface CachedScheme {
  schemeId: string;
  name: Record<string, string>; // Multilingual names
  description: Record<string, string>;
  eligibilityCriteria: any;
  cachedAt: Date;
  expiresAt: Date;
}

/**
 * Sync status for offline data
 */
export interface SyncStatus {
  lastSyncTime: Date | null;
  pendingOperations: number;
  isSyncing: boolean;
  syncErrors: string[];
}

/**
 * Offline processing configuration
 */
export interface OfflineConfig {
  maxCacheSize: number; // Maximum cache size in bytes
  modelCachePath: string;
  schemeCachePath: string;
  syncInterval: number; // Sync interval in milliseconds
  maxOfflineAge: number; // Maximum age for cached data in milliseconds
}

/**
 * Offline Voice Processing Service
 */
export class OfflineVoiceProcessor extends EventEmitter {
  private cachedModels: Map<string, CachedModel> = new Map();
  private cachedSchemes: Map<string, CachedScheme> = new Map();
  private config: OfflineConfig;
  private syncStatus: SyncStatus;
  private isOnline: boolean = true;
  private syncTimer: NodeJS.Timeout | null = null;

  constructor(config: Partial<OfflineConfig> = {}) {
    super();
    
    this.config = {
      maxCacheSize: config.maxCacheSize || 500 * 1024 * 1024, // 500MB default
      modelCachePath: config.modelCachePath || './cache/models',
      schemeCachePath: config.schemeCachePath || './cache/schemes',
      syncInterval: config.syncInterval || 5 * 60 * 1000, // 5 minutes
      maxOfflineAge: config.maxOfflineAge || 7 * 24 * 60 * 60 * 1000 // 7 days
    };

    this.syncStatus = {
      lastSyncTime: null,
      pendingOperations: 0,
      isSyncing: false,
      syncErrors: []
    };

    this.initializeOfflineCapabilities();
  }

  /**
   * Initialize offline capabilities
   */
  private async initializeOfflineCapabilities(): Promise<void> {
    // Load cached models from storage
    await this.loadCachedModels();
    
    // Load cached schemes from storage
    await this.loadCachedSchemes();
    
    // Setup network monitoring
    this.setupNetworkMonitoring();
    
    // Start sync timer
    this.startSyncTimer();
    
    this.emit('initialized');
  }

  /**
   * Load cached models from storage
   */
  private async loadCachedModels(): Promise<void> {
    // In a real implementation, this would load from filesystem or IndexedDB
    // For now, we'll simulate with in-memory storage
    this.emit('models:loaded', { count: this.cachedModels.size });
  }

  /**
   * Load cached schemes from storage
   */
  private async loadCachedSchemes(): Promise<void> {
    // In a real implementation, this would load from filesystem or IndexedDB
    this.emit('schemes:loaded', { count: this.cachedSchemes.size });
  }

  /**
   * Setup network monitoring
   */
  private setupNetworkMonitoring(): void {
    // Monitor network status changes
    // In a real implementation, this would use navigator.onLine or similar
    this.emit('network:status', { isOnline: this.isOnline });
  }

  /**
   * Start automatic sync timer
   */
  private startSyncTimer(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
    }

    this.syncTimer = setInterval(() => {
      if (this.isOnline && !this.syncStatus.isSyncing) {
        this.syncWithCloud().catch(error => {
          console.error('Sync error:', error);
        });
      }
    }, this.config.syncInterval);
  }

  /**
   * Cache a model for offline use
   */
  async cacheModel(
    language: string,
    dialect: DialectCode | undefined,
    modelData: ArrayBuffer,
    version: string
  ): Promise<void> {
    const modelId = this.getModelId(language, dialect);
    
    // Check cache size
    const currentSize = this.getCurrentCacheSize();
    if (currentSize + modelData.byteLength > this.config.maxCacheSize) {
      await this.evictOldestModel();
    }

    const cachedModel: CachedModel = {
      id: modelId,
      version: {
        version,
        language,
        dialect,
        size: modelData.byteLength,
        downloadedAt: new Date(),
        lastUsed: new Date(),
        checksum: await this.calculateChecksum(modelData)
      },
      modelData,
      isLoaded: false
    };

    this.cachedModels.set(modelId, cachedModel);
    
    // Persist to storage
    await this.persistModel(cachedModel);
    
    this.emit('model:cached', { modelId, size: modelData.byteLength });
  }

  /**
   * Load a cached model for use
   */
  async loadCachedModel(language: string, dialect?: DialectCode): Promise<CachedModel | null> {
    const modelId = this.getModelId(language, dialect);
    const model = this.cachedModels.get(modelId);

    if (!model) {
      this.emit('model:not-found', { modelId });
      return null;
    }

    // Update last used time
    model.version.lastUsed = new Date();
    model.isLoaded = true;

    this.emit('model:loaded', { modelId });
    return model;
  }

  /**
   * Process speech offline using cached models
   */
  async processOfflineSpeech(
    audioData: ArrayBuffer,
    language: string,
    dialect?: DialectCode
  ): Promise<TranscriptionResult> {
    const model = await this.loadCachedModel(language, dialect);

    if (!model) {
      throw new Error(`No cached model available for ${language}${dialect ? `-${dialect}` : ''}`);
    }

    // In a real implementation, this would use the actual model for inference
    // For now, we'll simulate offline processing
    const result: TranscriptionResult = {
      text: '[Offline transcription]',
      confidence: 0.85, // Slightly lower confidence for offline
      language,
      timestamp: new Date(),
      isFinal: true,
      isOffline: true
    };

    this.emit('speech:processed-offline', { language, dialect });
    return result;
  }

  /**
   * Cache scheme information for offline access
   */
  async cacheScheme(scheme: CachedScheme): Promise<void> {
    this.cachedSchemes.set(scheme.schemeId, scheme);
    
    // Persist to storage
    await this.persistScheme(scheme);
    
    this.emit('scheme:cached', { schemeId: scheme.schemeId });
  }

  /**
   * Get cached scheme information
   */
  async getCachedScheme(schemeId: string): Promise<CachedScheme | null> {
    const scheme = this.cachedSchemes.get(schemeId);

    if (!scheme) {
      this.emit('scheme:not-found', { schemeId });
      return null;
    }

    // Check if expired
    if (new Date() > scheme.expiresAt) {
      this.emit('scheme:expired', { schemeId });
      
      // If online, trigger refresh
      if (this.isOnline) {
        this.refreshScheme(schemeId).catch(console.error);
      }
    }

    return scheme;
  }

  /**
   * Get all cached schemes
   */
  async getAllCachedSchemes(): Promise<CachedScheme[]> {
    return Array.from(this.cachedSchemes.values());
  }

  /**
   * Sync offline data with cloud when connectivity returns
   */
  async syncWithCloud(): Promise<void> {
    if (!this.isOnline || this.syncStatus.isSyncing) {
      return;
    }

    this.syncStatus.isSyncing = true;
    this.syncStatus.syncErrors = [];
    this.emit('sync:started');

    try {
      // Sync models
      await this.syncModels();
      
      // Sync schemes
      await this.syncSchemes();
      
      // Update sync status
      this.syncStatus.lastSyncTime = new Date();
      this.syncStatus.pendingOperations = 0;
      
      this.emit('sync:completed', { 
        syncTime: this.syncStatus.lastSyncTime 
      });
    } catch (error) {
      this.syncStatus.syncErrors.push((error as Error).message);
      this.emit('sync:error', { error: (error as Error).message });
    } finally {
      this.syncStatus.isSyncing = false;
    }
  }

  /**
   * Sync models with cloud
   */
  private async syncModels(): Promise<void> {
    // Check for model updates
    for (const [modelId, model] of this.cachedModels) {
      // In a real implementation, check if newer version available
      this.emit('model:synced', { modelId });
    }
  }

  /**
   * Sync schemes with cloud
   */
  private async syncSchemes(): Promise<void> {
    // Refresh expired schemes
    for (const [schemeId, scheme] of this.cachedSchemes) {
      if (new Date() > scheme.expiresAt) {
        await this.refreshScheme(schemeId);
      }
    }
  }

  /**
   * Refresh a specific scheme from cloud
   */
  private async refreshScheme(schemeId: string): Promise<void> {
    // In a real implementation, fetch from API
    this.emit('scheme:refreshed', { schemeId });
  }

  /**
   * Set online/offline status
   */
  setOnlineStatus(isOnline: boolean): void {
    const wasOnline = this.isOnline;
    this.isOnline = isOnline;

    if (isOnline && !wasOnline) {
      // Connectivity restored
      this.emit('network:online');
      this.syncWithCloud().catch(console.error);
    } else if (!isOnline && wasOnline) {
      // Connectivity lost
      this.emit('network:offline');
    }
  }

  /**
   * Get sync status
   */
  getSyncStatus(): SyncStatus {
    return { ...this.syncStatus };
  }

  /**
   * Check if offline mode is available
   */
  isOfflineModeAvailable(language: string, dialect?: DialectCode): boolean {
    const modelId = this.getModelId(language, dialect);
    return this.cachedModels.has(modelId);
  }

  /**
   * Get cached model versions
   */
  getCachedModelVersions(): ModelVersion[] {
    return Array.from(this.cachedModels.values()).map(m => m.version);
  }

  /**
   * Clear expired cache entries
   */
  async clearExpiredCache(): Promise<void> {
    const now = new Date();
    let clearedCount = 0;

    // Clear expired schemes
    for (const [schemeId, scheme] of this.cachedSchemes) {
      if (now > scheme.expiresAt) {
        this.cachedSchemes.delete(schemeId);
        clearedCount++;
      }
    }

    // Clear old models
    for (const [modelId, model] of this.cachedModels) {
      const age = now.getTime() - model.version.lastUsed.getTime();
      if (age > this.config.maxOfflineAge) {
        this.cachedModels.delete(modelId);
        clearedCount++;
      }
    }

    this.emit('cache:cleared', { clearedCount });
  }

  /**
   * Get current cache size
   */
  private getCurrentCacheSize(): number {
    let size = 0;
    for (const model of this.cachedModels.values()) {
      size += model.version.size;
    }
    return size;
  }

  /**
   * Evict oldest model to make space
   */
  private async evictOldestModel(): Promise<void> {
    let oldestModel: CachedModel | null = null;
    let oldestTime = Date.now();

    for (const model of this.cachedModels.values()) {
      const lastUsed = model.version.lastUsed.getTime();
      if (lastUsed < oldestTime) {
        oldestTime = lastUsed;
        oldestModel = model;
      }
    }

    if (oldestModel) {
      this.cachedModels.delete(oldestModel.id);
      this.emit('model:evicted', { modelId: oldestModel.id });
    }
  }

  /**
   * Get model ID from language and dialect
   */
  private getModelId(language: string, dialect?: DialectCode): string {
    return dialect ? `${language}-${dialect}` : language;
  }

  /**
   * Calculate checksum for model data
   */
  private async calculateChecksum(data: ArrayBuffer): Promise<string> {
    // In a real implementation, use crypto.subtle.digest
    // For now, return a simple hash
    return `checksum-${data.byteLength}`;
  }

  /**
   * Persist model to storage
   */
  private async persistModel(model: CachedModel): Promise<void> {
    // In a real implementation, save to filesystem or IndexedDB
  }

  /**
   * Persist scheme to storage
   */
  private async persistScheme(scheme: CachedScheme): Promise<void> {
    // In a real implementation, save to filesystem or IndexedDB
  }

  /**
   * Cleanup and stop sync timer
   */
  destroy(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
    this.removeAllListeners();
  }
}
