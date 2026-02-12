import base64
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import cloudscraper
from datetime import datetime, timedelta
import os

# Importamos tus módulos locales
from tvlibree_parser import parse_tvlibree_channel
from resolvers import resolve_url

AGENDA_URL = "https://tvlibree.com/agenda/"
# URL de la API (Render o Local según variable de entorno)
API_GO_URL = os.getenv("API_URL", "http://localhost:8080/api/agenda/update")
BASE_URL = "https://tvlibree.com"

scraper = cloudscraper.create_scraper()

def fix_time_offset(time_str):
    """
    TvLibree cambia la hora según la IP del visitante.
    GitHub Actions suele tener IP de UTC o Europa, lo que suma +4 horas.
    Esta función fuerza la resta de 4 horas para volver a hora Argentina.
    Entrada: "23:00" -> Salida: "19:00"
    Entrada: "04:00" -> Salida: "00:00"
    """
    try:
        # 1. Parsear la hora (ej: 23:00)
        dt = datetime.strptime(time_str, "%H:%M")
        
        # 2. Restar 4 horas
        new_dt = dt - timedelta(hours=4)
        
        # 3. Devolver como string limpio
        return new_dt.strftime("%H:%M")
    except Exception:
        # Si falla (ej: viene vacío), devolvemos lo que llegó
        return time_str

def get_deep_sources(relative_url):
    full_url = BASE_URL + relative_url if relative_url.startswith('/') else relative_url
    try:
        # print(f"      🕵️ Profundizando: {relative_url}")
        resp = scraper.get(full_url)
        resp.encoding = 'utf-8'
        html = resp.text
        raw_options = parse_tvlibree_channel(html)
        
        resolved_sources = []
        for opt in raw_options:
            resolved = resolve_url(opt['raw_url'])
            if resolved:
                resolved_sources.append({
                    "name": opt['name_display'],
                    "url": resolved['url'],
                    "type": resolved['type'],
                    "drm": resolved.get('drm')
                })
        return resolved_sources
    except Exception as e:
        print(f"      ⚠️ Error en deep crawl: {e}")
        return []

def parse_agenda():
    print(f"📅 Iniciando Crawler de Agenda...")
    
    # 1. FECHA: Forzamos hora Argentina (UTC-3) para la FECHA del evento
    utc_now = datetime.utcnow()
    arg_time = utc_now - timedelta(hours=3)
    current_date = arg_time.strftime("%Y-%m-%d")
    print(f"🕒 Fecha para base de datos: {current_date}")

    try:
        resp = scraper.get(AGENDA_URL)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        events = []
        
        list_items = soup.find_all('li')
        order_counter = 0 # Para mantener el orden visual de la página

        for li in list_items:
            # Ignoramos sub-items
            if 'subitem1' in li.get('class', []): continue
            
            link_tag = li.find('a', href="#")
            if not link_tag: continue
            
            # --- CORRECCIÓN DE HORA Y TÍTULO ---
            
            # 1. Extraemos el SPAN de la hora
            time_span = link_tag.find('span', class_='t')
            time_text_raw = ""
            
            if time_span:
                time_text_raw = time_span.get_text(strip=True)
                # ¡IMPORTANTE! Lo sacamos del árbol HTML para que no ensucie el título
                time_span.decompose()
            
            # 2. Corregimos el desfase horario (+4 horas -> Normal)
            final_time = fix_time_offset(time_text_raw)
            
            # 3. Obtenemos el título limpio (ya sin la hora adentro)
            title = link_tag.get_text(" ", strip=True).strip()
            
            if not title: continue

            # --- BUSCAR OPCIONES DE CANALES ---
            options_for_event = []
            sub_ul = li.find('ul')
            
            if sub_ul:
                sub_items = sub_ul.find_all('li', class_='subitem1')
                for sub in sub_items:
                    opt_a = sub.find('a')
                    if not opt_a: continue
                    
                    chan_name = str(opt_a.contents[0]).strip() if opt_a.contents else "Opción"
                    href = opt_a.get('href', '')

                    # Lógica de extracción
                    if "/en-vivo/" in href:
                        deep_chans = get_deep_sources(href)
                        for dc in deep_chans:
                            options_for_event.append({
                                "name": f"{chan_name} - {dc['name']}",
                                "url": dc['url'],
                                "type": dc['type'],
                                "drm": dc.get('drm')
                            })
                    elif "?r=" in href:
                        try:
                            parsed = urlparse(href)
                            params = parse_qs(parsed.query)
                            if 'r' in params:
                                decoded_url = base64.b64decode(params['r'][0]).decode('utf-8')
                                resolved = resolve_url(decoded_url)
                                options_for_event.append({
                                    "name": chan_name,
                                    "url": resolved['url'],
                                    "type": resolved['type'],
                                    "drm": resolved.get('drm')
                                })
                        except: pass

            # Solo agregamos si hay título y opciones
            if options_for_event:
                order_counter += 1
                events.append({
                    "title": title,
                    "time": final_time, # Usamos la hora corregida
                    "date": current_date,
                    "league": li.get('class')[0] if li.get('class') else "Varios",
                    "channels": options_for_event,
                    "order": order_counter # Guardamos el orden original
                })
                print(f"   ⚽ [{final_time}] {title} ({len(options_for_event)} opc)")

        # --- ENVIAR AL BACKEND ---
        if events:
            print(f"📤 Enviando {len(events)} eventos corregidos a Go...")
            try:
                r = requests.post(API_GO_URL, json={"events": events})
                if r.status_code == 200:
                    print("✅ Agenda actualizada correctamente.")
                else:
                    print(f"⚠️ El servidor respondió: {r.status_code}")
            except Exception as e:
                print(f"❌ Error enviando datos: {e}")
        else:
            print("⚠️ No se encontraron eventos válidos.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    parse_agenda()
