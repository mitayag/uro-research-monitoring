import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppShell from "./components/layout/AppShell";
import Dashboard from "./pages/Dashboard";
import Research from "./pages/Research";
import ResearchDetail from "./pages/ResearchDetail";
import Login from "./pages/Login";

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="research" element={<Research />} />
            <Route path="research/:id" element={<ResearchDetail />} />
            <Route path="submissions" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Submissions</h1><p className="text-gray-500 mt-2">Coming in Phase 2</p></div>} />
            <Route path="researchers" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Researchers</h1><p className="text-gray-500 mt-2">Coming in Phase 3</p></div>} />
            <Route path="evaluators" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Evaluators</h1><p className="text-gray-500 mt-2">Coming in Phase 10</p></div>} />
            <Route path="irb" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">IRB</h1><p className="text-gray-500 mt-2">Coming in Phase 12</p></div>} />
            <Route path="turnitin" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Turnitin</h1><p className="text-gray-500 mt-2">Coming in Phase 9</p></div>} />
            <Route path="monitoring" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Monitoring</h1><p className="text-gray-500 mt-2">Coming in Phase 12</p></div>} />
            <Route path="reports" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Reports</h1><p className="text-gray-500 mt-2">Coming in Phase 16</p></div>} />
            <Route path="resources" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Resources</h1><p className="text-gray-500 mt-2">Coming later</p></div>} />
            <Route path="settings" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Settings</h1><p className="text-gray-500 mt-2">Coming in Phase 3</p></div>} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
