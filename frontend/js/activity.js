function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function renderActivityList(items) {
    const list = document.getElementById('activity-list');

    if (items.length === 0) {
        list.innerHTML = '<div class="row py-2"><div class="col text-muted">No activity yet.</div></div>';
        return;
    }

    list.innerHTML = items.map(({ from_user_name, is_it_me, description, currency, value, created_at }) => {
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
                        <strong>${displayName}</strong> added <strong>"${description}"</strong>
                    </div>
                </div>
                <div class="row">
                    <div class="col">
                        <span class="${amountClass}">${amountLabel} ${currency} ${formattedValue}</span>
                    </div>
                </div>
                <div class="row">
                    <div class="col">
                        <small>${formatDate(created_at)}</small>
                    </div>
                </div>
            </div>
        </div>`;
    }).join('');
}

(async () => {
    const response = await apiGet(API_EXPENSES_ACTIVITY);
    if (!response.ok) return;

    const items = await response.json();
    renderActivityList(items);
})();
