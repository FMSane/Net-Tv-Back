import base64
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import cloudscraper
from datetime import datetime, timedelta

# Importamos tus herramientas
from tvlibree_parser import parse_tvlibree_channel
from resolvers import resolve_url

AGENDA_URL = "https://tvlibree.com/agenda/"
# Recuerda: Si corre en GitHub, usa la variable de entorno. Si es local, usa localhost.
import os
API_GO_URL = os.getenv("API_URL", "http://localhost:8080/api/agenda/update")
BASE_URL = "https://tvlibree.com"

scraper = cloudscraper.create_scraper()

def get_deep_sources(relative_url):
    full_url = BASE_URL + relative_url if relative_url.startswith('/') else relative_url
    try:
        # print(f"      🕵️ Profundizando: {relative_url}") 
        # Comentamos el print para no saturar logs, solo errores
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
    
    # 1. CORRECCIÓN DE FECHA (Timezone Fix)
    # GitHub Actions corre en UTC. Argentina es UTC-3.
    # Restamos 3 horas para obtener la fecha real en Argentina.
    utc_now = datetime.utcnow()
    arg_time = utc_now - timedelta(hours=3)
    current_date = arg_time.strftime("%Y-%m-%d")
    print(f"🕒 Fecha detectada para Argentina: {current_date}")

    try:
        resp = scraper.get(AGENDA_URL)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        events = []
        
        list_items = soup.find_all('li')

        # Usamos un contador para preservar el orden visual de la página
        order_counter = 0

        for li in list_items:
            if 'subitem1' in li.get('class', []): continue
            
            link_tag = li.find('a', href="#")
            if not link_tag: continue
            
            # 2. CORRECCIÓN DE EXTRACCIÓN DE TÍTULO Y HORA
            # En lugar de replace, sacamos el elemento span del árbol HTML temporalmente
            time_span = link_tag.find('span', class_='t')
            time_text = ""
            
            if time_span:
                time_text = time_span.get_text(strip=True)
                # Eliminamos el span para que no se mezcle con el título
                time_span.decompose() 
            
            # Ahora link_tag solo tiene el texto del título
            title = link_tag.get_text(" ", strip=True).strip()
            
            # Si no hay hora o título, saltamos
            if not title: continue

            options_for_event = []
            sub_ul = li.find('ul')
            
            if sub_ul:
                sub_items = sub_ul.find_all('li', class_='subitem1')
                for sub in sub_items:
                    opt_a = sub.find('a')
                    if not opt_a: continue
                    
                    # Manejo seguro del nombre del canal
                    if opt_a.contents:
                        chan_name = str(opt_a.contents[0]).strip()
                    else:
                        chan_name = "Opción"

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
                    "time": time_text,
                    "date": current_date,
                    "league": li.get('class')[0] if li.get('class') else "Varios",
                    "channels": options_for_event,
                    "order": order_counter # <--- Nuevo campo para ordenar
                })
                print(f"   ⚽ [{time_text}] {title} ({len(options_for_event)} fuentes)")

        if events:
            print(f"📤 Enviando {len(events)} eventos al backend...")
            try:
                r = requests.post(API_GO_URL, json={"events": events})
                print(f"🎉 Respuesta del servidor: {r.status_code}")
            except Exception as e:
                print(f"❌ Error conectando al backend: {e}")
        else:
            print("⚠️ No se encontraron eventos válidos hoy.")

    except Exception as e:
        print(f"❌ Error critico en crawler: {e}")

if __name__ == "__main__":
    parse_agenda()
