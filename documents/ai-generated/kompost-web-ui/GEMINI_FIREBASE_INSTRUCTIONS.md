# STRICT INSTRUCTIONS FOR GEMINI: Firebase FFMPEG Analytics MVP

## ⚠️ CRITICAL CONSTRAINTS - READ FIRST

**YOU ARE BUILDING AN MVP. NO FEATURE CREEP ALLOWED.**

### 🛑 ABSOLUTE PROHIBITIONS
- **NO** fancy visualizations or charts initially
- **NO** real-time dashboards or complex UI
- **NO** AI/ML features or pattern recognition algorithms  
- **NO** advanced authentication beyond Google OAuth
- **NO** complex state management or caching layers
- **NO** mobile apps or PWA features
- **NO** notifications, alerts, or background processing
- **NO** file upload interfaces or media management

### ✅ MVP SCOPE ONLY

Build exactly these 4 features in order:

#### 1. Google Authentication Setup
- Firebase project with Google OAuth
- Simple login/logout functionality
- User session management
- Basic security rules

#### 2. FFMPEG Operation Tracking
- Firestore collection: `/users/{userId}/operations/{operationId}`
- Store operation type, parameters, timestamp, success/failure
- Simple HTTP endpoint for MCP server integration
- Basic form to manually add test operations

#### 3. Personal Operation History
- Simple table showing user's operations
- Columns: timestamp, operation type, success/failure
- Basic filtering by operation type
- No charts, no analytics, just raw data display

#### 4. REST API Endpoints
- POST `/api/operations` - Log FFMPEG operation
- GET `/api/operations` - Retrieve user operations
- Basic validation and error handling

## 🏗️ TECHNOLOGY REQUIREMENTS

### Mandatory Stack
- **Frontend**: React 18 + TypeScript
- **Styling**: Tailwind CSS (basic utility classes only)
- **Database**: Cloud Firestore
- **Authentication**: Firebase Auth with Google provider
- **Hosting**: Firebase Hosting
- **Functions**: Cloud Functions (minimal)

### Forbidden Technologies
- No chart libraries (Chart.js, Recharts, etc.)
- No complex state management (Redux, Zustand)
- No real-time listeners initially
- No external APIs or integrations
- No advanced CSS frameworks or component libraries

## 📋 EXACT DATA SCHEMA

```typescript
interface FFMPEGOperation {
  id: string;
  userId: string;
  timestamp: FirebaseTimestamp;
  platform: "mcp" | "komposteur";
  
  // Operation details
  operation: {
    type: string;        // "trim", "resize", "convert", etc.
    parameters: string;  // JSON string of parameters
    inputFormat?: string;
    outputFormat?: string;
  };
  
  // Simple metrics only
  metrics: {
    success: boolean;
    processingTime?: number; // milliseconds
    errorMessage?: string;
  };
}
```

## 🔒 SECURITY RULES

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId}/operations/{operationId} {
      allow create, read: if request.auth.uid == userId;
      allow update, delete: if false;
    }
  }
}
```

## 📱 UI REQUIREMENTS

### Single Page Layout
```
Header: [kompo.st Analytics] [User Avatar] [Logout]
Main: 
  - Title: "My FFMPEG Operations"
  - Filter: [All Operations] [Dropdown: operation type]
  - Table: [Timestamp] [Operation] [Success] [Parameters]
  - Pagination: Simple prev/next
Footer: Basic copyright
```

### Design Constraints
- Maximum 3 colors total
- No animations or transitions
- No loading states beyond basic spinners
- No modals, popovers, or complex interactions
- Basic responsive design only

## 🔌 MCP Integration Point

Create single Cloud Function:
```typescript
export const logOperation = onRequest(async (req, res) => {
  // Validate auth token
  // Parse operation data
  // Write to Firestore
  // Return success/error
});
```

## 📁 Project Structure
```
firebase-ffmpeg-analytics/
├── src/
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── OperationTable.tsx
│   │   └── LoginForm.tsx
│   ├── hooks/
│   │   └── useAuth.ts
│   ├── types/
│   │   └── Operation.ts
│   └── App.tsx
├── functions/
│   └── src/
│       └── index.ts
├── firestore.rules
├── firebase.json
└── package.json
```

## ✅ COMPLETION CRITERIA

The MVP is complete when:
1. User can login with Google
2. User can view their operation history in a table
3. HTTP endpoint accepts operation data from MCP server
4. Data persists in Firestore with proper security
5. Basic filtering works
6. Application deploys to Firebase Hosting

## 🚫 FEATURE REQUESTS POLICY

**ANY REQUEST FOR ADDITIONAL FEATURES MUST BE REJECTED** with response:
> "This feature is outside the MVP scope. The current implementation focuses on basic operation tracking only. Additional features can be considered in future phases."

## 🎯 SUCCESS METRICS

- Lines of code: < 500 total
- Components: < 6 React components
- Load time: < 2 seconds
- Setup time: < 30 minutes for new Firebase project

## 📋 STEP-BY-STEP IMPLEMENTATION

1. **Initialize Firebase project** with Authentication + Firestore
2. **Create React app** with TypeScript + Tailwind
3. **Implement Google authentication** with Firebase Auth
4. **Create operation logging endpoint** as Cloud Function
5. **Build simple table view** for operation history
6. **Add basic filtering** by operation type
7. **Deploy to Firebase Hosting**
8. **Test integration** with sample MCP calls

**TOTAL ESTIMATED TIME: 4-6 hours maximum**

---

**REMINDER**: This is phase 1 of a larger system. Keep it simple, functional, and focused. Advanced features will be added in controlled phases after this foundation is proven.