// static/js/inventory.js
// Improved inventory script: uses window.INITIAL_* where available, otherwise calls /api/*
// Put this file at app/static/js/inventory.js

// ---------- State ----------
let toolsData = [];       // array of tool objects (server shape: serialize_tool)
let categoriesData = [];
let employeesData = [];
let movementsData = [];

let currentView = 'grid';
let currentPage = 1;
const itemsPerPage = 12;
let filteredTools = [];

// ---------- DOM refs (safe) ----------
const $ = id => document.getElementById(id);
const toolsGrid = $('toolsGrid');
const toolsList = $('toolsList');
const toolsTableBody = $('toolsTableBody');
const gridViewBtn = $('gridView');
const listViewBtn = $('listView');
const filterSection = $('filterSection');
const filterToggle = $('filterToggle');
const addToolBtn = $('addToolBtn');
const addCategoryBtn = $('addCategoryBtn');
const addToolModal = $('addToolModal');
const addCategoryModal = $('addCategoryModal');
const toolDetailModal = $('toolDetailModal');
const categoryFilter = $('categoryFilter');
const employeeFilter = $('employeeFilter');
const searchInput = $('search');
const statusFilter = $('statusFilter');
const dateAddedFilter = $('dateAddedFilter');
const applyFiltersBtn = $('applyFilters');
const clearFiltersBtn = $('clearFilters');
const toolCategorySelect = $('toolCategory');
const toolPhotoInput = $('toolPhoto');
const photoPreview = $('photoPreview');
const previewImage = $('previewImage');
const submitToolBtn = $('submitTool');
const cancelAddToolBtn = $('cancelAddTool');
const submitCategoryBtn = $('submitCategory');
const cancelAddCategoryBtn = $('cancelAddCategory');
const closeToolDetailBtn = $('closeToolDetail');
const prevPageBtn = $('prev-page');
const nextPageBtn = $('next-page');

// Defensive: some elements may not exist on every page
const safeAddEvent = (el, ev, fn) => { if (el) el.addEventListener(ev, fn); };

// ---------- Utilities ----------
function debounce(fn, wait = 250) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), wait);
    };
}

function isoToDate(str) {
    if (!str) return null;
    return new Date(str);
}

function formatDate(d) {
    if (!d) return '—';
    const dt = (d instanceof Date) ? d : new Date(d);
    return dt.toISOString().slice(0, 10);
}

function placeholderImage() {
    // small inline SVG placeholder (100x100)
    return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 24 24" fill="none" stroke="%23777" stroke-width="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M8 10h8M8 14h8" stroke-linecap="round"/></svg>';
}

// ---------- Event wiring ----------
safeAddEvent(gridViewBtn, 'click', () => switchView('grid'));
safeAddEvent(listViewBtn, 'click', () => switchView('list'));
safeAddEvent(filterToggle, 'click', toggleFilterSection);
safeAddEvent(addToolBtn, 'click', showAddToolModal);
safeAddEvent(addCategoryBtn, 'click', showAddCategoryModal);
safeAddEvent(applyFiltersBtn, 'click', applyFilters);
safeAddEvent(clearFiltersBtn, 'click', clearFilters);
safeAddEvent(toolPhotoInput, 'change', handlePhotoPreview);
safeAddEvent(submitToolBtn, 'click', submitToolForm);
safeAddEvent(cancelAddToolBtn, 'click', closeAddToolModal);
safeAddEvent(submitCategoryBtn, 'click', submitCategoryForm);
safeAddEvent(cancelAddCategoryBtn, 'click', closeAddCategoryModal);
safeAddEvent(closeToolDetailBtn, 'click', closeToolDetailModal);
safeAddEvent(prevPageBtn, 'click', (e) => { e.preventDefault(); goToPrevPage(); });
safeAddEvent(nextPageBtn, 'click', (e) => { e.preventDefault(); goToNextPage(); });
if (searchInput) searchInput.addEventListener('input', debounce(() => { applyFilters(); }, 300));

