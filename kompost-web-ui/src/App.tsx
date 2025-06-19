import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useAuthStateListener } from './hooks/useStore';
import { KompositionList, ElmEditorPage, LoginPage } from './components';
import VideoProcessor from './components/VideoProcessor';
import AIKompositionGenerator from './components/AIKompositionGenerator';

function App() {
  // Initialize auth state listener
  useAuthStateListener();

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<KompositionList />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/edit/:id" element={<ElmEditorPage />} />
          <Route path="/edit/new" element={<ElmEditorPage />} />
          <Route path="/process" element={<VideoProcessor />} />
          <Route path="/ai-generate" element={<AIKompositionGenerator />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;