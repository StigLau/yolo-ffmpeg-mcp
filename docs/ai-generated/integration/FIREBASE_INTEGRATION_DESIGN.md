# 🔥 Firebase Integration Design for KompostEdit

**Status**: 🚧 **IN PROGRESS** - Comprehensive Firebase integration plan

## 📊 **Firestore Schema Design**

### **Core Collections Structure**

#### **`kompositions/` Collection**
```typescript
interface KompositionDoc {
  // Document ID: auto-generated or user-defined
  id: string
  
  // Metadata
  userId: string              // Firebase Auth UID for security
  name: string               // User-friendly name
  revision: string           // Version tracking
  dvlType: string           // "video" | "audio" | "image"
  
  // Music composition data
  bpm: number               // Beats per minute (30-250)
  
  // Nested data
  segments: SegmentData[]   // Video/audio segments
  sources: SourceData[]     // Media file references
  config: VideoConfigData   // Output configuration
  beatpattern?: BeatPatternData  // Optional beat pattern
  
  // Firebase metadata
  createdAt: Timestamp
  updatedAt: Timestamp
  createdBy: string         // User email/name
  lastModifiedBy: string    // User email/name
  
  // Collaboration
  sharedWith?: string[]     // Array of user IDs (future feature)
  isPublic: boolean         // Public sharing flag
  
  // Search/indexing
  tags?: string[]           // Searchable tags
  description?: string      // Optional description
}
```

#### **`users/` Collection** (User Profiles)
```typescript
interface UserProfileDoc {
  // Document ID: Firebase Auth UID
  userId: string
  
  // Profile data
  email: string
  displayName: string
  photoURL?: string
  
  // Preferences
  defaultBpm: number
  defaultVideoConfig: VideoConfigData
  
  // Usage tracking
  kompositionCount: number
  totalStorageUsed: number  // In bytes
  lastActive: Timestamp
  
  // Firebase metadata
  createdAt: Timestamp
  updatedAt: Timestamp
}
```

#### **`sources/` Collection** (Media Files)
```typescript
interface SourceDoc {
  // Document ID: auto-generated
  id: string
  
  // Ownership
  userId: string            // Owner's Firebase Auth UID
  
  // File metadata
  url: string              // Firebase Storage URL or external URL
  filename: string         // Original filename
  checksum: string         // File integrity check
  format: string           // "mp4", "mp3", "wav", etc.
  extensionType: string    // "video", "audio", "image"
  mediaType: string        // MIME type
  
  // Media properties
  width?: number           // Video/image width
  height?: number          // Video/image height
  duration?: number        // Media duration in milliseconds
  fileSize: number         // File size in bytes
  
  // Processing
  startingOffset?: number  // Default starting offset
  
  // Firebase metadata
  createdAt: Timestamp
  uploadedAt: Timestamp
  
  // Sharing
  isShared: boolean        // Available to other users
  sharedWith?: string[]    // Specific user IDs
}
```

### **Nested Data Types**

#### **SegmentData**
```typescript
interface SegmentData {
  id: string
  sourceId: string         // Reference to sources collection
  start: number           // Start time in milliseconds
  duration: number        // Duration in milliseconds
  end: number            // End time (start + duration)
  
  // Effects and transformations
  effects?: EffectData[]
  volume?: number
  speed?: number
}
```

#### **SourceData**
```typescript
interface SourceData {
  id: string
  url: string
  startingOffset?: number
  checksum: string
  format: string
  extensionType: string
  mediaType: string
  width?: number
  height?: number
}
```

#### **VideoConfigData**
```typescript
interface VideoConfigData {
  width: number
  height: number
  framerate: number
  extensionType: string    // Output format
}
```

#### **BeatPatternData**
```typescript
interface BeatPatternData {
  fromBeat: number
  toBeat: number
  masterBPM: number
}
```

## 🔒 **Firebase Security Rules**

