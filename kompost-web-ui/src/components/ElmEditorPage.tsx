import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ElmEditor from './ElmEditor';
import { useStore } from '../hooks/useStore';
import { Komposition } from '../types';

const ElmEditorPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { 
    currentKomposition, 
    loadKomposition, 
    saveKomposition, 
    createKomposition,
    isLoading, 
    error,
    user
  } = useStore();
  
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }

    if (id && id !== 'new') {
      // Load existing komposition
      loadKomposition(id);
    } else if (id === 'new') {
      // Create new komposition
      const newName = `Music Video ${new Date().toLocaleDateString()}`;
      createKomposition(newName);
    }
  }, [id, user, loadKomposition, createKomposition, navigate]);

  const handleKompositionUpdate = async (updatedKomposition: Komposition) => {
    try {
      await saveKomposition(updatedKomposition);
      setHasUnsavedChanges(false);
      
      // If this was a new komposition, update the URL to use the new ID
      if (id === 'new' && updatedKomposition.id) {
        navigate(`/edit/${updatedKomposition.id}`, { replace: true });
      }
    } catch (error) {
      console.error('Failed to save komposition:', error);
      setHasUnsavedChanges(true);
    }
  };

  const handleBackToList = () => {
    if (hasUnsavedChanges) {
      const shouldLeave = window.confirm('You have unsaved changes. Are you sure you want to leave?');
      if (!shouldLeave) return;
    }
    navigate('/');
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-4">Authentication Required</h2>
          <p className="text-gray-600 mb-4">Please sign in to access the Elm komposition editor.</p>
          <button 
            onClick={() => navigate('/')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
          >
            Go to Sign In
          </button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="spinner-border" role="status">
            <span className="sr-only">Loading...</span>
          </div>
          <p className="mt-2">Loading komposition...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <h3 className="font-bold">Error Loading Komposition</h3>
          <p>{error}</p>
          <button 
            onClick={handleBackToList}
            className="mt-2 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
          >
            Back to List
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="elm-editor-page">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button 
                onClick={handleBackToList}
                className="text-gray-600 hover:text-gray-800 transition-colors"
              >
                ← Back to Kompositions
              </button>
              <h1 className="text-xl font-semibold">
                {currentKomposition?.name || 'New Komposition'}
              </h1>
              {hasUnsavedChanges && (
                <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">
                  Unsaved changes
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              {currentKomposition && (
                <>
                  <span>BPM: {currentKomposition.bpm}</span>
                  <span>•</span>
                  <span>{currentKomposition.segments.length} segments</span>
                  <span>•</span>
                  <span>{currentKomposition.sources.length} sources</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Elm Editor */}
      <main className="container mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow-sm border">
          <ElmEditor 
            komposition={currentKomposition}
            onKompositionUpdate={handleKompositionUpdate}
          />
        </div>
      </main>

      {/* Footer with integration info */}
      <footer className="bg-gray-50 border-t">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <span className="font-semibold">Elm Editor Integration:</span>
              {currentKomposition ? (
                <span className="ml-2 text-green-600">✓ Active</span>
              ) : (
                <span className="ml-2 text-yellow-600">⚡ Loading</span>
              )}
            </div>
            <div>
              Data sync with Firebase Firestore
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ElmEditorPage;