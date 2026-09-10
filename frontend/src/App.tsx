import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import RoleGuard from "./components/RoleGuard";
import AppShell from "./components/layout/AppShell";
import Dashboard from "./pages/Dashboard";
import Research from "./pages/Research";
import ResearchDetail from "./pages/ResearchDetail";
import NewSubmission from "./pages/NewSubmission";
import Login from "./pages/Login";
import DeanEndorsements from "./pages/DeanEndorsements";
import DeanEndorsementReview from "./pages/DeanEndorsementReview";
import DeanResearch from "./pages/DeanResearch";
import DeanResearchDetail from "./pages/DeanResearchDetail";
import DeanResearchers from "./pages/DeanResearchers";
import DeanMonitoring from "./pages/DeanMonitoring";
import DeanCompleted from "./pages/DeanCompleted";
import DeanReports from "./pages/DeanReports";
import DeanAcademicStaff from "./pages/DeanAcademicStaff";
import AdminSchools from "./pages/AdminSchools";
import DeanDepartments from "./pages/DeanDepartments";

const DEAN_ROLES = ["DEAN", "ADMIN"];
const ADMIN_ROLES = ["ADMIN", "URO_DIRECTOR", "URO_STAFF", "DEAN"];

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
            <Route path="research/new" element={<NewSubmission />} />
            <Route path="research/:id" element={<ResearchDetail />} />
            <Route path="submissions" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Submissions</h1><p className="text-gray-500 mt-2">Coming in Phase 2</p></div>} />
            <Route path="researchers" element={
              <RoleGuard allowedRoles={ADMIN_ROLES}>
                <div className="p-6"><h1 className="font-heading text-2xl font-bold">Researchers</h1><p className="text-gray-500 mt-2">Coming in Phase 3</p></div>
              </RoleGuard>
            } />
            <Route path="evaluators" element={
              <RoleGuard allowedRoles={ADMIN_ROLES}>
                <div className="p-6"><h1 className="font-heading text-2xl font-bold">Evaluators</h1><p className="text-gray-500 mt-2">Coming in Phase 10</p></div>
              </RoleGuard>
            } />
            <Route path="irb" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">IRB</h1><p className="text-gray-500 mt-2">Coming in Phase 12</p></div>} />
            <Route path="turnitin" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Turnitin</h1><p className="text-gray-500 mt-2">Coming in Phase 9</p></div>} />
            <Route path="monitoring" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Monitoring</h1><p className="text-gray-500 mt-2">Coming in Phase 12</p></div>} />
            <Route path="reports" element={
              <RoleGuard allowedRoles={ADMIN_ROLES}>
                <div className="p-6"><h1 className="font-heading text-2xl font-bold">Reports</h1><p className="text-gray-500 mt-2">Coming in Phase 16</p></div>
              </RoleGuard>
            } />
            <Route path="resources" element={<div className="p-6"><h1 className="font-heading text-2xl font-bold">Resources</h1><p className="text-gray-500 mt-2">Coming later</p></div>} />
            <Route path="settings" element={
              <RoleGuard allowedRoles={ADMIN_ROLES}>
                <div className="p-6"><h1 className="font-heading text-2xl font-bold">Settings</h1><p className="text-gray-500 mt-2">Coming in Phase 3</p></div>
              </RoleGuard>
            } />

            {/* Admin Organization Routes */}
            <Route path="admin/schools" element={
              <RoleGuard allowedRoles={ADMIN_ROLES}>
                <AdminSchools />
              </RoleGuard>
            } />

            {/* Dean Module Routes */}
            <Route path="dean/endorsements" element={
              <RoleGuard allowedRoles={DEAN_ROLES}>
                <DeanEndorsements />
              </RoleGuard>
            } />
            <Route path="dean/endorsements/:id" element={
              <RoleGuard allowedRoles={DEAN_ROLES}>
                <DeanEndorsementReview />
              </RoleGuard>
            } />
            <Route path="dean/research" element={
              <RoleGuard allowedRoles={DEAN_ROLES}>
                <DeanResearch />
              </RoleGuard>
            } />
            <Route path="dean/research/:id" element={
              <RoleGuard allowedRoles={DEAN_ROLES}>
                <DeanResearchDetail />
              </RoleGuard>
            } />
            <Route path="dean/researchers" element={
              <RoleGuard allowedRoles={DEAN_ROLES}>
                <DeanResearchers />
              </RoleGuard>
            } />
            <Route path="dean/staff" element={
              <RoleGuard allowedRoles={DEAN_ROLES}>
                <DeanAcademicStaff />
              </RoleGuard>
            } />
            <Route path="dean/departments" element={
              <RoleGuard allowedRoles={DEAN_ROLES}>
                <DeanDepartments />
              </RoleGuard>
            } />
            <Route path="dean/monitoring" element={
              <RoleGuard allowedRoles={DEAN_ROLES}>
                <DeanMonitoring />
              </RoleGuard>
            } />
            <Route path="dean/completed" element={
              <RoleGuard allowedRoles={DEAN_ROLES}>
                <DeanCompleted />
              </RoleGuard>
            } />
            <Route path="dean/reports" element={
              <RoleGuard allowedRoles={DEAN_ROLES}>
                <DeanReports />
              </RoleGuard>
            } />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
