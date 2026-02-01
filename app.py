from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

# KONFIGURACJA CORS: Pozwala przeglądarce łączyć się z serwerem Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# FUNKCJA POMOCNICZA: Łączenie z plikiem bazy danych
def get_db():
    conn = sqlite3.connect("uczelnia.db")
    return conn

# START: Tworzenie tabel przy uruchomieniu
with get_db() as conn:
    # Tabela 1: Prowadzący (Klucz główny: id)
    conn.execute("CREATE TABLE IF NOT EXISTS prowadzacy (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    
    # Tabela 2: Rezerwacje (Klucz obcy: prowadzacy_id)
    conn.execute("""CREATE TABLE IF NOT EXISTS rezerwacje (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    sala TEXT, data TEXT, godzina TEXT, 
                    prowadzacy_id INTEGER, 
                    FOREIGN KEY(prowadzacy_id) REFERENCES prowadzacy(id))""")
    
    # DODAWANIE ZIUTKOW 
    uzytkownicy = [
            ('nowak', '123'),
            ('kowalski', 'abc'),
            ('wisniewski', 'haslo789')
        ]
    conn.executemany(
            "INSERT OR IGNORE INTO prowadzacy (username, password) VALUES (?, ?)", 
            uzytkownicy
        )
    conn.commit()
    
# MODELE DANYCH: Definiują, co przesyłamy w formacie JSON
class LoginData(BaseModel):
    username: str
    password: str

class ResData(BaseModel):
    sala: str
    data: str
    godzina: str
    user_id: int

# --- ENDPOINTY (Trasy API) ---

@app.post("/login")
def login(data: LoginData):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM prowadzacy WHERE username=? AND password=?", (data.username, data.password))
        user = cursor.fetchone()
        if user:
            return {"id": user[0], "username": data.username}
        raise HTTPException(status_code=401, detail="Błędne dane logowania")

@app.post("/rezerwuj")
def add_res(res: ResData):
    with get_db() as conn:
        conn.execute("INSERT INTO rezerwacje (sala, data, godzina, prowadzacy_id) VALUES (?, ?, ?, ?)",
                     (res.sala, res.data, res.godzina, res.user_id))
        return {"msg": "Zarezerwowano!"}

@app.get("/rezerwacje")
def list_res():
    with get_db() as conn:
        cursor = conn.cursor()
        # JOIN: Łączymy tabele, by zamiast numeru ID widzieć nazwisko prowadzącego
        cursor.execute("""SELECT r.id, r.sala, r.data, r.godzina, p.username 
                          FROM rezerwacje r JOIN prowadzacy p ON r.prowadzacy_id = p.id""")
        return cursor.fetchall()

@app.delete("/usun/{res_id}")
def delete_res(res_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM rezerwacje WHERE id=?", (res_id,))
        return {"msg": "Usunięto"}

@app.get("/dodaj_usera")
def manual_add_user(user: str, haslo: str):
    with get_db() as conn:
        # INSERT OR IGNORE sprawia, że jeśli login 'user' już jest w bazie,
        # to po prostu nic się nie wydarzy (nie doda go drugi raz).
        conn.execute("INSERT OR IGNORE INTO prowadzacy (username, password) VALUES (?, ?)", (user, haslo))
        conn.commit()
        return {"status": "Gotowe", "info": f"Próbowano dodać: {user}"}
    