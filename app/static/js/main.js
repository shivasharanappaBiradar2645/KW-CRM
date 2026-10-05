let cachedCustomers = [];
let cachedProducts = [];
let cachedOrders = [];

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});

function showTab(tabName) {
    document.querySelectorAll('.content-section').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.sidebar li a').forEach(el => el.classList.remove('active'));

    const activeSec = document.getElementById(`section-${tabName}`);
    if (activeSec) activeSec.style.display = 'block';

    const activeNav = document.getElementById(`nav-${tabName}`);
    if (activeNav) activeNav.classList.add('active');

    const titleMap = {
        'dashboard': 'Dashboard Overview',
        'customers': 'Customer Management',
        'contacts': 'Contacts & People Tracking',
        'products': 'Product Catalog',
        'contracts': 'Contracts Management',
        'orders': 'Orders & Billing Engine',
        'analytics': 'Pipeline Financials & Stock Depletion Analytics',
        'communications': 'Engagement Timeline & AI Auto-Replies'
    };
    document.getElementById('page-title').innerText = titleMap[tabName] || 'Dashboard';
}

async function loadDashboardData() {
    try {
        const [custRes, contRes, prodRes, contractRes, ordRes, commRes, pipeRes, stockRes] = await Promise.all([
            fetch('/api/customers'),
            fetch('/api/contacts'),
            fetch('/api/products'),
            fetch('/api/contracts'),
            fetch('/api/orders'),
            fetch('/api/communications'),
            fetch('/api/analytics/pipeline'),
            fetch('/api/analytics/stock-depletion')
        ]);

        cachedCustomers = await custRes.json();
        const contacts = await contRes.json();
        cachedProducts = await prodRes.json();
        const contracts = await contractRes.json();
        cachedOrders = await ordRes.json();
        const comms = await commRes.json();
        const pipelineData = await pipeRes.json();
        const stockData = await stockRes.json();

        // Update Stats
        document.getElementById('stat-pipeline').innerText = `$${pipelineData.total_pipeline_value.toFixed(2)}`;
        document.getElementById('stat-customers').innerText = cachedCustomers.length;
        document.getElementById('stat-contacts').innerText = contacts.length;
        document.getElementById('stat-contracts').innerText = contracts.length;

        // Render Tables
        renderCustomers(cachedCustomers);
        renderContacts(contacts);
        renderProducts(cachedProducts);
        renderContracts(contracts);
        renderOrders(cachedOrders);
        renderCommunications(comms);
        renderAnalytics(stockData);

        // Populate Dropdowns for Forms
        populateDropdowns();

    } catch (err) {
        console.error('Error loading dashboard data:', err);
    }
}

function renderCustomers(data) {
    const tbody = document.getElementById('tbl-customers');
    tbody.innerHTML = data.map(c => `
        <tr>
            <td><strong>${c.company_name}</strong></td>
            <td>${c.email}</td>
            <td>${c.created_at ? c.created_at.split('T')[0] : ''}</td>
            <td><span class="badge badge-info">${c.contacts ? c.contacts.length : 0} contacts</span></td>
        </tr>
    `).join('');
}

function renderContacts(data) {
    const tbody = document.getElementById('tbl-contacts');
    tbody.innerHTML = data.map(c => `
        <tr>
            <td><strong>${c.first_name} ${c.last_name}</strong></td>
            <td>${c.job_title || '-'}</td>
            <td>${c.email || '-'}</td>
            <td>${c.phone || '-'}</td>
            <td>${c.birthday ? `<span class="badge badge-purple">🎂 ${c.birthday}</span>` : '-'}</td>
            <td>${c.anniversary ? `<span class="badge badge-info">🎉 ${c.anniversary}</span>` : '-'}</td>
        </tr>
    `).join('');
}

function renderProducts(data) {
    const tbody = document.getElementById('tbl-products');
    tbody.innerHTML = data.map(p => `
        <tr>
            <td><strong>${p.name}</strong></td>
            <td><code>${p.sku}</code></td>
            <td>$${p.price.toFixed(2)}</td>
        </tr>
    `).join('');
}

function renderContracts(data) {
    const tbody = document.getElementById('tbl-contracts');
    tbody.innerHTML = data.map(ct => `
        <tr>
            <td><code>${ct.id.substring(0, 8)}...</code></td>
            <td><code>${ct.customer_id.substring(0, 8)}...</code></td>
            <td>${ct.start_date}</td>
            <td>${ct.end_date}</td>
            <td><span class="badge badge-success">${ct.status}</span></td>
        </tr>
    `).join('');
}

