/**
 * DocMind API Client
 * Handles all communication with the FastAPI backend.
 * Token is stored in localStorage (also set as httpOnly cookie by server).
 */

const API = (() => {
  const BASE = '';  // Same origin

  function getToken() {
    return localStorage.getItem('dm_token');
  }

  function setToken(token) {
    localStorage.setItem('dm_token', token);
  }

  function clearToken() {
    localStorage.removeItem('dm_token');
    localStorage.removeItem('dm_user');
  }

  function getUser() {
    try { return JSON.parse(localStorage.getItem('dm_user') || 'null'); }
    catch { return null; }
  }

  function setUser(user) {
    localStorage.setItem('dm_user', JSON.stringify(user));
  }

  async function request(method, path, body = null, isFormData = false) {
    const headers = {};
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (!isFormData && body) headers['Content-Type'] = 'application/json';

    const opts = { method, headers, credentials: 'include' };
    if (body) {
      opts.body = isFormData ? body : JSON.stringify(body);
    }

    const res = await fetch(BASE + path, opts);

    if (res.status === 401) {
      clearToken();
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    const data = res.headers.get('content-type')?.includes('application/json')
      ? await res.json()
      : await res.text();

    if (!res.ok) {
      throw new Error(data?.detail || data || `HTTP ${res.status}`);
    }

    return data;
  }

  return {
    getToken, setToken, clearToken, getUser, setUser,

    // ── Auth ──────────────────────────────────────────────────────────────
    async register(payload) {
      const data = await request('POST', '/api/auth/register', payload);
      return data;
    },

    async login(email, password) {
      const data = await request('POST', '/api/auth/login', { email, password });
      if (data.access_token) {
        setToken(data.access_token);
        setUser(data.user);
      }
      return data;
    },

    async logout() {
      await request('POST', '/api/auth/logout').catch(() => {});
      clearToken();
      window.location.href = '/login';
    },

    async getMe() {
      return request('GET', '/api/users/me');
    },

    // ── Files ─────────────────────────────────────────────────────────────
    async uploadFiles(fileList) {
      const fd = new FormData();
      for (const file of fileList) fd.append('files', file);
      return request('POST', '/api/files/upload', fd, true);
    },

    async getFiles(params = {}) {
      const qs = new URLSearchParams();
      if (params.category && params.category !== 'all') qs.set('category', params.category);
      if (params.search) qs.set('search', params.search);
      if (params.status) qs.set('status', params.status);
      return request('GET', `/api/files?${qs}`);
    },

    async deleteFile(fileId) {
      return request('DELETE', `/api/files/${fileId}`);
    },

    async updateFileCategory(fileId, category) {
      return request('PATCH', `/api/files/${fileId}/category`, { category });
    },

    getDownloadUrl(fileId) {
      return `/api/files/${fileId}/download`;
    },

    // ── Chatbots ──────────────────────────────────────────────────────────
    async buildChatbot(payload) {
      return request('POST', '/api/chatbots', payload);
    },

    async getChatbots() {
      return request('GET', '/api/chatbots');
    },

    async getChatbot(botId) {
      return request('GET', `/api/chatbots/${botId}`);
    },

    async updateChatbot(botId, payload) {
      return request('PATCH', `/api/chatbots/${botId}`, payload);
    },

    async deleteChatbot(botId) {
      return request('DELETE', `/api/chatbots/${botId}`);
    },

    async sendMessage(botId, question, history = []) {
      return request('POST', `/api/chatbots/${botId}/chat`, { question, history });
    },

    async getChatHistory(botId) {
      return request('GET', `/api/chatbots/${botId}/history`);
    },

    async clearHistory(botId) {
      return request('DELETE', `/api/chatbots/${botId}/history`);
    },

    // ── Users ─────────────────────────────────────────────────────────────
    async getStats() {
      return request('GET', '/api/users/me/stats');
    },

    async updateProfile(payload) {
      return request('PATCH', '/api/users/me', payload);
    },

    async changePassword(payload) {
      return request('POST', '/api/users/me/password', payload);
    },

    async updatePreferences(payload) {
      return request('PATCH', '/api/users/me/preferences', payload);
    },

    async getApiKeys() {
      return request('GET', '/api/users/me/api-keys');
    },

    async createApiKey(name) {
      return request('POST', `/api/users/me/api-keys?name=${encodeURIComponent(name)}`);
    },

    async revokeApiKey(keyId) {
      return request('DELETE', `/api/users/me/api-keys/${keyId}`);
    },

    async deleteAccount() {
      return request('DELETE', '/api/users/me');
    },
  };
})();

// ── UI Utilities ──────────────────────────────────────────────────────────────

function showToast(message, type = 'success', duration = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;';
    document.body.appendChild(container);
  }

  const colors = {
    success: { bg: 'rgba(16,185,129,0.15)', border: '#10b981', icon: '✓' },
    error: { bg: 'rgba(239,68,68,0.15)', border: '#ef4444', icon: '✕' },
    info: { bg: 'rgba(0,229,255,0.1)', border: '#00e5ff', icon: 'ℹ' },
    warning: { bg: 'rgba(245,158,11,0.15)', border: '#f59e0b', icon: '⚠' },
  };
  const c = colors[type] || colors.info;

  const toast = document.createElement('div');
  toast.style.cssText = `
    display:flex;align-items:center;gap:10px;
    padding:12px 16px;border-radius:2px;
    background:${c.bg};border:1px solid ${c.border};
    font-family:'Syne',sans-serif;font-size:13px;color:#e2e8f0;
    min-width:260px;max-width:380px;
    box-shadow:0 8px 24px rgba(0,0,0,0.4);
    animation:slideIn 0.25s ease;
  `;
  toast.innerHTML = `<span style="color:${c.border};font-weight:700;">${c.icon}</span><span>${message}</span>`;

  if (!document.getElementById('toast-style')) {
    const s = document.createElement('style');
    s.id = 'toast-style';
    s.textContent = `@keyframes slideIn{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}@keyframes slideOut{from{opacity:1;transform:translateX(0)}to{opacity:0;transform:translateX(20px)}}`;
    document.head.appendChild(s);
  }

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.25s ease forwards';
    setTimeout(() => toast.remove(), 250);
  }, duration);
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB';
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function requireAuth() {
  if (!API.getToken()) {
    window.location.href = '/login';
    return false;
  }
  return true;
}

function populateUserUI() {
  const user = API.getUser();
  if (!user) return;
  document.querySelectorAll('[data-user-name]').forEach(el => el.textContent = user.full_name || user.email);
  document.querySelectorAll('[data-user-initials]').forEach(el => el.textContent = user.initials || '??');
  document.querySelectorAll('[data-user-plan]').forEach(el => el.textContent = (user.plan || 'free').toUpperCase() + ' TIER');
  document.querySelectorAll('[data-user-email]').forEach(el => el.textContent = user.email);
}
