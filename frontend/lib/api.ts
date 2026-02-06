const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("token") || "";
}

async function request(path: string, options: RequestInit = {}) {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
        Authorization: getToken() ? `Bearer ${getToken()}` : "",
      },
    });
  } catch {
    throw new Error("Network error. Please try again.");
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let detail = "";
    try {
      const data = text ? JSON.parse(text) : {};
      detail = data.detail || "";
    } catch {
      detail = text;
    }

    if (res.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
      }
      throw new Error("Session expired. Please log in again.");
    }

    throw new Error(detail || "Request failed");
  }

  return res.json();
}

async function requestForm(path: string, formData: FormData) {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      body: formData,
      headers: {
        ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      },
    });
  } catch {
    throw new Error("Network error. Please try again.");
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let detail = "";
    try {
      const data = text ? JSON.parse(text) : {};
      detail = data.detail || "";
    } catch {
      detail = text;
    }

    if (res.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
      }
      throw new Error("Session expired. Please log in again.");
    }

    throw new Error(detail || "Request failed");
  }

  return res.json();
}

export async function apiSignup(email: string, password: string) {
  const data = await request("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return data.access_token as string;
}

export async function apiLogin(email: string, password: string) {
  const data = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return data.access_token as string;
}

export async function apiGenerate(prompt: string, preset: string) {
  return request("/brochures/generate", {
    method: "POST",
    body: JSON.stringify({ prompt, preset }),
  });
}

export async function apiGenerateWithHero(prompt: string, heroFile: File, preset: string) {
  const form = new FormData();
  form.append("prompt", prompt);
  form.append("preset", preset);
  form.append("hero_file", heroFile);
  return requestForm("/brochures/generate", form);
}

export async function apiEdit(brochureId: number, instruction: string) {
  return request(`/brochures/${brochureId}/edit`, {
    method: "POST",
    body: JSON.stringify({ instruction }),
  });
}

export async function apiUploadGallery(brochureId: number, files: File[]) {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  return requestForm(`/brochures/${brochureId}/assets/gallery`, form);
}

export async function apiUpdateContact(
  brochureId: number,
  payload: { email?: string; phone?: string; website?: string; address?: string },
) {
  return request(`/brochures/${brochureId}/contact`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function apiHistory() {
  return request("/brochures/my", { method: "GET" });
}