// ---------- Init ----------
document.addEventListener('DOMContentLoaded', init);

async function init() {
    // 1) Try inline initial data
    if (window.INITIAL_RECENT_TOOLS) {
        // server sent serialize_tool objects
        toolsData = window.INITIAL_RECENT_TOOLS.map(normalizeToolFromServer);
    }
    if (window.INITIAL_RECENT_BORROWS) {
        movementsData = window.INITIAL_RECENT_BORROWS;
    }
    if (window.INITIAL_STATS) {
        // optional: display counters immediately (server inlined)
        renderStats(window.INITIAL_STATS);
    }

    // 2) fetch categories & employees (if not present)
    if (!window.INITIAL_CATEGORIES && !categoriesData.length) {
        categoriesData = await fetchJSON('/api/categories');
    } else {
        // if server inlined categories into template (not implemented here), you'd use them
        categoriesData = categoriesData.length ? categoriesData : (window.INITIAL_CATEGORIES || []);
    }
    if (!window.INITIAL_EMPLOYEES && !employeesData.length) {
        employeesData = await fetchJSON('/api/employees');
    } else {
        employeesData = employeesData.length ? employeesData : (window.INITIAL_EMPLOYEES || []);
    }

    // 3) if toolsData empty, fetch first page
    if (!toolsData || toolsData.length === 0) {
        await loadToolsPage(1);
    } else {
        // if inline data provided, ensure filters use it
        filteredTools = [...toolsData];
    }

    // 4) Populate selects and render
    populateFilters();
    updateStats();
    renderTools();

    // Optionally fetch fresh stats in background (non-blocking)
    fetchJSON('/api/stats').then(renderStats).catch(()=>{});
}

// ---------- Fetch helpers ----------
async function fetchJSON(url, opts = {}) {
    try {
        const res = await fetch(url, opts);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error('fetchJSON error', err, url);
        return null;
    }
}

// ---------- Normalization ----------
function normalizeToolFromServer(t) {
    // server shape: date strings; this normalizes to friendly JS object
    return {
        id: t.id,
        name: t.name,
        category_id: t.category_id || t.category || null,
        category: t.category || null,
        loc_row: t.loc_row,
        loc_col: t.loc_col,
        loc_shelf: t.loc_shelf,
        description: t.description,
        date_ajout: t.date_ajout ? new Date(t.date_ajout) : null,
        purchase_date: t.purchase_date ? new Date(t.purchase_date) : null,
        last_maintenance: t.last_maintenance ? new Date(t.last_maintenance) : null,
        last_checked_out: t.last_checked_out ? new Date(t.last_checked_out) : null,
        price: t.price,
        status: t.status,
        photo: t.photo || null
    };
}

// ---------- Pagination / loading ----------
async function loadToolsPage(page = 1, per_page = itemsPerPage) {
    const url = `/api/tools?page=${page}&per_page=${per_page}`;
    const json = await fetchJSON(url);
    if (!json) return;
    toolsData = (json.items || []).map(normalizeToolFromServer);
    filteredTools = [...toolsData];
    currentPage = json.page || 1;
    renderTools();
}

// ---------- Rendering ----------
function renderStats(stats) {
    if (!stats) return;
    if ($('total-tools')) $('total-tools').textContent = stats.total_tools ?? $('total-tools').textContent;
    if ($('available-tools')) $('available-tools').textContent = stats.available_tools ?? $('available-tools').textContent;
    if ($('borrowed-tools')) $('borrowed-tools').textContent = stats.borrowed_tools ?? $('borrowed-tools').textContent;
    if ($('maintenance-tools')) $('maintenance-tools').textContent = stats.maintenance_tools ?? $('maintenance-tools').textContent;
}

