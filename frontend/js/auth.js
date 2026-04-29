(async () => {
    const response = await fetch(API_USERS_ME, {
        credentials: 'include',
    });

    if(window.location.pathname === '/' ||
            window.location.pathname.startsWith('/signin.html') ||
            window.location.pathname.startsWith('/signup.html')){

        if (response.status === 200){
            window.location.href = 'friends.html';
        }
    }else if (response.status === 401) {
        window.location.href = 'signin.html?unauthenticatedUser=true';
    }

})();
