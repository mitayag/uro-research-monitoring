import { useEffect, useState, useCallback } from "react";
import { Plus, Edit, Eye, X, Building2 } from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface DepartmentData {
  id: string;
  name: string;
  code: string;
  description: string | null;
  is_active: boolean;
  faculty_count: number;
  active_research: number;
  created_at: string;
  updated_at: string;
}

export default function DeanDepartments() {
  const { token } = useAuth();
  const [departments, setDepartments] = useState<DepartmentData[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [editingDept, setEditingDept] = useState<DepartmentData | null>(null);
  const [selectedDept, setSelectedDept] = useState<DepartmentData | null>(null);
  const [formData, setFormData] = useState({ name: "", code: "", description: "" });
  const [error, setError] = useState("");

  const loadDepartments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiRequest<DepartmentData[]>("/dean/departments", { token: token! });
      setDepartments(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { loadDepartments(); }, [loadDepartments]);

  const openAdd = () => {
    setEditingDept(null);
    setFormData({ name: "", code: "", description: "" });
    setShowModal(true);
    setError("");
  };

  const openEdit = (dept: DepartmentData) => {
    setEditingDept(dept);
    setFormData({ name: dept.name, code: dept.code, description: dept.description || "" });
    setShowModal(true);
    setError("");
  };

  const openDetail = (dept: DepartmentData) => {
    setSelectedDept(dept);
    setShowDetail(true);
  };

  const handleSubmit = async () => {
    setError("");
    try {
      if (editingDept) {
        await apiRequest(`/dean/departments/${editingDept.id}`, {
          token: token!,
          method: "PUT",
          body: formData,
        });
      } else {
        await apiRequest("/dean/departments", {
          token: token!,
          method: "POST",
          body: formData,
        });
      }
      setShowModal(false);
      loadDepartments();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeactivate = async (dept: DepartmentData) => {
    if (!confirm(`Deactivate department "${dept.name}"?`)) return;
    try {
      await apiRequest(`/dean/departments/${dept.id}/deactivate`, { token: token!, method: "POST" });
      loadDepartments();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleActivate = async (dept: DepartmentData) => {
    try {
      await apiRequest(`/dean/departments/${dept.id}/activate`, { token: token!, method: "POST" });
      loadDepartments();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading text-2xl font-bold text-maron">Departments</h1>
          <p className="text-gray-500 text-sm mt-1">Manage departments in your School/College</p>
        </div>
        <button onClick={openAdd} className="flex items-center gap-2 px-4 py-2 bg-maron text-white rounded-lg hover:bg-maron/90">
          <Plus size={18} /> Add Department
        </button>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg">{error}</div>}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left">
                <th className="px-4 py-3 font-medium text-gray-600">Code</th>
                <th className="px-4 py-3 font-medium text-gray-600">Department Name</th>
                <th className="px-4 py-3 font-medium text-gray-600 text-center">Faculty</th>
                <th className="px-4 py-3 font-medium text-gray-600 text-center">Active Research</th>
                <th className="px-4 py-3 font-medium text-gray-600 text-center">Status</th>
                <th className="px-4 py-3 font-medium text-gray-600 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="text-center py-8 text-gray-400">Loading...</td></tr>
              ) : departments.length === 0 ? (
                <tr><td colSpan={6} className="text-center py-8 text-gray-400">No departments yet. Add your first department.</td></tr>
              ) : (
                departments.map((dept) => (
                  <tr key={dept.id} className="border-t border-gray-50 hover:bg-gray-50/50">
                    <td className="px-4 py-3 font-medium">{dept.code}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{dept.name}</div>
                      {dept.description && <div className="text-xs text-gray-400 mt-0.5">{dept.description}</div>}
                    </td>
                    <td className="px-4 py-3 text-center">{dept.faculty_count}</td>
                    <td className="px-4 py-3 text-center">{dept.active_research}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        dept.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                      }`}>
                        {dept.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <button onClick={() => openDetail(dept)} className="p-1.5 rounded hover:bg-gray-100" title="View">
                          <Eye size={14} className="text-gray-500" />
                        </button>
                        <button onClick={() => openEdit(dept)} className="p-1.5 rounded hover:bg-gray-100" title="Edit">
                          <Edit size={14} className="text-gray-500" />
                        </button>
                        {dept.is_active ? (
                          <button onClick={() => handleDeactivate(dept)} className="p-1.5 rounded hover:bg-gray-100" title="Deactivate">
                            <X size={14} className="text-red-500" />
                          </button>
                        ) : (
                          <button onClick={() => handleActivate(dept)} className="p-1.5 rounded hover:bg-gray-100" title="Activate">
                            <Building2 size={14} className="text-green-500" />
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
      </div>

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading text-lg font-bold text-maron">
                {editingDept ? "Edit Department" : "Add Department"}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-1 rounded hover:bg-gray-100"><X size={18} /></button>
            </div>
            {error && <div className="mb-3 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>}
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Department Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron"
                  placeholder="e.g., Computer Science"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Code</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron"
                  placeholder="e.g., CS"
                  maxLength={20}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maron/20 focus:border-maron"
                  rows={3}
                  placeholder="Optional description..."
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">Cancel</button>
              <button
                onClick={handleSubmit}
                disabled={!formData.name || !formData.code}
                className="px-4 py-2 text-sm bg-maron text-white rounded-lg hover:bg-maron/90 disabled:opacity-40"
              >
                {editingDept ? "Save Changes" : "Create Department"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetail && selectedDept && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading text-lg font-bold text-maron">Department Details</h2>
              <button onClick={() => setShowDetail(false)} className="p-1 rounded hover:bg-gray-100"><X size={18} /></button>
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Name</span><span className="font-medium">{selectedDept.name}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Code</span><span className="font-medium">{selectedDept.code}</span></div>
              {selectedDept.description && (
                <div><span className="text-gray-500">Description</span><p className="mt-1">{selectedDept.description}</p></div>
              )}
              <div className="flex justify-between"><span className="text-gray-500">Faculty Count</span><span className="font-medium">{selectedDept.faculty_count}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Active Research</span><span className="font-medium">{selectedDept.active_research}</span></div>
              <div className="flex justify-between">
                <span className="text-gray-500">Status</span>
                <span className={`font-medium ${selectedDept.is_active ? "text-green-600" : "text-red-600"}`}>
                  {selectedDept.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              <div className="flex justify-between"><span className="text-gray-500">Created</span><span>{selectedDept.created_at ? new Date(selectedDept.created_at).toLocaleDateString() : "N/A"}</span></div>
            </div>
            <div className="flex justify-end mt-6">
              <button onClick={() => setShowDetail(false)} className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
