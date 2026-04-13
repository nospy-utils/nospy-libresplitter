document.getElementById('signout-btn').addEventListener('click', async function () {
    await apiPost(API_USERS_SIGNOUT, '{}');
    window.location.href = 'signin.html';
});
