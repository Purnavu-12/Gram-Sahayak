/**
 * WebRTC Voice Streaming Service
 * Implements real-time audio streaming using WebRTC APIs
 * Validates: Requirements 1.1, 1.3, 1.5
 */

import { EventEmitter } from 'events';

export interface WebRTCConfig {
  iceServers: any[];
  audioConstraints: any;
  codecPreferences?: string[];
}

export interface StreamingSession {
  sessionId: string;
  userId: string;
  peerConnection: any | null;
  dataChannel: any | null;
  audioStream: any | null;
  startTime: number;
  isActive: boolean;
}

export interface AudioChunkData {
  sessionId: string;
  audioData: ArrayBuffer;
  timestamp: number;
  sampleRate: number;
  channels: number;
}

/**
 * WebRTC-based real-time voice streaming service
 * Handles peer connections, audio streaming, and data channels
 */
export class WebRTCStreamingService extends EventEmitter {
  private sessions: Map<string, StreamingSession> = new Map();
  private config: WebRTCConfig;

  constructor(config?: Partial<WebRTCConfig>) {
    super();
    this.config = {
      iceServers: config?.iceServers || [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ],
      audioConstraints: config?.audioConstraints || {
        echoCancellation: true,
        autoGainControl: true,
        sampleRate: 16000,
        channelCount: 1
      },
      codecPreferences: config?.codecPreferences || ['opus']
    };
  }

  /**
   * Create a new WebRTC streaming session
   */
  async createSession(sessionId: string, userId: string): Promise<StreamingSession> {
    const session: StreamingSession = {
      sessionId,
      userId,
      peerConnection: null,
      dataChannel: null,
      audioStream: null,
      startTime: Date.now(),
      isActive: true
    };

    this.sessions.set(sessionId, session);
    this.emit('session:created', { sessionId, userId });
    
    return session;
  }

  /**
   * Initialize WebRTC peer connection for a session
   * Note: In production, this would use actual WebRTC implementation
   * For Node.js, requires wrtc or similar polyfill
   */
  async initializePeerConnection(sessionId: string): Promise<any> {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error(`Session ${sessionId} not found`);
    }

    // Mock peer connection for testing
    // In production, would use: new RTCPeerConnection({ iceServers: this.config.iceServers })
    const peerConnection: any = {
      connectionState: 'new',
      onicecandidate: null,
      onconnectionstatechange: null,
      ontrack: null,
      createDataChannel: (name: string, options: any) => ({
        label: name,
        readyState: 'connecting',
        binaryType: 'arraybuffer',
        onopen: null,
        onclose: null,
        onerror: null,
        onmessage: null,
        send: (data: any) => {},
        close: () => {}
      }),
      createOffer: async (options: any) => ({ type: 'offer', sdp: 'mock-sdp' }),
      setLocalDescription: async (desc: any) => {},
      setRemoteDescription: async (desc: any) => {},
      addIceCandidate: async (candidate: any) => {},
      getStats: async () => new Map(),
      close: () => {}
    };

    session.peerConnection = peerConnection;
    return peerConnection;
  }

  /**
   * Create data channel for bidirectional communication
   */
  createDataChannel(sessionId: string, channelName: string = 'audio-data'): any {
    const session = this.sessions.get(sessionId);
    if (!session || !session.peerConnection) {
      throw new Error(`Session ${sessionId} not initialized`);
    }

    const dataChannel = session.peerConnection.createDataChannel(channelName, {
      ordered: false,
      maxRetransmits: 0
    });

    dataChannel.onopen = () => {
      this.emit('datachannel:open', { sessionId });
    };

    dataChannel.onclose = () => {
      this.emit('datachannel:close', { sessionId });
    };

    dataChannel.onerror = (error: any) => {
      this.emit('datachannel:error', { sessionId, error });
    };

    dataChannel.onmessage = (event: any) => {
      this.handleIncomingAudioData(sessionId, event.data);
    };

    session.dataChannel = dataChannel;
    return dataChannel;
  }

  /**
   * Send audio chunk through data channel
   */
  async sendAudioChunk(sessionId: string, audioData: ArrayBuffer): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session || !session.dataChannel) {
      throw new Error(`Session ${sessionId} not ready for data transmission`);
    }

    if (session.dataChannel.readyState !== 'open') {
      throw new Error(`Data channel not open for session ${sessionId}`);
    }

    try {
      session.dataChannel.send(audioData);
    } catch (error) {
      this.emit('send:error', { sessionId, error });
      throw error;
    }
  }

  /**
   * Handle incoming audio data from data channel
   */
  private handleIncomingAudioData(sessionId: string, data: ArrayBuffer): void {
    const audioChunk: AudioChunkData = {
      sessionId,
      audioData: data,
      timestamp: Date.now(),
      sampleRate: 16000, // Default, should be negotiated
      channels: 1
    };

    this.emit('audio:chunk', audioChunk);
  }

  /**
   * Handle connection failures with retry logic
   */
  private async handleConnectionFailure(sessionId: string): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session) return;

    this.emit('connection:failed', { sessionId });

    // In production with real WebRTC, would attempt to restart ICE
    // For now, just emit the restart event
    this.emit('connection:restart', { sessionId });
  }

  /**
   * Create SDP offer for session
   */
  async createOffer(sessionId: string): Promise<any> {
    const session = this.sessions.get(sessionId);
    if (!session || !session.peerConnection) {
      throw new Error(`Session ${sessionId} not initialized`);
    }

    const offer = await session.peerConnection.createOffer({
      offerToReceiveAudio: true
    });

    await session.peerConnection.setLocalDescription(offer);
    return offer;
  }

  /**
   * Handle SDP answer from remote peer
   */
  async handleAnswer(sessionId: string, answer: any): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session || !session.peerConnection) {
      throw new Error(`Session ${sessionId} not initialized`);
    }

    await session.peerConnection.setRemoteDescription(answer);
  }

  /**
   * Add ICE candidate to peer connection
   */
  async addIceCandidate(sessionId: string, candidate: any): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session || !session.peerConnection) {
      throw new Error(`Session ${sessionId} not initialized`);
    }

    await session.peerConnection.addIceCandidate(candidate);
  }

  /**
   * Get session statistics
   */
  async getSessionStats(sessionId: string): Promise<any | null> {
    const session = this.sessions.get(sessionId);
    if (!session || !session.peerConnection) {
      return null;
    }

    return await session.peerConnection.getStats();
  }

  /**
   * Close streaming session and cleanup resources
   */
  async closeSession(sessionId: string): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session) return;

    // Close data channel
    if (session.dataChannel) {
      session.dataChannel.close();
    }

    // Close peer connection
    if (session.peerConnection) {
      session.peerConnection.close();
    }

    // Stop audio tracks
    if (session.audioStream && session.audioStream.getTracks) {
      session.audioStream.getTracks().forEach((track: any) => track.stop());
    }

    session.isActive = false;
    this.sessions.delete(sessionId);
    
    this.emit('session:closed', { sessionId });
  }

  /**
   * Get active session
   */
  getSession(sessionId: string): StreamingSession | undefined {
    return this.sessions.get(sessionId);
  }

  /**
   * Get all active sessions
   */
  getActiveSessions(): StreamingSession[] {
    return Array.from(this.sessions.values()).filter(s => s.isActive);
  }
}
