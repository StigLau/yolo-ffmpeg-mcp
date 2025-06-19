import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import express from 'express';
import cors from 'cors';
import { createHash } from 'crypto';

// Initialize Firebase Admin SDK
admin.initializeApp();

const app = express();

// Enable CORS for all routes
app.use(cors({ origin: true }));

// Parse JSON requests
app.use(express.json());

// Environment configuration
const MCP_API_KEY_HASH = functions.config().mcp?.api_key_hash ||
  '747bcec4bd585e8e8abacaf3814a2d4500fd3c0eb4b773b179b174366534faac'; // Default hash for demo key

// Middleware for API key validation
const validateApiKey = (req: express.Request, res: express.Response, next: express.NextFunction) => {
  try {
    const apiKey = req.headers['x-api-key'] as string;
    if (!apiKey) {
      res.status(401).json({ error: 'API key required' });
      return;
    }

    // Hash the provided key and compare with stored hash
    const providedKeyHash = createHash('sha256').update(apiKey).digest('hex');
    if (providedKeyHash !== MCP_API_KEY_HASH) {
      res.status(401).json({ error: 'Invalid API key' });
      return;
    }

    next();
  } catch (error) {
    console.error('API key validation error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// Middleware for Firebase Authentication
const validateFirebaseToken = async (req: any, res: express.Response, next: express.NextFunction) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      res.status(401).json({ error: 'Unauthorized', reason: 'missing-bearer-token' });
      return;
    }
    
    const idToken = authHeader.split('Bearer ')[1];
    const decodedToken = await admin.auth().verifyIdToken(idToken);
    req.user = decodedToken;
    next();
  } catch (error) {
    console.error('Firebase auth error:', error);
    res.status(401).json({ error: 'Unauthorized', reason: 'invalid-token' });
  }
};

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'edit.kompo.st-firebase-functions',
    version: '1.0.0'
  });
});

// Public API endpoint for MCP server to log operations
app.post('/api/public/logOperation', validateApiKey, async (req, res) => {
  try {
    const operationData = req.body;
    
    // Validate required fields
    if (!operationData.id || !operationData.timestamp || !operationData.operation?.type) {
      res.status(400).json({
        error: 'Missing required fields: id, timestamp, operation.type'
      });
      return;
    }

    const db = admin.firestore();
    
    // Store in system_operations collection for MCP operations
    const systemDocRef = await db.collection('system_operations').add({
      ...operationData,
      source: 'mcp_server',
      receivedAt: admin.firestore.FieldValue.serverTimestamp()
    });

    // Also store in analytics collection for pattern analysis
    await db.collection('analytics').add({
      type: 'operation',
      platform: operationData.platform || 'mcp',
      operation_type: operationData.operation.type,
      success: operationData.metrics.success,
      processing_time: operationData.metrics.processingTime,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      user_id: operationData.userId || 'system',
      raw_data: operationData
    });

    // Update aggregated statistics
    await updateAggregatedStats(operationData);

    res.status(200).json({
      success: true,
      message: 'Operation logged successfully',
      id: systemDocRef.id
    });
  } catch (error) {
    console.error('Error logging operation:', error);
    res.status(500).json({ error: 'Failed to log operation' });
  }
});

// CouchDB-compatible REST API for Kompositions

