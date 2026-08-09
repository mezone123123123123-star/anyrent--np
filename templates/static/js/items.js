/* ============================================================
   AnyRent — Marketplace
   Item data now comes from the Flask server (window.ITEMS).
   Renting, messaging and saving are real actions.
   ============================================================ */

const items = window.ITEMS || [];
const savedIds = window.SAVED || [];
const LOGGED_IN = window.LOGGED_IN === true;
const LOGIN_URL = window.LOGIN_URL || '/auth';

const DEFAULT_IMAGE =
    "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&w=900&q=80";

const savedSet = new Set(savedIds.map(String));

const categoryIcons = {
    Camera: 'fa-camera',
    Music: 'fa-guitar',
    Bike: 'fa-bicycle',
    Electronics: 'fa-laptop',
    Other: 'fa-box',
};

let currentCategory = 'All';

/* =====================================================
   HELPERS
   ===================================================== */

function formatPrice(price) {
    return Number(price || 0).toLocaleString('en-IN');
}

function escapeHtml(text) {
    return String(text || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function requireLogin() {
    if (!LOGGED_IN) {
        location.href = LOGIN_URL;
        return false;
    }
    return true;
}

/* =====================================================
   CREATE CARD
   ===================================================== */

function createCard(item) {
    const icon = categoryIcons[item.category] || 'fa-box';
    const saved = savedSet.has(String(item.id));
    const heartIcon = saved ? 'fa-solid' : 'fa-regular';

    return `
        <article class="item-card" onclick="openItem(${item.id})">
            <div class="item-card-image">
                <img
                    src="${escapeHtml(item.image || DEFAULT_IMAGE)}"
                    alt="${escapeHtml(item.name)}"
                    onerror="this.onerror=null;this.src='${DEFAULT_IMAGE}';"
                >
                <span class="item-category">
                    <i class="fa-solid ${icon}"></i>
                    ${escapeHtml(item.category)}
                </span>
                <span class="available">● Available</span>
                <button
                    class="save-btn ${saved ? 'saved' : ''}"
                    title="${saved ? 'Remove from saved' : 'Save item'}"
                    onclick="event.stopPropagation(); toggleSave(${item.id})"
                    aria-label="${saved ? 'Remove from saved' : 'Save item'}"
                >
                    <i class="${heartIcon} fa-heart"></i>
                </button>
            </div>
            <div class="item-card-content">
                <h3 class="item-card-title">${escapeHtml(item.name)}</h3>
                <div class="item-location">
                    <i class="fa-solid fa-location-dot"></i>
                    ${escapeHtml(item.location)}
                </div>
                <div class="card-bottom">
                    <div class="item-price">
                        Rs ${formatPrice(item.price)}
                        <span>/ day</span>
                    </div>
                    <button class="item-arrow" onclick="event.stopPropagation(); openItem(${item.id})">
                        <i class="fa-solid fa-arrow-right"></i>
                    </button>
                </div>
            </div>
        </article>
    `;
}

/* =====================================================
   DISPLAY ITEMS
   ===================================================== */

function renderItems(list) {
    const grid = document.getElementById('itemGrid');
    grid.innerHTML = '';

    if (!list.length) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-magnifying-glass"></i>
                <h3>Nothing found</h3>
                <p>Try another search or category.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = list.map(createCard).join('');
}

function currentFiltered() {
    const query = (document.getElementById('searchInput')?.value || '')
        .toLowerCase().trim();

    return items.filter(item => {
        const categoryMatch = currentCategory === 'All' || item.category === currentCategory;
        if (!categoryMatch) return false;

        if (!query) return true;

        const haystack = [
            item.name,
            item.category,
            item.type,
            item.location,
            item.seller,
        ].join(' ').toLowerCase();

        return haystack.includes(query);
    });
}

function searchItems() {
    renderItems(currentFiltered());
}

function sortItems() {
    const sort = document.getElementById('sortSelect').value;
    const list = currentFiltered();

    if (sort === 'low') list.sort((a, b) => a.price - b.price);
    if (sort === 'high') list.sort((a, b) => b.price - a.price);

    renderItems(list);
}

function filterCategory(category, button) {
    currentCategory = category;

    document.querySelectorAll('.category').forEach(btn => {
        btn.classList.toggle('active', btn === button);
    });

    searchItems();
}

/* =====================================================
   OPEN ITEM / DETAILS
   ===================================================== */

function openItem(id) {
    const item = items.find(product => product.id === id);
    if (!item) return;

    const details = document.getElementById('itemDetails');
    const content = document.getElementById('detailContent');

    details.classList.remove('hidden');

    content.innerHTML = `
        <div class="detail-layout">
            <div>
                <img
                    src="${escapeHtml(item.image || DEFAULT_IMAGE)}"
                    class="detail-image"
                    alt="${escapeHtml(item.name)}"
                    onerror="this.onerror=null;this.src='${DEFAULT_IMAGE}';"
                >
                ${item.video ? `
                    <div class="detail-video-wrap">
                        <span class="detail-video-label"><i class="fa-solid fa-video"></i> Showcase video</span>
                        <video class="detail-video" src="${escapeHtml(item.video)}" controls muted playsinline preload="metadata"></video>
                    </div>
                ` : ''}
            </div>
            <div>
                <span class="detail-category">${escapeHtml(item.category)}</span>
                <h1 class="detail-title">${escapeHtml(item.name)}</h1>
                <div class="detail-location">
                    <i class="fa-solid fa-location-dot"></i>
                    ${escapeHtml(item.location)}
                    &nbsp;&nbsp;
                    <span class="item-rating">⭐ ${item.rating} (${item.reviews} reviews)</span>
                </div>
                <div class="rating-form-row" style="margin-top:8px;margin-bottom:8px;">
                    <form id="rating-form" onsubmit="event.preventDefault(); submitRating(${item.id});" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        <label for="rating-select">Your rating</label>
                        <select id="rating-select" name="rating" style="padding:6px;border-radius:8px;border:1px solid #e6e6e6">
                            <option value="5">5 - Excellent</option>
                            <option value="4">4 - Good</option>
                            <option value="3">3 - Okay</option>
                            <option value="2">2 - Poor</option>
                            <option value="1">1 - Terrible</option>
                        </select>
                        <input id="rating-comment" name="comment" placeholder="Optional comment" style="padding:6px;border-radius:8px;border:1px solid #e6e6e6;min-width:220px"> 
                        <button type="submit" class="btn btn-ghost">Submit</button>
                        <span id="rating-result" style="margin-left:8px;font-weight:700"></span>
                    </form>
                </div>
                <p class="detail-description">${escapeHtml(item.description)}</p>
                <div class="detail-price">
                    Rs ${formatPrice(item.price)}
                    <span>/ day</span>
                </div>
                <div class="security-box">
                    <div class="security-row">
                        <span>Security deposit (listing)</span>
                        <strong>Rs ${formatPrice(item.deposit)}</strong>
                    </div>
                    <div class="security-row">
                        <span>Owner</span>
                        <strong>
                            @${escapeHtml(item.seller)}
                            <i class="fa-solid fa-circle-check" style="color:#2563eb"></i>
                        </strong>
                    </div>
                    <div class="security-row">
                        <span>Availability</span>
                        <strong style="color:#16a34a">Available</strong>
                    </div>
                </div>
                <button class="rent-button" onclick="openRentModal(${item.id})">
                    <i class="fa-solid fa-calendar-check"></i>
                    Rent this item
                </button>
                <button class="message-button" onclick="openMsgModal(${item.id})">
                    <i class="fa-solid fa-envelope"></i>
                    Message the owner
                </button>
                <div class="trust-row">
                    <span><i class="fa-solid fa-shield-halved"></i> Verified owner</span>
                    <span><i class="fa-solid fa-lock"></i> Secure payment</span>
                </div>
                <section class="reviews-section" style="margin-top:14px;">
                    <h3>Reviews</h3>
                    <div id="reviews-list">
                        ${ (item.reviews_list && item.reviews_list.length) ? item.reviews_list.map(r => `
                            <div class="review-item" style="padding:8px 0;border-bottom:1px solid #eee;"> 
                                <strong>${escapeHtml(r.user || 'Anonymous')}</strong>
                                <span style="margin-left:8px;color:#666;">— ⭐ ${r.rating}</span>
                                <div style="margin-top:6px;color:#333;">${escapeHtml(r.comment || '')}</div>
                            </div>
                        `).join('') : '<div class="empty-state"><p>No reviews yet. Be the first to rate this item.</p></div>' }
                    </div>
                </section>
            </div>
        </div>
    `;

    document.getElementById('relatedTitle').innerText = `More ${item.category.toLowerCase()}s`;

    const relatedGrid = document.getElementById('relatedGrid');
    const related = items.filter(product =>
        product.category === item.category && product.id !== item.id);

    relatedGrid.innerHTML = related.length
        ? related.map(createCard).join('')
        : '<div class="empty-state"><p>No other items in this category yet.</p></div>';

    details.scrollIntoView({ behavior: 'smooth' });
}

function closeDetails() {
    document.getElementById('itemDetails').classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* =====================================================
   SAVE / UNSAVE
   ===================================================== */

function toggleSave(id) {
    if (!requireLogin()) return;

    const item = items.find(product => product.id === id);
    if (!item) return;

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/items/${id}/save`;
    document.body.appendChild(form);
    form.submit();
}

/* =====================================================
   RENT MODAL
   ===================================================== */

function openRentModal(id) {
    if (!requireLogin()) return;

    const item = items.find(product => product.id === id);
    if (!item) return;

    document.getElementById('rentItemId').value = item.id;
    document.getElementById('rentItemLine').textContent =
        `${item.name} · Rs ${formatPrice(item.price)}/day · deposit Rs ${formatPrice(item.deposit)}`;

    const start = document.getElementById('rentStart');
    const end = document.getElementById('rentEnd');
    const today = new Date().toISOString().split('T')[0];

    start.min = today;
    end.min = today;
    start.value = '';
    end.value = '';
    document.getElementById('rentTotal').textContent = '';

    start.onchange = function () {
        end.min = start.value || today;
        updateRentTotal(item);
    };
    end.onchange = function () {
        updateRentTotal(item);
    };

    document.getElementById('rentModal').classList.add('open');
}

function updateRentTotal(item) {
    const start = document.getElementById('rentStart').value;
    const end = document.getElementById('rentEnd').value;
    const totalEl = document.getElementById('rentTotal');

    if (!start || !end) {
        totalEl.textContent = '';
        return;
    }

    const d1 = new Date(start);
    const d2 = new Date(end);
    const days = Math.round((d2 - d1) / 86400000) + 1;

    if (days < 1) {
        totalEl.textContent = 'Return date must be after the start date.';
        return;
    }

    const total = item.price * days;
    const deposit = Math.round(total * 0.20); // 20% of total
    const adminCommission = Math.round(deposit * 0.15); // 15% of deposit to admin

    totalEl.innerHTML =
        `<strong>Rs ${formatPrice(total)}</strong> total for ${days} day${days > 1 ? 's' : ''}`
        + `<span> · Deposit (20%): Rs ${formatPrice(deposit)} (admin commission: Rs ${formatPrice(adminCommission)})</span>`;
}

function closeRentModal() {
    document.getElementById('rentModal').classList.remove('open');
}

/* =====================================================
   MESSAGE MODAL
   ===================================================== */

function openMsgModal(id) {
    if (!requireLogin()) return;

    const item = items.find(product => product.id === id);
    if (!item) return;

    document.getElementById('msgItemId').value = item.id;
    document.getElementById('msgItemLine').textContent = `To @${item.seller} about ${item.name}`;
    document.getElementById('msgBody').value = '';

    const msgForm = document.getElementById('msgForm');
    msgForm.action = `/items/${item.id}/message`;

    document.getElementById('msgModal').classList.add('open');
}

function closeMsgModal() {
    document.getElementById('msgModal').classList.remove('open');
}

/* =====================================================
   CLOSE MODALS (outside click / escape)
   ===================================================== */

document.addEventListener('click', function (event) {
    if (event.target.classList.contains('rent-modal')) {
        event.target.classList.remove('open');
    }
});

document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        closeRentModal();
        closeMsgModal();
    }
});

/* =====================================================
   INITIAL LOAD
   ===================================================== */

renderItems(items);
