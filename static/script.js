let currentUser = null;
const API = "http://127.0.0.1:8000";

// 1. Funkcja logowania
async function login() {
    const u = document.getElementById('user').value;
    const p = document.getElementById('pass').value;

    try {
        const response = await fetch(`${API}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: u, password: p})
        });

        if (response.ok) {
            currentUser = await response.json();
            // Przełączanie widoków
            document.getElementById('login-section').classList.add('hidden');
            document.getElementById('app-section').classList.remove('hidden');
            document.getElementById('welcome-msg').innerText = `Zalogowany jako: ${currentUser.username}`;
            loadReservations();
        } else {
            alert("Błędne dane! Spróbuj: nowak / 123");
        }
    } catch (error) {
        alert("Błąd: Upewnij się, że serwer FastAPI działa!");
    }
}

// 2. Dodawanie nowej rezerwacji
async function addReservation() {
    const sala = document.getElementById('sala').value;
    const data = document.getElementById('data').value;
    const godzina = document.getElementById('godzina').value;

    if (!sala || !data || !godzina) {
        alert("Wypełnij wszystkie pola!");
        return;
    }

    const payload = {
        sala: sala,
        data: data,
        godzina: godzina,
        user_id: currentUser.id
    };

    const response = await fetch(`${API}/rezerwuj`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });

    if (response.ok) {
        loadReservations(); // Odśwież listę po dodaniu
    }
}

// 3. Pobieranie listy rezerwacji z bazy
async function loadReservations() {
    const response = await fetch(`${API}/rezerwacje`);
    const data = await response.json();
    const list = document.getElementById('res-list');
    
    list.innerHTML = data.map(res => 
    `<li>
        <div style="display: inline-block; width: 80%;">
            <strong>Sala ${res[1]}</strong><br>
            Termin: ${res[2]} r. o godz. ${res[3]}<br>
            <small>Rezerwacja: ${res[4]}</small>
        </div>
    <button type="button" onclick="deleteReservation(${res[0]})" 
            style="width: auto; background: red; color: white; border: none; 
                   padding: 5px 10px; cursor: pointer; float: right;">
        X
    </button>
    <div style="clear: both;"></div>
    </li>`
    ).reverse().join(''); // Reverse, żeby najnowsze były na górze
}

async function deleteReservation(id) {
    if (confirm("Czy na pewno chcesz usunąć tę rezerwację?")) {
        try {
            const response = await fetch(`${API}/usun/${id}`, { method: 'DELETE' });
            if (response.ok) {
                loadReservations(); 
            } else {
                alert("Serwer zwrócił błąd przy usuwaniu.");
            }
        } catch (error) {
            alert("Nie można połączyć się z serwerem!");
        }
    }
}