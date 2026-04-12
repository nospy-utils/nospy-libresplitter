document.querySelector('form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const response = await apiPost(API_USERS_SIGNUP, JSON.stringify({ name, email, password }));

    if (response.ok) {
        window.location.href = 'signin.html?createdUser=true';
        return;
    }

    let errorMessage;
    try {
        const data = await response.json();
        errorMessage = data.error || data.message || JSON.stringify(data);
    } catch {
        errorMessage = await response.text();
    }

    const errorEl = document.getElementById('signup-error');
    errorEl.textContent = errorMessage;
    errorEl.style.display = 'block';
});
