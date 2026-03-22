# ELM Integration Knowledge & Reference

## Overview
This document captures the knowledge and experience gained from integrating ELM (specifically KompostEdit) with a Next.js Firebase application.

## Architecture Pattern: Next.js + ELM Hybrid

### Successful Integration Pattern
```typescript
// Page-specific ELM loading (not global)
const [elmScriptLoaded, setElmScriptLoaded] = useState(false);

// Dynamic script loading in useEffect
useEffect(() => {
  const script = document.createElement('script');
  script.src = '/elm/kompost.js';
  script.onload = () => {
    // Set up global config after script loads
    (window as any).KOMPOST_CONFIG = {
      elm: {
        available: typeof (window as any).Elm !== 'undefined' && (window as any).Elm.Main,
        version: '1.0.0'
      },
      integration: {
        type: 'nextjs-elm-hybrid',
        firebase: true,
        couchdb_compatible: true
      }
    };
    setElmScriptLoaded(true);
  };
  document.head.appendChild(script);
}, []);

// ELM app initialization (wait for script + auth)
useEffect(() => {
  if ((firebaseToken || !user) && elmScriptLoaded) {
    const app = (window as any).Elm.Main.init({
      node: elmRef.current,
      flags: {
        apiToken: firebaseToken || 'anonymous',
        userProfile: user ? {...} : null,
        authMode: 'firebase_shell',
        skipAuth: true
      }
    });
  }
}, [user, firebaseToken, elmScriptLoaded]);
```

## Key Learnings

### ❌ What Doesn't Work

1. **Next.js Script Component Issues**
   ```tsx
   // This approach had timing issues
   <Script src="/elm/kompost.js" strategy="beforeInteractive" />
   ```
   - `beforeInteractive` strategy didn't work reliably
   - Script loading timing conflicts with React component lifecycle

2. **Global ELM Loading**
   ```tsx
   // Loading ELM in layout.tsx caused conflicts
   <script src="/elm/kompost.js"></script> // In layout
   ```
   - Loaded ELM on every page unnecessarily
   - Performance impact
   - Potential module conflicts

3. **Multiple ELM Scripts**
   ```
   Error: "Your page is loading multiple Elm scripts with a module named Elm.Main"
   ```
   - Having both `kompost.js` and `kompost-demo.js`
   - Multiple `_Platform_export` calls in concatenated files
   - Conflicting `interop.js`, `fileupload.js`, `userprofile.js`

### ✅ What Works

1. **Page-Specific Dynamic Loading**
   - Load ELM script only on pages that need it
   - Use `document.createElement('script')` with proper callbacks
   - Track loading state with React state

2. **Proper Script Sequencing**
   ```typescript
   // Wait for both conditions
   if ((firebaseToken || !user) && elmScriptLoaded) {
     // Initialize ELM
   }
   ```

3. **Clean ELM File Structure**
   ```
   public/elm/
   ├── kompost.js                    ✅ Main ELM app
   ├── elm-status.json              ✅ Metadata
   ├── jsrsasign-latest-all-min.js  ✅ Crypto library
   ├── verifier.js                  ✅ Utils
   ├── interop.js.disabled          ❌ Disabled to prevent conflicts
   ├── fileupload.js.disabled       ❌ Disabled to prevent conflicts
   └── userprofile.js.disabled      ❌ Disabled to prevent conflicts
   ```

## Firebase Integration Specifics

### Authentication Token Passing
```typescript
// Pass Firebase ID token to ELM
const token = await user.getIdToken();

// In ELM flags
flags: {
  apiToken: firebaseToken || 'anonymous',
  userProfile: user ? {
    id: user.uid,
    email: user.email,
    displayName: user.displayName || user.email,
    photoURL: user.photoURL || ''
  } : null,
  authMode: 'firebase_shell',
  skipAuth: true
}
```

### Port Communication Pattern
```typescript
// Listen for ELM updates
if (app.ports?.kompositionUpdated) {
  app.ports.kompositionUpdated.subscribe((data: any) => {
    console.log('Received from ELM:', data);
    // Save to Firebase/Firestore
  });
}

// Send updates to ELM
if (app.ports?.loadKomposition) {
  app.ports.loadKomposition.send(kompositionData);
}
```

## Common Issues & Solutions

### Issue: "Elm application not found"
**Cause**: Script not loaded or timing issue
**Solution**: Dynamic script loading with state tracking

### Issue: Multiple ELM modules conflict
**Cause**: Multiple scripts exporting `Elm.Main`
**Solution**: Keep only one `kompost.js`, disable conflicting files

### Issue: Firebase permission errors
**Cause**: Missing or incorrect Firestore security rules
**Solution**: 
```javascript
// firestore.rules
allow read, write, delete: if request.auth != null && request.auth.uid == resource.data.userId;
```

### Issue: ELM not initializing with Firebase auth
**Cause**: Token not available when ELM loads
**Solution**: Wait for both `elmScriptLoaded` AND `firebaseToken`

## File Structure for ELM Integration

```
src/app/kompostedit/
└── page.tsx                 # ELM integration page

public/elm/
├── kompost.js              # Main ELM application
└── *.js.disabled           # Disabled conflicting scripts

firebase.json               # Firebase config (rules only)
firestore.rules            # Security rules
storage.rules              # File access rules
```

## Performance Considerations

1. **Lazy Loading**: ELM loads only when `/kompostedit` is visited
2. **Script Size**: `kompost.js` is ~371KB - significant load
3. **Caching**: Firebase CDN caches static assets
4. **Error Boundaries**: Proper error handling for script failures

## Security Considerations

1. **Firebase Rules**: User-scoped data access only
2. **Token Passing**: ID tokens for authentication
3. **CORS**: ELM communicates through ports, not direct API calls
4. **XSS Prevention**: No `dangerouslySetInnerHTML` for dynamic content

## Future Improvements

1. **ELM Code Splitting**: Split large ELM app into smaller modules
2. **Service Worker**: Cache ELM script for offline use
3. **Error Recovery**: Better fallback when ELM fails to load
4. **Progress Indicators**: Show loading state during script download
5. **Hot Reloading**: Development-time ELM integration

## Debugging Tips

1. **Console Logs**: Check for `ELM script loaded, Elm available: true`
2. **Network Tab**: Verify `/elm/kompost.js` loads successfully
3. **Window Inspection**: Check `window.Elm.Main` availability
4. **Firebase Auth**: Verify user token in browser DevTools
5. **Port Communication**: Log all port message exchanges

## Conclusion

ELM integration with Next.js requires careful attention to:
- **Script loading timing**
- **State management** between React and ELM
- **Firebase authentication flow**
- **Avoiding module conflicts**

The dynamic script loading approach with proper state tracking provides the most reliable integration pattern for production use.