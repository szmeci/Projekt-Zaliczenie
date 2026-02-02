from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

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

# TABELE DO BAZY 
with get_db() as conn:
    # TUTAJ TABELA DO PROWADZACYCH (ID, USERNAME, PASSWORD)
    conn.execute("CREATE TABLE IF NOT EXISTS prowadzacy (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    
    # TUTAJ TABELA DO REZERWACJI (ID, SALA, DATA, GODZINA, PROWADZACY_ID)
    conn.execute("""CREATE TABLE IF NOT EXISTS rezerwacje (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    sala TEXT, data TEXT, godzina TEXT, 
                    prowadzacy_id INTEGER, 
                    FOREIGN KEY(prowadzacy_id) REFERENCES prowadzacy(id))""")
    
    # DODAWANIE UZYTKOWNIKOW PRZYKLADOWYCH 
    uzytkownicy = [
            ('kacper.fedeczko', '123'),
            ('emil.kaczmarczyk', '123'),
            ('sebastian.ledwon', '123'),
            ('szmeksik', '123'),
            ('a', 'a')
        ]
    conn.executemany(
            "INSERT OR IGNORE INTO prowadzacy (username, password) VALUES (?, ?)", 
            uzytkownicy
        )
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
        cursor.execute("SELECT id FROM prowadzacy WHERE username=? AND password=?", (data.username, data.password))
        user = cursor.fetchone()
        if user:
            return {"id": user[0], "username": data.username}
        raise HTTPException(status_code=401, detail="Błędne dane logowania")

# Dodawanie rezerwacji
@app.post("/rezerwuj")
def add_res(res: ResData):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT id FROM rezerwacje WHERE sala=? AND data=? AND godzina=?"
        cursor.execute(query, (res.sala, res.data, res.godzina))
        istniejaca = cursor.fetchone()

    # sprawdzam czy sala jest wolna w tym terminie    
        if istniejaca:
            raise HTTPException(status_code=400, detail="Sala jest zajeta w tym terminie")
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
