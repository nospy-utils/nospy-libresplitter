function formatAmount(value) {
    return Number(value).toFixed(2);
}


(async () => {
    const params = new URLSearchParams(window.location.search);

    const friendId = params.get('friendId');
    const friendName = params.get('friendName');
    const currency = params.get('currency');
    const total = params.get('total');
    const reverse = params.get('reverse') === 'true';
    if (!friendId || !friendName || !currency || !total ){
        console.error('Missing required parameter');
        return;
    }

    const descEl = document.getElementById('settle-step2-fg-desc');
    if (reverse){
        descEl.innerText = `${friendName} paid you`;
    }else {
        descEl.innerText = `You paid ${friendName}`;
    }

    document.getElementById('settle-step2-fg-currency').textContent = currency;
    document.getElementById('settle-step2-fg-value').value = formatAmount(Math.abs(total));

    document.getElementById('settle-step2-form').addEventListener('submit', async function (e) {
        e.preventDefault();

        const value = parseFloat(document.getElementById('settle-step2-fg-value').value);
        const errorEl = document.getElementById('settle-step2-error');
        errorEl.style.display = 'none';

        const response = await apiPost(
            `${API_EXPENSES_FRIEND}/${friendId}/settleup`,
            JSON.stringify({ currency, value, reverse })
        );

        if (response.ok) {
            window.location.href = `friend-detail.html?user_id=${friendId}`;
            return;
        }

        const data = await response.json();
        errorEl.textContent = data.description || 'Something went wrong.';
        errorEl.style.display = 'block';
    });
})();
