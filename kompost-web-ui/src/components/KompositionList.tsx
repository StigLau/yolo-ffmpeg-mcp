import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useStore } from '../hooks/useStore';
import { Komposition } from '../types';

const KompositionList: React.FC = () => {
  const navigate = useNavigate();
  const { 
    user, 
    kompositions, 
    isLoading, 
    error, 
    signIn, 
    signOut, 
    loadKompositions,
    deleteKomposition,
    createKomposition 
  } = useStore();

  useEffect(() => {
    if (user) {
      loadKompositions();
    }
  }, [user, loadKompositions]);

  const handleCreateNew = async () => {
    try {
      await createKomposition(`Music Video ${new Date().toLocaleDateString()}`);
      // The store will be updated, and we can navigate to the new composition
      navigate('/edit/new');
    } catch (error) {
      console.error('Failed to create komposition:', error);
    }
  };

  const handleDelete = async (komposition: Komposition) => {
    const confirmed = window.confirm(`Are you sure you want to delete "${komposition.name}"?`);
    if (confirmed) {
      try {
        await deleteKomposition(komposition.id);
      } catch (error) {
        console.error('Failed to delete komposition:', error);
      }
    }
  };

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">kompo.st</h1>
            <p className="text-gray-600 mb-6">
              Video Composition Platform with Elm Editor Integration
            </p>
            <button
              onClick={signIn}
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
            >
              {isLoading ? 'Signing in...' : 'Sign in with Google'}
            </button>
            {error && (
              <p className="mt-4 text-red-600 text-sm">{error}</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">kompo.st</h1>
              <span className="ml-3 text-sm text-gray-500">Video Composition Platform</span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {user.photoURL && (
                  <img 
                    src={user.photoURL} 
                    alt={user.displayName || user.email}
                    className="w-8 h-8 rounded-full"
                  />
                )}
                <span className="text-sm text-gray-700">
                  {user.displayName || user.email}
                </span>
              </div>
              <button
                onClick={signOut}
                className="text-gray-500 hover:text-gray-700 text-sm"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Your Kompositions</h2>
            <p className="text-gray-600">Create and edit video compositions with the Elm editor</p>
          </div>
          <div className="flex space-x-3">
            <Link
              to="/ai-generate"
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              🤖 AI Generator
            </Link>
            <Link
              to="/process"
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              🎬 Video Processing
            </Link>
            <button
              onClick={handleCreateNew}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors"
            >
              New Komposition
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="spinner-border" role="status">
                <span className="sr-only">Loading...</span>
              </div>
              <p className="mt-2 text-gray-600">Loading kompositions...</p>
            </div>
          </div>
        ) : kompositions.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2C7 1.44772 7.44772 1 8 1H16C16.5523 1 17 1.44772 17 2V4H20C20.5523 4 21 4.44772 21 5S20.5523 6 20 6H19V20C19 21.1046 18.1046 22 17 22H7C5.89543 22 5 21.1046 5 20V6H4C3.44772 6 3 5.55228 3 5S3.44772 4 4 4H7ZM9 8V18H11V8H9ZM13 8V18H15V8H13Z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No kompositions yet</h3>
            <p className="text-gray-600 mb-4">Get started by creating your first video composition</p>
            <button
              onClick={handleCreateNew}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors"
            >
              Create Your First Komposition
            </button>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {kompositions.map((komposition) => (
              <div key={komposition.id} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {komposition.name}
                      </h3>
                      <p className="text-sm text-gray-500">
                        BPM: {komposition.bpm} • {komposition.segments.length} segments
                      </p>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(komposition.status)}`}>
                      {komposition.status}
                    </span>
                  </div>
                  
                  <div className="text-sm text-gray-600 mb-4">
                    <p>Updated: {formatDate(komposition.updatedAt)}</p>
                    <p>Format: {komposition.config.width}x{komposition.config.height}</p>
                  </div>

                  <div className="flex space-x-2">
                    <Link
                      to={`/edit/${komposition.id}`}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 px-3 rounded text-center transition-colors"
                    >
                      Edit in Elm
                    </Link>
                    <button
                      onClick={() => handleDelete(komposition)}
                      className="bg-red-100 hover:bg-red-200 text-red-700 text-sm font-medium py-2 px-3 rounded transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <span className="font-semibold">kompo.st</span> - React + Elm hybrid video editor
            </div>
            <div>
              Powered by Firebase & MCP FFMPEG integration
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default KompositionList;