(async () => {
    const response = await fetch(API_USERS_ME, {
        credentials: 'include',
    });
    if (response.status === 401) {
        window.location.href = 'signin.html?unauthenticatedUser=true';
    }
})();
