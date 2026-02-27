import express from 'express';
import { ConversationOrchestrator, ConversationInput } from '../services/conversation-orchestrator';
import { tracingMiddleware, DistributedTracer } from '../services/distributed-tracing';
import { globalErrorHandler } from '../services/error-handler';

const router = express.Router();
const orchestrator = new ConversationOrchestrator();
const tracer = new DistributedTracer('conversation-api');

// Apply tracing middleware
router.use(tracingMiddleware('conversation-api'));

/**
 * Start a new conversation
 */
router.post('/start', async (req, res) => {
  const span = tracer.startTrace('start-conversation', {
    userId: req.body.userId,
  });

  try {
    const input: ConversationInput = {
      userId: req.body.userId,
      preferredLanguage: req.body.preferredLanguage,
      textInput: req.body.textInput,
    };

    tracer.log(span, 'info', 'Starting new conversation', { userId: input.userId });

    const output = await orchestrator.processConversation(input);

    tracer.log(span, 'info', 'Conversation started successfully', {
      sessionId: output.sessionId,
      stage: output.stage,
    });

    tracer.finishSpan(span, 'success');

    res.json({
      success: true,
      data: output,
    });
  } catch (error: any) {
    tracer.log(span, 'error', 'Failed to start conversation', {
      error: error.message,
    });
    tracer.finishSpan(span, 'error', error);

    const recovery = await globalErrorHandler.handleError(
      error,
      { userId: req.body.userId } as any,
      'conversation-api',
      'start-conversation',
      span
    );

    res.status(500).json({
      success: false,
      error: error.message,
      recovery: recovery.fallbackResponse,
    });
  }
});

/**
 * Continue an existing conversation
 */
router.post('/continue', async (req, res) => {
  const span = tracer.startTrace('continue-conversation', {
    sessionId: req.body.sessionId,
    userId: req.body.userId,
  });

  try {
    const input: ConversationInput = {
      sessionId: req.body.sessionId,
      userId: req.body.userId,
      audioData: req.body.audioData,
      textInput: req.body.textInput,
    };

    tracer.log(span, 'info', 'Continuing conversation', {
      sessionId: input.sessionId,
      hasAudio: !!input.audioData,
      hasText: !!input.textInput,
    });

    const output = await orchestrator.processConversation(input);

    tracer.log(span, 'info', 'Conversation continued successfully', {
      stage: output.stage,
      hasResponse: !!output.response,
    });

    tracer.finishSpan(span, 'success');

    res.json({
      success: true,
      data: output,
    });
  } catch (error: any) {
    tracer.log(span, 'error', 'Failed to continue conversation', {
      error: error.message,
    });
    tracer.finishSpan(span, 'error', error);

    const recovery = await globalErrorHandler.handleError(
      error,
      { sessionId: req.body.sessionId, userId: req.body.userId } as any,
      'conversation-api',
      'continue-conversation',
      span
    );

    res.status(500).json({
      success: false,
      error: error.message,
      recovery: recovery.fallbackResponse,
    });
  }
});

/**
 * Get conversation history
 */
router.get('/:sessionId/history', async (req, res) => {
  const span = tracer.startTrace('get-conversation-history', {
    sessionId: req.params.sessionId,
  });

  try {
    tracer.log(span, 'info', 'Fetching conversation history', {
      sessionId: req.params.sessionId,
    });

    const history = await orchestrator.getConversationHistory(req.params.sessionId);

    tracer.log(span, 'info', 'History fetched successfully', {
      messageCount: history.length,
    });

    tracer.finishSpan(span, 'success');

    res.json({
      success: true,
      data: {
        sessionId: req.params.sessionId,
        history,
      },
    });
  } catch (error: any) {
    tracer.log(span, 'error', 'Failed to fetch history', {
      error: error.message,
    });
    tracer.finishSpan(span, 'error', error);

    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

/**
 * Delete a conversation
 */
router.delete('/:sessionId', async (req, res) => {
  const span = tracer.startTrace('delete-conversation', {
    sessionId: req.params.sessionId,
  });

  try {
    tracer.log(span, 'info', 'Deleting conversation', {
      sessionId: req.params.sessionId,
    });

    await orchestrator.deleteConversation(req.params.sessionId);

    tracer.log(span, 'info', 'Conversation deleted successfully');
    tracer.finishSpan(span, 'success');

    res.json({
      success: true,
      message: 'Conversation deleted',
    });
  } catch (error: any) {
    tracer.log(span, 'error', 'Failed to delete conversation', {
      error: error.message,
    });
    tracer.finishSpan(span, 'error', error);

    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

/**
 * Get error statistics
 */
router.get('/errors/stats', async (req, res) => {
  try {
    const stats = globalErrorHandler.getErrorStats();

    res.json({
      success: true,
      data: stats,
    });
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

export default router;