function updateStats() {
    const totalTools = toolsData.length;
    const availableTools = toolsData.filter(t => t.status === 'Disponible').length;
    const borrowedTools = toolsData.filter(t => t.status === 'Emprunté' || t.status === 'Checked Out').length;
    const maintenanceTools = toolsData.filter(t => t.status === 'En réparation' || t.status === 'Maintenance').length;

    if ($('total-tools')) $('total-tools').textContent = totalTools;
    if ($('available-tools')) $('available-tools').textContent = availableTools;
    if ($('borrowed-tools')) $('borrowed-tools').textContent = borrowedTools;
    if ($('maintenance-tools')) $('maintenance-tools').textContent = maintenanceTools;
}

function renderTools() {
    // Render grid
    if (toolsGrid) {
        toolsGrid.innerHTML = '';
        filteredTools.slice(0, itemsPerPage).forEach(tool => {
            const card = document.createElement('div');
            card.className = 'bg-gray-50 rounded-lg shadow hover:shadow-lg transition p-3 flex flex-col items-center';
            card.dataset.toolId = tool.id;

            const img = document.createElement('img');
            img.src = tool.photo || placeholderImage();
            img.alt = tool.name || 'Tool';
            img.className = 'w-28 h-28 object-cover rounded-lg mb-3';
            card.appendChild(img);

            const h4 = document.createElement('h4');
            h4.className = 'text-sm font-semibold text-gray-800';
            h4.textContent = tool.name;
            card.appendChild(h4);

            const pLoc = document.createElement('p');
            pLoc.className = 'text-xs text-gray-500 mb-1';
            pLoc.textContent = `Étagère ${tool.loc_shelf ?? '-'} · Ligne ${tool.loc_row ?? '-'} · Col ${tool.loc_col ?? '-'}`;
            card.appendChild(pLoc);

            const status = document.createElement('span');
            status.className = 'text-xs px-2 py-1 rounded mb-2';
            if (tool.status === 'En réparation') status.classList.add('bg-yellow-100', 'text-yellow-800');
            else if (tool.status === 'Disponible') status.classList.add('bg-green-100', 'text-green-800');
            else status.classList.add('bg-red-100', 'text-red-800');
            status.textContent = tool.status || '—';
            card.appendChild(status);

            const last = document.createElement('p');
            last.className = 'text-xs text-gray-400';
            last.textContent = `Dernière vérif: ${tool.last_checked_out ? formatDate(tool.last_checked_out) : 'Jamais'}`;
            card.appendChild(last);

            // click to open detail (event delegation alternative)
            card.addEventListener('click', () => openToolDetail(tool.id));

            toolsGrid.appendChild(card);
        });
    }

    // Render list/table
    if (toolsTableBody) {
        toolsTableBody.innerHTML = '';
        filteredTools.slice(0, itemsPerPage).forEach(tool => {
            const tr = document.createElement('tr');
            tr.className = 'border-b';

            tr.innerHTML = `
                <td class="py-2 px-4">${escapeHtml(tool.id)}</td>
                <td class="py-2 px-4 flex items-center">
                    <img src="${tool.photo || placeholderImage()}" alt="${escapeHtml(tool.name)}" class="w-10 h-10 object-cover rounded mr-3">
                    <div>
                        <div class="font-medium text-sm">${escapeHtml(tool.name)}</div>
                        <div class="text-xs text-gray-500">${escapeHtml(tool.description || '')}</div>
                    </div>
                </td>
                <td class="py-2 px-4">${escapeHtml(tool.category || '')}</td>
                <td class="py-2 px-4">${escapeHtml(`Shelf ${tool.loc_shelf || '-'} / R${tool.loc_row || '-'}C${tool.loc_col || '-'}`)}</td>
                <td class="py-2 px-4">${escapeHtml(tool.status || '')}</td>
                <td class="py-2 px-4">
                    <button data-tool="${escapeHtml(tool.id)}" class="open-detail inline-flex items-center px-2 py-1 border rounded text-sm bg-white">View</button>
                </td>
            `;
            // Attach click handler for the "View" button
            const btn = tr.querySelector('button.open-detail');
            if (btn) btn.addEventListener('click', (e) => {
                e.stopPropagation();
                openToolDetail(tool.id);
            });

            toolsTableBody.appendChild(tr);
        });
    }

    updateStats();
}

