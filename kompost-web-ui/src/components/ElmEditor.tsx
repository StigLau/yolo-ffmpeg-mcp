import React, { useEffect, useRef, useState } from 'react';
import { Komposition, ElmApp } from '../types';
import { useStore } from '../hooks/useStore';

interface ElmEditorProps {
  komposition: Komposition | null;
  onKompositionUpdate: (komposition: Komposition) => void;
}

const ElmEditor: React.FC<ElmEditorProps> = ({ komposition, onKompositionUpdate }) => {
  const elmRef = useRef<HTMLDivElement>(null);
  const elmAppRef = useRef<ElmApp | null>(null);
  const [isElmLoaded, setIsElmLoaded] = useState(false);
  const [elmError, setElmError] = useState<string | null>(null);
  const { user } = useStore();

  useEffect(() => {
    // Load Elm application
    const loadElmApp = async () => {
      try {
        // Check if Elm is available globally (loaded from CDN or static files)
        if (!(window as any).Elm?.Main?.init) {
          throw new Error('Elm application not found. Please ensure kompost.js is loaded.');
        }

        if (elmRef.current && !elmAppRef.current) {
          // Initialize Elm app with CouchDB-compatible REST API configuration
          const app = (window as any).Elm.Main.init({
            node: elmRef.current,
            flags: {
              apiToken: user?.id || '',
              kompoUrl: process.env.REACT_APP_KOMPO_API_URL || 'https://api.kompo.st',
              metaUrl: process.env.REACT_APP_META_URL || 'https://meta.kompo.st', 
              cacheUrl: process.env.REACT_APP_CACHE_URL || 'https://cache.kompo.st',
              integrationDestination: process.env.REACT_APP_KOMPOSTEUR_URL || 'https://komposteur.kompo.st',
              integrationFormat: 'json'
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
            if (app.ports.firebaseTokenUpdated && user) {
              app.ports.firebaseTokenUpdated.send(user.id);
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

    loadElmApp();

    // Cleanup on unmount
    return () => {
      if (elmAppRef.current && elmRef.current) {
        elmRef.current.innerHTML = '';
        elmAppRef.current = null;
        setIsElmLoaded(false);
      }
    };
  }, [user, onKompositionUpdate]);

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