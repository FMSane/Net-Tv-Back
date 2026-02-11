import base64
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import cloudscraper

# Importamos las herramientas que ya tenemos
from tvlibree_parser import parse_tvlibree_channel
from resolvers import resolve_url

AGENDA_URL = "https://tvlibree.com/agenda/"
API_GO_URL = "http://localhost:8080/api/agenda/update"
BASE_URL = "https://tvlibree.com"

scraper = cloudscraper.create_scraper()

def get_deep_sources(relative_url):
    """
    Entra a la página del canal (ej: /en-vivo/tudn/) y extrae 
    todas las opciones (Opción 1, 2, 3...) ya resueltas.
    """
    full_url = BASE_URL + relative_url if relative_url.startswith('/') else relative_url
    try:
        print(f"      🕵️ Entrando a profundizar: {relative_url}")
        html = scraper.get(full_url).text
        # Usamos el parser que ya teníamos para la home
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
    try:
        resp = scraper.get(AGENDA_URL)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        events = []
        
        # Seleccionamos los eventos (LI que no son subitems)
        list_items = soup.find_all('li')

        for li in list_items:
            if 'subitem1' in li.get('class', []): continue
            
            link_tag = li.find('a', href="#")
            if not link_tag: continue
            
            time_text = link_tag.find('span', class_='t').get_text(strip=True) if link_tag.find('span', class_='t') else ""
            title = link_tag.get_text(" ", strip=True).replace(time_text, "").strip()
            
            options_for_event = []
            sub_ul = li.find('ul')
            
            if sub_ul:
                sub_items = sub_ul.find_all('li', class_='subitem1')
                for sub in sub_items:
                    opt_a = sub.find('a')
                    if not opt_a: continue
                    
                    chan_name = opt_a.contents[0].strip()
                    href = opt_a.get('href')

                    # --- LÓGICA DE EXTRACCIÓN PROFUNDA ---
                    if "/en-vivo/" in href:
                        # Si es un canal de la parrilla, entramos a sacar sus 3 o 4 opciones
                        deep_chans = get_deep_sources(href)
                        for dc in deep_chans:
                            options_for_event.append({
                                "name": f"{chan_name} - {dc['name']}",
                                "url": dc['url'],
                                "type": dc['type'],
                                "drm": dc.get('drm')
                            })
                    else:
                        # Si es un link directo Base64 (?r=...)
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

            if title and options_for_event:
                events.append({
                    "title": title,
                    "time": time_text,
                    "date": current_date, # <--- ENVIAMOS LA FECHA
                    "league": li.get('class')[0] if li.get('class') else "Varios",
                    "channels": options_for_event
                })
                print(f"   ⚽ {title} resuelto con {len(options_for_event)} fuentes.")


        # Enviar a GO
        requests.post(API_GO_URL, json={"events": events})
        print("🎉 Agenda profunda enviada a Go.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    parse_agenda()
