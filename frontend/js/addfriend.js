document.querySelector('#addfriend-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    const email = document.getElementById('email').value;

    const response = await apiPost(API_FRIENDS, JSON.stringify({ email }));

    if (response.ok) {
        window.location.href = 'friends.html';
        return;
    }

    const data = await response.json();
    const errorEl = document.getElementById('addfriend-error');
    errorEl.textContent = `${data.name} - ${data.description}`;
    errorEl.style.display = 'block';
});