### **Firestore Rules**
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Kompositions - user-scoped access
    match /kompositions/{kompositionId} {
      allow read, write, delete: if request.auth != null 
        && request.auth.uid == resource.data.userId;
      
      // Allow read for public kompositions
      allow read: if resource.data.isPublic == true;
      
      // Allow read for shared kompositions
      allow read: if request.auth != null 
        && request.auth.uid in resource.data.sharedWith;
    }
    
    // User profiles - self-access only
    match /users/{userId} {
      allow read, write: if request.auth != null 
        && request.auth.uid == userId;
    }
    
    // Sources - owner and shared access
    match /sources/{sourceId} {
      allow read, write, delete: if request.auth != null 
        && request.auth.uid == resource.data.userId;
      
      // Allow read for shared sources
      allow read: if request.auth != null 
        && (resource.data.isShared == true 
        || request.auth.uid in resource.data.sharedWith);
    }
  }
}
```

### **Firebase Storage Rules**
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    
    // User media files - private by default
    match /media/{userId}/{allPaths=**} {
      allow read, write, delete: if request.auth != null 
        && request.auth.uid == userId;
    }
    
    // Shared media files - controlled access
    match /shared/{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null 
        && request.auth.uid == resource.metadata.uploadedBy;
    }
  }
}
```

## 🔌 **ELM Ports for Firebase Integration**

### **Outgoing Ports (ELM → JavaScript)**
```elm
-- Komposition operations
port saveKomposition : Komposition -> Cmd msg
port loadKomposition : String -> Cmd msg  -- kompositionId
port deleteKomposition : String -> Cmd msg
port searchKompositions : String -> Cmd msg  -- search query

-- Source operations  
port uploadSource : SourceUploadRequest -> Cmd msg
port deleteSource : String -> Cmd msg  -- sourceId

-- User operations
port saveUserPreferences : UserPreferences -> Cmd msg
port loadUserProfile : () -> Cmd msg

-- Real-time subscriptions
port subscribeToKomposition : String -> Cmd msg  -- kompositionId
port unsubscribeFromKomposition : String -> Cmd msg
```

### **Incoming Ports (JavaScript → ELM)**
```elm
-- Komposition responses
port kompositionSaved : (KompositionSaveResult -> msg) -> Sub msg
port kompositionLoaded : (Komposition -> msg) -> Sub msg
port kompositionDeleted : (String -> msg) -> Sub msg  -- kompositionId
port kompositionsSearched : (List Komposition -> msg) -> Sub msg

-- Source responses
port sourceUploaded : (SourceUploadResult -> msg) -> Sub msg
port sourceDeleted : (String -> msg) -> Sub msg

-- User responses
port userProfileLoaded : (UserProfile -> msg) -> Sub msg
port userPreferencesSaved : (Bool -> msg) -> Sub msg

-- Real-time updates
port kompositionUpdated : (Komposition -> msg) -> Sub msg
port collaboratorJoined : (CollaboratorInfo -> msg) -> Sub msg

-- Error handling
port firebaseError : (FirebaseError -> msg) -> Sub msg
```

## ⚛️ **React Firebase Adapter Layer**

