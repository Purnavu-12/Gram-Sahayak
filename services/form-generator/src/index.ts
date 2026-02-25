import express, { Request, Response } from 'express';
import { FormGeneratorService } from './form-generator-service';

const app = express();
app.use(express.json());

const formService = new FormGeneratorService();

// Initialize Redis connection
formService.connect().then(() => {
  console.log('Form Generator Service connected to Redis');
}).catch(err => {
  console.error('Failed to connect to Redis:', err);
  process.exit(1);
});

// Start form filling session
app.post('/api/forms/start', async (req: Request, res: Response) => {
  try {
    const { schemeId, userId } = req.body;
    
    if (!schemeId || !userId) {
      return res.status(400).json({ error: 'schemeId and userId are required' });
    }

    const session = await formService.startFormFilling(schemeId, userId);
    res.json(session);
  } catch (error) {
    console.error('Error starting form session:', error);
    res.status(500).json({ error: (error as Error).message });
  }
});

// Process user response
app.post('/api/forms/process', async (req: Request, res: Response) => {
  try {
    const { sessionId, response } = req.body;
    
    if (!sessionId || !response) {
      return res.status(400).json({ error: 'sessionId and response are required' });
    }

    const update = await formService.processUserResponse(sessionId, response);
    res.json(update);
  } catch (error) {
    console.error('Error processing response:', error);
    res.status(500).json({ error: (error as Error).message });
  }
});

// Get form template
app.get('/api/forms/template/:schemeId', (req: Request, res: Response) => {
  try {
    const { schemeId } = req.params;
    const template = formService.getFormTemplate(schemeId);
    
    if (!template) {
      return res.status(404).json({ error: 'Template not found' });
    }

    res.json(template);
  } catch (error) {
    console.error('Error getting template:', error);
    res.status(500).json({ error: (error as Error).message });
  }
});

// Get format template and examples
app.get('/api/forms/format/:fieldType', (req: Request, res: Response) => {
  try {
    const { fieldType } = req.params;
    const template = formService.getFormatTemplate(fieldType);
    res.json(template);
  } catch (error) {
    console.error('Error getting format template:', error);
    res.status(500).json({ error: (error as Error).message });
  }
});

// Convert input to specific format
app.post('/api/forms/convert', (req: Request, res: Response) => {
  try {
    const { input, fieldType, fieldName } = req.body;
    
    if (!input || !fieldType) {
      return res.status(400).json({ error: 'input and fieldType are required' });
    }

    const result = formService.convertToFormat(input, fieldType, fieldName);
    res.json(result);
  } catch (error) {
    console.error('Error converting format:', error);
    res.status(500).json({ error: (error as Error).message });
  }
});

// Generate PDF for completed form
app.post('/api/forms/generate-pdf', async (req: Request, res: Response) => {
  try {
    const { sessionId } = req.body;
    
    if (!sessionId) {
      return res.status(400).json({ error: 'sessionId is required' });
    }

    const pdfDoc = await formService.generatePDF(sessionId);
    
    // Set headers for PDF download
    res.setHeader('Content-Type', pdfDoc.mimeType);
    res.setHeader('Content-Disposition', `attachment; filename="${pdfDoc.filename}"`);
    res.send(pdfDoc.buffer);
  } catch (error) {
    console.error('Error generating PDF:', error);
    res.status(500).json({ error: (error as Error).message });
  }
});

// Validate form data
app.post('/api/forms/validate', async (req: Request, res: Response) => {
  try {
    const { formData, schemeId } = req.body;
    
    if (!formData || !schemeId) {
      return res.status(400).json({ error: 'formData and schemeId are required' });
    }

    const result = await formService.validateForm(formData, schemeId);
    res.json(result);
  } catch (error) {
    console.error('Error validating form:', error);
    res.status(500).json({ error: (error as Error).message });
  }
});

// Get PDF template for a scheme
app.get('/api/forms/pdf-template/:schemeId', (req: Request, res: Response) => {
  try {
    const { schemeId } = req.params;
    const template = formService.getPDFTemplate(schemeId);
    
    if (!template) {
      return res.status(404).json({ error: 'PDF template not found' });
    }

    res.json(template);
  } catch (error) {
    console.error('Error getting PDF template:', error);
    res.status(500).json({ error: (error as Error).message });
  }
});

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'ok', service: 'form-generator' });
});

const PORT = process.env.PORT || 3002;

app.listen(PORT, () => {
  console.log(`Form Generator Service listening on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully');
  await formService.disconnect();
  process.exit(0);
});

export { formService };
