const PAGE_SIZE = 5;
let currentPage = 0;
let hasNext = true;
let isLoading = false;
let friendName = '';
let userId;
let scrollObserver;

function formatAmount(value) {
    return Number(value).toFixed(2);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const month = date.toLocaleDateString(undefined, { month: 'short' });
    const day = date.getDate();
    return { month, day };
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

function renderSummary(friendName, expenses) {
    const nameEl = document.getElementById('friend-name');
    const summaryEl = document.getElementById('friend-summary');

    nameEl.textContent = friendName;

    const netByCurrency = {};
    for (const { from_user_name, currency, value } of expenses) {
        if (!netByCurrency[currency]) netByCurrency[currency] = 0;
        netByCurrency[currency] += from_user_name === 'You' ? value : -value;
    }

    let currencies = Object.entries(netByCurrency);
    if (currencies.length === 0) {
        summaryEl.textContent = 'You are settled up';
        return;
    }

    // filter out currencies that have already been settled
    currencies = currencies.filter(n => n[1] !== 0);

    const parts = currencies.map(([currency, net]) => {
        const cssClass = net >= 0 ? 'positive' : 'negative';
        const label = net >= 0 ? `${friendName} owes you` : 'you owe';
        return `${label} <span class="${cssClass}">${currency} ${formatAmount(Math.abs(net))}</span>`;
    });

    summaryEl.innerHTML = parts.join(' and ');
}

function buildExpenseRow({ from_user_name, description, currency, expense_total, value, created_at }) {
    const { month, day } = formatDate(created_at);
    const iPaid = from_user_name === 'You';
    const payerLabel = iPaid ? 'You paid' : `${friendName} paid`;
    const amountClass = iPaid ? 'positive' : 'negative';
    const amountLabel = iPaid ? 'you lent' : 'you borrowed';

    return `
    <div class="row py-2">
        <div class="col-1 text-start">
            <div class="row">
                <div class="col">
                    <small>${month}</small>
                </div>
            </div>
            <div class="row">
                <div class="col">
                    ${day}
                </div>
            </div>
        </div>
        <div class="col-2">
            <div class="expense-thumbnail">
                <img src="vendor/img/icons/receipt.svg" alt=""/>
            </div>
        </div>
        <div class="col">
            <div class="row">
                <div class="col">
                    ${description}
                </div>
            </div>
            <div class="row">
                <div class="col">
                    <small>${payerLabel} ${currency} ${formatAmount(expense_total)}</small>
                </div>
            </div>
        </div>
        <div class="col-3 text-end">
            <div class="row">
                <div class="col">
                    <span class="${amountClass}">${amountLabel}</span>
                </div>
            </div>
            <div class="row">
                <div class="col">
                    <span class="${amountClass}">${currency} ${formatAmount(value)}</span>
                </div>
            </div>
        </div>
    </div>`;
}

function appendExpenses(expenses) {
    const list = document.getElementById('expenses-list');
    expenses.forEach(expense => {
        const tmp = document.createElement('div');
        tmp.innerHTML = buildExpenseRow(expense).trim();
        list.appendChild(tmp.firstChild);
    });
}

async function loadNextPage() {
    if (isLoading || !hasNext) return;
    isLoading = true;
    showSpinner();

    const response = await apiGet(`${API_EXPENSES_FRIEND}/${userId}?page=${currentPage + 1}&page_size=${PAGE_SIZE}`);
    isLoading = false;

    if (!response.ok) {
        hideSpinner();
        const { description } = await response.json();
        showError(description);
        return;
    }

    const data = await response.json();
    currentPage = data.page;
    hasNext = data.has_next;

    appendExpenses(data.expenses);
    hideSpinner();

    if (!hasNext && scrollObserver) {
        scrollObserver.disconnect();
    }
}

(async () => {
    const params = new URLSearchParams(window.location.search);
    userId = params.get('user_id');
    if (!userId) return;

    document.getElementById("friend-details-settle-user-id").value = userId;

    const expensesResp = await apiGet(`${API_EXPENSES_FRIEND}/${userId}?page=1&page_size=${PAGE_SIZE}`);

    if (!expensesResp.ok) {
        const { description } = await expensesResp.json();
        showError(description);
        return;
    }

    const expensesData = await expensesResp.json();
    friendName = expensesData.friend_name;
    currentPage = expensesData.page;
    hasNext = expensesData.has_next;

    renderSummary(friendName, expensesData.expenses);

    if (expensesData.total === 0) {
        document.getElementById('expenses-list').innerHTML =
            '<div class="row py-2"><div class="col text-muted">No expenses yet.</div></div>';
    } else {
        appendExpenses(expensesData.expenses);
    }

    if (hasNext) {
        const sentinel = document.getElementById('scroll-sentinel');
        scrollObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) loadNextPage();
        }, { threshold: 0.1 });
        scrollObserver.observe(sentinel);
    }
})();
