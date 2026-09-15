// Shared auth helpers for every authenticated page. Tokens live in
// localStorage, standard practice for a JWT-in-header API like this one;
// an httpOnly cookie would be a reasonable future hardening step, but
// isn't needed to get a real, working login flow shipped today.
const TOKEN_KEY = "attachify_access_token";
const REFRESH_KEY = "attachify_refresh_token";

function getAccessToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setTokens(access, refresh) {
    localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

function clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
}

function isLoggedIn() {
    return !!getAccessToken();
}

function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = "/login";
    }
}

// Wrapper around fetch that attaches the bearer token and redirects to
// /login on a 401, so every authenticated page doesn't need to repeat that
// handling itself.
async function apiFetch(path, options = {}) {
    const token = getAccessToken();
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const response = await fetch(`/api/v1${path}`, { ...options, headers });
    if (response.status === 401) {
        clearTokens();
        window.location.href = "/login";
        throw new Error("Not authenticated");
    }
    return response;
}
