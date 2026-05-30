/**
 * Centralised API base URL.
 *
 * In development (npm start) set REACT_APP_API_URL in .env.local:
 *   REACT_APP_API_URL=http://localhost:8000
 *
 * In production (Azure App Service) the React app is served from the same
 * origin as the API, so an empty string (same-origin) works automatically.
 */
const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

export default API_BASE;
