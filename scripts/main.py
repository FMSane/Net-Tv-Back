import time
import cloudscraper
import requests

from dotenv import load_dotenv

# Importamos tus módulos
from crawler_home import parse_home_grid
from tvlibree_parser import parse_tvlibree_channel
from resolvers import resolve_url

load_dotenv()

API_GO_URL = os.getenv("API_URL_CHANNELS", "http://localhost:8080/api/tv/update-sources"
HOME_URL = "https://tvlibree.com" 

scraper = cloudscraper.create_scraper()

def main():
    print("🚀 INICIANDO ACTUALIZACIÓN PROFUNDA DE CANALES...")
    
    # 1. Obtener la lista de canales desde la portada (Filtrando Paraguay y Adultos)
    try:
        home_html = scraper.get(HOME_URL).text
        channel_list = parse_home_grid(home_html)
        print(f"✅ Se encontraron {len(channel_list)} canales para procesar.")
    except Exception as e:
        print(f"❌ Error conectando a la home: {e}")
        return

    # 2. Deep Crawl: Entrar a cada canal para sacar sus fuentes reales
    for i, canal in enumerate(channel_list):
        # Mostramos progreso
        print(f"\n[{i+1}/{len(channel_list)}] 📺 Canal: {canal['name']} ({canal['category']})")
        
        try:
            # A. Entramos a la URL del canal (ej: tvlibree.com/en-vivo/telefe)
            resp = scraper.get(canal['url'])
            resp.encoding = 'utf-8' # Evitar problemas de tildes
            channel_html = resp.text
            
            # B. Extraemos los botones (Opción 1, 2, 3...)
            # Esta función ya maneja tu lógica de Nebunexa (/fl/ -> nebunexa.life)
            raw_options = parse_tvlibree_channel(channel_html)
            
            final_sources = []

            # C. Resolvemos cada opción (Convertimos URLs a streamings reales)
            for opt in raw_options:
                # resolve_url se encarga de convertir nebunexa.life a DASH .mpd con DRM
                resolved = resolve_url(opt['raw_url'])
                
                if resolved:
                    final_sources.append({
                        "name": opt['name_display'],
                        "url": resolved['url'],
                        "type": resolved['type'],
                        "drm": resolved.get('drm'),
                        "headers": resolved.get('headers'),
                        "priority": 1
                    })
                    print(f"      🔗 Fuente hallada: {opt['name_display']} ({resolved['type']})")

            # D. Si encontramos fuentes, enviamos a Go
            if final_sources:
                payload = {
                    "name": canal['name'],
                    "category": canal['category'],
                    "logo": canal['logo'],
                    "sources": final_sources
                }
                
                try:
                    r = requests.post(API_GO_URL, json=payload)
                    if r.status_code == 200:
                        print(f"      ✅ Guardado en DB con {len(final_sources)} opciones.")
                    else:
                        print(f"      ⚠️ Error Go: {r.status_code}")
                except:
                    print("      ❌ Error de conexión con el Backend.")
            else:
                print("      ⚠️ No se encontraron fuentes válidas dentro del canal.")

            # Pausa para no ser baneados por exceso de peticiones
            time.sleep(0.5)

        except Exception as e:
            print(f"      ❌ Error procesando canal: {e}")

if __name__ == "__main__":
    main()
