import React, { useEffect, useRef, useState } from 'react';
import { Komposition, ElmApp } from '../types';
import { useStore } from '../hooks/useStore';
import { getAuth } from 'firebase/auth';

interface ElmEditorProps {
  komposition: Komposition | null;
  onKompositionUpdate: (komposition: Komposition) => void;
}

const ElmEditor: React.FC<ElmEditorProps> = ({ komposition, onKompositionUpdate }) => {
  const elmRef = useRef<HTMLDivElement>(null);
  const elmAppRef = useRef<ElmApp | null>(null);
  const [isElmLoaded, setIsElmLoaded] = useState(false);
  const [elmError, setElmError] = useState<string | null>(null);
  const [firebaseToken, setFirebaseToken] = useState<string | null>(null);
  const { user } = useStore();

  // Get Firebase ID token when user changes
  useEffect(() => {
    const fetchToken = async () => {
      if (user) {
        try {
          const auth = getAuth();
          const currentUser = auth.currentUser;
          if (currentUser) {
            const token = await currentUser.getIdToken();
            setFirebaseToken(token);
          }
        } catch (error) {
          console.error('Error getting Firebase ID token:', error);
          setFirebaseToken(null);
        }
      } else {
        setFirebaseToken(null);
      }
    };

    fetchToken();
  }, [user]);

  useEffect(() => {
    // Load Elm application
    const loadElmApp = async () => {
      try {
        // Check if Elm is available globally (loaded from CDN or static files)
        if (!(window as any).Elm?.Main?.init) {
          throw new Error('Elm application not found. Please ensure kompost.js is loaded.');
        }

        if (elmRef.current && !elmAppRef.current) {
          // Initialize Elm app with Firebase auth context and CouchDB-compatible REST API
          const app = (window as any).Elm.Main.init({
            node: elmRef.current,
            flags: {
              // Pass Firebase ID token for authentication
              apiToken: firebaseToken || 'anonymous',
              // Pass user info to Elm
              userProfile: user ? {
                id: user.id,
                email: user.email,
                displayName: user.displayName || user.email,
                photoURL: user.photoURL || ''
              } : null,
              // Firebase Functions REST API endpoints (CouchDB-compatible)
              kompoUrl: process.env.REACT_APP_FIREBASE_FUNCTIONS_URL ? 
                `${process.env.REACT_APP_FIREBASE_FUNCTIONS_URL}/api/kompositions` : 
                'http://localhost:5001/kompost-web-ui/us-central1/api/api/kompositions',
              metaUrl: process.env.REACT_APP_FIREBASE_FUNCTIONS_URL ? 
                `${process.env.REACT_APP_FIREBASE_FUNCTIONS_URL}/api/meta` : 
                'http://localhost:5001/kompost-web-ui/us-central1/api/api/meta',
              cacheUrl: process.env.REACT_APP_FIREBASE_FUNCTIONS_URL ? 
                `${process.env.REACT_APP_FIREBASE_FUNCTIONS_URL}/api/cache` : 
                'http://localhost:5001/kompost-web-ui/us-central1/api/api/cache',
              integrationDestination: process.env.REACT_APP_FIREBASE_FUNCTIONS_URL ? 
                `${process.env.REACT_APP_FIREBASE_FUNCTIONS_URL}/api/process` : 
                'http://localhost:5001/kompost-web-ui/us-central1/api/api/process',
              integrationFormat: 'json',
              // Authentication mode - tell Elm it's running in an authenticated shell
              authMode: 'firebase_shell',
              // Skip Elm's own auth flow
              skipAuth: true
            }
          });

          elmAppRef.current = app;

          // Set up Elm ports for communication
          if (app.ports) {
            // Listen for komposition updates from Elm
            if (app.ports.kompositionUpdated) {
              app.ports.kompositionUpdated.subscribe((updatedKomposition: Komposition) => {
                console.log('Received komposition update from Elm:', updatedKomposition);
                onKompositionUpdate(updatedKomposition);
              });
            }

            // Listen for save requests from Elm
            if (app.ports.saveKomposition) {
              app.ports.saveKomposition.subscribe((kompositionData: any) => {
                console.log('Elm requested save:', kompositionData);
                // Convert Elm format to our TypeScript format if needed
                const convertedKomposition: Komposition = {
                  id: kompositionData.id || '',
                  name: kompositionData.name || 'Untitled',
                  revision: kompositionData.revision || '1.0',
                  dvlType: kompositionData.dvlType || 'music_video',
                  bpm: kompositionData.bpm || 120,
                  segments: kompositionData.segments || [],
                  sources: kompositionData.sources || [],
                  config: kompositionData.config || {
                    width: 1920,
                    height: 1080,
                    fps: 25,
                    format: 'mp4'
                  },
                  status: 'draft',
                  userId: user?.id || '',
                  createdAt: new Date(),
                  updatedAt: new Date(),
                  beatpattern: kompositionData.beatpattern
                };
                onKompositionUpdate(convertedKomposition);
              });
            }

            // Send Firebase auth token updates to Elm
            if (app.ports.firebaseTokenUpdated && firebaseToken) {
              app.ports.firebaseTokenUpdated.send(firebaseToken);
            }
          }

          setIsElmLoaded(true);
          setElmError(null);
        }
      } catch (error) {
        console.error('Failed to load Elm application:', error);
        setElmError(error instanceof Error ? error.message : 'Unknown error loading Elm app');
        setIsElmLoaded(false);
      }
    };

    // Only load Elm when we have a Firebase token (or no user)
    if (firebaseToken || !user) {
      loadElmApp();
    }

    // Cleanup on unmount
    return () => {
      if (elmAppRef.current && elmRef.current) {
        elmRef.current.innerHTML = '';
        elmAppRef.current = null;
        setIsElmLoaded(false);
      }
    };
  }, [user, firebaseToken, onKompositionUpdate]);

  // Send komposition updates to Elm when they change
  useEffect(() => {
    if (isElmLoaded && elmAppRef.current?.ports?.loadKomposition && komposition) {
      console.log('Sending komposition to Elm:', komposition);
      elmAppRef.current.ports.loadKomposition.send(komposition);
    }
  }, [komposition, isElmLoaded]);

  if (elmError) {
    return (
      <div className="elm-editor-error">
        <h3>Elm Editor Error</h3>
        <p>{elmError}</p>
        <details>
          <summary>Integration Instructions</summary>
          <p>To enable the Elm editor, you need to:</p>
          <ol>
            <li>Build the Elm application: <code>elm make src/Main.elm --output=public/elm/kompost.js</code></li>
            <li>Include it in your HTML: <code>&lt;script src="/elm/kompost.js"&gt;&lt;/script&gt;</code></li>
            <li>Ensure the Elm app exposes the required ports for React communication</li>
          </ol>
          <p>The symlink to the Elm project is: <code>elm-kompostedit -&gt; /Users/stiglau/utvikling/privat/ElmMoro/kompostedit</code></p>
        </details>
      </div>
    );
  }

  if (!isElmLoaded) {
    return (
      <div className="elm-editor-loading">
        <p>Loading Elm Editor...</p>
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="elm-editor-container">
      <div 
        ref={elmRef} 
        className="elm-editor"
        style={{ 
          width: '100%', 
          minHeight: '600px',
          border: '1px solid #ddd',
          borderRadius: '4px'
        }}
      />
    </div>
  );
};

export default ElmEditor;