// small helper to avoid XSS when injecting strings into innerHTML
function escapeHtml(str) {
    if (str === undefined || str === null) return '';
    return String(str).replace(/[&<>"]/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[s]));
}

// ---------- Filters ----------
function applyFilters() {
    const q = searchInput ? searchInput.value.trim().toLowerCase() : '';
    const cat = categoryFilter ? categoryFilter.value : '';
    const emp = employeeFilter ? employeeFilter.value : '';
    const status = statusFilter ? statusFilter.value : '';
    const dateAdded = dateAddedFilter ? dateAddedFilter.value : '';

    filteredTools = toolsData.filter(t => {
        if (q) {
            const inName = (t.name || '').toString().toLowerCase().includes(q);
            const inId = (t.id || '').toString().toLowerCase().includes(q);
            if (!inName && !inId) return false;
        }
        if (cat && (String(t.category_id) !== String(cat) && String(t.category) !== String(cat))) return false;
        if (status && t.status !== status) return false;
        if (dateAdded) {
            const da = t.date_ajout ? formatDate(t.date_ajout) : '';
            if (da !== dateAdded) return false;
        }
        return true;
    });

    currentPage = 1;
    renderTools();
}

// ---------- UI helpers ----------
function switchView(view) {
    currentView = view;
    if (view === 'grid') {
        if (toolsGrid) toolsGrid.classList.remove('hidden');
        if (toolsList) toolsList.classList.add('hidden');
        gridViewBtn && gridViewBtn.classList.add('bg-white', 'shadow-sm', 'text-blue-600');
        listViewBtn && listViewBtn.classList.remove('bg-white');
    } else {
        if (toolsGrid) toolsGrid.classList.add('hidden');
        if (toolsList) toolsList.classList.remove('hidden');
        listViewBtn && listViewBtn.classList.add('bg-white', 'shadow-sm');
    }
}

function toggleFilterSection() {
    if (!filterSection) return;
    filterSection.classList.toggle('hidden');
}

function populateFilters() {
    // categories
    if (categoryFilter) {
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        categoriesData.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = c.name;
            categoryFilter.appendChild(opt);
        });
    }
    // employees
    if (employeeFilter) {
        employeeFilter.innerHTML = '<option value="">All Employees</option>';
        employeesData.forEach(e => {
            const opt = document.createElement('option');
            opt.value = e.id;
            opt.textContent = e.name;
            employeeFilter.appendChild(opt);
        });
    }
    // toolCategorySelect for add-tool form
    if (toolCategorySelect) {
        toolCategorySelect.innerHTML = '';
        categoriesData.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = c.name;
            toolCategorySelect.appendChild(opt);
        });
    }
}

