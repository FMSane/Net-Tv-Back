import requests
import re
import time
from bs4 import BeautifulSoup

# Configuración
TARGET_URL = "https://futbol-libre-ejemplo.com" # URL DE LA PORTADA
API_GO_URL = "http://localhost:8080/api/tv/update"

# Headers para parecer un navegador real (MUY IMPORTANTE)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://google.com'
}

def get_channels_from_home():
    """
    Fase 1: Escanear la portada y sacar la lista de canales disponibles.
    Devuelve una lista de diccionarios: [{'name': 'ESPN', 'link': '...'}, ...]
    """
    print(f"🕷️ Escaneando portada: {TARGET_URL}...")
    try:
        resp = requests.get(TARGET_URL, headers=HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        channels_found = []

        # AQUÍ ESTÁ LA MAGIA DEL CRAWLER:
        # Debes inspeccionar (F12) la portada para ver qué clase tienen los items.
        # Supongamos que cada canal es un <a class="btn-channel"> o está en un <div class="card">
        # Ejemplo genérico:
        items = soup.find_all('a', href=True) 

        for item in items:
            link = item['href']
            text = item.get_text().strip()

            # Filtramos basura: Solo queremos links que parezcan canales
            # (Esto depende del sitio, a veces tienen '/canal/' o '/ver/')
            if "/ver/" in link or "en-vivo" in link:
                
                # Corregir rutas relativas (si el link es "/ver/espn", agregar el dominio)
                if not link.startswith("http"):
                    link = TARGET_URL + link
                
                channels_found.append({
                    "name": text, # Ej: "ESPN Premium"
                    "link": link  # Ej: "https://sitio.com/ver/espn-premium"
                })

        # Eliminamos duplicados (a veces ponen el mismo link 2 veces)
        # Truco de Python para quitar duplicados en lista de dicts
        unique_channels = {v['name']:v for v in channels_found}.values()
        
        print(f"✅ Se encontraron {len(unique_channels)} canales potenciales.")
        return list(unique_channels)

    except Exception as e:
        print(f"❌ Error en la portada: {e}")
        return []

def extract_stream_url(channel_name, url):
    """
    Fase 2: Entrar al canal específico y buscar el tesoro (m3u8 o iframe).
    """
    print(f"   🔍 Analizando {channel_name}...")
    try:
        resp = requests.get(url, headers=HEADERS)
        html = resp.text
        
        # PATRÓN 1: Buscar token m3u8 directo (común en scripts)
        # Busca algo como: source: "https://...m3u8"
        m3u8_match = re.search(r'source:\s*["\'](.*?\.m3u8.*?)["\']', html)
        
        if m3u8_match:
            return {"type": "m3u8", "url": m3u8_match.group(1)}

        # PATRÓN 2: Buscar iframe (común en reproductores embed)
        iframe_match = re.search(r'<iframe.*?src=["\'](.*?)["\']', html)
        if iframe_match:
            return {"type": "iframe", "url": iframe_match.group(1)}
            
        # PATRÓN 3: Clappr Player (muy común en fútbol)
        if "clappr" in html.lower():
             # A veces está en una variable var player = ...
             pass 

        return None # No se encontró nada

    except Exception as e:
        print(f"   ⚠️ Error extrayendo {channel_name}: {e}")
        return None

def main():
    # 1. Obtener lista de la portada
    channels_list = get_channels_from_home()
    
    # 2. Recorrer cada canal
    for canal in channels_list:
        # Pausa de cortesía para no saturar al servidor (y evitar ban)
        time.sleep(1) 
        
        stream_data = extract_stream_url(canal['name'], canal['link'])
        
        if stream_data:
            print(f"   🎉 ÉXITO: {stream_data['type']} encontrado para {canal['name']}")
            
            # 3. Enviar a GO
            payload = {
                "name": canal['name'],
                "sources": [{
                    "name": "Opción Auto",
                    "url": stream_data['url'],
                    "type": stream_data['type'],
                    "priority": 1
                }]
            }
            # requests.post(API_GO_URL, json=payload) <--- Descomentar cuando Go esté listo
        else:
            print(f"   Fail: No se pudo extraer video.")

if __name__ == "__main__":
    main()
