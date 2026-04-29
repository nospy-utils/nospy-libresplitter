const params = new URLSearchParams(window.location.search);

if (params.get('createdUser') === 'true') {
    const cubEl = document.getElementById('created-user-banner');
    cubEl.classList.toggle('invisible');
    cubEl.classList.toggle('d-none');
}

if (params.get('unauthenticatedUser') === 'true') {
    const uub = document.getElementById('unauthenticated-user-banner');
    uub.classList.toggle('invisible');
    uub.classList.toggle('d-none');
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
    errorEl.classList.toggle('d-none');
});


document.getElementById('signin-button-signup').addEventListener('click', ()=> window.location.href='/signup.html');