// ---------- Tool detail modal ----------
async function openToolDetail(toolId) {
    // find tool locally first
    const tool = toolsData.find(t => t.id === toolId);
    // fill quick info from local data
    if (tool && document.getElementById('detailToolImage')) {
        document.getElementById('detailToolImage').src = tool.photo || placeholderImage();
        document.getElementById('detailToolId').textContent = tool.id;
        document.getElementById('detailToolName').textContent = tool.name;
        document.getElementById('detailToolCategory').textContent = tool.category || '';
        document.getElementById('detailToolStatus').textContent = tool.status || '';
        document.getElementById('detailToolLocation').textContent = `Shelf ${tool.loc_shelf || '-'} · R${tool.loc_row || '-'} · C${tool.loc_col || '-'}`;
        document.getElementById('detailToolPrice').textContent = tool.price ? `${tool.price} €` : '';
        document.getElementById('detailPurchaseDate').textContent = tool.purchase_date ? formatDate(tool.purchase_date) : '';
        document.getElementById('detailDateAdded').textContent = tool.date_ajout ? formatDate(tool.date_ajout) : '';
        document.getElementById('detailToolDescription').textContent = tool.description || '';
    }
    // fetch full movement history (optional API endpoint not yet created)
    // If you add /api/tool/<id>/movements return, call it here and populate movementHistoryBody
    if (document.getElementById('movementHistoryBody')) {
        const tbody = document.getElementById('movementHistoryBody');
        tbody.innerHTML = '<tr><td colspan="4" class="p-4 text-sm text-gray-500">Loading...</td></tr>';
        // try to fetch movements (endpoint not implemented in blueprint above)
        const resp = await fetchJSON(`/api/tools?tool_id=${encodeURIComponent(toolId)}`); // fallback
        // if you implement a dedicated endpoint, replace above with /api/tool/{id}/movements
        if (!resp || !resp.items) {
            tbody.innerHTML = '<tr><td colspan="4" class="p-4 text-sm text-gray-500">No history available</td></tr>';
        } else {
            // For demo, use movementsData local store
            const history = movementsData.filter(m => m.tool_id === toolId);
            if (history.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="p-4 text-sm text-gray-500">No history</td></tr>';
            } else {
                tbody.innerHTML = '';
                history.forEach(h => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="py-3.5 pl-4 pr-3 text-sm">${formatDate(h.date_emprunt)}</td>
                        <td class="px-3 py-3.5 text-sm">${(employeesData.find(e => e.id === h.employee_id) || {}).name || ('#' + (h.employee_id||''))}</td>
                        <td class="px-3 py-3.5 text-sm">${h.status}</td>
                        <td class="px-3 py-3.5 text-sm">${h.return_date ? formatDate(h.return_date) : '—'}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }
    }

    // show modal (it should be hidden by default)
    if (toolDetailModal) toolDetailModal.classList.remove('hidden');
}
function closeToolDetailModal() {
    if (toolDetailModal) toolDetailModal.classList.add('hidden');
}

// ---------- Add tool/category modals (minimal) ----------
function showAddToolModal() { if (addToolModal) addToolModal.classList.remove('hidden'); }
function closeAddToolModal() { if (addToolModal) addToolModal.classList.add('hidden'); }
function showAddCategoryModal() { if (addCategoryModal) addCategoryModal.classList.remove('hidden'); }
function closeAddCategoryModal() { if (addCategoryModal) addCategoryModal.classList.add('hidden'); }

function handlePhotoPreview(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) {
        if (photoPreview) photoPreview.classList.add('hidden');
        return;
    }
    const reader = new FileReader();
    reader.onload = function (ev) {
        if (previewImage) {
            previewImage.src = ev.target.result;
            photoPreview.classList.remove('hidden');
        }
    };
    reader.readAsDataURL(file);
}

async function submitToolForm(e) {
    e && e.preventDefault && e.preventDefault();
    // Collect form fields (assumes inputs have ids used in template)
    const payload = new FormData(document.getElementById('addToolForm') || undefined);
    // TODO: endpoint to accept multipart/form-data to create a new tool
    // Example:
    // const resp = await fetch('/api/tools', { method: 'POST', body: payload, headers: { 'X-CSRFToken': '...' } });
    // if success => refresh list (call loadToolsPage(1) or push to toolsData)
    alert('Submit tool: implement POST /api/tools on backend. FormData prepared.');
}

async function submitCategoryForm(e) {
    e && e.preventDefault && e.preventDefault();
    // Collect categoryName & categoryDescription (ids in template: categoryName, categoryDescription)
    const name = document.getElementById('categoryName')?.value;
    const description = document.getElementById('categoryDescription')?.value;
    if (!name) { alert('Category name required'); return; }
    // TODO: POST /api/categories endpoint on backend
    alert('Submit category: implement POST /api/categories on backend.');
}

// ---------- Pagination helpers ----------
function goToPrevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadToolsPage(currentPage);
    }
}
function goToNextPage() {
    currentPage++;
    loadToolsPage(currentPage);
}
