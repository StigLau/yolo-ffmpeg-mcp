import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useAuthStateListener } from './hooks/useStore';
import KompositionList from './components/KompositionList';
import ElmEditorPage from './components/ElmEditorPage';
import LoginPage from './components/LoginPage';

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
        </Routes>
      </div>
    </Router>
  );
}

export default App;