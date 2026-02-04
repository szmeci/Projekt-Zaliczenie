from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import sqlite3

# HASHOWANIE HASŁA 
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

app = FastAPI()

# KONFIGURACJA CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# LACZE SEI Z SQLITE
def get_db():
    conn = sqlite3.connect("uczelnia.db")
    return conn

# TABELE I UŻYTKOWNICY 
with get_db() as conn:
    cursor = conn.cursor()

    # tworzenie tabel
    conn.execute("CREATE TABLE IF NOT EXISTS prowadzacy (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS rezerwacje (id INTEGER PRIMARY KEY AUTOINCREMENT, sala TEXT, data TEXT, godzina TEXT, prowadzacy_id INTEGER, FOREIGN KEY(prowadzacy_id) REFERENCES prowadzacy(id))")
    
    # tworzenie kont
    konta = {
        'admin': 'admin'
    }

    # sprawdzamnie czy konto istnieje, jeśli nie to stworzenie
    for user, pw in konta.items():
        cursor.execute("SELECT 1 FROM prowadzacy WHERE username = ?", (user,))
        if not cursor.fetchone():
            conn.execute("INSERT INTO prowadzacy (username, password) VALUES (?, ?)", (user, pwd_context.hash(pw)))
            print(f" Utworzono konto: {user}")

    conn.commit()
    
# modele danych, co zbieraja co przesyłamy z javaScript postem 
class LoginData(BaseModel):
    username: str
    password: str

class ResData(BaseModel):
    sala: str
    data: str
    godzina: str
    user_id: int

# ---- ENDPOINTY ----
@app.post("/login")
def login(data: LoginData):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM prowadzacy WHERE username=?", (data.username,))
        user = cursor.fetchone()

        if user:
            user_id, hashed_password = user
            if pwd_context.verify(data.password, hashed_password):
                return {"id": user_id, "username": data.username}
        raise HTTPException(status_code=401, detail="Błędne dane logowania")

# Dodawanie rezerwacji
@app.post("/rezerwuj")
def add_res(res: ResData):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # pobieram istniejące rezerwacje dla danej sali i daty
        cursor.execute("SELECT godzina FROM rezerwacje WHERE sala=? AND data=?", (res.sala, res.data))
        istniejace_godziny = cursor.fetchall()

        # obliczam czas zakończenia rezerwacji
        nowy_start = datetime.strptime(res.godzina, "%H:%M")
        nowy_koniec = nowy_start + timedelta(minutes=90)

        # sprawdzam czy nowa rezerwacja koliduje z istniejącymi
        for (godz,) in istniejace_godziny:
            stary_start = datetime.strptime(godz, "%H:%M")
            stary_koniec = stary_start + timedelta(minutes=90)

            if nowy_start < stary_koniec and nowy_koniec > stary_start:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Sala zajęta. Kolizja z rezerwacją o godz. {godz} (trwa do {(stary_start + timedelta(minutes=90)).strftime('%H:%M')})"
                )

        conn.execute(
            "INSERT INTO rezerwacje (sala, data, godzina, prowadzacy_id) VALUES (?, ?, ?, ?)",
            (res.sala, res.data, res.godzina, res.user_id)
        )
        conn.commit()
        return {"msg": "Zarezerwowano!"}
    
# Usuwanie rezerwacji
@app.delete("/usun/{res_id}")
def delete_res(res_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM rezerwacje WHERE id=?", (res_id,))
        return {"msg": "Usunięto"}
    
# Pobieranie rezerwacji konkretnego użytkownika
@app.get("/moje-rezerwacje/{user_id}")
def get_my_res(user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, sala, data, godzina FROM rezerwacje WHERE prowadzacy_id = ?", (user_id,))
        rows = cursor.fetchall()
        return [{"id": r[0], "sala": r[1], "data": r[2], "godzina": r[3]} for r in rows]

# Sprawdzanie wszystkich rezerwacji z filtrami
@app.get("/sprawdz")
def check_res(sala: str = None, data: str = None):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT r.sala, r.data, r.godzina, p.username 
            FROM rezerwacje r 
            JOIN prowadzacy p ON r.prowadzacy_id = p.id 
            WHERE 1=1
        """
        params = []
        if sala:
            query += " AND r.sala = ?"
            params.append(sala)
        if data:
            query += " AND r.data = ?"
            params.append(data)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [{"sala": r[0], "data": r[1], "godzina": r[2], "kto": r[3]} for r in rows]


# (ADMIN)
# DODAWANIE UŻYTKOWNIKÓW (ADMIN)
@app.post("/dodaj-uzytkownika")
def add_user(data: LoginData):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            hashed_pw = pwd_context.hash(data.password)
            cursor.execute("INSERT INTO prowadzacy (username, password) VALUES (?, ?)", 
                           (data.username, hashed_pw))
            conn.commit()
            return {"msg": f"Użytkownik {data.username} dodany!"}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Ten użytkownik już istnieje!")
        
# Pobieranie listy wszystkich userow
@app.get("/uzytkownicy")
def get_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM prowadzacy WHERE username != 'admin'")
        rows = cursor.fetchall()
        return [{"id": r[0], "username": r[1]} for r in rows]

# Usuwanie użytkownika
@app.delete("/usun-uzytkownika/{user_id}")
def delete_user(user_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM prowadzacy WHERE id = ?", (user_id,))
        conn.execute("DELETE FROM rezerwacje WHERE prowadzacy_id = ?", (user_id,))
        conn.commit()
        return {"msg": "Użytkownik usunięty"}

# Zmiana hasła 
@app.put("/zmien-haslo")
def change_password(data: LoginData): 
    with get_db() as conn:
        hashed_pw = pwd_context.hash(data.password)
        conn.execute("UPDATE prowadzacy SET password = ? WHERE username = ?", (hashed_pw, data.username))
        conn.commit()
        return {"msg": f"Hasło dla {data.username} zmienione"}