function renderOrders(data) {
    const tbody = document.getElementById('tbl-orders');
    tbody.innerHTML = data.map(o => `
        <tr>
            <td><code>${o.id.substring(0, 8)}...</code></td>
            <td><code>${o.customer_id.substring(0, 8)}...</code></td>
            <td><strong>$${o.total_amount.toFixed(2)}</strong></td>
            <td><span class="badge badge-success">${o.order_status}</span></td>
            <td><span class="badge badge-info">${o.items ? o.items.length : 0} items</span></td>
            <td>${o.created_at ? o.created_at.split('T')[0] : ''}</td>
        </tr>
    `).join('');
}

function renderAnalytics(data) {
    const tbody = document.getElementById('tbl-analytics');
    if (!tbody) return;
    tbody.innerHTML = data.map(st => `
        <tr>
            <td><code>${st.sku}</code></td>
            <td><strong>${st.product_name}</strong></td>
            <td>$${st.unit_price.toFixed(2)}</td>
            <td><strong>${st.recent_sales_qty} units</strong></td>
            <td>${st.prev_sales_qty} units</td>
            <td>
                ${st.spike_detected 
                    ? `<span class="badge badge-danger">⚡ HIGH DEPLETION SPIKE (+${st.sales_growth_qty})</span>` 
                    : `<span class="badge badge-info">Normal Velocity (+${st.sales_growth_qty})</span>`}
            </td>
        </tr>
    `).join('');
}

function renderCommunications(data) {
    const tbody = document.getElementById('tbl-communications');
    tbody.innerHTML = data.map(c => {
        let badgeClass = 'badge-info';
        if (c.direction === 'Outbound' && c.channel === 'System_Notification') {
            badgeClass = 'badge-purple';
        } else if (c.direction === 'Outbound') {
            badgeClass = 'badge-success';
        } else if (c.direction === 'Inbound') {
            badgeClass = 'badge-warning';
        }

        return `
            <tr>
                <td><span class="badge ${badgeClass}">${c.direction}</span></td>
                <td><strong>${c.channel}</strong></td>
                <td>${c.subject || '-'}</td>
                <td>${c.body}</td>
                <td>${c.sent_at ? c.sent_at.replace('T', ' ').substring(0, 19) : ''}</td>
            </tr>
        `;
    }).join('');
}

function populateDropdowns() {
    const custOptions = cachedCustomers.map(c => `<option value="${c.id}">${c.company_name} (${c.email})</option>`).join('');
    
    ['modalCustomerSelect', 'contactCustomerSelect', 'contractCustomerSelect', 'orderCustomerSelect'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = custOptions;
    });

    const prodOptions = cachedProducts.map(p => `<option value="${p.id}" data-price="${p.price}">${p.name} ($${p.price.toFixed(2)})</option>`).join('');
    const prodSelect = document.getElementById('itemProductSelect');
    if (prodSelect) {
        prodSelect.innerHTML = prodOptions;
        prodSelect.onchange = (e) => {
            const opt = e.target.options[e.target.selectedIndex];
            if (opt) document.getElementById('itemUnitPrice').value = opt.getAttribute('data-price');
        };
        if (cachedProducts.length > 0) {
            document.getElementById('itemUnitPrice').value = cachedProducts[0].price;
        }
    }

    const orderOptions = cachedOrders.map(o => `<option value="${o.id}">Order #${o.id.substring(0,8)}... ($${o.total_amount.toFixed(2)})</option>`).join('');
    const orderSelect = document.getElementById('itemOrderSelect');
    if (orderSelect) orderSelect.innerHTML = orderOptions;
}

// Modal Toggle Functions
function openModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

function openCustomerModal() { openModal('customerModal'); }
function openContactModal() { openModal('contactModal'); }
function openProductModal() { openModal('productModal'); }
function openContractModal() { openModal('contractModal'); }
function openOrderModal() { openModal('orderModal'); }
function openOrderItemModal() { openModal('orderItemModal'); }
function openComplaintModal() { openModal('complaintModal'); }

// Form Submissions with Error Reporting
async function submitCustomerForm(e) {
    e.preventDefault();
    const company_name = document.getElementById('custCompanyName').value;
    const email = document.getElementById('custEmail').value;

    const res = await fetch('/api/customers', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ company_name, email })
    });
    if (res.ok) {
        closeModal('customerModal');
        loadDashboardData();
    } else {
        const err = await res.json();
        alert('Error creating customer: ' + (err.error || res.statusText));
    }
}

