import base64
import requests
import time
import re  # <--- NUEVA IMPORTACIÓN
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import cloudscraper
from datetime import datetime, timedelta
import os

from dotenv import load_dotenv

# Importamos tus módulos locales
from tvlibree_parser import parse_tvlibree_channel
from resolvers import resolve_url

load_dotenv()

AGENDA_URL = "https://tvlibree.com/agenda/"
# URL de la API (Render o Local según variable de entorno)
API_GO_URL = os.getenv("API_URL_AGENDA", "http://localhost:8080/api/agenda/update")
BASE_URL = "https://tvlibree.com"

scraper = cloudscraper.create_scraper()

def fix_time_offset(time_str):
    """
    TvLibree cambia la hora según la IP del visitante.
    GitHub Actions suele tener IP de UTC o Europa, lo que suma +4 horas.
    Esta función fuerza la resta de 4 horas para volver a hora Argentina.
    """
    try:
        dt = datetime.strptime(time_str, "%H:%M")
        new_dt = dt - timedelta(hours=4)
        return new_dt.strftime("%H:%M")
    except Exception:
        return time_str

def get_deep_sources(relative_url):
    full_url = BASE_URL + relative_url if relative_url.startswith('/') else relative_url
    try:
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
    
    # 1. FECHA: Forzamos hora Argentina (UTC-3)
    utc_now = datetime.utcnow()
    arg_time = utc_now - timedelta(hours=3)
    current_date = arg_time.strftime("%Y-%m-%d")
    print(f"🕒 Fecha para base de datos: {current_date}")

    try:
        resp = scraper.get(AGENDA_URL)
        resp.encoding = 'utf-8'
        html_text = resp.text # Guardamos el texto crudo para buscar el CSS
        
        soup = BeautifulSoup(html_text, 'html.parser')
        events = []
        
        list_items = soup.find_all('li')
        order_counter = 0

        for li in list_items:
            if 'subitem1' in li.get('class', []): continue
            
            link_tag = li.find('a', href="#")
            if not link_tag: continue
            
            # --- CORRECCIÓN DE HORA Y TÍTULO ---
            time_span = link_tag.find('span', class_='t')
            time_text_raw = ""
            
            if time_span:
                time_text_raw = time_span.get_text(strip=True)
                time_span.decompose()
            
            final_time = fix_time_offset(time_text_raw)
            title = link_tag.get_text(" ", strip=True).strip()
            
            if not title: continue

            # --- NUEVO: EXTRACCIÓN DE IMAGEN DESDE CSS O PATRÓN ---
            li_classes = li.get('class', [])
            league_class = li_classes[0] if li_classes else ""
            league_name = league_class if league_class else "Varios"
            image_url = ""

            if league_class:
                # 1. Intentamos buscar la regla CSS exacta en el HTML crudo
                # Busca algo como: .FIH::before { background-image: url(https://bestleague.world/img/fih.webp); }
                pattern = rf"\.{league_class}[^}}]+background-image:\s*url\(['\"]?(.*?)['\"]?\)"
                match = re.search(pattern, html_text, re.IGNORECASE)
                
                if match:
                    raw_img_url = match.group(1)
                    if raw_img_url.startswith('http'):
                        image_url = raw_img_url
                    elif raw_img_url.startswith('//'):
                        image_url = "https:" + raw_img_url
                    else:
                        image_url = f"https://bestleague.world{raw_img_url}"
                else:
                    # 2. Si no encuentra el CSS (quizás está en un archivo externo), adivinamos la URL
                    image_url = f"https://bestleague.world/img/{league_class.lower()}.webp"
            # --------------------------------------------------------

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

            if options_for_event:
                order_counter += 1
                events.append({
                    "title": title,
                    "time": final_time,
                    "date": current_date,
                    "league": league_name,
                    "image": image_url, # <--- ENVIAMOS LA IMAGEN AL BACKEND
                    "channels": options_for_event,
                    "order": order_counter 
                })
                print(f"   ⚽ [{final_time}] {title} | 🖼️ {image_url}")

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
