import express from 'express';
import { WebSocketServer, WebSocket } from 'ws';
import { VoiceEngineService } from './voice-engine-service';

const app = express();
const port = process.env.PORT || 3001;

app.use(express.json());

const voiceEngine = new VoiceEngineService();
const webrtcService = voiceEngine.getWebRTCService();

// HTTP endpoints
app.post('/session/start', async (req, res) => {
  try {
    const { userId, preferredLanguage } = req.body;
    const sessionId = await voiceEngine.startVoiceSession(userId, preferredLanguage);
    res.json({ sessionId });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.post('/session/end', async (req, res) => {
  try {
    const { sessionId } = req.body;
    const summary = await voiceEngine.endVoiceSession(sessionId);
    res.json(summary);
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

// WebRTC signaling endpoints
app.post('/webrtc/offer', async (req, res) => {
  try {
    const { sessionId } = req.body;
    const offer = await webrtcService.createOffer(sessionId);
    res.json({ offer });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.post('/webrtc/answer', async (req, res) => {
  try {
    const { sessionId, answer } = req.body;
    await webrtcService.handleAnswer(sessionId, answer);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.post('/webrtc/ice-candidate', async (req, res) => {
  try {
    const { sessionId, candidate } = req.body;
    await webrtcService.addIceCandidate(sessionId, candidate);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.get('/session/:sessionId/vad-state', (req, res) => {
  try {
    const { sessionId } = req.params;
    const vadState = voiceEngine.getVADState(sessionId);
    const isSpeechActive = voiceEngine.isSpeechActive(sessionId);
    res.json({ vadState, isSpeechActive });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

// Offline capabilities endpoints
app.get('/offline/status', (req, res) => {
  try {
    const syncStatus = voiceEngine.getSyncStatus();
    res.json(syncStatus);
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.post('/offline/set-status', (req, res) => {
  try {
    const { isOnline } = req.body;
    voiceEngine.setOnlineStatus(isOnline);
    res.json({ success: true, isOnline });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.get('/offline/available/:language', (req, res) => {
  try {
    const { language } = req.params;
    const { dialect } = req.query;
    const isAvailable = voiceEngine.isOfflineModeAvailable(
      language,
      dialect as string | undefined
    );
    res.json({ isAvailable, language, dialect });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.post('/offline/cache-model', async (req, res) => {
  try {
    const { language, dialect, version, modelData } = req.body;
    const offlineProcessor = voiceEngine.getOfflineProcessor();
    
    // Convert base64 to ArrayBuffer if needed
    const buffer = Buffer.from(modelData, 'base64');
    await offlineProcessor.cacheModel(language, dialect, buffer.buffer, version);
    
    res.json({ success: true, language, dialect, version });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.get('/offline/cached-models', (req, res) => {
  try {
    const offlineProcessor = voiceEngine.getOfflineProcessor();
    const models = offlineProcessor.getCachedModelVersions();
    res.json({ models });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.post('/offline/cache-scheme', async (req, res) => {
  try {
    const { scheme } = req.body;
    const offlineProcessor = voiceEngine.getOfflineProcessor();
    await offlineProcessor.cacheScheme(scheme);
    res.json({ success: true, schemeId: scheme.schemeId });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.get('/offline/cached-schemes', async (req, res) => {
  try {
    const offlineProcessor = voiceEngine.getOfflineProcessor();
    const schemes = await offlineProcessor.getAllCachedSchemes();
    res.json({ schemes });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

app.post('/offline/sync', async (req, res) => {
  try {
    const offlineProcessor = voiceEngine.getOfflineProcessor();
    await offlineProcessor.syncWithCloud();
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

const server = app.listen(port, () => {
  console.log(`Voice Engine service listening on port ${port}`);
});

// WebSocket server for real-time audio streaming
const wss = new WebSocketServer({ server, path: '/audio-stream' });

wss.on('connection', (ws: WebSocket, req) => {
  console.log('WebSocket connection established');
  
  let sessionId: string | null = null;

  ws.on('message', async (data: Buffer) => {
    try {
      // First message should be session initialization
      if (!sessionId) {
        const message = JSON.parse(data.toString());
        if (message.type === 'init' && message.sessionId) {
          sessionId = message.sessionId;
          ws.send(JSON.stringify({ type: 'ready', sessionId }));
        }
        return;
      }

      // Process audio data
      const result = await voiceEngine.processAudioStream(sessionId, data.buffer);
      
      // Send transcription result if final
      if (result.isFinal && result.text) {
        ws.send(JSON.stringify({
          type: 'transcription',
          result
        }));
      }
    } catch (error) {
      ws.send(JSON.stringify({
        type: 'error',
        message: (error as Error).message
      }));
    }
  });

  ws.on('close', () => {
    console.log('WebSocket connection closed');
    if (sessionId) {
      voiceEngine.endVoiceSession(sessionId).catch(console.error);
    }
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});
