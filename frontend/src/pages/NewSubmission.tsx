import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Plus, Trash2, Upload } from "lucide-react";
import { apiRequest } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

interface AuthorEntry {
  name: string;
  affiliation: string;
  email: string;
  is_lead: boolean;
}

interface FormData {
  title: string;
  nature_of_research: string;
  research_agenda: string;
  target_journal: string;
  is_continuation: boolean;
  continuation_ref: string;
  mobile_number: string;
  institutional_email: string;
  authors: AuthorEntry[];
}

interface FormErrors {
  title?: string;
  authors?: string;
  general?: string;
}

const RESEARCH_TYPES = [
  "Quantitative",
  "Qualitative",
  "Mixed Methods",
  "Literature Review",
  "Case Study",
  "Action Research",
  "Experimental",
  "Descriptive",
  "Correlational",
  "Other",
];

export default function NewSubmission() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const [form, setForm] = useState<FormData>({
    title: "",
    nature_of_research: "",
    research_agenda: "",
    target_journal: "",
    is_continuation: false,
    continuation_ref: "",
    mobile_number: "",
    institutional_email: user?.email || "",
    authors: [
      {
        name: user?.full_name || "",
        affiliation: "Holy Angel University",
        email: user?.email || "",
        is_lead: true,
      },
    ],
  });

  const updateField = (field: keyof FormData, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors.general) setErrors((prev) => ({ ...prev, general: undefined }));
  };

  const addAuthor = () => {
    setForm((prev) => ({
      ...prev,
      authors: [
        ...prev.authors,
        { name: "", affiliation: "", email: "", is_lead: false },
      ],
    }));
  };

  const removeAuthor = (index: number) => {
    if (form.authors[index].is_lead) return;
    setForm((prev) => ({
      ...prev,
      authors: prev.authors.filter((_, i) => i !== index),
    }));
  };

  const updateAuthor = (index: number, field: keyof AuthorEntry, value: string | boolean) => {
    setForm((prev) => ({
      ...prev,
      authors: prev.authors.map((a, i) =>
        i === index ? { ...a, [field]: value } : a
      ),
    }));
  };

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!form.title.trim()) {
      newErrors.title = "Research title is required";
    }
    if (form.title.length > 500) {
      newErrors.title = "Title must be 500 characters or less";
    }
    const hasEmptyName = form.authors.some((a) => !a.name.trim());
    if (hasEmptyName) {
      newErrors.authors = "All authors must have a name";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const buildPayload = () => ({
    title: form.title.trim(),
    nature_of_research: form.nature_of_research || null,
    research_agenda: form.research_agenda.trim() || null,
    target_journal: form.target_journal.trim() || null,
    is_continuation: form.is_continuation,
    continuation_ref: form.is_continuation ? form.continuation_ref.trim() || null : null,
    mobile_number: form.mobile_number.trim() || null,
    institutional_email: form.institutional_email.trim() || null,
    authors: form.authors
      .filter((a) => a.name.trim())
      .map((a) => ({
        name: a.name.trim(),
        affiliation: a.affiliation.trim() || null,
        email: a.email.trim() || null,
        is_lead: a.is_lead,
      })),
  });

  const saveDraft = async () => {
    if (!validate() || !token) return;
    setSaving(true);
    try {
      const result = await apiRequest<{ id: string }>("/research", {
        token,
        method: "POST",
        body: buildPayload(),
      });
      setToast({ type: "success", message: "Draft saved successfully" });
      setTimeout(() => navigate(`/research/${result.id}`), 800);
    } catch (err: any) {
      setErrors({ general: err.detail || "Failed to save draft. Please try again." });
    } finally {
      setSaving(false);
    }
  };

  const submitApplication = async () => {
    if (!validate() || !token) return;
    setSubmitting(true);
    try {
      const result = await apiRequest<{ id: string }>("/research", {
        token,
        method: "POST",
        body: buildPayload(),
      });
      await apiRequest(`/research/${result.id}/transition`, {
        token,
        method: "POST",
        body: { action: "SUBMIT" },
      });
      setToast({ type: "success", message: "Application submitted successfully" });
      setTimeout(() => navigate(`/research/${result.id}`), 800);
    } catch (err: any) {
      setErrors({ general: err.detail || "Failed to submit application. Please try again." });
    } finally {
      setSubmitting(false);
      setShowSubmitConfirm(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-control text-sm font-medium shadow-modal ${
          toast.type === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white"
        }`}>
          {toast.message}
          <button onClick={() => setToast(null)} className="ml-3 underline">Dismiss</button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate("/research")} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <ArrowLeft size={20} className="text-gray-600" />
        </button>
        <div>
          <h1 className="font-heading text-2xl font-bold text-gray-800">New Research Submission</h1>
          <p className="text-sm text-gray-500 mt-1">Create a new research application for URO review</p>
        </div>
      </div>

      {/* General Error */}
      {errors.general && (
        <div className="bg-red-50 border border-red-200 rounded-card p-4 text-sm text-red-700">
          {errors.general}
        </div>
      )}

      {/* Research Information */}
      <div className="bg-white rounded-card border border-gray-200 p-6 shadow-card space-y-5">
        <h2 className="font-heading text-base font-bold text-gray-800 border-b border-gray-100 pb-3">Research Information</h2>

        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Research Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => updateField("title", e.target.value)}
            placeholder="Enter the full title of your research"
            className={`w-full px-3 py-2.5 rounded-control border text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30 ${
              errors.title ? "border-red-300" : "border-gray-200"
            }`}
            maxLength={500}
          />
          {errors.title && <p className="text-xs text-red-500 mt-1">{errors.title}</p>}
          <p className="text-xs text-gray-400 mt-1">{form.title.length}/500 characters</p>
        </div>

        {/* Nature of Research */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Research Type</label>
          <select
            value={form.nature_of_research}
            onChange={(e) => updateField("nature_of_research", e.target.value)}
            className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
          >
            <option value="">Select research type</option>
            {RESEARCH_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {/* Research Agenda */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Research Description / Abstract</label>
          <textarea
            value={form.research_agenda}
            onChange={(e) => updateField("research_agenda", e.target.value)}
            placeholder="Provide a brief description or abstract of your research..."
            rows={4}
            className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
          />
        </div>

        {/* Target Journal */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Target Journal</label>
          <input
            type="text"
            value={form.target_journal}
            onChange={(e) => updateField("target_journal", e.target.value)}
            placeholder="Where do you intend to publish this research?"
            className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
          />
        </div>

        {/* Continuation */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="is_continuation"
            checked={form.is_continuation}
            onChange={(e) => updateField("is_continuation", e.target.checked)}
            className="w-4 h-4 text-maroon-600 border-gray-300 rounded focus:ring-maroon-500"
          />
          <label htmlFor="is_continuation" className="text-sm font-medium text-gray-700">
            This is a continuation of a previous research
          </label>
        </div>
        {form.is_continuation && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Previous Research Reference</label>
            <input
              type="text"
              value={form.continuation_ref}
              onChange={(e) => updateField("continuation_ref", e.target.value)}
              placeholder="Reference of the previous research"
              className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
            />
          </div>
        )}
      </div>

      {/* Contact Information */}
      <div className="bg-white rounded-card border border-gray-200 p-6 shadow-card space-y-5">
        <h2 className="font-heading text-base font-bold text-gray-800 border-b border-gray-100 pb-3">Contact Information</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Mobile Number</label>
            <input
              type="tel"
              value={form.mobile_number}
              onChange={(e) => updateField("mobile_number", e.target.value)}
              placeholder="+63 9XX XXX XXXX"
              className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Institutional Email</label>
            <input
              type="email"
              value={form.institutional_email}
              onChange={(e) => updateField("institutional_email", e.target.value)}
              placeholder="your.email@hau.edu.ph"
              className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
            />
          </div>
        </div>
      </div>

      {/* Authors */}
      <div className="bg-white rounded-card border border-gray-200 p-6 shadow-card space-y-5">
        <div className="flex items-center justify-between border-b border-gray-100 pb-3">
          <h2 className="font-heading text-base font-bold text-gray-800">Researchers / Authors</h2>
          <button
            onClick={addAuthor}
            className="flex items-center gap-1.5 text-sm font-medium text-maroon-700 hover:text-maroon-600 transition-colors"
          >
            <Plus size={16} /> Add Author
          </button>
        </div>

        {errors.authors && (
          <p className="text-xs text-red-500">{errors.authors}</p>
        )}

        <div className="space-y-4">
          {form.authors.map((author, index) => (
            <div key={index} className="border border-gray-100 rounded-card p-4 space-y-3 relative">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-500 uppercase">
                  {author.is_lead ? "Principal Researcher (You)" : `Co-Researcher ${index}`}
                </span>
                {!author.is_lead && (
                  <button
                    onClick={() => removeAuthor(index)}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-gray-600 mb-1">Full Name <span className="text-red-500">*</span></label>
                  <input
                    type="text"
                    value={author.name}
                    onChange={(e) => updateAuthor(index, "name", e.target.value)}
                    disabled={author.is_lead}
                    className="w-full px-3 py-2 rounded-control border border-gray-200 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-maroon-500/30 disabled:opacity-60"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
                  <input
                    type="email"
                    value={author.email}
                    onChange={(e) => updateAuthor(index, "email", e.target.value)}
                    disabled={author.is_lead}
                    className="w-full px-3 py-2 rounded-control border border-gray-200 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-maroon-500/30 disabled:opacity-60"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Affiliation</label>
                <input
                  type="text"
                  value={author.affiliation}
                  onChange={(e) => updateAuthor(index, "affiliation", e.target.value)}
                  className="w-full px-3 py-2 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-maroon-500/30"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Document Upload Placeholder */}
      <div className="bg-white rounded-card border border-gray-200 p-6 shadow-card space-y-4">
        <h2 className="font-heading text-base font-bold text-gray-800 border-b border-gray-100 pb-3">Research Proposal Document</h2>
        <div className="border-2 border-dashed border-gray-200 rounded-card p-8 text-center hover:border-maroon-300 transition-colors cursor-pointer">
          <Upload size={32} className="mx-auto text-gray-400 mb-3" />
          <p className="text-sm font-medium text-gray-600">Click to upload or drag and drop</p>
          <p className="text-xs text-gray-400 mt-1">PDF, DOCX, or DOC (max 50MB)</p>
          <p className="text-xs text-gray-400 mt-2">Document upload will be available after saving the draft</p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pb-8">
        <button
          onClick={() => navigate("/research")}
          className="px-5 py-2.5 rounded-control text-sm font-medium border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={saveDraft}
          disabled={saving || submitting}
          className="px-5 py-2.5 rounded-control text-sm font-semibold border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save as Draft"}
        </button>
        <button
          onClick={() => {
            if (validate()) setShowSubmitConfirm(true);
          }}
          disabled={saving || submitting}
          className="px-5 py-2.5 rounded-control text-sm font-semibold bg-maroon-700 text-white hover:bg-maroon-600 transition-colors disabled:opacity-50"
        >
          Submit Application
        </button>
      </div>

      {/* Submit Confirmation Modal */}
      {showSubmitConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowSubmitConfirm(false)}>
          <div className="bg-white rounded-modal p-6 w-full max-w-md shadow-modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-heading text-lg font-bold mb-2">Submit Research Application?</h3>
            <p className="text-sm text-gray-600 mb-6">
              Once submitted, this application will be forwarded into the approval workflow. You will not be able to edit it after submission.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowSubmitConfirm(false)}
                className="px-4 py-2 rounded-control text-sm font-medium border border-gray-200 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={submitApplication}
                disabled={submitting}
                className="px-4 py-2 rounded-control text-sm font-semibold text-white bg-maroon-700 hover:bg-maroon-600 disabled:opacity-50"
              >
                {submitting ? "Submitting..." : "Submit Application"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
