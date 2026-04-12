const rows = document.querySelectorAll(".friend-row");

rows.forEach(el => el.addEventListener('click', event => {
    const userId = el.getAttribute("data-el");

    if (userId){
        window.location.href=`friend-detail.html?user_id=${userId}`;
    }
}));

