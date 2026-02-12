// Quartz Email System - Common JS utilities

// Auto-init Bootstrap toasts
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toast').forEach(function(el) {
        new bootstrap.Toast(el).show();
    });
});

// Table search/filter
function initTableSearch(inputId, tableId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener('keyup', function() {
        const filter = this.value.toLowerCase();
        const table = document.getElementById(tableId);
        if (!table) return;
        const rows = table.querySelectorAll('tbody tr');
        let visible = 0;
        rows.forEach(row => {
            const match = row.textContent.toLowerCase().includes(filter);
            row.style.display = match ? '' : 'none';
            if (match) visible++;
        });
        // Update row count if exists
        const counter = document.getElementById(tableId + 'Count');
        if (counter) counter.textContent = visible;
    });
}

// Table column sorting
function initTableSort(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const headers = table.querySelectorAll('thead th');
    headers.forEach(function(th, colIdx) {
        th.style.cursor = 'pointer';
        th.title = 'Click to sort';
        th.addEventListener('click', function() {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const asc = !th.dataset.sortAsc || th.dataset.sortAsc === 'false';
            // Reset other headers
            headers.forEach(h => { h.dataset.sortAsc = ''; h.classList.remove('sort-asc', 'sort-desc'); });
            th.dataset.sortAsc = asc;
            th.classList.add(asc ? 'sort-asc' : 'sort-desc');
            rows.sort(function(a, b) {
                const aText = (a.cells[colIdx] || {}).textContent || '';
                const bText = (b.cells[colIdx] || {}).textContent || '';
                const aNum = parseFloat(aText);
                const bNum = parseFloat(bText);
                if (!isNaN(aNum) && !isNaN(bNum)) return asc ? aNum - bNum : bNum - aNum;
                return asc ? aText.localeCompare(bText) : bText.localeCompare(aText);
            });
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// Select all checkbox for batch operations
function initSelectAll(selectAllId, checkboxClass) {
    const selectAll = document.getElementById(selectAllId);
    if (!selectAll) return;
    selectAll.addEventListener('change', function() {
        document.querySelectorAll('.' + checkboxClass).forEach(function(cb) {
            cb.checked = selectAll.checked;
        });
    });
}

// Button loading state
function setButtonLoading(btn, loading) {
    if (loading) {
        btn.dataset.originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Loading...';
    } else {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
    }
}

// Form submit with loading state (prevent double-submit)
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('form[data-loading]').forEach(function(form) {
        form.addEventListener('submit', function() {
            var btn = form.querySelector('button[type="submit"]');
            if (btn) setButtonLoading(btn, true);
        });
    });
});

// Confirm action with Bootstrap modal (fallback to confirm())
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Delete attachment via fetch
function deleteFile(filename) {
    if (confirm('Are you sure you want to delete ' + filename + '? This action cannot be undone.')) {
        fetch('/attachments/delete/' + encodeURIComponent(filename), {method: 'POST'})
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            });
    }
}

// Send individual customer email
function sendOne(custId, stage, btn) {
    if (!confirm('Send AI-generated email to this customer at Stage ' + stage + '?')) return;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = '/batch_send/run';
    var inp1 = document.createElement('input');
    inp1.type = 'hidden'; inp1.name = 'stage'; inp1.value = stage;
    var inp2 = document.createElement('input');
    inp2.type = 'hidden'; inp2.name = 'customer_ids'; inp2.value = custId;
    form.appendChild(inp1);
    form.appendChild(inp2);
    document.body.appendChild(form);
    form.submit();
}
