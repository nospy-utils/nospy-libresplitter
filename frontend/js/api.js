const API_BASE = 'http://localhost:8080';
const API_USERS_SIGNUP = API_BASE + '/api/users/signup';
const API_USERS_ME = API_BASE + '/api/users/me';
const API_USERS_SIGNIN = API_BASE + '/api/users/signin';
const API_USERS_SIGNOUT = API_BASE + '/api/users/signout';
const API_FRIENDS = API_BASE + '/api/friends';
const API_EXPENSES_ME = API_BASE + '/api/expenses/me';
const API_EXPENSES_FRIEND = API_BASE + '/api/expenses/friend';
const API_EXPENSES_ACTIVITY = API_BASE + '/api/expenses/activity';

async function apiPost(url, body) {
    const MAX_RETRIES = 3;
    let attempt = 0;
    let response;

    while (attempt < MAX_RETRIES) {
        response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: body,
        });

        if (response.status !== 503) break;
        attempt++;
    }

    return response;
}

async function apiGet(url) {
    const MAX_RETRIES = 3;
    let attempt = 0;
    let response;

    while (attempt < MAX_RETRIES) {
        response = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
        });

        if (response.status !== 503) break;
        attempt++;
    }

    return response;
}