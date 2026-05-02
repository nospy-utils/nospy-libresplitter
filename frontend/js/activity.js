const PAGE_SIZE = 10;
let currentPage = 0;
let hasNext = true;
let isLoading = false;
let scrollObserver;

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-banner').classList.add('visible');
}

function showSpinner() {
    document.getElementById('loading-spinner').classList.add('visible');
}

function hideSpinner() {
    document.getElementById('loading-spinner').classList.remove('visible');
}

function buildActivityRow({ from_user_name, is_it_me, description, currency, value, created_at }) {
    const displayName = is_it_me ? 'You' : from_user_name;
    const amountClass = is_it_me ? 'positive' : 'negative';
    const amountLabel = is_it_me ? 'You lent' : 'You owe';
    const formattedValue = Number(value).toFixed(2);

    return `
    <div class="row py-2 activity-row">
        <div class="col-sm-2 col-lg-1 d-none d-sm-block">
            <div class="activity-thumbnail">
                <img src="vendor/img/icons/receipt.svg" alt=""/>
            </div>
            <div class="activity-friend-thumbnail">
                <img src="vendor/img/icons/person.svg" alt=""/>
            </div>
        </div>
        <div class="col-sm-10 col-lg-11">
            <div class="row">
                <div class="col">
                    <strong>${escapeHtml(displayName)}</strong> added <strong>"${escapeHtml(description)}"</strong>
                </div>
            </div>
            <div class="row">
                <div class="col">
                    <span class="${amountClass}">${escapeHtml(amountLabel)} ${escapeHtml(currency)} ${formattedValue}</span>
                </div>
            </div>
            <div class="row">
                <div class="col">
                    <small>${formatDate(created_at)}</small>
                </div>
            </div>
        </div>
    </div>`;
}

function appendActivity(items) {
    const list = document.getElementById('activity-list');
    items.forEach(item => {
        const tmp = document.createElement('div');
        tmp.innerHTML = buildActivityRow(item).trim();
        list.appendChild(tmp.firstChild);
    });
}

async function loadNextPage() {
    if (isLoading || !hasNext) return;
    isLoading = true;
    showSpinner();

    const response = await apiGet(`${API_EXPENSES_ACTIVITY}?page=${currentPage + 1}&page_size=${PAGE_SIZE}`);
    isLoading = false;

    if (!response.ok) {
        hideSpinner();
        const { name, description } = await response.json();
        const errorMessage = `${name} - ${description}`;
        showError(errorMessage);
        return;
    }

    const data = await response.json();
    currentPage = data.page;
    hasNext = data.has_next;

    appendActivity(data.activity);
    hideSpinner();

    if (!hasNext && scrollObserver) {
        scrollObserver.disconnect();
    }
}

(async () => {
    const response = await apiGet(`${API_EXPENSES_ACTIVITY}?page=1&page_size=${PAGE_SIZE}`);

    if (!response.ok) {
        const { name, description } = await response.json();
        const errorMessage = `${name} - ${description}`;
        showError(errorMessage);
        return;
    }

    const data = await response.json();
    currentPage = data.page;
    hasNext = data.has_next;

    if (data.total === 0) {
        document.getElementById('activity-list').innerHTML =
            '<div class="row py-2"><div class="col text-muted">No activity yet.</div></div>';
    } else {
        appendActivity(data.activity);
    }

    if (hasNext) {
        const sentinel = document.getElementById('scroll-sentinel');
        scrollObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) loadNextPage();
        }, { threshold: 0.1 });
        scrollObserver.observe(sentinel);
    }
})();
