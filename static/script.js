let currentUser = null;
const API = "http://127.0.0.1:8000";

document.getElementById('data').min = new Date().toISOString().split("T")[0];

// FUNKCJA DO LOGOWANIA
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
            showSection('main-menu');
        } else {
            alert("jak cos wszedzie jest imie.nazwisko i 123 hasla ok");
        }
    } catch (error) {
        alert("Błąd: Upewnij się, że serwer FastAPI działa!");
    }
}

// FUNKCJA DODAWANIA REZERWACJI
async function addReservation() {
    const sala = document.getElementById('sala').value;
    const data = document.getElementById('data').value;
    const godzina = document.getElementById('godzina').value;

    //sprawdza czy wszystkie pola są wypełnione
    if (!sala || !data || !godzina) {
        alert("Wypełnij wszystkie pola!");
        return;
    }

// SPRAWDZANIE DATY I GODZINY
    const wybranaData = new Date(data);
    const dzis = new Date();
    dzis.setHours(0, 0, 0, 0); 

    // sprawdza czy data nie jest w przeszłości
    if (wybranaData < dzis) {
        alert("ten dzien juz byl");
        return;
    }

    //  sprawdza czy godzina jest w przedziale 7-19
    const godzinaH = parseInt(godzina.split(":")[0]); 
    if (godzinaH < 7 || godzinaH >= 19) {
        alert("mozna rezerwowac sale tylko w godzinach 7-19");
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
        alert("Dokonano rezerwacji!");
        loadUserReservations(); 
    } else {
        const errorData = await response.json();
        alert("uwaga: " + errorData.detail);
    }
}

// FUNKCJA USUWANIA REZERWACJI
async function deleteReservation(id) {
    if (confirm("Czy na pewno chcesz usunąć tę rezerwację?")) {
        try {
            const response = await fetch(`${API}/usun/${id}`, { method: 'DELETE' });
            if (response.ok) {
                loadUserReservations(); 
            } else {
                alert("Serwer zwrócił błąd przy usuwaniu.");
            }
        } catch (error) {
            alert("Nie można połączyć się z serwerem!");
        }
    }
}

// FUNKCJA WYLOGOWANIA
function logout() {
    currentUser = null;

    document.getElementById('user').value = "";
    document.getElementById('pass').value = "";

    document.getElementById('app-section').classList.add('hidden');
    document.getElementById('login-section').classList.remove('hidden');

    console.log("Użytkownik został wylogowany.");
}

// FUNKCJA ZARZADZANIA WIDOKIEM SEKCJI
function showSection(sectionId) {
    // Ukrywamy wszystkie części panelu aplikacji
    document.getElementById('main-menu').classList.add('hidden');
    document.getElementById('check-section').classList.add('hidden');
    document.getElementById('new-res-section').classList.add('hidden');

    // Pokazujemy tę, którą chcemy
    document.getElementById(sectionId).classList.remove('hidden');

    // Jeśli wchodzimy w nową rezerwację, odświeżamy listę usera
    if (sectionId === 'new-res-section') {
        loadUserReservations();
    }
}

// FUNKCJA WYPISYWANIA REZERWACJI ZALOGOWANEGO UŻYTKOWNIKA
async function loadUserReservations() {
    const response = await fetch(`${API}/moje-rezerwacje/${currentUser.id}`);
    const data = await response.json();
    const list = document.getElementById('res-list-user');
    
    list.innerHTML = data.map(res => {
            const [h, m] = res.godzina.split(':').map(Number);
            
            const dateObj = new Date();
            dateObj.setHours(h, m, 0);
            dateObj.setMinutes(dateObj.getMinutes() + 90);
            
            const godzinaKonca = dateObj.toTimeString().slice(0, 5);

            return `<li>
                <div class="res-info">
                    <strong>Sala ${res.sala}</strong><br>
                    <span> ${res.data}</span><br>
                    <span> ${res.godzina} — ${godzinaKonca} <small>(90 min)</small></span>
                </div>
                <button onclick="deleteReservation(${res.id})" class="delete-btn">×</button>
            </li>`;
        }).reverse().join('');
}

// FUNKCJA SPRAWDZANIA REZERWACJI Z FILTREM
async function loadFilteredReservations() {
    const sala = document.getElementById('filter-sala').value;
    const data = document.getElementById('filter-data').value;

    let url = `${API}/sprawdz?`;
    if (sala) url += `sala=${sala}&`;
    if (data) url += `data=${data}`;

    const response = await fetch(url);
    const reservations = await response.json();
    const list = document.getElementById('res-list-all');
    
    list.innerHTML = reservations.map(res => {
        const [h, m] = res.godzina.split(':');
        const date = new Date();
        date.setHours(h, m);
        date.setMinutes(date.getMinutes() + 90);
        const godzinaKonca = date.toTimeString().slice(0, 5);

        return `<li>
            <strong>Sala ${res.sala}</strong> | ${res.data}<br>
            🕒 ${res.godzina} - ${godzinaKonca} (90 min)<br>
            <small>Zarezerwował: ${res.kto}</small>
        </li>`;
    }).join('');
}