async function submitContactForm(e) {
    e.preventDefault();
    const customer_id = document.getElementById('contactCustomerSelect').value;
    const first_name = document.getElementById('contactFirstName').value;
    const last_name = document.getElementById('contactLastName').value;
    const job_title = document.getElementById('contactJobTitle').value;
    const email = document.getElementById('contactEmail').value;
    const phone = document.getElementById('contactPhone').value;
    const birthday = document.getElementById('contactBirthday').value;
    const anniversary = document.getElementById('contactAnniversary').value;

    if (!customer_id) {
        alert('Please select or create a Customer Company first!');
        return;
    }

    const res = await fetch('/api/contacts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ customer_id, first_name, last_name, job_title, email, phone, birthday, anniversary })
    });
    if (res.ok) {
        closeModal('contactModal');
        loadDashboardData();
    } else {
        const err = await res.json();
        alert('Error creating contact: ' + (err.error || res.statusText));
    }
}

async function submitProductForm(e) {
    e.preventDefault();
    const name = document.getElementById('prodName').value;
    const sku = document.getElementById('prodSKU').value;
    const price = parseFloat(document.getElementById('prodPrice').value);

    const res = await fetch('/api/products', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name, sku, price })
    });
    if (res.ok) {
        closeModal('productModal');
        loadDashboardData();
    } else {
        const err = await res.json();
        alert('Error creating product: ' + (err.error || res.statusText));
    }
}

async function submitContractForm(e) {
    e.preventDefault();
    const customer_id = document.getElementById('contractCustomerSelect').value;
    const start_date = document.getElementById('contractStartDate').value;
    const end_date = document.getElementById('contractEndDate').value;
    const terms_text = document.getElementById('contractTermsText').value;

    if (!customer_id) {
        alert('Please select or create a Customer Company first!');
        return;
    }

    const res = await fetch('/api/contracts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ customer_id, start_date, end_date, terms_text })
    });
    if (res.ok) {
        closeModal('contractModal');
        loadDashboardData();
    } else {
        const err = await res.json();
        alert('Error creating contract: ' + (err.error || res.statusText));
    }
}

async function submitOrderForm(e) {
    e.preventDefault();
    const customer_id = document.getElementById('orderCustomerSelect').value;
    const order_status = document.getElementById('orderStatusSelect').value;

    if (!customer_id) {
        alert('Please select or create a Customer Company first!');
        return;
    }

    const res = await fetch('/api/orders', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ customer_id, order_status })
    });
    if (res.ok) {
        closeModal('orderModal');
        loadDashboardData();
    } else {
        const err = await res.json();
        alert('Error creating order: ' + (err.error || res.statusText));
    }
}

async function submitOrderItemForm(e) {
    e.preventDefault();
    const order_id = document.getElementById('itemOrderSelect').value;
    const product_id = document.getElementById('itemProductSelect').value;
    const quantity = parseInt(document.getElementById('itemQuantity').value);
    const unit_price = parseFloat(document.getElementById('itemUnitPrice').value);

    if (!order_id || !product_id) {
        alert('Please ensure both Order and Product exist!');
        return;
    }

    const res = await fetch(`/api/orders/${order_id}/items`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ product_id, quantity, unit_price })
    });
    if (res.ok) {
        closeModal('orderItemModal');
        loadDashboardData();
    } else {
        const err = await res.json();
        alert('Error adding line item: ' + (err.error || res.statusText));
    }
}

async function submitCustomerComplaint(event) {
    event.preventDefault();
    const customerId = document.getElementById('modalCustomerSelect').value;
    const channel = document.getElementById('modalChannel').value;
    const subject = document.getElementById('modalSubject').value;
    const body = document.getElementById('modalBody').value;

    if (!customerId) {
        alert('Please select a Customer Company!');
        return;
    }

    const res = await fetch('/api/communications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            customer_id: customerId,
            direction: 'Inbound',
            channel: channel,
            subject: subject,
            body: body
        })
    });

    if (res.ok) {
        closeModal('complaintModal');
        showTab('communications');
        loadDashboardData();
    } else {
        const err = await res.json();
        alert('Error submitting complaint: ' + (err.error || res.statusText));
    }
}

async function triggerSnoozedCheck() {
    alert('Running Snoozed Lead Check (Pending orders > 48h)...');
    try {
        const res = await fetch('/api/analytics/run-snoozed-check?hours=48', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        showTab('communications');
        loadDashboardData();
    } catch (err) {
        alert('Error running check: ' + err.message);
    }
}

async function syncWooCommerce() {
    alert('Attempting WooCommerce Sync...');
    try {
        const res = await fetch('/api/woocommerce/sync/orders', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            alert(data.message);
            loadDashboardData();
        } else {
            alert('Notice: ' + (data.error || 'WooCommerce credentials not configured. Endpoint ready.'));
        }
    } catch (err) {
        alert('Could not sync WooCommerce: ' + err.message);
    }
}
