import base64
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import cloudscraper
from datetime import datetime # <--- VITAL

# Importamos tus herramientas
from tvlibree_parser import parse_tvlibree_channel
from resolvers import resolve_url

AGENDA_URL = "https://tvlibree.com/agenda/"
API_GO_URL = "http://localhost:8080/api/agenda/update"
BASE_URL = "https://tvlibree.com"

scraper = cloudscraper.create_scraper()

def get_deep_sources(relative_url):
    full_url = BASE_URL + relative_url if relative_url.startswith('/') else relative_url
    try:
        print(f"      🕵️ Entrando a profundizar: {relative_url}")
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
    print(f"📅 Obteniendo agenda profunda...")
    # --- SOLUCIÓN AL ERROR: Definir la fecha aquí arriba ---
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        resp = scraper.get(AGENDA_URL)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        events = []
        
        list_items = soup.find_all('li')

        for li in list_items:
            # Saltamos sub-elementos para no duplicar
            if 'subitem1' in li.get('class', []): continue
            
            link_tag = li.find('a', href="#")
            if not link_tag: continue
            
            time_span = link_tag.find('span', class_='t')
            time_text = time_span.get_text(strip=True) if time_span else ""
            title = link_tag.get_text(" ", strip=True).replace(time_text, "").strip()
            
            options_for_event = []
            sub_ul = li.find('ul')
            
            if sub_ul:
                sub_items = sub_ul.find_all('li', class_='subitem1')
                for sub in sub_items:
                    opt_a = sub.find('a')
                    if not opt_a: continue
                    
                    chan_name = opt_a.contents[0].strip()
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
                            decoded_url = base64.b64decode(params['r'][0]).decode('utf-8')
                            resolved = resolve_url(decoded_url)
                            options_for_event.append({
                                "name": chan_name,
                                "url": resolved['url'],
                                "type": resolved['type'],
                                "drm": resolved.get('drm')
                            })
                        except: pass

            if title and options_for_event:
                events.append({
                    "title": title,
                    "time": time_text,
                    "date": current_date, # <--- Ahora sí está definida
                    "league": li.get('class')[0] if li.get('class') else "Varios",
                    "channels": options_for_event
                })
                print(f"   ⚽ {title} resuelto ({len(options_for_event)} fuentes).")

        if events:
            # Enviar a GO
            print(f"📤 Enviando {len(events)} eventos al backend...")
            r = requests.post(API_GO_URL, json={"events": events})
            print(f"🎉 Respuesta del servidor: {r.status_code}")
        else:
            print("⚠️ No se encontraron eventos hoy.")

    except Exception as e:
        print(f"❌ Error general en la agenda: {e}")

if __name__ == "__main__":
    parse_agenda()
