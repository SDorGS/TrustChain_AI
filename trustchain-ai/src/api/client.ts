const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://trustchain-ai-avzs.onrender.com/api/v1";;

async function request(path: string, options: RequestInit) {
  const res = await fetch(`${API_BASE_URL}${path}`, options);

  if (!res.ok) {
    const error = await res.json().catch(() => ({
      detail: `HTTP ${res.status}`,
    }));
    throw new Error(error.detail ?? `Request failed with status ${res.status}`);
  }

  return res.json();
}

export const api = {
  post: (path: string, body: FormData | Record<string, unknown>, options?: RequestInit) => {
    const isFormData = body instanceof FormData;

    return request(path, {
      method: "POST",
      headers: isFormData ? undefined : { "Content-Type": "application/json" },
      body: isFormData ? body : JSON.stringify(body),
      ...options,
    });
  },
  get: (path: string) => request(path, { method: "GET" }),
};

export const runVerification = async (formData: FormData) => {
  return api.post("/verify/run", formData);
};
