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

    document.getElementById('settle-step2-ih-currency').value = currency;
    document.getElementById('settle-step2-ih-value').value = formatAmount(Math.abs(total));

    const descEl = document.getElementById('settle-step2-fg-desc');
    if (reverse){
        descEl.innerText = `${friendName} paid you`;
    }else {
        descEl.innerText = `You paid ${friendName}`;
    }

    document.getElementById('settle-step2-fg-currency').value = currency;
    document.getElementById('settle-step2-fg-value').value = formatAmount(Math.abs(total));
})();
