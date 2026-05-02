function showError(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-banner').classList.toggle('invisible');
    document.getElementById('error-banner').classList.toggle('d-none');
}

function formatAmount(amount) {
    return Math.abs(amount).toFixed(2);
}

function renderOverallSummary(totalsByCurrency) {
    const summary = document.getElementById('overall-summary');

    if (totalsByCurrency.length === 0) {
        summary.textContent = 'Overall, you are settled up';
        return;
    }

    const parts = totalsByCurrency.map(({ currency, my_total }) => {
        const cssClass = my_total >= 0 ? 'positive' : 'negative';
        const label = my_total >= 0 ? 'you are owed' : 'you owe';
        return `${escapeHtml(label)} <span class="${cssClass}">${escapeHtml(currency)} ${formatAmount(my_total)}</span>`;
    });

    summary.innerHTML = 'Overall, ' + parts.join(' and ');
}

function renderFriendAmounts(currencies) {
    return currencies.map(({ currency, net_total }) => {
        const cssClass = net_total >= 0 ? 'positive' : 'negative';
        const label = net_total >= 0 ? 'owes you' : 'you owe';
        return `<div>${escapeHtml(label)} <span class="${cssClass}">${escapeHtml(currency)} ${formatAmount(net_total)}</span></div>`;
    }).join('');
}

function renderFriendsList(totalsByFriend) {
    const list = document.getElementById('friends-list');

    if (totalsByFriend.length === 0) {
        list.innerHTML = '';
        return;
    }

    list.innerHTML = totalsByFriend.map(({ friend_id, friend_name, currencies }) => `
        <div class="row py-2 friend-row" data-el="${escapeHtml(String(friend_id))}">
            <div class="col-2 align-content-center">
                <div class="friend-thumbnail">
                    <img src="vendor/img/icons/person.svg" alt=""/>
                </div>
            </div>
            <div class="col-6 align-content-center">
                <h3 class="text-truncate">${escapeHtml(friend_name)}</h3>
            </div>
            <div class="col-4 align-content-center text-end">
                ${renderFriendAmounts(currencies)}
            </div>
        </div>
    `).join('');

    document.querySelectorAll('.friend-row[data-el]').forEach(el => {
        el.addEventListener('click', () => {
            const userId = el.getAttribute('data-el');
            if (userId) {
                window.location.href = `friend-detail.html?user_id=${userId}`;
            }
        });
    });
}

(async () => {
    const response = await fetch(API_EXPENSES_ME, { credentials: 'include' });
    if (!response.ok) {
        const { name, description } = await response.json();
        const errorMessage = `${name} - ${description}`;
        showError(errorMessage);
        return;
    }

    const { totals_by_currency, totals_by_friend } = await response.json();
    renderOverallSummary(totals_by_currency);
    renderFriendsList(totals_by_friend);
})();
