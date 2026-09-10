import { useEffect, useState, useCallback } from "react";
import { Plus, Search, Edit, UserCheck, UserX, Eye, X } from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface StaffMember {
  id: string;
  employee_id: string | null;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  full_name: string;
  email: string;
  department_id: string | null;
  department_name: string | null;
  roles: string[];
  is_active: boolean;
  active_research: number;
  completed_research: number;
  total_research: number;
  created_at: string | null;
}

interface Department {
  id: string;
  name: string;
  code: string;
}

interface StaffFormData {
  employee_id: string;
  email: string;
  password: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  department_id: string;
  role_name: string;
}

const EMPTY_FORM: StaffFormData = {
  employee_id: "",
  email: "",
  password: "changeme123",
  first_name: "",
  middle_name: "",
  last_name: "",
  department_id: "",
  role_name: "RESEARCHER",
};

export default function DeanAcademicStaff() {
  const { token } = useAuth();
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterDept, setFilterDept] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedStaff, setSelectedStaff] = useState<StaffMember | null>(null);
  const [formData, setFormData] = useState<StaffFormData>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchStaff = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (search) params.set("search", search);
      if (filterDept) params.set("department_id", filterDept);
      const data = await apiRequest<{ items: StaffMember[]; total: number }>(`/dean/staff?${params}`, { token });
      setStaff(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [token, page, search, filterDept]);

  const fetchDepartments = useCallback(async () => {
    if (!token) return;
    try {
      const data = await apiRequest<Department[]>(`/dean/staff/departments`, { token });
      setDepartments(data);
    } catch (err) {
      console.error(err);
    }
  }, [token]);

  useEffect(() => { fetchDepartments(); }, [fetchDepartments]);
  useEffect(() => { fetchStaff(); }, [fetchStaff]);

  const validateForm = (isEdit: boolean = false): boolean => {
    const errors: Record<string, string> = {};
    if (!formData.first_name.trim()) errors.first_name = "First name is required";
    if (!formData.last_name.trim()) errors.last_name = "Last name is required";
    if (!formData.email.trim()) errors.email = "Email is required";
    else if (!formData.email.includes("@")) errors.email = "Invalid email format";
    if (!formData.department_id) errors.department_id = "Department is required";
    if (!isEdit && !formData.password.trim()) errors.password = "Password is required";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleAdd = async () => {
    if (!validateForm() || !token) return;
    setSaving(true);
    try {
      await apiRequest("/dean/staff", {
        token,
        method: "POST",
        body: {
          employee_id: formData.employee_id || undefined,
          email: formData.email.trim(),
          password: formData.password,
          first_name: formData.first_name.trim(),
          middle_name: formData.middle_name.trim() || undefined,
          last_name: formData.last_name.trim(),
          department_id: formData.department_id,
          role_name: formData.role_name,
        },
      });
      setToast({ type: "success", message: "Academic staff created successfully" });
      setShowAddModal(false);
      setFormData(EMPTY_FORM);
      await fetchStaff();
    } catch (err: any) {
      setToast({ type: "error", message: err.detail || "Failed to create staff" });
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = async () => {
    if (!validateForm(true) || !token || !selectedStaff) return;
    setSaving(true);
    try {
      await apiRequest(`/dean/staff/${selectedStaff.id}`, {
        token,
        method: "PUT",
        body: {
          employee_id: formData.employee_id || undefined,
          first_name: formData.first_name.trim(),
          middle_name: formData.middle_name.trim() || undefined,
          last_name: formData.last_name.trim(),
          email: formData.email.trim(),
          department_id: formData.department_id,
          role_name: formData.role_name,
        },
      });
      setToast({ type: "success", message: "Staff updated successfully" });
      setShowEditModal(false);
      setSelectedStaff(null);
      await fetchStaff();
    } catch (err: any) {
      setToast({ type: "error", message: err.detail || "Failed to update staff" });
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (staffMember: StaffMember) => {
    if (!token) return;
    const action = staffMember.is_active ? "deactivate" : "activate";
    try {
      await apiRequest(`/dean/staff/${staffMember.id}/${action}`, {
        token,
        method: "POST",
      });
      setToast({
        type: "success",
        message: `${staffMember.full_name} ${action}d successfully`,
      });
      await fetchStaff();
    } catch (err: any) {
      setToast({ type: "error", message: err.detail || `Failed to ${action} staff` });
    }
  };

  const openEditModal = (member: StaffMember) => {
    setSelectedStaff(member);
    setFormData({
      employee_id: member.employee_id || "",
      email: member.email,
      password: "",
      first_name: member.first_name,
      middle_name: member.middle_name || "",
      last_name: member.last_name,
      department_id: member.department_id || "",
      role_name: member.roles[0] || "RESEARCHER",
    });
    setFormErrors({});
    setShowEditModal(true);
  };

  const openDetailModal = async (member: StaffMember) => {
    if (!token) return;
    try {
      const detail = await apiRequest<StaffMember & { research: any[] }>(`/dean/staff/${member.id}`, { token });
      setSelectedStaff(detail as StaffMember);
      setShowDetailModal(true);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-control text-sm font-medium shadow-modal ${
          toast.type === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white"
        }`}>
          {toast.message}
          <button onClick={() => setToast(null)} className="ml-3 underline">Dismiss</button>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-2xl font-bold text-gray-800">Academic Staff</h1>
          <p className="text-sm text-gray-500 mt-1">Manage academic staff in your school/college</p>
        </div>
        <button
          onClick={() => { setFormData(EMPTY_FORM); setFormErrors({}); setShowAddModal(true); }}
          className="flex items-center gap-2 px-4 py-2.5 bg-maroon-700 text-white rounded-control text-sm font-semibold hover:bg-maroon-600 transition-colors"
        >
          <Plus size={16} />
          Add Academic Staff
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-card border border-gray-200 p-4 shadow-card flex gap-4">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, email, or employee ID..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-control text-sm focus:ring-2 focus:ring-maroon-500 focus:border-maroon-500"
          />
        </div>
        <select
          value={filterDept}
          onChange={(e) => { setFilterDept(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-300 rounded-control text-sm focus:ring-2 focus:ring-maroon-500"
        >
          <option value="">All Departments</option>
          {departments.map(d => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>

      {/* Staff Table */}
      <div className="bg-white rounded-card border border-gray-200 shadow-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400">Loading...</div>
        ) : staff.length === 0 ? (
          <div className="p-8 text-center text-gray-400">No academic staff found</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Name</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Employee ID</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Department</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Role</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Research</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {staff.map((member) => (
                <tr key={member.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{member.full_name}</p>
                      <p className="text-xs text-gray-400">{member.email}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 font-mono">{member.employee_id || "—"}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{member.department_name || "—"}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                      {member.roles[0] || "N/A"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-sm">
                    <span className="text-green-600 font-medium">{member.active_research}</span>
                    <span className="text-gray-400 mx-1">/</span>
                    <span className="text-gray-600">{member.completed_research}</span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      member.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"
                    }`}>
                      {member.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => openDetailModal(member)} className="p-1.5 hover:bg-gray-100 rounded-lg" title="View">
                        <Eye size={14} className="text-gray-500" />
                      </button>
                      <button onClick={() => openEditModal(member)} className="p-1.5 hover:bg-gray-100 rounded-lg" title="Edit">
                        <Edit size={14} className="text-gray-500" />
                      </button>
                      <button
                        onClick={() => handleToggleActive(member)}
                        className={`p-1.5 hover:bg-gray-100 rounded-lg ${member.is_active ? "text-red-500" : "text-green-500"}`}
                        title={member.is_active ? "Deactivate" : "Activate"}
                      >
                        {member.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {/* Pagination */}
        {total > 20 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <span className="text-sm text-gray-500">Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} of {total}</span>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 text-sm border rounded disabled:opacity-50">Prev</button>
              <button onClick={() => setPage(p => p + 1)} disabled={page * 20 >= total} className="px-3 py-1 text-sm border rounded disabled:opacity-50">Next</button>
            </div>
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-card shadow-modal w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading text-lg font-bold">Add Academic Staff</h2>
              <button onClick={() => setShowAddModal(false)} className="p-1 hover:bg-gray-100 rounded"><X size={18} /></button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                  <input value={formData.first_name} onChange={e => setFormData({...formData, first_name: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
                  {formErrors.first_name && <p className="text-xs text-red-500 mt-1">{formErrors.first_name}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                  <input value={formData.last_name} onChange={e => setFormData({...formData, last_name: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
                  {formErrors.last_name && <p className="text-xs text-red-500 mt-1">{formErrors.last_name}</p>}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Middle Name</label>
                <input value={formData.middle_name} onChange={e => setFormData({...formData, middle_name: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Employee ID</label>
                <input value={formData.employee_id} onChange={e => setFormData({...formData, employee_id: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
                {formErrors.email && <p className="text-xs text-red-500 mt-1">{formErrors.email}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input type="password" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
                {formErrors.password && <p className="text-xs text-red-500 mt-1">{formErrors.password}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Department *</label>
                <select value={formData.department_id} onChange={e => setFormData({...formData, department_id: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm">
                  <option value="">Select Department</option>
                  {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
                {formErrors.department_id && <p className="text-xs text-red-500 mt-1">{formErrors.department_id}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select value={formData.role_name} onChange={e => setFormData({...formData, role_name: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm">
                  <option value="RESEARCHER">Researcher</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button onClick={() => setShowAddModal(false)} className="px-4 py-2 text-sm border rounded-control hover:bg-gray-50">Cancel</button>
                <button onClick={handleAdd} disabled={saving} className="px-4 py-2 text-sm bg-maroon-700 text-white rounded-control hover:bg-maroon-600 disabled:opacity-50">
                  {saving ? "Creating..." : "Create Staff"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedStaff && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-card shadow-modal w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading text-lg font-bold">Edit Academic Staff</h2>
              <button onClick={() => { setShowEditModal(false); setSelectedStaff(null); }} className="p-1 hover:bg-gray-100 rounded"><X size={18} /></button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                  <input value={formData.first_name} onChange={e => setFormData({...formData, first_name: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
                  {formErrors.first_name && <p className="text-xs text-red-500 mt-1">{formErrors.first_name}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                  <input value={formData.last_name} onChange={e => setFormData({...formData, last_name: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
                  {formErrors.last_name && <p className="text-xs text-red-500 mt-1">{formErrors.last_name}</p>}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Middle Name</label>
                <input value={formData.middle_name} onChange={e => setFormData({...formData, middle_name: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Employee ID</label>
                <input value={formData.employee_id} onChange={e => setFormData({...formData, employee_id: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm" />
                {formErrors.email && <p className="text-xs text-red-500 mt-1">{formErrors.email}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Department *</label>
                <select value={formData.department_id} onChange={e => setFormData({...formData, department_id: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm">
                  <option value="">Select Department</option>
                  {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
                {formErrors.department_id && <p className="text-xs text-red-500 mt-1">{formErrors.department_id}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select value={formData.role_name} onChange={e => setFormData({...formData, role_name: e.target.value})} className="w-full px-3 py-2 border rounded-control text-sm">
                  <option value="RESEARCHER">Researcher</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button onClick={() => { setShowEditModal(false); setSelectedStaff(null); }} className="px-4 py-2 text-sm border rounded-control hover:bg-gray-50">Cancel</button>
                <button onClick={handleEdit} disabled={saving} className="px-4 py-2 text-sm bg-maroon-700 text-white rounded-control hover:bg-maroon-600 disabled:opacity-50">
                  {saving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetailModal && selectedStaff && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-card shadow-modal w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading text-lg font-bold">Staff Details</h2>
              <button onClick={() => { setShowDetailModal(false); setSelectedStaff(null); }} className="p-1 hover:bg-gray-100 rounded"><X size={18} /></button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500">Name</span><p className="font-medium">{selectedStaff.full_name}</p></div>
                <div><span className="text-gray-500">Employee ID</span><p className="font-medium font-mono">{selectedStaff.employee_id || "—"}</p></div>
                <div><span className="text-gray-500">Email</span><p className="font-medium">{selectedStaff.email}</p></div>
                <div><span className="text-gray-500">Department</span><p className="font-medium">{selectedStaff.department_name || "—"}</p></div>
                <div><span className="text-gray-500">Role</span><p className="font-medium">{selectedStaff.roles?.join(", ") || "—"}</p></div>
                <div><span className="text-gray-500">Status</span>
                  <p className={`font-medium ${selectedStaff.is_active ? "text-green-600" : "text-red-600"}`}>
                    {selectedStaff.is_active ? "Active" : "Inactive"}
                  </p>
                </div>
              </div>
              <div className="border-t pt-4">
                <h3 className="font-heading text-sm font-bold mb-2">Research Activity</h3>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-3 bg-gray-50 rounded-card">
                    <p className="text-2xl font-bold text-maroon-700">{selectedStaff.active_research || 0}</p>
                    <p className="text-xs text-gray-500">Active</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-card">
                    <p className="text-2xl font-bold text-green-600">{selectedStaff.completed_research || 0}</p>
                    <p className="text-xs text-gray-500">Completed</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-card">
                    <p className="text-2xl font-bold text-gray-600">{selectedStaff.total_research || 0}</p>
                    <p className="text-xs text-gray-500">Total</p>
                  </div>
                </div>
              </div>
              <div className="flex justify-end pt-2">
                <button onClick={() => { setShowDetailModal(false); setSelectedStaff(null); }} className="px-4 py-2 text-sm border rounded-control hover:bg-gray-50">Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