// List all kompositions for authenticated user
app.get('/api/kompositions', validateFirebaseToken, async (req: any, res) => {
  try {
    const db = admin.firestore();
    const kompositionsRef = await db.collection('kompositions')
      .where('userId', '==', req.user.uid)
      .orderBy('updatedAt', 'desc')
      .get();
    
    const kompositions = kompositionsRef.docs.map(doc => ({
      _id: doc.id,
      _rev: `1-${doc.updateTime?.toMillis().toString(16)}`,
      ...doc.data(),
      id: doc.id
    }));
    
    res.json({
      total_rows: kompositions.length,
      offset: 0,
      rows: kompositions.map(kompo => ({
        id: kompo._id,
        key: kompo._id,
        value: { rev: kompo._rev },
        doc: kompo
      }))
    });
  } catch (error) {
    console.error('Error listing kompositions:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get specific komposition by ID
app.get('/api/kompositions/:id', validateFirebaseToken, async (req: any, res) => {
  try {
    const db = admin.firestore();
    const docRef = db.collection('kompositions').doc(req.params.id);
    const doc = await docRef.get();
    
    if (!doc.exists) {
      res.status(404).json({ error: 'not_found', reason: 'missing' });
      return;
    }
    
    const data = doc.data();
    
    // Security check: ensure user owns the komposition
    if (data?.userId !== req.user.uid) {
      res.status(403).json({ error: 'forbidden' });
      return;
    }
    
    const komposition = {
      _id: doc.id,
      _rev: `1-${doc.updateTime?.toMillis().toString(16)}`,
      ...data,
      id: doc.id
    };
    
    res.json(komposition);
  } catch (error) {
    console.error('Error getting komposition:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create new komposition
app.post('/api/kompositions', validateFirebaseToken, async (req: any, res) => {
  try {
    const db = admin.firestore();
    const kompositionData = {
      ...req.body,
      userId: req.user.uid,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
      status: req.body.status || 'draft'
    };
    
    // Remove CouchDB specific fields if present
    delete kompositionData._id;
    delete kompositionData._rev;
    
    const docRef = await db.collection('kompositions').add(kompositionData);
    const newDoc = await docRef.get();
    
    res.status(201).json({
      ok: true,
      id: docRef.id,
      rev: `1-${newDoc.updateTime?.toMillis().toString(16)}`
    });
  } catch (error) {
    console.error('Error creating komposition:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Update existing komposition
app.put('/api/kompositions/:id', validateFirebaseToken, async (req: any, res) => {
  try {
    const db = admin.firestore();
    const docRef = db.collection('kompositions').doc(req.params.id);
    const doc = await docRef.get();
    
    if (!doc.exists) {
      res.status(404).json({ error: 'not_found', reason: 'missing' });
      return;
    }
    
    const existingData = doc.data();
    
    // Security check: ensure user owns the komposition
    if (existingData?.userId !== req.user.uid) {
      res.status(403).json({ error: 'forbidden' });
      return;
    }
    
    const updateData = {
      ...req.body,
      userId: req.user.uid, // Ensure userId cannot be changed
      updatedAt: admin.firestore.FieldValue.serverTimestamp()
    };
    
    // Remove CouchDB specific fields
    delete updateData._id;
    delete updateData._rev;
    delete updateData.id;
    
    await docRef.update(updateData);
    const updatedDoc = await docRef.get();
    
    res.json({
      ok: true,
      id: req.params.id,
      rev: `1-${updatedDoc.updateTime?.toMillis().toString(16)}`
    });
  } catch (error) {
    console.error('Error updating komposition:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Delete komposition
app.delete('/api/kompositions/:id', validateFirebaseToken, async (req: any, res) => {
  try {
    const db = admin.firestore();
    const docRef = db.collection('kompositions').doc(req.params.id);
    const doc = await docRef.get();
    
    if (!doc.exists) {
      res.status(404).json({ error: 'not_found', reason: 'missing' });
      return;
    }
    
    const data = doc.data();
    
    // Security check: ensure user owns the komposition
    if (data?.userId !== req.user.uid) {
      res.status(403).json({ error: 'forbidden' });
      return;
    }
    
    await docRef.delete();
    
    res.json({
      ok: true,
      id: req.params.id,
      rev: `1-${doc.updateTime?.toMillis().toString(16)}`
    });
  } catch (error) {
    console.error('Error deleting komposition:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Helper function to update aggregated statistics
async function updateAggregatedStats(operationData: any) {
  try {
    const db = admin.firestore();
    const statsRef = db.collection('public_analytics').doc('operation_stats');
    
    await db.runTransaction(async (transaction) => {
      const statsDoc = await transaction.get(statsRef);
      const currentData = statsDoc.exists ? statsDoc.data() : {};
      
      const stats = {
        totalOperations: (currentData?.totalOperations || 0) + 1,
        operationCounts: currentData?.operationCounts || {},
        avgProcessingTimes: currentData?.avgProcessingTimes || {},
        successRates: currentData?.successRates || {},
        successCounts: currentData?.successCounts || {},
        lastUpdated: admin.firestore.FieldValue.serverTimestamp()
      };
      
      // Update counters
      const opType = operationData.operation.type;
      stats.operationCounts[opType] = (stats.operationCounts[opType] || 0) + 1;
      
      // Update processing times
      if (operationData.metrics.processingTime) {
        const currentAvg = stats.avgProcessingTimes[opType] || 0;
        const currentCount = stats.operationCounts[opType];
        const newAvg = ((currentAvg * (currentCount - 1)) + operationData.metrics.processingTime) / currentCount;
        stats.avgProcessingTimes[opType] = Math.round(newAvg);
      }
      
      // Update success rates
      const successCount = stats.successCounts[opType] || 0;
      const totalCount = stats.operationCounts[opType];
      if (operationData.metrics.success) {
        stats.successCounts[opType] = successCount + 1;
      }
      stats.successRates[opType] = Math.round((stats.successCounts[opType] / totalCount) * 100);
      
      transaction.set(statsRef, stats);
    });
  } catch (error) {
    console.error('Error updating aggregated stats:', error);
  }
}

// Export the Express app as a Cloud Function
export const api = functions.https.onRequest(app);

// Scheduled function to clean up old data
export const cleanupOldData = functions.pubsub.schedule('every 24 hours').onRun(async () => {
  try {
    const db = admin.firestore();
    const cutoffDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000); // 30 days ago
    
    // Clean up old system operations
    const oldOpsQuery = await db.collection('system_operations')
      .where('receivedAt', '<', cutoffDate)
      .limit(100)
      .get();
    
    const batch = db.batch();
    oldOpsQuery.docs.forEach(doc => {
      batch.delete(doc.ref);
    });
    
    await batch.commit();
    console.log(`Cleaned up ${oldOpsQuery.size} old operations`);
  } catch (error) {
    console.error('Error during cleanup:', error);
  }
});

// Function to handle user profile creation
export const createUserProfile = functions.auth.user().onCreate(async (user) => {
  try {
    const db = admin.firestore();
    await db.collection('users').doc(user.uid).set({
      email: user.email,
      displayName: user.displayName,
      photoURL: user.photoURL,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      settings: {
        defaultResolution: '1920x1080',
        defaultFPS: 30,
        defaultBPM: 120,
        notifications: {
          processingComplete: true,
          weeklyAnalytics: false,
          systemUpdates: true
        }
      }
    });
    console.log(`Created profile for user: ${user.uid}`);
  } catch (error) {
    console.error('Error creating user profile:', error);
  }
});