const API_BASE = 'http://localhost:5000';
const API_USERS_SIGNUP = API_BASE + '/api/users/signup';
const API_USERS_ME = API_BASE + '/api/users/me';

async function apiPost(url, body) {
    const MAX_RETRIES = 3;
    let attempt = 0;
    let response;

    while (attempt < MAX_RETRIES) {
        response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body,
        });

        if (response.status !== 503) break;
        attempt++;
    }

    return response;
}