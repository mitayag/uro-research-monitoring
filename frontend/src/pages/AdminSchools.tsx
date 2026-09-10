import { useEffect, useState, useCallback } from "react";
import {
  Plus,
  Search,
  Edit,
  UserCheck,
  X,
  CheckCircle,
  AlertTriangle,
  UserPlus,
  Info,
  Building2,
  Loader2,
} from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface SchoolData {
  id: string;
  name: string;
  code: string;
  description: string | null;
  dean_user_id: string | null;
  dean_name: string | null;
  is_active: boolean;
  department_count: number;
  faculty_count: number;
  created_at: string;
  updated_at: string;
}

interface SchoolLookup {
  id: string;
  name: string;
  code: string;
  dean_user_id: string | null;
}

interface DeanData {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  assigned_school_id: string | null;
  assigned_school_name: string | null;
}

interface Toast {
  id: number;
  type: "success" | "error";
  message: string;
}

interface SchoolFormErrors {
  name?: string;
  code?: string;
}

interface DeanFormErrors {
  first_name?: string;
  last_name?: string;
  employee_id?: string;
  email?: string;
  school_college_id?: string;
}

let toastCounter = 0;

export default function AdminSchools() {
  const { token } = useAuth();
  const [schools, setSchools] = useState<SchoolData[]>([]);
  const [deans, setDeans] = useState<DeanData[]>([]);
  const [schoolLookup, setSchoolLookup] = useState<SchoolLookup[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  // Modals
  const [showSchoolModal, setShowSchoolModal] = useState(false);
  const [showDeanAssignModal, setShowDeanAssignModal] = useState(false);
  const [showDeanCreateModal, setShowDeanCreateModal] = useState(false);
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);

  // School form state
  const [editingSchool, setEditingSchool] = useState<SchoolData | null>(null);
  const [selectedSchool, setSelectedSchool] = useState<SchoolData | null>(null);
  const [schoolForm, setSchoolForm] = useState({ name: "", code: "", description: "" });
  const [schoolFormErrors, setSchoolFormErrors] = useState<SchoolFormErrors>({});
  const [schoolSubmitting, setSchoolSubmitting] = useState(false);

  // Dean form state
  const [selectedDeanId, setSelectedDeanId] = useState("");
  const [deanForm, setDeanForm] = useState({
    employee_id: "",
    first_name: "",
    middle_name: "",
    last_name: "",
    email: "",
    school_college_id: "",
  });
  const [deanFormErrors, setDeanFormErrors] = useState<DeanFormErrors>({});
  const [deanSubmitting, setDeanSubmitting] = useState(false);

  // Toasts
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (type: "success" | "error", message: string) => {
    const id = ++toastCounter;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  const loadSchools = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "10" });
      if (search) params.set("search", search);
      const data = await apiRequest<{ items: SchoolData[]; total: number }>(
        `/admin/schools?${params}`,
        { token: token! }
      );
      setSchools(data.items);
      setTotal(data.total);
    } catch (err: any) {
      showToast("error", err.message);
    } finally {
      setLoading(false);
    }
  }, [token, page, search]);

  const loadDeans = useCallback(async () => {
    try {
      const data = await apiRequest<DeanData[]>("/admin/deans", { token: token! });
      setDeans(data);
    } catch {}
  }, [token]);

  const loadSchoolLookup = useCallback(async () => {
    try {
      const data = await apiRequest<SchoolLookup[]>("/admin/schools/lookup", { token: token! });
      setSchoolLookup(data);
    } catch {}
  }, [token]);

  useEffect(() => { loadSchools(); }, [loadSchools]);
  useEffect(() => { loadDeans(); }, [loadDeans]);
  useEffect(() => { loadSchoolLookup(); }, [loadSchoolLookup]);

  // ── School Create/Edit ──
  const openAddSchool = () => {
    setEditingSchool(null);
    setSchoolForm({ name: "", code: "", description: "" });
    setSchoolFormErrors({});
    setSchoolSubmitting(false);
    setShowSchoolModal(true);
  };

  const openEditSchool = (school: SchoolData) => {
    setEditingSchool(school);
    setSchoolForm({ name: school.name, code: school.code, description: school.description || "" });
    setSchoolFormErrors({});
    setSchoolSubmitting(false);
    setShowSchoolModal(true);
  };

  const validateSchoolForm = (): boolean => {
    const errors: SchoolFormErrors = {};
    if (!schoolForm.name.trim()) {
      errors.name = "School / College name is required";
    }
    if (!schoolForm.code.trim()) {
      errors.code = "Code is required";
    }
    setSchoolFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmitSchool = async () => {
    if (!validateSchoolForm()) return;
    setSchoolSubmitting(true);
    try {
      const normalizedCode = schoolForm.code.trim().toUpperCase();
      const payload = { ...schoolForm, code: normalizedCode };

      if (editingSchool) {
        await apiRequest(`/admin/schools/${editingSchool.id}`, {
          token: token!, method: "PUT", body: payload,
        });
        showToast("success", `${payload.name} updated successfully.`);
      } else {
        await apiRequest("/admin/schools", {
          token: token!, method: "POST", body: payload,
        });
        showToast("success", `${payload.name} created successfully.`);
      }
      setShowSchoolModal(false);
      loadSchools();
      loadSchoolLookup();
    } catch (err: any) {
      const msg = err.message || "";
      if (msg.toLowerCase().includes("code already exists")) {
        setSchoolFormErrors((prev) => ({ ...prev, code: "This code already exists" }));
      } else if (msg.toLowerCase().includes("name already exists")) {
        setSchoolFormErrors((prev) => ({ ...prev, name: "A School / College with this name already exists" }));
      } else {
        showToast("error", msg);
      }
    } finally {
      setSchoolSubmitting(false);
    }
  };

  // ── Dean Assign ──
  const openDeanAssign = (school: SchoolData) => {
    setSelectedSchool(school);
    setSelectedDeanId(school.dean_user_id || "");
    setShowDeanAssignModal(true);
  };

  const handleAssignDean = async () => {
    if (!selectedSchool || !selectedDeanId) return;
    try {
      await apiRequest(`/admin/schools/${selectedSchool.id}/assign-dean`, {
        token: token!, method: "POST",         body: { dean_user_id: selectedDeanId },
      });
      const dean = deans.find((d) => d.id === selectedDeanId);
      showToast("success", `${dean?.full_name || "Dean"} assigned to ${selectedSchool.name}.`);
      setShowDeanAssignModal(false);
      loadSchools();
      loadDeans();
    } catch (err: any) {
      showToast("error", err.message);
    }
  };

  // ── Dean Create & Assign ──
  const openDeanCreate = () => {
    setDeanForm({ employee_id: "", first_name: "", middle_name: "", last_name: "", email: "", school_college_id: "" });
    setDeanFormErrors({});
    setDeanSubmitting(false);
    setShowDeanCreateModal(true);
  };

  const validateDeanForm = (): boolean => {
    const errors: DeanFormErrors = {};
    if (!deanForm.first_name.trim()) errors.first_name = "First name is required";
    if (!deanForm.last_name.trim()) errors.last_name = "Last name is required";
    if (!deanForm.employee_id.trim()) errors.employee_id = "Employee ID is required";
    if (!deanForm.email.trim()) {
      errors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(deanForm.email)) {
      errors.email = "Invalid email format";
    }
    if (!deanForm.school_college_id) errors.school_college_id = "Please select a School / College";
    setDeanFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmitDean = async () => {
    if (!validateDeanForm()) return;
    setDeanSubmitting(true);
    try {
      await apiRequest("/admin/deans/create-and-assign", {
        token: token!,
        method: "POST",
        body: deanForm,
      });
      const school = schoolLookup.find((s) => s.id === deanForm.school_college_id);
      showToast("success", `${deanForm.first_name} ${deanForm.last_name} has been assigned as Dean of ${school?.name || "the selected school"}.`);
      setShowDeanCreateModal(false);
      loadSchools();
      loadDeans();
      loadSchoolLookup();
    } catch (err: any) {
      showToast("error", err.message);
    } finally {
      setDeanSubmitting(false);
    }
  };

  // ── Deactivate / Activate ──
  const openDeactivate = (school: SchoolData) => {
    setSelectedSchool(school);
    setShowDeactivateModal(true);
  };

  const handleDeactivate = async () => {
    if (!selectedSchool) return;
    try {
      await apiRequest(`/admin/schools/${selectedSchool.id}/deactivate`, { token: token!, method: "POST" });
      showToast("success", `${selectedSchool.name} deactivated.`);
      setShowDeactivateModal(false);
      loadSchools();
    } catch (err: any) {
      showToast("error", err.message);
    }
  };

  const handleActivate = async (school: SchoolData) => {
    try {
      await apiRequest(`/admin/schools/${school.id}/activate`, { token: token!, method: "POST" });
      showToast("success", `${school.name} activated.`);
      loadSchools();
    } catch (err: any) {
      showToast("error", err.message);
    }
  };

  const unassignedDeans = deans.filter((d) => d.is_active && !d.assigned_school_id);
  const allActiveDeans = deans.filter((d) => d.is_active);
  const availableSchools = schoolLookup.filter((s) => !s.dean_user_id);

  return (
    <div className="p-6 relative">
      {/* Toast */}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2">
        {toasts.map((t) => (
          <div key={t.id} className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all ${
            t.type === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white"
          }`}>
            {t.type === "success" ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
            {t.message}
          </div>
        ))}
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading text-2xl font-bold text-maron">Schools / Colleges</h1>
          <p className="text-gray-500 text-sm mt-1">Manage university academic units</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={openDeanCreate} className="flex items-center gap-2 px-4 py-2.5 border-2 border-maron text-maron rounded-lg hover:bg-maron/5 font-medium text-sm transition-colors">
            <UserPlus size={18} /> Create Dean
          </button>
          <button onClick={openAddSchool} className="flex items-center gap-2 px-5 py-2.5 bg-maron text-white rounded-lg hover:bg-maron/90 font-semibold text-sm shadow-sm transition-colors">
            <Plus size={18} strokeWidth={2.5} /> Add School / College
          </button>
        </div>
      </div>

      {/* Workflow hint */}
      <div className="mb-4 p-3 bg-blue-50 border border-blue-100 rounded-lg flex items-start gap-2 text-sm text-blue-700">
        <Info size={16} className="mt-0.5 shrink-0" />
        <span>
          <strong>Setup workflow:</strong> Create School → Create Dean (select School) → Dean creates Departments &amp; adds Faculty.
        </span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-4 border-b border-gray-100">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input type="text" placeholder="Search schools by name or code..." value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron" />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left">
                <th className="px-4 py-3 font-medium text-gray-600 w-20">Code</th>
                <th className="px-4 py-3 font-medium text-gray-600">School / College</th>
                <th className="px-4 py-3 font-medium text-gray-600">Assigned Dean</th>
                <th className="px-4 py-3 font-medium text-gray-600 text-center">Departments</th>
                <th className="px-4 py-3 font-medium text-gray-600 text-center">Faculty</th>
                <th className="px-4 py-3 font-medium text-gray-600 text-center">Status</th>
                <th className="px-4 py-3 font-medium text-gray-600 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} className="text-center py-12 text-gray-400">Loading...</td></tr>
              ) : schools.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-12 text-gray-400">No schools found</td></tr>
              ) : (
                schools.map((school) => (
                  <tr key={school.id} className="border-t border-gray-50 hover:bg-gray-50/50">
                    <td className="px-4 py-3 font-mono font-semibold text-gray-700">{school.code}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{school.name}</div>
                      {school.description && <div className="text-xs text-gray-400 mt-0.5 line-clamp-1">{school.description}</div>}
                    </td>
                    <td className="px-4 py-3">
                      {school.dean_name ? (
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-full bg-maron/10 flex items-center justify-center">
                            <UserCheck size={14} className="text-maron" />
                          </div>
                          <div>
                            <div className="font-medium text-gray-900 text-sm">{school.dean_name}</div>
                            <div className="text-xs text-green-600">Assigned</div>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-full bg-amber-50 flex items-center justify-center">
                            <AlertTriangle size={14} className="text-amber-500" />
                          </div>
                          <div>
                            <div className="text-amber-600 text-sm font-medium">No Dean Assigned</div>
                            <button onClick={() => openDeanAssign(school)} className="text-xs text-maron hover:underline font-medium">Assign Dean now</button>
                          </div>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center font-medium text-gray-700">{school.department_count}</td>
                    <td className="px-4 py-3 text-center font-medium text-gray-700">{school.faculty_count}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        school.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                      }`}>{school.is_active ? "Active" : "Inactive"}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => openEditSchool(school)} className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-gray-600 rounded-md hover:bg-gray-100 transition-colors" title="Edit School / College">
                          <Edit size={14} /> Edit
                        </button>
                        <button onClick={() => openDeanAssign(school)} className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-maron rounded-md hover:bg-maron/5 transition-colors" title="Assign Dean">
                          <UserCheck size={14} /> Assign Dean
                        </button>
                        {school.is_active ? (
                          <button onClick={() => openDeactivate(school)} className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-red-600 rounded-md hover:bg-red-50 transition-colors" title="Deactivate School">
                            <X size={14} /> Deactivate
                          </button>
                        ) : (
                          <button onClick={() => handleActivate(school)} className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-green-600 rounded-md hover:bg-green-50 transition-colors" title="Activate School">
                            <CheckCircle size={14} /> Activate
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {total > 10 && (
          <div className="p-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
            <span>Showing {(page - 1) * 10 + 1}–{Math.min(page * 10, total)} of {total}</span>
            <div className="flex gap-2">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-50">Previous</button>
              <button disabled={page * 10 >= total} onClick={() => setPage(page + 1)} className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-50">Next</button>
            </div>
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════ */}
      {/* MODAL: Add / Edit School / College             */}
      {/* ═══════════════════════════════════════════════ */}
      {showSchoolModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
              <h2 className="font-heading text-lg font-bold text-maron">
                {editingSchool ? "Edit School / College" : "Add School / College"}
              </h2>
              <button onClick={() => setShowSchoolModal(false)} className="p-1.5 rounded-lg hover:bg-gray-100"><X size={18} /></button>
            </div>
            {/* Scrollable body */}
            <div className="px-6 py-4 space-y-4 overflow-y-auto flex-1">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">School / College Name <span className="text-red-500">*</span></label>
                <input type="text" value={schoolForm.name}
                  onChange={(e) => {
                    setSchoolForm({ ...schoolForm, name: e.target.value });
                    if (schoolFormErrors.name) setSchoolFormErrors((prev) => ({ ...prev, name: undefined }));
                  }}
                  className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron ${
                    schoolFormErrors.name ? "border-red-400" : "border-gray-200"
                  }`}
                  placeholder="e.g., School of Computing" />
                {schoolFormErrors.name && <p className="text-xs text-red-500 mt-1">{schoolFormErrors.name}</p>}
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Code <span className="text-red-500">*</span></label>
                <input type="text" value={schoolForm.code}
                  onChange={(e) => {
                    setSchoolForm({ ...schoolForm, code: e.target.value });
                    if (schoolFormErrors.code) setSchoolFormErrors((prev) => ({ ...prev, code: undefined }));
                  }}
                  className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron font-mono ${
                    schoolFormErrors.code ? "border-red-400" : "border-gray-200"
                  }`}
                  placeholder="e.g., SOC" maxLength={20} />
                {schoolFormErrors.code && <p className="text-xs text-red-500 mt-1">{schoolFormErrors.code}</p>}
                {!schoolFormErrors.code && <p className="text-xs text-gray-400 mt-1">Short unique code (e.g., SOC, SBA, SEA)</p>}
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Description</label>
                <textarea value={schoolForm.description} onChange={(e) => setSchoolForm({ ...schoolForm, description: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron"
                  rows={3} placeholder="Optional description of this school or college..." />
              </div>
              {editingSchool && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span className="font-medium">Status:</span>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                    editingSchool.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                  }`}>{editingSchool.is_active ? "Active" : "Inactive"}</span>
                  <span className="text-xs text-gray-400">(use Deactivate/Activate in the table to change)</span>
                </div>
              )}
            </div>
            {/* Sticky footer — always visible */}
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50/50 rounded-b-xl shrink-0">
              <button onClick={() => setShowSchoolModal(false)}
                className="px-4 py-2.5 text-sm font-medium border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                Cancel
              </button>
              <button onClick={handleSubmitSchool} disabled={schoolSubmitting || !schoolForm.name.trim() || !schoolForm.code.trim()}
                className="px-5 py-2.5 text-sm font-semibold bg-maron text-white rounded-lg hover:bg-maron/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors inline-flex items-center gap-2">
                {schoolSubmitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Creating...
                  </>
                ) : (
                  editingSchool ? "Save Changes" : "Create School / College"
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════ */}
      {/* MODAL: Assign Dean                            */}
      {/* ═══════════════════════════════════════════════ */}
      {showDeanAssignModal && selectedSchool && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
              <div>
                <h2 className="font-heading text-lg font-bold text-maron">Assign Dean</h2>
                <p className="text-sm text-gray-500 mt-0.5">{selectedSchool.name}</p>
              </div>
              <button onClick={() => setShowDeanAssignModal(false)} className="p-1.5 rounded-lg hover:bg-gray-100"><X size={18} /></button>
            </div>
            <div className="px-6 py-4 space-y-4 overflow-y-auto flex-1">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">School / College</label>
                <div className="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-700">
                  {selectedSchool.code} — {selectedSchool.name}
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm font-semibold text-gray-700">Select Dean</label>
                  <button onClick={() => { setShowDeanAssignModal(false); openDeanCreate(); }}
                    className="text-xs font-medium text-maron hover:underline flex items-center gap-1">
                    <UserPlus size={12} /> Create New Dean
                  </button>
                </div>
                <select value={selectedDeanId} onChange={(e) => setSelectedDeanId(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron">
                  <option value="">-- Select a Dean --</option>
                  {unassignedDeans.length > 0 && (
                    <optgroup label="Unassigned Deans (Recommended)">
                      {unassignedDeans.map((dean) => (
                        <option key={dean.id} value={dean.id}>{dean.full_name} ({dean.email})</option>
                      ))}
                    </optgroup>
                  )}
                  {allActiveDeans.filter((d) => d.assigned_school_id).length > 0 && (
                    <optgroup label="Currently Assigned Deans (Reassign)">
                      {allActiveDeans.filter((d) => d.assigned_school_id).map((dean) => (
                        <option key={dean.id} value={dean.id}>{dean.full_name} ({dean.email}) — {dean.assigned_school_name}</option>
                      ))}
                    </optgroup>
                  )}
                </select>
                {unassignedDeans.length === 0 && (
                  <p className="text-xs text-amber-600 mt-1.5 flex items-center gap-1">
                    <AlertTriangle size={12} /> No unassigned Deans available.{" "}
                    <button onClick={() => { setShowDeanAssignModal(false); openDeanCreate(); }} className="underline font-medium">Create a new Dean account</button>
                  </p>
                )}
              </div>
            </div>
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50/50 rounded-b-xl shrink-0">
              <button onClick={() => setShowDeanAssignModal(false)} className="px-4 py-2.5 text-sm font-medium border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
              <button onClick={handleAssignDean} disabled={!selectedDeanId}
                className="px-5 py-2.5 text-sm font-semibold bg-maron text-white rounded-lg hover:bg-maron/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                Assign Dean
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════ */}
      {/* MODAL: Create & Assign Dean Account            */}
      {/* ═══════════════════════════════════════════════ */}
      {showDeanCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
              <div>
                <h2 className="font-heading text-lg font-bold text-maron">Create Dean Account</h2>
                <p className="text-sm text-gray-500 mt-0.5">Create account and assign to a School / College</p>
              </div>
              <button onClick={() => setShowDeanCreateModal(false)} className="p-1.5 rounded-lg hover:bg-gray-100"><X size={18} /></button>
            </div>

            {/* Scrollable body */}
            <div className="px-6 py-4 space-y-4 overflow-y-auto flex-1">
              {/* Name fields */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">First Name <span className="text-red-500">*</span></label>
                  <input type="text" value={deanForm.first_name} onChange={(e) => setDeanForm({ ...deanForm, first_name: e.target.value })}
                    className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron ${
                      deanFormErrors.first_name ? "border-red-400" : "border-gray-200"
                    }`} placeholder="First name" />
                  {deanFormErrors.first_name && <p className="text-xs text-red-500 mt-1">{deanFormErrors.first_name}</p>}
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">Last Name <span className="text-red-500">*</span></label>
                  <input type="text" value={deanForm.last_name} onChange={(e) => setDeanForm({ ...deanForm, last_name: e.target.value })}
                    className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron ${
                      deanFormErrors.last_name ? "border-red-400" : "border-gray-200"
                    }`} placeholder="Last name" />
                  {deanFormErrors.last_name && <p className="text-xs text-red-500 mt-1">{deanFormErrors.last_name}</p>}
                </div>
              </div>

              {/* Middle Name */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Middle Name</label>
                <input type="text" value={deanForm.middle_name} onChange={(e) => setDeanForm({ ...deanForm, middle_name: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron"
                  placeholder="Middle name (optional)" />
              </div>

              {/* Employee ID */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Employee ID <span className="text-red-500">*</span></label>
                <input type="text" value={deanForm.employee_id} onChange={(e) => setDeanForm({ ...deanForm, employee_id: e.target.value })}
                  className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron ${
                    deanFormErrors.employee_id ? "border-red-400" : "border-gray-200"
                  }`} placeholder="e.g., 44890" />
                {deanFormErrors.employee_id && <p className="text-xs text-red-500 mt-1">{deanFormErrors.employee_id}</p>}
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Email <span className="text-red-500">*</span></label>
                <input type="email" value={deanForm.email} onChange={(e) => setDeanForm({ ...deanForm, email: e.target.value })}
                  className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron ${
                    deanFormErrors.email ? "border-red-400" : "border-gray-200"
                  }`} placeholder="e.g., dean.name@hau.edu.ph" />
                {deanFormErrors.email && <p className="text-xs text-red-500 mt-1">{deanFormErrors.email}</p>}
              </div>

              {/* School / College */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm font-semibold text-gray-700">School / College <span className="text-red-500">*</span></label>
                  <button onClick={() => { setShowDeanCreateModal(false); openAddSchool(); }}
                    className="text-xs font-medium text-maron hover:underline flex items-center gap-1">
                    <Plus size={12} /> Add School / College
                  </button>
                </div>
                {schoolLookup.length === 0 ? (
                  <div className="p-3 bg-amber-50 border border-amber-100 rounded-lg">
                    <p className="text-sm text-amber-700 flex items-center gap-2">
                      <Building2 size={14} />
                      No School / College available.
                    </p>
                    <button onClick={() => { setShowDeanCreateModal(false); openAddSchool(); }}
                      className="text-xs font-medium text-maron hover:underline mt-2 flex items-center gap-1">
                      <Plus size={12} /> Add School / College
                    </button>
                  </div>
                ) : (
                  <select value={deanForm.school_college_id} onChange={(e) => setDeanForm({ ...deanForm, school_college_id: e.target.value })}
                    className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron ${
                      deanFormErrors.school_college_id ? "border-red-400" : "border-gray-200"
                    }`}>
                    <option value="">-- Select School / College --</option>
                    {availableSchools.length > 0 && (
                      <optgroup label="Available (No Dean Assigned)">
                        {availableSchools.map((s) => (
                          <option key={s.id} value={s.id}>{s.code} — {s.name}</option>
                        ))}
                      </optgroup>
                    )}
                    {schoolLookup.filter((s) => s.dean_user_id).length > 0 && (
                      <optgroup label="Already Assigned (Will Replace Current Dean)">
                        {schoolLookup.filter((s) => s.dean_user_id).map((s) => (
                          <option key={s.id} value={s.id}>{s.code} — {s.name} (has Dean)</option>
                        ))}
                      </optgroup>
                    )}
                  </select>
                )}
                {deanFormErrors.school_college_id && <p className="text-xs text-red-500 mt-1">{deanFormErrors.school_college_id}</p>}
              </div>

              {/* Role badge */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-semibold text-gray-700">Role:</span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-maron/10 text-maron">DEAN</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">Deans manage their assigned School/College — create departments, add faculty, and endorse research.</p>
              </div>
            </div>

            {/* Sticky footer */}
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50/50 rounded-b-xl shrink-0">
              <button onClick={() => setShowDeanCreateModal(false)}
                className="px-4 py-2.5 text-sm font-medium border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                Cancel
              </button>
              <button onClick={handleSubmitDean} disabled={deanSubmitting || schoolLookup.length === 0}
                className="px-5 py-2.5 text-sm font-semibold bg-maron text-white rounded-lg hover:bg-maron/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-2">
                {deanSubmitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create & Assign Dean"
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════ */}
      {/* MODAL: Confirm Deactivation                   */}
      {/* ═══════════════════════════════════════════════ */}
      {showDeactivateModal && selectedSchool && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
              <h2 className="font-heading text-lg font-bold text-maron">Deactivate School / College</h2>
              <button onClick={() => setShowDeactivateModal(false)} className="p-1.5 rounded-lg hover:bg-gray-100"><X size={18} /></button>
            </div>
            <div className="px-6 py-4 overflow-y-auto flex-1">
              <p className="text-sm text-gray-700 mb-3">Are you sure you want to deactivate <strong>{selectedSchool.name}</strong>?</p>
              <div className="p-3 bg-amber-50 border border-amber-100 rounded-lg text-sm text-amber-700">
                <strong>Note:</strong> This will prevent new activity under this School/College but will preserve existing Departments, Faculty, and research records.
              </div>
            </div>
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50/50 rounded-b-xl shrink-0">
              <button onClick={() => setShowDeactivateModal(false)} className="px-4 py-2.5 text-sm font-medium border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
              <button onClick={handleDeactivate} className="px-5 py-2.5 text-sm font-semibold bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">Deactivate</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
