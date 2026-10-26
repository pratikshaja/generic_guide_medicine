const API = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export async function analyzePrescription({ mode, text, file }) {
  const url = `${API}/api/analyze/`;
  let response;
  try {
    if (mode === "image") {
      const form = new FormData();
      form.append("image", file);
      response = await fetch(url, { method: "POST", body: form });
    } else {
      response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
    }
  } catch {
    throw new Error(`Can't reach the server at ${API}. Check that the backend is running.`);
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 429) throw new Error("Too many requests. Wait a few minutes and try again.");
    throw new Error(body?.error || `The server returned an error (${response.status}).`);
  }
  return body;
}
