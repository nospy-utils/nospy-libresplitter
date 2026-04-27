// flow variable
let userIds = [];
let friends = [];

// components
const expenseInput = document.getElementById('addexpense-step2-expense-value');
const chipList = document.getElementById('addexpense-step2-friend-list');
const exactList = document.getElementById('addexpense-step2-modal-list-exact-amounts-list');
const pctList = document.getElementById('addexpense-step2-modal-list-percentage-list');
const expenseForm = document.getElementById('addexpense-step2-expense-form');
const saveForm = document.getElementById('addexpense-step2-save-form');
const cancelButton = document.getElementById('cancel-btn');
const descriptionInput = document.getElementById('addexpense-step2-description');
const currencySelect = document.getElementById('addexpense-step2-currency');
const paymentOptionsBtn = document.getElementById('paymentOptions');
const modalCancelBtn1 = document.getElementById('addexpense-step2-modal-btn-cancel-1');
const modalCancelBtn2 = document.getElementById('addexpense-step2-modal-btn-cancel-2');


function buildFriendChip({name}) {
    return `<div class="d-inline-block addexpense-step2-friend-wrapper">
                <img class="d-inline" src="vendor/img/icons/person.svg" alt="placeholder"/>
                <h3 class="d-inline">${escapeHtml(name)}</h3>
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
                    <h3 class="text-truncate">${escapeHtml(name)}</h3>
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
                    <h3 class="text-truncate">${escapeHtml(name)}</h3>
                </div>
                <div class="col-4 align-content-center">
                    <div class="mb-3 input-group">
                        <input type="number" class="form-control" min="0" max="100" step="1" value="0" inputmode="decimal"/>
                        <span class="input-group-text">%</span>
                    </div>
                </div>
            </div>`;
}

// helper functions
function sum(inputs) {
    return inputs.reduce((acc, el) => acc + (parseFloat(el.value) || 0), 0);
}

function syncHiddenInputs() {
    getExactInputs().forEach((input, i) => {
        expenseForm.elements[`user_${friends[i].id}`].value = (parseFloat(input.value) || 0).toFixed(2);
    });
}

function updatePaymentOptionsBtn() {
    paymentOptionsBtn.disabled = (parseFloat(expenseInput.value) || 0) <= 0;
}

function getExactInputs() {
    return [...exactList.querySelectorAll('input[type="number"]')];
}

function getPctInputs() {
    return [...pctList.querySelectorAll('input[type="number"]')];
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-banner').classList.add('visible');
}

// meaningful functions
async function fetchDataFromUpstream() {
    const [meResponse, ...results] = await Promise.all([
        apiGet(API_USERS_ME),
        ...userIds.map(id => apiGet(`${API_FRIENDS}/${id}`))
    ]);

    const me = await meResponse.json();
    friends = [{id: me.user_id, name: 'You'}];
    for (const response of results) {
        if (!response.ok) continue;
        friends.push(await response.json());
    }
}

async function createDynamicElements() {
    for (const friend of friends) {
        chipList.insertAdjacentHTML('beforeend', buildFriendChip(friend));
        exactList.insertAdjacentHTML('beforeend', buildExactAmountRow(friend));
        pctList.insertAdjacentHTML('beforeend', buildPercentageRow(friend));
    }

    for (const friend of friends) {
        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = `user_${friend.id}`;
        hidden.value = '0.00';
        expenseForm.appendChild(hidden);
    }
}

async function saveExpense() {
    const description = descriptionInput.value.trim();
    const currency = currencySelect.value;
    const value = parseFloat(expenseInput.value) || 0;

    if (!description) {
        showError('Please enter a description.')
        return;
    }
    if (value <= 0) {
        showError('Please enter a valid expense amount.')
        return;
    }

    const participants = friends.map(friend => ({
        user_id: friend.id,
        share: parseFloat(expenseForm.elements[`user_${friend.id}`].value) || 0,
    }));

    const response = await apiPost(API_EXPENSES, JSON.stringify({description, currency, value, participants}));

    if (!response.ok) {
        const body = await response.json();
        const errorMessage = `${body.name} - ${body.description}`;
        showError(errorMessage);
        return;
    }

    if (userIds.length > 1) {
        window.location.href = 'friends.html';
    } else {
        window.location.href = `friend-detail.html?user_id=${userIds[0]}`;
    }
}

async function addEventListenerForUI() {
    cancelButton.addEventListener('click', () => history.back());

    saveForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveExpense();
    });

    expenseInput.addEventListener('input', updatePaymentOptionsBtn);

    const resetSplits = () => expenseInput.dispatchEvent(new Event('blur'));
    modalCancelBtn1.addEventListener('click', resetSplits);
    modalCancelBtn2.addEventListener('click', resetSplits);

    exactList.addEventListener('focusout', () => {
        const total = parseFloat(expenseInput.value) || 0;
        if (!total) return;
        getExactInputs().forEach((input, i) => {
            getPctInputs()[i].value = ((parseFloat(input.value) || 0) / total * 100).toFixed(2);
        });
        syncHiddenInputs();

        const diff = Math.abs(sum(getExactInputs()) - total);
        const exactError = document.getElementById('addexpense-step2-exact-error');
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
        const pctError = document.getElementById('addexpense-step2-pct-error');
        pctError.textContent = 'Percentages must add up to 100%';
        pctError.classList.toggle('d-none', diff <= 0.01);
    });

    expenseInput.addEventListener('blur', () => {
        const count = friends.length;
        const total = parseFloat(expenseInput.value) || 0;
        const perPerson = Math.floor(total / count * 100) / 100;
        const perPersonPct = Math.floor(100 / count * 100) / 100;

        const exactInputs = [...exactList.querySelectorAll('input[type="number"]')];
        const pctInputs = [...pctList.querySelectorAll('input[type="number"]')];

        exactInputs.forEach(input => {
            input.value = perPerson.toFixed(2);
        });
        pctInputs.forEach(input => {
            input.value = perPersonPct.toFixed(2);
        });

        const exactRemainder = (total - perPerson * count).toFixed(2);
        const pctRemainder = (100 - perPersonPct * count).toFixed(2);

        exactInputs[0].value = (perPerson + parseFloat(exactRemainder)).toFixed(2);
        pctInputs[0].value = (perPersonPct + parseFloat(pctRemainder)).toFixed(2);
        syncHiddenInputs();
    });
}


(async () => {
    const params = new URLSearchParams(window.location.search);
    userIds = params.getAll('user_id');
    if (!userIds.length) return;

    await fetchDataFromUpstream();
    await createDynamicElements();
    await addEventListenerForUI();
})();
