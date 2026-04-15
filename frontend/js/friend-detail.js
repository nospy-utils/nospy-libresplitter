function formatAmount(value) {
    return Number(value).toFixed(2);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const month = date.toLocaleDateString(undefined, { month: 'short' });
    const day = date.getDate();
    return { month, day };
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

    const currencies = Object.entries(netByCurrency);
    if (currencies.length === 0) {
        summaryEl.textContent = 'You are settled up';
        return;
    }

    const parts = currencies.map(([currency, net]) => {
        const cssClass = net >= 0 ? 'positive' : 'negative';
        const label = net >= 0 ? `${friendName} owes you` : 'you owe';
        return `${label} <span class="${cssClass}">${currency} ${formatAmount(Math.abs(net))}</span>`;
    });

    summaryEl.innerHTML = parts.join(' and ');
}

function renderExpenses(friendName, expenses) {
    const list = document.getElementById('expenses-list');

    if (expenses.length === 0) {
        list.innerHTML = '<div class="row py-2"><div class="col text-muted">No expenses yet.</div></div>';
        return;
    }

    list.innerHTML = expenses.map(({ from_user_name, description, currency, expense_total, value, created_at }) => {
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
    }).join('');
}

(async () => {
    const params = new URLSearchParams(window.location.search);
    const userId = params.get('user_id');
    if (!userId) return;

    // update controls
    document.getElementById("friend-details-settle-user-id").value = userId;

    const response = await apiGet(`${API_EXPENSES_FRIEND}/${userId}`);
    if (!response.ok) {
        const { description } = await response.json();
        document.getElementById('error-message').textContent = description;
        document.getElementById('error-banner').classList.add('visible');
        return;
    }

    const { friend_name, expenses } = await response.json();
    renderSummary(friend_name, expenses);
    renderExpenses(friend_name, expenses);
})();
