const params = new URLSearchParams(window.location.search);

if (params.get('createdUser') === 'true') {
    document.getElementById('created-user-banner').style.display = 'block';
}

if (params.get('unauthenticatedUser') === 'true') {
    document.getElementById('unauthenticated-user-banner').style.display = 'block';
}
