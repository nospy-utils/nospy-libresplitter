const params = new URLSearchParams(window.location.search);

if (params.get('createdUser') === 'true') {
    document.getElementById('created-user-banner').classList.toggle('invisible');
}

if (params.get('unauthenticatedUser') === 'true') {
    document.getElementById('unauthenticated-user-banner').classList.toggle('invisible');
}

document.querySelector('form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const response = await apiPost(API_USERS_SIGNIN, JSON.stringify({ email, password }));

    if (response.ok) {
        window.location.href = 'friends.html';
        return;
    }

    const data = await response.json();
    const errorMessage = `${data.name} - ${data.description}`;

    const errorEl = document.getElementById('signin-error');
    errorEl.textContent = errorMessage;
    errorEl.classList.toggle('invisible');
});
