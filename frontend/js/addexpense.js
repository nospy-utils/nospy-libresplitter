function buildFriendChip({name}) {
    return `<div class="d-inline-block addexpense-step2-friend-wrapper">
    <img class="d-inline" src="vendor/img/icons/person.svg" alt="placeholder"/>
    <h3 class="d-inline">${name}</h3>
</div>`;
}

function buildExactAmountRow({name}) {
    return `<div class="row py-2">
    <div class="col-2">
        <div class="addexpense-modal-friend-thumbnail">
            <img src="vendor/img/icons/person.svg" alt=""/>
        </div>
    </div>
    <div class="col-4 align-content-center">
        <h3 class="text-truncate">${name}</h3>
    </div>
    <div class="col-6 align-content-center">
        <div class="mb-3 input-group">
            <span class="input-group-text">$</span>
            <input type="number" class="form-control" min="0.00" step="0.01" value="0.00" inputmode="decimal"/>
        </div>
    </div>
</div>`;
}

function buildPercentageRow({name}) {
    return `<div class="row py-2">
    <div class="col-2">
        <div class="addexpense-modal-friend-thumbnail">
            <img src="vendor/img/icons/person.svg" alt="placeholder"/>
        </div>
    </div>
    <div class="col-6 align-content-center">
        <h3 class="text-truncate">${name}</h3>
    </div>
    <div class="col-4 align-content-center">
        <div class="mb-3 input-group">
            <input type="number" class="form-control" min="0" max="100" step="1" value="0" inputmode="decimal"/>
            <span class="input-group-text">%</span>
        </div>
    </div>
</div>`;
}

(async () => {
    const params = new URLSearchParams(window.location.search);
    const userIds = params.getAll('user_id');
    if (!userIds.length) return;

    const [meResponse, ...results] = await Promise.all([
        apiGet(API_USERS_ME),
        ...userIds.map(id => apiGet(`${API_FRIENDS}/${id}`))
    ]);

    const me = await meResponse.json();
    const friends = [{id: me.user_id, name: 'You'}];
    for (const response of results) {
        if (!response.ok) continue;
        friends.push(await response.json());
    }

    const chipList = document.getElementById('addexpense-step2-friend-list');
    const exactList = document.getElementById('addexpense-step2-modal-list-exact-amounts-list');
    const pctList = document.getElementById('addexpense-step2-modal-list-percentage-list');

    for (const friend of friends) {
        chipList.insertAdjacentHTML('beforeend', buildFriendChip(friend));
        exactList.insertAdjacentHTML('beforeend', buildExactAmountRow(friend));
        pctList.insertAdjacentHTML('beforeend', buildPercentageRow(friend));
    }

    const count = friends.length;
    const expenseInput = document.getElementById('addexpense-step2-expense-value');
    const expenseForm  = document.getElementById('addexpense-step2-expense-form');

    for (const friend of friends) {
        const hidden = document.createElement('input');
        hidden.type  = 'hidden';
        hidden.name  = `user_${friend.id}`;
        hidden.value = '0.00';
        expenseForm.appendChild(hidden);
    }

    function syncHiddenInputs() {
        getExactInputs().forEach((input, i) => {
            expenseForm.elements[`user_${friends[i].id}`].value = (parseFloat(input.value) || 0).toFixed(2);
        });
    }
    const paymentOptionsBtn = document.getElementById('paymentOptions');

    function updatePaymentOptionsBtn() {
        paymentOptionsBtn.disabled = (parseFloat(expenseInput.value) || 0) <= 0;
    }
    updatePaymentOptionsBtn();
    expenseInput.addEventListener('input', updatePaymentOptionsBtn);

    const exactError = document.getElementById('addexpense-step2-exact-error');
    const pctError   = document.getElementById('addexpense-step2-pct-error');

    function getExactInputs() { return [...exactList.querySelectorAll('input[type="number"]')]; }
    function getPctInputs()   { return [...pctList.querySelectorAll('input[type="number"]')]; }
    function sum(inputs) { return inputs.reduce((acc, el) => acc + (parseFloat(el.value) || 0), 0); }

    exactList.addEventListener('focusout', () => {
        const total = parseFloat(expenseInput.value) || 0;
        if (!total) return;
        getExactInputs().forEach((input, i) => {
            getPctInputs()[i].value = ((parseFloat(input.value) || 0) / total * 100).toFixed(2);
        });
        syncHiddenInputs();
        const diff = Math.abs(sum(getExactInputs()) - total);
        exactError.textContent = `Amounts must add up to $${total.toFixed(2)}`;
        exactError.classList.toggle('d-none', diff <= 0.01);
    });

    pctList.addEventListener('focusout', () => {
        const total = parseFloat(expenseInput.value) || 0;
        if (!total) return;
        getPctInputs().forEach((input, i) => {
            getExactInputs()[i].value = ((parseFloat(input.value) || 0) / 100 * total).toFixed(2);
        });
        syncHiddenInputs();
        const diff = Math.abs(sum(getPctInputs()) - 100);
        pctError.textContent = 'Percentages must add up to 100%';
        pctError.classList.toggle('d-none', diff <= 0.01);
    });

    expenseInput.addEventListener('blur', () => {
        const total = parseFloat(expenseInput.value) || 0;
        const perPerson = Math.floor(total / count * 100) / 100;
        const perPersonPct = Math.floor(100 / count * 100) / 100;

        const exactInputs = [...exactList.querySelectorAll('input[type="number"]')];
        const pctInputs = [...pctList.querySelectorAll('input[type="number"]')];

        exactInputs.forEach(input => { input.value = perPerson.toFixed(2); });
        pctInputs.forEach(input => { input.value = perPersonPct.toFixed(2); });

        const exactRemainder = (total - perPerson * count).toFixed(2);
        const pctRemainder = (100 - perPersonPct * count).toFixed(2);

        exactInputs[0].value = (perPerson + parseFloat(exactRemainder)).toFixed(2);
        pctInputs[0].value = (perPersonPct + parseFloat(pctRemainder)).toFixed(2);
        syncHiddenInputs();
    });
})();
