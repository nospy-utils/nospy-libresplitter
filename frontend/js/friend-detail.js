const PAGE_SIZE = 5;
let currentPage = 0;
let hasNext = true;
let isLoading = false;
let friendName = '';
let userId;
let scrollObserver;

const loadingContainer = document.getElementById('friend-details-loadingpage-container');
const contentContainer = document.getElementById('friend-details-content-container');

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

function showSettleUp() {
    const row = document.getElementById('friend-details-settle-row');
    row.classList.toggle('invisible');
    row.classList.toggle('d-none');
}

function hideLoadingContainer(){
    loadingContainer.classList.add('invisible');
    loadingContainer.classList.add('d-none');
    contentContainer.classList.remove('invisible');
    contentContainer.classList.remove('d-none');
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
        return `${escapeHtml(label)} <span class="${cssClass}">${escapeHtml(currency)} ${formatAmount(Math.abs(net_total))}</span>`;
    });

    summaryEl.innerHTML = parts.join(' and ');
}

function buildExpenseRow({id, from_user_name, description, currency, expense_total, value, created_at}) {
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
                    <small>${escapeHtml(month)}</small>
                </div>
            </div>
            <div class="row">
                <div class="col">
                    ${escapeHtml(String(day))}
                </div>
            </div>
        </div>
        <div class="col text-truncate">
            <div class="row">
                <div class="col title text-truncate">
                    ${escapeHtml(description)}
                </div>
            </div>
            <div class="row">
                <div class="col">
                    <small>${escapeHtml(payerLabel)} ${escapeHtml(currency)} ${formatAmount(expense_total)}</small>
                </div>
            </div>
        </div>
        <div class="col-4 text-end">
            <div class="row">
                <div class="col">
                    <small class="${amountClass}">${escapeHtml(amountLabel)}</small>
                </div>
            </div>
            <div class="row">
                <div class="col">
                    <span class="${amountClass} title">${escapeHtml(currency)} ${formatAmount(value)}</span>
                </div>
            </div>
        </div>
        <div class="col-2">
            <div class="expense-bin" data-el-expense-id="${escapeHtml(String(id))}">
                <svg title="delete" version="1.1" x="0px" y="0px" viewBox="0 0 100 125" enable-background="new 0 0 100 100" xml:space="preserve"><ellipse cx="40.881" cy="52.812" rx="1.875" ry="2.812"/><ellipse cx="59.631" cy="52.812" rx="1.875" ry="2.812"/><path d="M55.882,58.438c-0.519,0-0.938,0.419-0.938,0.938c0,2.585-2.102,4.688-4.687,4.688  c-2.586,0-4.688-2.102-4.688-4.688c0-0.518-0.419-0.938-0.937-0.938c-0.519,0-0.938,0.419-0.938,0.938  c0,3.618,2.944,6.562,6.563,6.562c3.618,0,6.562-2.944,6.562-6.562C56.819,58.857,56.399,58.438,55.882,58.438z"/><path d="M78.382,19.062H60.474c-0.436-2.139-2.327-3.75-4.592-3.75h-11.25c-2.266,0-4.157,1.611-4.593,3.75H22.132  c-1.551,0-2.812,1.262-2.812,2.812c0,1.24,0.811,2.283,1.928,2.655l3.699,51.786l0,0v0.002c0.176,2.459,2.363,4.62,4.683,4.622  c0.002,0,0.002,0,0.002,0c0.004,0,0.005-0.002,0.009-0.002h41.231c0.004,0,0.006,0.002,0.009,0.002c0,0,0,0,0.002,0  c2.32-0.002,4.508-2.163,4.684-4.622v-0.002l0,0l3.698-51.786c1.117-0.372,1.929-1.415,1.929-2.655  C81.194,20.324,79.932,19.062,78.382,19.062z M44.632,17.188h11.25c1.221,0,2.252,0.787,2.64,1.875h-16.53  C42.379,17.975,43.41,17.188,44.632,17.188z M73.696,76.184L73.696,76.184c0,0.002,0,0.002,0,0.002  c-0.104,1.474-1.47,2.871-2.809,2.876c-0.002,0-0.003,0-0.005,0h-41.25c-0.002,0-0.004,0-0.005,0  c-1.339-0.005-2.704-1.403-2.809-2.876c0,0,0,0,0-0.002l0,0l-3.678-51.497h54.235L73.696,76.184z M78.382,22.812h-56.25  c-0.517,0-0.938-0.421-0.938-0.938s0.421-0.938,0.938-0.938h56.25c0.516,0,0.937,0.421,0.937,0.938S78.898,22.812,78.382,22.812z"/></svg>
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
    attachDeleteHandlers();
}

function attachDeleteHandlers() {
    document.querySelectorAll('.expense-bin').forEach(bin => {
        if (bin.dataset.listenerAttached) return;
        bin.dataset.listenerAttached = 'true';
        bin.addEventListener('click', async () => {
            const expenseId = bin.getAttribute('data-el-expense-id');
            if (!expenseId) return;

            const row = bin.closest('.row.py-2');
            const description = row ? row.querySelector('.title')?.textContent.trim() : '';

            const message = `Are you sure you want to delete expense #${expenseId} "${description}"?`;

            const confirmed = confirm(message);
            if (!confirmed) return;

            const response = await apiDelete(`${API_EXPENSES}/${expenseId}`);

            if (!response.ok) {
                const { name, description } = await response.json();
                const errorMessage = `${name} - ${description}`;
                showError(errorMessage);
                return;
            }

            window.location.reload();

        });
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
        const { name, description } = await response.json();
        const errorMessage = `${name} - ${description}`;
        showError(errorMessage);
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

    hideLoadingContainer();
    if (!expensesResp.ok) {
        const { name, description } = await expensesResp.json();
        const errorMessage = `${name} - ${description}`;
        showError(errorMessage);
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
        showSettleUp();
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