### **Firebase Service (`src/services/firebaseKompostService.ts`)**
```typescript
import { 
  collection, 
  doc, 
  addDoc, 
  updateDoc, 
  deleteDoc, 
  getDoc, 
  getDocs, 
  query, 
  where, 
  orderBy,
  onSnapshot,
  Timestamp 
} from 'firebase/firestore'
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage'
import { db, storage, auth } from '../lib/firebase/config'

export class FirebaseKompostService {
  
  // Komposition CRUD operations
  async saveKomposition(komposition: Komposition): Promise<string> {
    const userId = auth.currentUser?.uid
    if (!userId) throw new Error('User not authenticated')
    
    const kompoData = {
      ...komposition,
      userId,
      updatedAt: Timestamp.now(),
      lastModifiedBy: auth.currentUser.email
    }
    
    if (komposition.id) {
      // Update existing
      await updateDoc(doc(db, 'kompositions', komposition.id), kompoData)
      return komposition.id
    } else {
      // Create new
      const docRef = await addDoc(collection(db, 'kompositions'), {
        ...kompoData,
        createdAt: Timestamp.now(),
        createdBy: auth.currentUser.email
      })
      return docRef.id
    }
  }
  
  async loadKomposition(kompositionId: string): Promise<Komposition> {
    const docSnap = await getDoc(doc(db, 'kompositions', kompositionId))
    if (!docSnap.exists()) {
      throw new Error('Komposition not found')
    }
    return { id: docSnap.id, ...docSnap.data() } as Komposition
  }
  
  async deleteKomposition(kompositionId: string): Promise<void> {
    await deleteDoc(doc(db, 'kompositions', kompositionId))
  }
  
  async searchKompositions(searchQuery: string): Promise<Komposition[]> {
    const userId = auth.currentUser?.uid
    if (!userId) return []
    
    const q = query(
      collection(db, 'kompositions'),
      where('userId', '==', userId),
      where('name', '>=', searchQuery),
      where('name', '<=', searchQuery + '\uf8ff'),
      orderBy('updatedAt', 'desc')
    )
    
    const querySnapshot = await getDocs(q)
    return querySnapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    })) as Komposition[]
  }
  
  // Source operations
  async uploadSource(file: File): Promise<SourceUploadResult> {
    const userId = auth.currentUser?.uid
    if (!userId) throw new Error('User not authenticated')
    
    // Upload to Firebase Storage
    const storageRef = ref(storage, `media/${userId}/${file.name}`)
    const snapshot = await uploadBytes(storageRef, file)
    const downloadURL = await getDownloadURL(snapshot.ref)
    
    // Save metadata to Firestore
    const sourceData = {
      userId,
      url: downloadURL,
      filename: file.name,
      format: file.name.split('.').pop()?.toLowerCase() || '',
      mediaType: file.type,
      fileSize: file.size,
      createdAt: Timestamp.now(),
      uploadedAt: Timestamp.now(),
      isShared: false
    }
    
    const docRef = await addDoc(collection(db, 'sources'), sourceData)
    
    return {
      success: true,
      sourceId: docRef.id,
      url: downloadURL
    }
  }
  
  // Real-time subscriptions
  subscribeToKomposition(
    kompositionId: string, 
    callback: (komposition: Komposition) => void
  ): () => void {
    return onSnapshot(
      doc(db, 'kompositions', kompositionId),
      (doc) => {
        if (doc.exists()) {
          callback({ id: doc.id, ...doc.data() } as Komposition)
        }
      }
    )
  }
}
```

### **ELM Port Integration (`src/services/elmPortHandler.ts`)**
```typescript
export class ElmPortHandler {
  private firebaseService = new FirebaseKompostService()
  
  setupPorts(elmApp: any) {
    // Outgoing port handlers (ELM → Firebase)
    elmApp.ports.saveKomposition?.subscribe(async (komposition: Komposition) => {
      try {
        const kompositionId = await this.firebaseService.saveKomposition(komposition)
        elmApp.ports.kompositionSaved.send({
          success: true,
          kompositionId,
          komposition: { ...komposition, id: kompositionId }
        })
      } catch (error) {
        elmApp.ports.firebaseError.send({
          operation: 'saveKomposition',
          message: error.message
        })
      }
    })
    
    elmApp.ports.loadKomposition?.subscribe(async (kompositionId: string) => {
      try {
        const komposition = await this.firebaseService.loadKomposition(kompositionId)
        elmApp.ports.kompositionLoaded.send(komposition)
      } catch (error) {
        elmApp.ports.firebaseError.send({
          operation: 'loadKomposition',
          message: error.message
        })
      }
    })
    
    elmApp.ports.searchKompositions?.subscribe(async (searchQuery: string) => {
      try {
        const kompositions = await this.firebaseService.searchKompositions(searchQuery)
        elmApp.ports.kompositionsSearched.send(kompositions)
      } catch (error) {
        elmApp.ports.firebaseError.send({
          operation: 'searchKompositions',
          message: error.message
        })
      }
    })
    
    elmApp.ports.uploadSource?.subscribe(async (uploadRequest: SourceUploadRequest) => {
      try {
        const result = await this.firebaseService.uploadSource(uploadRequest.file)
        elmApp.ports.sourceUploaded.send(result)
      } catch (error) {
        elmApp.ports.firebaseError.send({
          operation: 'uploadSource',
          message: error.message
        })
      }
    })
  }
}
```

