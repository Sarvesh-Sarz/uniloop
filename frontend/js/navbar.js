/**
 * Uniloop Universal Navigation & Notification Handler
 */

document.addEventListener("DOMContentLoaded", () => {
  renderNavbar();
  if (API.isAuthenticated()) {
    initNotifications();
  }
});

function renderNavbar() {
  const mount = document.getElementById("navbar-placeholder");
  if (!mount) return;

  const user = API.getUser();
  const isAuth = API.isAuthenticated();
  const isAdmin = isAuth && user && user.role === "admin";
  const path = window.location.pathname;

  const html = `
    <nav class="navbar">
      <div class="container nav-container">
        <!-- Logo -->
        <a href="/index.html" class="brand-logo">
          <div class="brand-badge">⚡</div>
          <div>Uniloop<span class="accent"></span></div>
        </a>

        <!-- Desktop Navigation Links -->
        <ul class="nav-links" id="nav-links">
          <li><a href="/marketplace.html" class="nav-link ${path.includes('marketplace.html') ? 'active' : ''}">Explore Marketplace</a></li>
          <li><a href="/marketplace.html?semester=1" class="nav-link">Semester Resources</a></li>
          ${isAuth ? `
            <li><a href="/create-listing.html" class="nav-link ${path.includes('create-listing.html') ? 'active' : ''}">+ List an Item</a></li>
            <li><a href="/rentals.html" class="nav-link ${path.includes('rentals.html') ? 'active' : ''}">My Rentals</a></li>
            <li><a href="/messages.html" class="nav-link ${path.includes('messages.html') ? 'active' : ''}">Messages</a></li>
            <li><a href="/dashboard.html" class="nav-link ${path.includes('dashboard.html') ? 'active' : ''}">Dashboard</a></li>
            ${isAdmin ? `<li><a href="/admin.html" class="nav-link ${path.includes('admin.html') ? 'active' : ''}" style="color: var(--danger); font-weight: 700;">Admin Panel</a></li>` : ''}
          ` : ''}
        </ul>

        <!-- Right Actions -->
        <div class="nav-actions">
          ${isAuth ? `
            <!-- Notifications Bell -->
            <div class="notif-wrapper">
              <button class="notif-btn" id="notif-btn" title="Notifications">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                  <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
                <span class="notif-badge" id="notif-count-badge" style="display: none;">0</span>
              </button>

              <!-- Notifications Dropdown -->
              <div class="notif-dropdown" id="notif-dropdown">
                <div class="notif-header">
                  <span>Notifications</span>
                  <button id="mark-all-read-btn" style="background:none; border:none; color:var(--primary); font-size:0.75rem; cursor:pointer; font-weight:600;">Mark all read</button>
                </div>
                <div class="notif-list" id="notif-list">
                  <div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">Loading notifications...</div>
                </div>
              </div>
            </div>

            <!-- User Menu Chip -->
            <div style="position: relative;">
              <button class="user-menu-btn" id="user-menu-toggle">
                <div class="user-avatar">${user.name ? user.name.charAt(0).toUpperCase() : 'U'}</div>
                <span>${user.name ? user.name.split(' ')[0] : 'Account'}</span>
                <span style="font-size: 0.7rem; color: var(--text-muted);">▼</span>
              </button>

              <!-- Dropdown Menu -->
              <div class="notif-dropdown" id="user-dropdown-menu" style="width: 200px; right: 0;">
                <div style="padding: 0.85rem 1rem; border-bottom: 1px solid var(--border);">
                  <div style="font-weight: 700; font-size: 0.9rem;">${user.name}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${user.department} • ${user.year}</div>
                  <div style="margin-top: 0.4rem;">${getTrustBadgeHtml(user.trust_score || 50)}</div>
                </div>
                <a href="/profile.html" class="nav-link" style="padding: 0.6rem 1rem; border-radius: 0;">My Profile</a>
                <a href="/wishlist.html" class="nav-link" style="padding: 0.6rem 1rem; border-radius: 0;">Saved Items (Wishlist)</a>
                <a href="/dashboard.html" class="nav-link" style="padding: 0.6rem 1rem; border-radius: 0;">Student Dashboard</a>
                <button id="logout-btn" style="width: 100%; text-align: left; padding: 0.6rem 1rem; background: none; border: none; border-top: 1px solid var(--border); color: var(--danger); font-weight: 600; cursor: pointer; font-size: 0.85rem;">
                  Sign Out
                </button>
              </div>
            </div>
          ` : `
            <!-- Public Auth Buttons -->
            <a href="/login.html" class="btn btn-secondary btn-sm">Log In</a>
            <a href="/register.html" class="btn btn-primary btn-sm">Sign Up</a>
          `}

          <!-- Mobile Hamburger Toggle -->
          <button class="mobile-toggle" id="mobile-toggle" aria-label="Toggle Menu">
            ☰
          </button>
        </div>
      </div>
    </nav>
  `;

  mount.innerHTML = html;

  // Event Listeners
  const mobileToggle = document.getElementById("mobile-toggle");
  const navLinks = document.getElementById("nav-links");
  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener("click", () => {
      navLinks.classList.toggle("open");
    });
  }

  const userToggle = document.getElementById("user-menu-toggle");
  const userDropdown = document.getElementById("user-dropdown-menu");
  if (userToggle && userDropdown) {
    userToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle("show");
      const notifDrop = document.getElementById("notif-dropdown");
      if (notifDrop) notifDrop.classList.remove("show");
    });
  }

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      API.clearSession();
      showToast("You have been signed out.", "info");
      setTimeout(() => {
        window.location.href = "/login.html";
      }, 500);
    });
  }

  // Close menus when clicking outside
  document.addEventListener("click", () => {
    if (userDropdown) userDropdown.classList.remove("show");
    const notifDrop = document.getElementById("notif-dropdown");
    if (notifDrop) notifDrop.classList.remove("show");
  });
}

