export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, { headers: { Accept: "application/json", "Content-Type": "application/json", ...options.headers }, ...options });
  if (!response.ok) { const payload = await response.json().catch(() => null); throw new Error(payload?.detail ?? `Request failed (${response.status})`); }
  return response.json();
}
export const getDashboard = (signal) => request("/api/dashboard", { signal });
export const getEvents = (signal) => request("/api/events", { signal });
export const getAnalytics = (signal) => request("/api/analytics?history_limit=60", { signal });
export const getDevices = (signal) => request("/api/devices", { signal });
export const getBooks = (signal) => request("/api/books", { signal });
export const getStudents = (signal) => request("/api/students", { signal });
export const getLoans = (signal) => request("/api/loans", { signal });
export const post = (path, body) => request(path, { method: "POST", body: JSON.stringify(body) });
export const identifyStudent = (text, confidence) => post("/api/students/identify", { text, confidence });
export const identifyBook = (code) => post("/api/books/identify", { code });
export const issueLoan = (student_code, book_code) => post("/api/loans/issue", { student_code, book_code });
export const returnLoan = (book_code) => post("/api/loans/return", { book_code });
