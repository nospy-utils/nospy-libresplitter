const PAGE_SIZE = 10;
let currentPage = 0;
let hasNext = true;
let isLoading = false;
let scrollObserver;

const loadingContainer = document.getElementById('addexpensestep1-loadingpage-container');
const contentContainer = document.getElementById('addexpensestep1-content-container');

function hideLoadingContainer(){
    loadingContainer.classList.add('invisible');
    loadingContainer.classList.add('d-none');
    contentContainer.classList.remove('invisible');
    contentContainer.classList.remove('d-none');
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

function buildFriendRow({id, name}) {
    return `
    <div class="row py-2" data-friend-id="${escapeHtml(String(id))}">
        <div class="col-sm-2 col-lg-1 d-none d-sm-block">
            <div class="addexpense-step1-friend-thumbnail">
                <img src="vendor/img/icons/person.svg" alt="placeholder"/>
            </div>
        </div>
        <div class="col-sm-10 col-lg-11 align-content-center">
            <div class="addexpense-step1-list-name">
                <h3>${escapeHtml(name)}</h3>
            </div>
            <div class="addexpense-step1-list-input">
                <input class="form-check-input addexpense-radio-input friend-checkbox" type="checkbox" data-friend-id="${escapeHtml(String(id))}">
            </div>
        </div>
    </div>`;
}

function appendFriends(friends) {
    const list = document.getElementById('friends-list');
    friends.forEach(friend => {
        const tmp = document.createElement('div');
        tmp.innerHTML = buildFriendRow(friend).trim();
        list.appendChild(tmp.firstChild);
    });
}

async function loadNextPage() {
    if (isLoading || !hasNext) return;
    isLoading = true;
    showSpinner();

    const response = await apiGet(`${API_FRIENDS_RECENT}?page=${currentPage + 1}&page_size=${PAGE_SIZE}`);
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

    appendFriends(data.friends);
    hideSpinner();

    if (!hasNext && scrollObserver) {
        scrollObserver.disconnect();
    }
}

document.getElementById('cancel-btn').addEventListener('click', () => history.back());

document.getElementById('save-btn').addEventListener('click', () => {
    const checked = document.querySelectorAll('.friend-checkbox:checked');
    const params = new URLSearchParams();
    checked.forEach(cb => params.append('user_id', cb.dataset.friendId));
    window.location.href = `addexpense-step2.html?${params.toString()}`;
});

(async () => {
    const response = await apiGet(`${API_FRIENDS_RECENT}?page=1&page_size=${PAGE_SIZE}`);

    hideLoadingContainer();
    if (!response.ok) {
        const { name, description } = await response.json();
        const errorMessage = `${name} - ${description}`;
        showError(errorMessage);
        return;
    }

    const data = await response.json();
    currentPage = data.page;
    hasNext = data.has_next;

    if (data.total === 0) {
        document.getElementById('friends-list').innerHTML =
            '<div class="row py-2"><div class="col text-muted">No recent friends.</div></div>';
    } else {
        appendFriends(data.friends);
    }

    if (hasNext) {
        const sentinel = document.getElementById('scroll-sentinel');
        scrollObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) loadNextPage();
        }, {threshold: 0.1});
        scrollObserver.observe(sentinel);
    }
})();