## 🔍 **Search and Indexing Strategy**

### **Firestore Composite Indexes**
```javascript
// Required composite indexes for efficient queries
[
  {
    collection: "kompositions",
    fields: [
      { field: "userId", mode: "ASCENDING" },
      { field: "updatedAt", mode: "DESCENDING" }
    ]
  },
  {
    collection: "kompositions", 
    fields: [
      { field: "userId", mode: "ASCENDING" },
      { field: "name", mode: "ASCENDING" }
    ]
  },
  {
    collection: "kompositions",
    fields: [
      { field: "isPublic", mode: "ASCENDING" },
      { field: "updatedAt", mode: "DESCENDING" }
    ]
  }
]
```

### **Advanced Search Implementation**
```typescript
class KompositionSearchService {
  
  // Full-text search using tags
  async searchByTags(tags: string[]): Promise<Komposition[]> {
    const q = query(
      collection(db, 'kompositions'),
      where('tags', 'array-contains-any', tags),
      orderBy('updatedAt', 'desc')
    )
    
    const snapshot = await getDocs(q)
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }))
  }
  
  // BPM range search
  async searchByBPMRange(minBpm: number, maxBpm: number): Promise<Komposition[]> {
    const q = query(
      collection(db, 'kompositions'),
      where('bpm', '>=', minBpm),
      where('bpm', '<=', maxBpm),
      orderBy('bpm', 'asc')
    )
    
    const snapshot = await getDocs(q)
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }))
  }
  
  // Recent kompositions
  async getRecentKompositions(limit: number = 10): Promise<Komposition[]> {
    const userId = auth.currentUser?.uid
    if (!userId) return []
    
    const q = query(
      collection(db, 'kompositions'),
      where('userId', '==', userId),
      orderBy('updatedAt', 'desc'),
      limit(limit)
    )
    
    const snapshot = await getDocs(q)
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }))
  }
}
```

## 🔄 **Real-time Collaboration Features**

### **Operational Transform for Concurrent Editing**
```typescript
interface KompositionOperation {
  type: 'addSegment' | 'removeSegment' | 'updateSegment' | 'updateBPM' | 'updateName'
  timestamp: number
  userId: string
  data: any
}

class CollaborationManager {
  private operations: KompositionOperation[] = []
  
  applyOperation(operation: KompositionOperation, komposition: Komposition): Komposition {
    switch (operation.type) {
      case 'addSegment':
        return {
          ...komposition,
          segments: [...komposition.segments, operation.data]
        }
        
      case 'updateBPM':
        return {
          ...komposition,
          bpm: operation.data.bpm
        }
        
      // ... other operations
    }
  }
}
```

---

## 🎯 **Implementation Priority**

### **Phase 1: Core CRUD Operations** ⭐ **HIGH PRIORITY**
1. Firestore schema setup
2. Basic save/load/delete operations
3. User authentication integration
4. Security rules implementation

### **Phase 2: Advanced Features** ⭐ **MEDIUM PRIORITY**
1. Search functionality
2. File upload integration
3. User preferences
4. Backup/export features

### **Phase 3: Collaboration** ⭐ **LOW PRIORITY**
1. Real-time synchronization
2. Sharing mechanisms
3. Operational transforms
4. Conflict resolution

This design provides a solid foundation for Firebase integration while maintaining ELM's functional programming principles and ensuring data security and scalability.