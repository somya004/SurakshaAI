import axios from "axios";

const configuredBaseUrl =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";

const normalizedBaseUrl = configuredBaseUrl.replace(/\/$/, "");
const apiBaseUrl = normalizedBaseUrl.endsWith("/api/v1")
  ? normalizedBaseUrl
  : `${normalizedBaseUrl}/api/v1`;

const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

export default apiClient;
