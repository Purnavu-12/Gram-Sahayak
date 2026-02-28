/**
 * Network Optimization Module
 * 
 * Provides network optimization capabilities including:
 * - Audio compression and bandwidth optimization
 * - Offline-to-online synchronization with conflict resolution
 * - Network condition detection and adaptive quality adjustment
 * - Queue management for offline operations
 * 
 * Validates Requirements 8.3, 8.4, 8.5
 */

import { EventEmitter } from 'events';

/**
 * Network condition levels
 */
export enum NetworkCondition {
  EXCELLENT = 'excellent',  // >5 Mbps, <50ms latency
  GOOD = 'good',           // 1-5 Mbps, 50-150ms latency
  FAIR = 'fair',           // 256kbps-1Mbps, 150-300ms latency
  POOR = 'poor',           // <256kbps, >300ms latency
  OFFLINE = 'offline'      // No connectivity
}

/**
 * Audio quality settings
 */
export interface AudioQualitySettings {
  sampleRate: number;      // Hz
  bitrate: number;         // kbps
  channels: number;        // 1 = mono, 2 = stereo
  compressionLevel: number; // 0-10
}

/**
 * Network metrics
 */
export interface NetworkMetrics {
  bandwidth: number;       // kbps
  latency: number;         // ms
  packetLoss: number;      // percentage
  jitter: number;          // ms
  timestamp: Date;
}

/**
 * Compression result
 */
export interface CompressionResult {
  compressedData: ArrayBuffer;
  originalSize: number;
  compressedSize: number;
  compressionRatio: number;
  compressionTime: number;
}

/**
 * Sync operation types
 */
export enum SyncOperationType {
  TRANSCRIPTION = 'transcription',
  USER_PROFILE = 'user_profile',
  SCHEME_DATA = 'scheme_data',
  APPLICATION = 'application',
  AUDIO_UPLOAD = 'audio_upload'
}

/**
 * Sync operation priority
 */
export enum SyncPriority {
  CRITICAL = 0,   // Must sync immediately
  HIGH = 1,       // Sync as soon as possible
  NORMAL = 2,     // Sync in regular batch
  LOW = 3         // Sync when idle
}

/**
 * Queued sync operation
 */
export interface SyncOperation {
  id: string;
  type: SyncOperationType;
  priority: SyncPriority;
  data: any;
  timestamp: Date;
  retryCount: number;
  maxRetries: number;
  conflictResolution?: ConflictResolutionStrategy;
}

/**
 * Conflict resolution strategies
 */
export enum ConflictResolutionStrategy {
  SERVER_WINS = 'server_wins',
  CLIENT_WINS = 'client_wins',
  MERGE = 'merge',
  MANUAL = 'manual'
}

/**
 * Sync conflict
 */
export interface SyncConflict {
  operationId: string;
  localData: any;
  serverData: any;
  conflictType: string;
  resolution: ConflictResolutionStrategy;
  resolvedData?: any;
}

/**
 * Network optimization configuration
 */
export interface NetworkOptimizationConfig {
  enableAdaptiveQuality: boolean;
  enableCompression: boolean;
  maxQueueSize: number;
  syncBatchSize: number;
  syncInterval: number;
  bandwidthTestInterval: number;
  compressionThreshold: number; // Compress if network < this (kbps)
}

/**
 * Network Optimization Service
 */
export class NetworkOptimizationService extends EventEmitter {
  private config: NetworkOptimizationConfig;
  private currentCondition: NetworkCondition = NetworkCondition.GOOD;
  private currentMetrics: NetworkMetrics | null = null;
  private currentQuality: AudioQualitySettings;
  private syncQueue: SyncOperation[] = [];
  private isSyncing: boolean = false;
  private syncTimer: NodeJS.Timeout | null = null;
  private metricsTimer: NodeJS.Timeout | null = null;

  // Quality presets for different network conditions
  private readonly qualityPresets: Record<NetworkCondition, AudioQualitySettings> = {
    [NetworkCondition.EXCELLENT]: {
      sampleRate: 48000,
      bitrate: 128,
      channels: 2,
      compressionLevel: 3
    },
    [NetworkCondition.GOOD]: {
      sampleRate: 16000,
      bitrate: 64,
      channels: 1,
      compressionLevel: 5
    },
    [NetworkCondition.FAIR]: {
      sampleRate: 16000,
      bitrate: 32,
      channels: 1,
      compressionLevel: 7
    },
    [NetworkCondition.POOR]: {
      sampleRate: 8000,
      bitrate: 16,
      channels: 1,
      compressionLevel: 9
    },
    [NetworkCondition.OFFLINE]: {
      sampleRate: 8000,
      bitrate: 16,
      channels: 1,
      compressionLevel: 10
    }
  };

