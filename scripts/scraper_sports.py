import requests
import re
from bs4 import BeautifulSoup

# Configuración
API_URL = "http://localhost:8080/api/tv/update-sources"
API_SECRET = "tu_token_secreto_interno" 

def get_espn_link():
    """
    Lógica sucia de scraping.
    Ejemplo ficticio: Entrar a una web pirata y sacar el m3u8
    """
    try:
        # 1. Fingir ser un navegador
        headers = {'User-Agent': 'Mozilla/5.0...'}
        
        # 2. Petición a la web fuente (ej: futbollibre-fake.com)
        response = requests.get("https://web-fuente.com/ver/espn", headers=headers)
        
        # 3. Buscar el m3u8 con Regex o BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Supongamos que encontramos el link en un script variable
        m3u8_match = re.search(r'source: "(.*?\.m3u8)"', response.text)
        
        if m3u8_match:
            return m3u8_match.group(1)
        return None
    except Exception as e:
        print(f"Error scraping: {e}")
        return None

def main():
    new_link = get_espn_link()
    
    if new_link:
        print(f"Nuevo link encontrado: {new_link}")
        
        payload = {
            "name": "ESPN",
            "sources": [
                {
                    "name": "Opción HD (Auto)",
                    "url": new_link,
                    "type": "direct_m3u8",
                    "priority": 1
                }
            ]
        }
        
        # Enviamos la data a GO
        resp = requests.post(API_URL, json=payload)
        if resp.status_code == 200:
            print("Base de datos actualizada con éxito via API Go")
        else:
            print(f"Error actualizando API: {resp.status_code}")

if __name__ == "__main__":
    main()
