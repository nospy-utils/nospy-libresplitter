function formatAmount(value) {
    return Number(value).toFixed(2);
}

function renderRows(data) {
    const container = document.getElementById('settle-rows');

    if (data.length === 0) {
        document.getElementById('settle-empty').classList.remove('d-none');
        return;
    }

    container.innerHTML = data.map(({ friend_id, friend_name, currency, net_total }) => {
        const isPositive = net_total >= 0;
        const cssClass = isPositive ? 'positive' : 'negative';
        const label = isPositive ? 'owes you' : 'you owe';
        const amount = formatAmount(Math.abs(net_total));

        return `
        <div class="row py-2 settle-row" data-friend-id="${escapeHtml(String(friend_id))}" data-friend-name="${escapeHtml(friend_name)}" data-currency="${escapeHtml(currency)}" data-total="${escapeHtml(String(net_total))}">
            <div class="col-2 align-content-center">
                <div class="settle-step1-friend-thumbnail">
                    <img src="vendor/img/icons/person.svg" alt=""/>
                </div>
            </div>
            <div class="col-6 align-content-center">
                <h3 class="text-truncate">${escapeHtml(friend_name)}</h3>
            </div>
            <div class="col-4 align-content-center text-end">
                <div class="row">
                    <div class="col">
                        <span class="${cssClass}">${escapeHtml(label)}</span>
                    </div>
                </div>
                <div class="row">
                    <div class="col">
                        <span class="${cssClass}">${escapeHtml(currency)} $${amount}</span>
                    </div>
                </div>
            </div>
        </div>`;
    }).join('');

    document.querySelectorAll('.settle-row[data-friend-id]').forEach(el => {
        el.addEventListener('click', () => {
            const friendId = el.getAttribute('data-friend-id');
            const friendName = el.getAttribute('data-friend-name');
            const currency = el.getAttribute('data-currency');
            const total = el.getAttribute('data-total');
            const reverse = total >= 0;

            window.location.href = `settle-step2.html?friendId=${friendId}&friendName=${friendName}&currency=${currency}&total=${total}&reverse=${reverse}`;
        });
    });
}

document.getElementById('cancel-btn').addEventListener('click', () => history.back());

(async () => {
    const params = new URLSearchParams(window.location.search);
    const userId = params.get('user_id');
    if (!userId) return;

    const response = await apiGet(`${API_EXPENSES_FRIEND}/${userId}/settleup`);
    if (!response.ok) {
        const { description } = await response.json();
        document.getElementById('error-message').textContent = description;
        document.getElementById('error-banner').classList.add('visible');
        return;
    }

    const data = await response.json();
    renderRows(data);
})();
