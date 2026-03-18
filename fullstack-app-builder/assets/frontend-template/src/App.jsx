import React from 'react';
import { Routes, Route } from 'react-router-dom';
// {{COMPONENT_IMPORTS}}
// {{PAGE_IMPORTS}}

function App() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: '#F4F6F9' }}>
      {/* {{NAVBAR}} */}
      <main className="max-w-[1360px] mx-auto px-6 lg:px-8 py-6">
        <Routes>
          {/* {{ROUTES}} */}
        </Routes>
      </main>
    </div>
  );
}

export default App;
