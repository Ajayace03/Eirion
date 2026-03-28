import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing.tsx";
import Wizard from "./pages/Wizard.tsx";
import Dashboard from "./pages/Dashboard.tsx";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-blue-gray-50 flex flex-col font-sans text-blue-gray-900">
        <header className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-blue-gray-100">
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
            <div className="text-xl font-bold tracking-tight text-blue-gray-900 flex items-center gap-2">
              <span className="w-8 h-8 rounded-full bg-blue-gray-900 flex items-center justify-center text-white text-sm">
                E
              </span>
              EIRION
            </div>
          </div>
        </header>

        <main className="flex-1 pt-16">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/onboarding" element={<Wizard />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