function initNotifications() {
  const notifBtn = document.getElementById("notif-btn");
  const notifDrop = document.getElementById("notif-dropdown");
  const badge = document.getElementById("notif-count-badge");
  const markAllBtn = document.getElementById("mark-all-read-btn");

  if (!notifBtn || !notifDrop) return;

  notifBtn.addEventListener("click", async (e) => {
    e.stopPropagation();
    notifDrop.classList.toggle("show");
    const userDrop = document.getElementById("user-dropdown-menu");
    if (userDrop) userDrop.classList.remove("show");

    if (notifDrop.classList.contains("show")) {
      await loadNotificationsList();
    }
  });

  if (markAllBtn) {
    markAllBtn.addEventListener("click", async () => {
      try {
        await API.request("/api/notifications/read-all", { method: "PUT" });
        if (badge) badge.style.display = "none";
        await loadNotificationsList();
        showToast("All notifications marked as read.", "success");
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  }

  // Poll unread count
  fetchUnreadCount();
  setInterval(fetchUnreadCount, 30000);
}

async function fetchUnreadCount() {
  const badge = document.getElementById("notif-count-badge");
  if (!badge || !API.isAuthenticated()) return;

  try {
    const res = await API.request("/api/notifications/unread-count");
    if (res.unread_count > 0) {
      badge.textContent = res.unread_count;
      badge.style.display = "block";
    } else {
      badge.style.display = "none";
    }
  } catch (err) {
    // Silent catch for background polling
  }
}

async function loadNotificationsList() {
  const listEl = document.getElementById("notif-list");
  if (!listEl) return;

  try {
    const notifs = await API.request("/api/notifications");
    if (notifs.length === 0) {
      listEl.innerHTML = `<div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">No notifications yet.</div>`;
      return;
    }

    listEl.innerHTML = notifs.map(n => `
      <div class="notif-item ${!n.is_read ? 'unread' : ''}" onclick="handleNotifClick(${n.id}, '${n.link || ''}')">
        <div class="notif-title">${n.title}</div>
        <div>${n.message}</div>
        <div class="notif-time">${formatDate(n.created_at)}</div>
      </div>
    `).join("");
  } catch (err) {
    listEl.innerHTML = `<div style="padding: 1rem; color: var(--danger); font-size: 0.85rem;">Failed to load notifications.</div>`;
  }
}

async function handleNotifClick(notifId, link) {
  try {
    await API.request(`/api/notifications/${notifId}/read`, { method: "PUT" });
  } catch (e) {
    // Continue navigation regardless
  }
  if (link) {
    window.location.href = link;
  }
}
