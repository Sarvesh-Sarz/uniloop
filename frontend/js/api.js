/**
 * Uniloop Central API Client & Utilities
 * Uses Vanilla Fetch API with JWT handling and Toast Notifications.
 */

const API = {
  // Token & User session management
  getToken() {
    return localStorage.getItem("Uniloop_token");
  },

  setSession(token, user) {
    localStorage.setItem("Uniloop_token", token);
    localStorage.setItem("Uniloop_user", JSON.stringify(user));
  },

  getUser() {
    const raw = localStorage.getItem("Uniloop_user");
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  clearSession() {
    localStorage.removeItem("Uniloop_token");
    localStorage.removeItem("Uniloop_user");
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  isAdmin() {
    const user = this.getUser();
    return user && user.role === "admin";
  },

  // Central fetch wrapper
  async request(endpoint, options = {}) {
    const token = this.getToken();
    const headers = {
      ...(options.headers || {})
    };

    // If body is not FormData, default to application/json
    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(endpoint, config);

      // Handle 401 Unauthorized
      if (response.status === 401) {
        // If not on login/register page, clear session and optionally redirect
        if (!window.location.pathname.includes("login.html") && !window.location.pathname.includes("register.html")) {
          this.clearSession();
          // Avoid redirecting if checking auth state
          if (endpoint !== "/api/auth/me") {
            window.location.href = "/login.html?expired=1";
          }
        }
      }

      // Parse JSON or text
      const contentType = response.headers.get("content-type") || "";
      let data = null;
      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorMsg = data && data.detail ? data.detail : `Error ${response.status}: Request failed`;
        throw new Error(typeof errorMsg === "string" ? errorMsg : JSON.stringify(errorMsg));
      }

      return data;
    } catch (err) {
      console.error("API Error:", err);
      throw err;
    }
  }
};

/**
 * Toast Notification System
 */
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const icon = type === "success" ? "✓" : type === "error" ? "✕" : "ℹ";
  toast.innerHTML = `<span style="font-weight: 700; font-size: 1.1rem;">${icon}</span> <span>${message}</span>`;

  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.add("show");
  });

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/**
 * UI Formatting Utilities
 */
function formatCurrency(amount) {
  if (amount === 0 || amount === 0.0) return "Free";
  return `₹${parseFloat(amount).toFixed(0)}`;
}

function formatDate(dateStr) {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function getTrustBadgeHtml(score) {
  let color = "#10b981";
  let label = "Highly Reliable";

  if (score >= 80) {
    color = "#10b981";
    label = "Highly Reliable";
  } else if (score >= 60) {
    color = "#3b82f6";
    label = "Reliable";
  } else if (score >= 40) {
    color = "#f59e0b";
    label = "Building Trust";
  } else {
    color = "#ef4444";
    label = "Low Trust";
  }

  return `
    <span class="trust-badge" title="${label}: ${score}/100">
      <span class="trust-dot" style="background-color: ${color};"></span>
      <span>${score}/100 • ${label}</span>
    </span>
  `;
}

function getStatusBadgeHtml(status) {
  const map = {
    "ACTIVE": { cls: "badge-primary", label: "Active Rental" },
    "REQUESTED": { cls: "badge-warning", label: "Requested" },
    "APPROVED": { cls: "badge-primary", label: "Approved" },
    "RETURN_REQUESTED": { cls: "badge-warning", label: "Return Submitted" },
    "COMPLETED": { cls: "badge-success", label: "Completed" },
    "OVERDUE": { cls: "badge-danger", label: "Overdue" },
    "DISPUTED": { cls: "badge-danger", label: "Disputed" },
    "REJECTED": { cls: "badge-secondary", label: "Declined" },
    "available": { cls: "badge-success", label: "Available" },
    "rented": { cls: "badge-warning", label: "Currently Rented" },
    "removed": { cls: "badge-secondary", label: "Removed" }
  };

  const item = map[status] || { cls: "badge-secondary", label: status };
  return `<span class="badge ${item.cls}">${item.label}</span>`;
}
