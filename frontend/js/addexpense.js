function buildFriendChip({name}) {
    return `<div class="d-inline-block addexpense-step2-friend-wrapper">
    <img class="d-inline" src="vendor/img/icons/person.svg" alt="placeholder"/>
    <h3 class="d-inline">${name}</h3>
</div>`;
}

function buildEqualShareRow({name}) {
    return `<div class="row py-2">
    <div class="col-2">
        <div class="addexpense-modal-friend-thumbnail">
            <img src="vendor/img/icons/person.svg" alt="placeholder"/>
        </div>
    </div>
    <div class="col-10 align-content-center">
        <div class="addexpense-modal-list-name"><h3>${name}</h3></div>
        <div class="addexpense-modal-list-input">
            <input class="form-check-input addexpense-radio-input" type="checkbox" checked>
        </div>
    </div>
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

    const results = await Promise.all(
        userIds.map(id => apiGet(`${API_FRIENDS}/${id}`))
    );

    const friends = [];
    for (const response of results) {
        if (!response.ok) continue;
        friends.push(await response.json());
    }

    const chipList = document.getElementById('addexpense-step2-friend-list');
    const equalList = document.getElementById('addexpense-step2-modal-list-equal-share-list');
    const exactList = document.getElementById('addexpense-step2-modal-list-exact-amounts-list');
    const pctList = document.getElementById('addexpense-step2-modal-list-percentage-list');

    const you = {id: currentUser?.user_id, name: 'You'};
    equalList.insertAdjacentHTML('beforeend', buildEqualShareRow(you));
    exactList.insertAdjacentHTML('beforeend', buildExactAmountRow(you));
    pctList.insertAdjacentHTML('beforeend', buildPercentageRow(you));

    for (const friend of friends) {
        chipList.insertAdjacentHTML('beforeend', buildFriendChip(friend));
        equalList.insertAdjacentHTML('beforeend', buildEqualShareRow(friend));
        exactList.insertAdjacentHTML('beforeend', buildExactAmountRow(friend));
        pctList.insertAdjacentHTML('beforeend', buildPercentageRow(friend));
    }
})();
