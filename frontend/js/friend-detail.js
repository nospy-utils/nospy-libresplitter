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
    const month = date.toLocaleDateString(undefined, {month: 'short'});
    const day = date.getDate();
    return {month, day};
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

function renderSummary(data) {
    const nameEl = document.getElementById('friend-name');
    const summaryEl = document.getElementById('friend-summary');

    nameEl.textContent = friendName;

    if (data.totals_by_currency.length === 0) {
        summaryEl.textContent = 'You are settled up';
        return;
    }

    const parts = data.totals_by_currency.map((item) => {
        const {currency, net_total} = item;
        const cssClass = net_total >= 0 ? 'positive' : 'negative';
        const label = net_total >= 0 ? `${friendName} owes you` : 'you owe';
        return `${label} <span class="${cssClass}">${currency} ${formatAmount(Math.abs(net_total))}</span>`;
    });

    summaryEl.innerHTML = parts.join(' and ');
}

function buildExpenseRow({from_user_name, description, currency, expense_total, value, created_at}) {
    const {month, day} = formatDate(created_at);
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
        const {description} = await response.json();
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

async function updateAddExpenseForm() {
    // context: when we have already selected the friend it makes no sense to go to step 1 of add expense
    // so I prefer to go straight to step2 to shorten the process.
    const form = document.getElementById("footerAddExpenseForm");
    form.action = 'addexpense-step2.html';
    const input = document.createElement("input"); // Create input element
    input.type = "hidden";
    input.name = "user_id";
    input.value = userId;
    form.appendChild(input);
}

(async () => {
    const params = new URLSearchParams(window.location.search);
    userId = params.get('user_id');
    if (!userId) return;

    // update controls
    document.getElementById("friend-details-settle-user-id").value = userId;
    updateAddExpenseForm();

    const expensesResp = await apiGet(`${API_EXPENSES_FRIEND}/${userId}?page=1&page_size=${PAGE_SIZE}`);

    if (!expensesResp.ok) {
        const {description} = await expensesResp.json();
        showError(description);
        return;
    }

    const data = await expensesResp.json();
    friendName = data.friend_name;
    currentPage = data.page;
    hasNext = data.has_next;

    renderSummary(data);

    if (data.total === 0) {
        document.getElementById('expenses-list').innerHTML =
            '<div class="row py-2"><div class="col text-muted">No expenses yet.</div></div>';
    } else {
        appendExpenses(data.expenses);
    }

    if (hasNext) {
        const sentinel = document.getElementById('scroll-sentinel');
        scrollObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) loadNextPage();
        }, {threshold: 0.1});
        scrollObserver.observe(sentinel);
    }
})();
