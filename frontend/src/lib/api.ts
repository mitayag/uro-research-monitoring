const API_BASE = "/api/v1";

interface ApiOptions {
  method?: string;
  body?: unknown;
  token?: string;
}

interface FileUploadOptions {
  token?: string;
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export async function apiRequest<T = unknown>(
  path: string,
  options: ApiOptions = {}
): Promise<T> {
  const { method = "GET", body, token } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const errBody = await res.json();
      const raw = errBody.detail ?? errBody.message ?? detail;
      if (Array.isArray(raw)) {
        detail = raw
          .map((item: any) => {
            if (typeof item === "string") return item;
            if (item?.msg) {
              const loc = Array.isArray(item.loc) ? item.loc.filter((l: any) => l !== "body").join(".") : "";
              return loc ? `${loc}: ${item.msg}` : item.msg;
            }
            if (item?.message) return item.message;
            return JSON.stringify(item);
          })
          .join("; ");
      } else if (typeof raw === "string") {
        detail = raw;
      } else {
        detail = String(raw);
      }
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  return res.json();
}

export async function fileUploadRequest<T = unknown>(
  path: string,
  formData: FormData,
  options: FileUploadOptions = {}
): Promise<T> {
  const { token } = options;

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const errBody = await res.json();
      const raw = errBody.detail ?? errBody.message ?? detail;
      if (Array.isArray(raw)) {
        detail = raw
          .map((item: any) => {
            if (typeof item === "string") return item;
            if (item?.msg) {
              const loc = Array.isArray(item.loc) ? item.loc.filter((l: any) => l !== "body").join(".") : "";
              return loc ? `${loc}: ${item.msg}` : item.msg;
            }
            if (item?.message) return item.message;
            return JSON.stringify(item);
          })
          .join("; ");
      } else if (typeof raw === "string") {
        detail = raw;
      } else {
        detail = String(raw);
      }
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  return res.json();
}
