from pathlib import Path

def get_connection():
    import pyodbc
    from dotenv import dotenv_values

    env_dosyasi = Path(__file__).resolve().parent.parent / ".env"
    ayarlar = dotenv_values(env_dosyasi, interpolate=False)
    parola = ayarlar["DB_PASSWORD"].replace("}", "}}")

    baglanti_metni = (
        f"DRIVER={{{ayarlar['DB_DRIVER']}}};"
        f"SERVER={ayarlar['DB_HOST']};"
        f"PORT={ayarlar['DB_PORT']};"
        f"DATABASE={ayarlar['DB_NAME']};"
        f"UID={ayarlar['DB_USER']};"
        f"PWD={{{parola}}};"
    )

    return pyodbc.connect(baglanti_metni, timeout=5)
