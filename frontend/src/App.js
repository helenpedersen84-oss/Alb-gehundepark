import React from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import BookingStatus from './pages/BookingStatus';
import Admin from './pages/Admin';
import { Toaster } from './components/ui/toaster';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <div className="App">
      <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/booking/status" element={<BookingStatus />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
          <Toaster />
        </BrowserRouter>
      </ErrorBoundary>
    </div>
  );
}

export default App;