  constructor(config: Partial<NetworkOptimizationConfig> = {}) {
    super();
    
    this.config = {
      enableAdaptiveQuality: config.enableAdaptiveQuality ?? true,
      enableCompression: config.enableCompression ?? true,
      maxQueueSize: config.maxQueueSize || 1000,
      syncBatchSize: config.syncBatchSize || 10,
      syncInterval: config.syncInterval || 30000, // 30 seconds
      bandwidthTestInterval: config.bandwidthTestInterval || 60000, // 1 minute
      compressionThreshold: config.compressionThreshold || 512 // 512 kbps
    };

    this.currentQuality = this.qualityPresets[NetworkCondition.GOOD];
    
    // Don't auto-initialize in test environments
    if (process.env.NODE_ENV !== 'test') {
      this.initialize();
    }
  }

  /**
   * Initialize network optimization
   */
  private initialize(): void {
    this.startNetworkMonitoring();
    this.startSyncTimer();
  }

  /**
   * Start network monitoring
   */
  private startNetworkMonitoring(): void {
    this.metricsTimer = setInterval(() => {
      this.measureNetworkConditions().catch(error => {
        console.error('Network measurement error:', error);
      });
    }, this.config.bandwidthTestInterval);

    // Initial measurement
    this.measureNetworkConditions().catch(console.error);
  }

  /**
   * Measure current network conditions
   */
  async measureNetworkConditions(): Promise<NetworkMetrics> {
    // In a real implementation, this would:
    // 1. Send test packets to measure bandwidth
    // 2. Measure round-trip time for latency
    // 3. Track packet loss
    // 4. Calculate jitter
    
    // Simulated metrics for now
    const metrics: NetworkMetrics = {
      bandwidth: 2000, // 2 Mbps
      latency: 100,    // 100ms
      packetLoss: 0.5, // 0.5%
      jitter: 10,      // 10ms
      timestamp: new Date()
    };

    this.currentMetrics = metrics;
    
    // Determine network condition
    const condition = this.determineNetworkCondition(metrics);
    
    if (condition !== this.currentCondition) {
      this.handleConditionChange(condition);
    }

    this.emit('metrics:updated', metrics);
    return metrics;
  }

  /**
   * Determine network condition from metrics
   */
  private determineNetworkCondition(metrics: NetworkMetrics): NetworkCondition {
    if (metrics.bandwidth === 0) {
      return NetworkCondition.OFFLINE;
    } else if (metrics.bandwidth > 5000 && metrics.latency < 50) {
      return NetworkCondition.EXCELLENT;
    } else if (metrics.bandwidth > 1000 && metrics.latency < 150) {
      return NetworkCondition.GOOD;
    } else if (metrics.bandwidth > 256 && metrics.latency < 300) {
      return NetworkCondition.FAIR;
    } else {
      return NetworkCondition.POOR;
    }
  }

  /**
   * Handle network condition change
   */
  private handleConditionChange(newCondition: NetworkCondition): void {
    const oldCondition = this.currentCondition;
    this.currentCondition = newCondition;

    // Adjust quality if adaptive quality is enabled
    if (this.config.enableAdaptiveQuality) {
      this.adjustAudioQuality(newCondition);
    }

    // Adjust sync behavior
    if (newCondition === NetworkCondition.OFFLINE) {
      this.emit('network:offline');
    } else if (oldCondition === NetworkCondition.OFFLINE) {
      this.emit('network:online');
      // Trigger sync when coming back online
      this.processSyncQueue().catch(console.error);
    }

    this.emit('condition:changed', {
      oldCondition,
      newCondition,
      metrics: this.currentMetrics
    });
  }

  /**
   * Adjust audio quality based on network condition
   */
  private adjustAudioQuality(condition: NetworkCondition): void {
    const newQuality = this.qualityPresets[condition];
    const oldQuality = this.currentQuality;
    
    this.currentQuality = newQuality;
    
    this.emit('quality:adjusted', {
      oldQuality,
      newQuality,
      condition
    });
  }

  /**
   * Compress audio data
   */
  async compressAudio(audioData: ArrayBuffer): Promise<CompressionResult> {
    const startTime = Date.now();
    const originalSize = audioData.byteLength;

    // Determine if compression is needed
    const shouldCompress = this.shouldCompressAudio();

    if (!shouldCompress) {
      return {
        compressedData: audioData,
        originalSize,
        compressedSize: originalSize,
        compressionRatio: 1.0,
        compressionTime: 0
      };
    }

    // In a real implementation, this would use:
    // - Opus codec for voice compression
    // - Adaptive bitrate based on network conditions
    // - Perceptual audio coding
    
    // Simulate compression (simple downsampling simulation)
    const compressionLevel = this.currentQuality.compressionLevel;
    const compressionRatio = 1 - (compressionLevel * 0.08); // 8% per level
    const compressedSize = Math.floor(originalSize * compressionRatio);
    
    // Create compressed buffer (in reality, this would be actual compressed data)
    const compressedData = new ArrayBuffer(compressedSize);
    
    const compressionTime = Date.now() - startTime;

    const result: CompressionResult = {
      compressedData,
      originalSize,
      compressedSize,
      compressionRatio,
      compressionTime
    };

    this.emit('audio:compressed', result);
    return result;
  }

  /**
   * Determine if audio should be compressed
   */
  private shouldCompressAudio(): boolean {
    if (!this.config.enableCompression) {
      return false;
    }

    // Compress if network is below threshold
    if (this.currentMetrics && this.currentMetrics.bandwidth < this.config.compressionThreshold) {
      return true;
    }

    // Compress in poor or fair conditions
    return this.currentCondition === NetworkCondition.POOR || 
           this.currentCondition === NetworkCondition.FAIR;
  }

  /**
   * Queue operation for synchronization
   */
  queueOperation(operation: Omit<SyncOperation, 'id' | 'timestamp' | 'retryCount'>): string {
    // Check queue size
    if (this.syncQueue.length >= this.config.maxQueueSize) {
      // Remove lowest priority items
      this.evictLowPriorityOperations();
    }

    const id = `sync_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const syncOp: SyncOperation = {
      id,
      timestamp: new Date(),
      retryCount: 0,
      ...operation
    };

    this.syncQueue.push(syncOp);
    
    // Sort by priority
    this.syncQueue.sort((a, b) => a.priority - b.priority);

    this.emit('operation:queued', { id, type: operation.type, priority: operation.priority });

    // If online and critical priority, sync immediately
    if (this.currentCondition !== NetworkCondition.OFFLINE && 
        operation.priority === SyncPriority.CRITICAL) {
      this.processSyncQueue().catch(console.error);
    }

    return id;
  }

  /**
   * Evict low priority operations to make space
   */
  private evictLowPriorityOperations(): void {
    // Remove operations with LOW priority first
    const lowPriorityIndex = this.syncQueue.findIndex(op => op.priority === SyncPriority.LOW);
    if (lowPriorityIndex !== -1) {
      const removed = this.syncQueue.splice(lowPriorityIndex, 1)[0];
      this.emit('operation:evicted', { id: removed.id, priority: removed.priority });
      return;
    }

    // If no LOW priority, remove oldest NORMAL priority
    const normalPriorityIndex = this.syncQueue.findIndex(op => op.priority === SyncPriority.NORMAL);
    if (normalPriorityIndex !== -1) {
      const removed = this.syncQueue.splice(normalPriorityIndex, 1)[0];
      this.emit('operation:evicted', { id: removed.id, priority: removed.priority });
    }
  }

  /**
   * Start sync timer
   */
  private startSyncTimer(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
    }

    this.syncTimer = setInterval(() => {
      if (this.currentCondition !== NetworkCondition.OFFLINE && !this.isSyncing) {
        this.processSyncQueue().catch(error => {
          console.error('Sync error:', error);
        });
      }
    }, this.config.syncInterval);
  }

  /**
   * Process sync queue
   */
  async processSyncQueue(): Promise<void> {
    if (this.isSyncing || this.syncQueue.length === 0) {
      return;
    }

    if (this.currentCondition === NetworkCondition.OFFLINE) {
      return;
    }

    this.isSyncing = true;
    this.emit('sync:started', { queueSize: this.syncQueue.length });

    try {
      // Process operations in batches based on priority
      const batch = this.getNextBatch();
      
      for (const operation of batch) {
        try {
          await this.syncOperation(operation);
          
          // Remove from queue on success
          const index = this.syncQueue.findIndex(op => op.id === operation.id);
          if (index !== -1) {
            this.syncQueue.splice(index, 1);
          }
          
          this.emit('operation:synced', { id: operation.id, type: operation.type });
        } catch (error) {
          await this.handleSyncError(operation, error as Error);
        }
      }

      this.emit('sync:completed', { 
        processed: batch.length,
        remaining: this.syncQueue.length 
      });
    } finally {
      this.isSyncing = false;
    }
  }

  /**
   * Get next batch of operations to sync
   */
  private getNextBatch(): SyncOperation[] {
    // Prioritize based on network condition
    let batchSize = this.config.syncBatchSize;
    
    if (this.currentCondition === NetworkCondition.POOR) {
      batchSize = Math.floor(batchSize / 2); // Reduce batch size in poor conditions
    } else if (this.currentCondition === NetworkCondition.EXCELLENT) {
      batchSize = batchSize * 2; // Increase batch size in excellent conditions
    }

    // Get operations, prioritizing CRITICAL and HIGH
    const batch: SyncOperation[] = [];
    
    for (const operation of this.syncQueue) {
      if (batch.length >= batchSize) {
        break;
      }
      
      // In poor conditions, only sync critical and high priority
      if (this.currentCondition === NetworkCondition.POOR && 
          operation.priority > SyncPriority.HIGH) {
        continue;
      }

      // In fair conditions, skip low priority operations
      if (this.currentCondition === NetworkCondition.FAIR && 
          operation.priority > SyncPriority.NORMAL) {
        continue;
      }
      
      batch.push(operation);
    }

    return batch;
  }

  /**
   * Sync a single operation
   */
  private async syncOperation(operation: SyncOperation): Promise<void> {
    // In a real implementation, this would:
    // 1. Send data to server
    // 2. Handle conflicts
    // 3. Update local state
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 50));

    // Check for conflicts
    if (Math.random() < 0.1) { // 10% chance of conflict for testing
      await this.handleConflict(operation);
    }
  }

  /**
   * Handle sync conflict
   */
  private async handleConflict(operation: SyncOperation): Promise<void> {
    const conflict: SyncConflict = {
      operationId: operation.id,
      localData: operation.data,
      serverData: { /* simulated server data */ },
      conflictType: 'data_mismatch',
      resolution: operation.conflictResolution || ConflictResolutionStrategy.SERVER_WINS
    };

    // Resolve based on strategy
    switch (conflict.resolution) {
      case ConflictResolutionStrategy.SERVER_WINS:
        conflict.resolvedData = conflict.serverData;
        break;
      
      case ConflictResolutionStrategy.CLIENT_WINS:
        conflict.resolvedData = conflict.localData;
        break;
      
      case ConflictResolutionStrategy.MERGE:
        conflict.resolvedData = this.mergeData(conflict.localData, conflict.serverData);
        break;
      
      case ConflictResolutionStrategy.MANUAL:
        // Emit event for manual resolution
        this.emit('conflict:manual', conflict);
        throw new Error('Manual conflict resolution required');
    }

    this.emit('conflict:resolved', conflict);
  }

  /**
   * Merge local and server data
   */
  private mergeData(localData: any, serverData: any): any {
    // Simple merge strategy - in reality, this would be type-specific
    return {
      ...serverData,
      ...localData,
      _merged: true,
      _mergedAt: new Date()
    };
  }

  /**
   * Handle sync error
   */
  private async handleSyncError(operation: SyncOperation, error: Error): Promise<void> {
    operation.retryCount++;

    if (operation.retryCount >= operation.maxRetries) {
      // Max retries reached, remove from queue
      const index = this.syncQueue.findIndex(op => op.id === operation.id);
      if (index !== -1) {
        this.syncQueue.splice(index, 1);
      }
      
      this.emit('operation:failed', {
        id: operation.id,
        type: operation.type,
        error: error.message,
        retries: operation.retryCount
      });
    } else {
      // Keep in queue for retry
      this.emit('operation:retry', {
        id: operation.id,
        type: operation.type,
        retryCount: operation.retryCount,
        maxRetries: operation.maxRetries
      });
    }
  }

  /**
   * Get current network condition
   */
  getNetworkCondition(): NetworkCondition {
    return this.currentCondition;
  }

  /**
   * Get current network metrics
   */
  getNetworkMetrics(): NetworkMetrics | null {
    return this.currentMetrics;
  }

  /**
   * Get current audio quality settings
   */
  getAudioQuality(): AudioQualitySettings {
    return { ...this.currentQuality };
  }

  /**
   * Set the network condition and adjust quality accordingly
   */
  setCondition(condition: NetworkCondition): void {
    this.handleConditionChange(condition);
  }

  /**
   * Get sync queue status
   */
  getSyncQueueStatus(): {
    queueSize: number;
    isSyncing: boolean;
    byPriority: Record<SyncPriority, number>;
  } {
    const byPriority: Record<SyncPriority, number> = {
      [SyncPriority.CRITICAL]: 0,
      [SyncPriority.HIGH]: 0,
      [SyncPriority.NORMAL]: 0,
      [SyncPriority.LOW]: 0
    };

    for (const operation of this.syncQueue) {
      byPriority[operation.priority]++;
    }

    return {
      queueSize: this.syncQueue.length,
      isSyncing: this.isSyncing,
      byPriority
    };
  }

  /**
   * Manually trigger sync
   */
  async triggerSync(): Promise<void> {
    await this.processSyncQueue();
  }

  /**
   * Clear sync queue
   */
  clearQueue(): void {
    const clearedCount = this.syncQueue.length;
    this.syncQueue = [];
    this.emit('queue:cleared', { clearedCount });
  }

  /**
   * Cleanup and stop timers
   */
  destroy(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
    
    if (this.metricsTimer) {
      clearInterval(this.metricsTimer);
      this.metricsTimer = null;
    }
    
    this.removeAllListeners();
  }
}
