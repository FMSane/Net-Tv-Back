import base64
import requests
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import cloudscraper
from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv

# Importamos tus módulos locales
from tvlibree_parser import parse_tvlibree_channel
from resolvers import resolve_url

load_dotenv()

# --- VARIABLES DINÁMICAS DESDE EL .ENV ---
TVLIBRE_DOMAIN = os.getenv("TVLIBRE_DOMAIN", "https://tvlibreonline.tv/")
DL_DOMAIN = os.getenv("DL_DOMAIN", "https://deporte-libre.online")

AGENDA_URL = f"{TVLIBRE_DOMAIN}/agenda/"
DL_AGENDA_URL = f"{DL_DOMAIN}/"

API_GO_URL = os.getenv("API_URL_AGENDA", "http://localhost:8080/api/agenda/update")
BASE_URL_TVLIBRE = TVLIBRE_DOMAIN
BASE_URL_DL = DL_DOMAIN

scraper = cloudscraper.create_scraper()

# ==========================================
# UTILIDADES DE FECHA Y HORA
# ==========================================

def get_current_arg_date():
    utc_now = datetime.now(timezone.utc)
    arg_time = utc_now - timedelta(hours=3)
    return arg_time.strftime("%Y-%m-%d")

def fix_time_offset(time_str):
    try:
        dt = datetime.strptime(time_str, "%H:%M")
        new_dt = dt - timedelta(hours=4)
        return new_dt.strftime("%H:%M")
    except Exception:
        return time_str

def fix_spain_to_arg_time(time_str):
    try:
        dt = datetime.strptime(time_str, "%H:%M")
        new_dt = dt - timedelta(hours=5)
        return new_dt.strftime("%H:%M")
    except Exception:
        return time_str

# ==========================================
# CRAWLERS PROFUNDOS (DEEP CRAWLERS)
# ==========================================

def get_tvlibre_deep_sources(relative_url):
    full_url = BASE_URL_TVLIBRE + relative_url if relative_url.startswith('/') else relative_url
    try:
        resp = scraper.get(full_url)
        resp.encoding = 'utf-8'
        html = resp.text
        raw_options = parse_tvlibree_channel(html)
        
        resolved_sources = []
        if raw_options:
            for opt in raw_options:
                resolved = resolve_url(opt['raw_url'])
                if resolved:
                    resolved_sources.append({
                        "name": opt['name_display'],
                        "url": resolved['url'],
                        "type": resolved['type'],
                        "drm": resolved.get('drm')
                    })
                    
        # FALLBACK: Si no hay opciones (botones), buscar el iframe directo en el HTML
        if not resolved_sources:
            soup = BeautifulSoup(html, 'html.parser')
            iframe = soup.find('iframe', id='miIframe') or soup.find('iframe', class_='shadow-lg')
            if iframe and iframe.get('src'):
                resolved_sources.append({"name": "Opción Directa", "url": iframe['src'], "type": "iframe", "drm": None})
            else:
                match_embed = re.search(r"atob\(['\"](.*?)['\"]\)", html)
                if match_embed:
                    decoded_url = base64.b64decode(match_embed.group(1)).decode('utf-8')
                    resolved_sources.append({"name": "Opción Directa", "url": decoded_url, "type": "iframe", "drm": None})
                    
        return resolved_sources
    except Exception as e:
        print(f"      ⚠️ Error en deep crawl TVLibre: {e}")
        return []

def get_deporte_libre_sources(relative_url):
    full_url = BASE_URL_DL + relative_url if relative_url.startswith('/') else relative_url
    sources = []
    try:
        resp = scraper.get(full_url)
        resp.encoding = 'utf-8'
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        
        botones = soup.find_all('a', attrs={'target': 'iframe'})
        for i, btn in enumerate(botones):
            href = btn.get('href', '')
            if href and href != "#" and not href.startswith('#'):
                resolved = resolve_url(href) if href.startswith('http') else None
                sources.append({
                    "name": f"{btn.text.strip()}",
                    "url": resolved['url'] if resolved else href,
                    "type": resolved['type'] if resolved else "iframe",
                    "drm": resolved.get('drm') if resolved else None
                })
        
        if not sources:
            iframe = soup.find('iframe', id='miIframe') or soup.find('iframe', class_='shadow-lg')
            if iframe and iframe.get('src'):
                sources.append({"name": "Opción Directa", "url": iframe['src'], "type": "iframe", "drm": None})
            else:
                match_embed = re.search(r"atob\(['\"](.*?)['\"]\)", html)
                if match_embed:
                    decoded_url = base64.b64decode(match_embed.group(1)).decode('utf-8')
                    sources.append({"name": "Opción Directa (Decodificada)", "url": decoded_url, "type": "iframe", "drm": None})
    except Exception:
        pass
    return sources

# ==========================================
# SCRAPERS DE AGENDAS
# ==========================================

def get_tvlibre_events(current_date):
    print("📺 Extrayendo eventos de TvLibre...")
    events = []
    try:
        resp = scraper.get(AGENDA_URL)
        resp.encoding = 'utf-8'
        html_text = resp.text
        soup = BeautifulSoup(html_text, 'html.parser')
        list_items = soup.find_all('li')
        order_counter = 0

        for li in list_items:
            if 'subitem1' in li.get('class', []): continue
            
            link_tag = li.find('a')
            if not link_tag: continue
            
            time_span = link_tag.find('span', class_='t')
            if not time_span: continue
            
            time_text_raw = time_span.get_text(strip=True)
            time_span.decompose()
            final_time = fix_time_offset(time_text_raw)
            
            title = link_tag.get_text(" ", strip=True).strip()
            if not title: continue

            li_classes = li.get('class', [])
            league_class = li_classes[0] if li_classes else ""
            league_name = league_class if league_class else "Varios"
            image_url = ""

            if league_class:
                pattern = rf"\.{league_class}[^}}]+background-image:\s*url\(['\"]?(.*?)['\"]?\)"
                match = re.search(pattern, html_text, re.IGNORECASE)
                if match:
                    raw_img_url = match.group(1)
                    if raw_img_url.startswith('http'): image_url = raw_img_url
                    elif raw_img_url.startswith('//'): image_url = "https:" + raw_img_url
                    else: image_url = f"https://bestleague.world{raw_img_url}"
                else:
                    image_url = f"https://bestleague.world/img/{league_class.lower()}.webp"

            options_for_event = []
            sub_ul = li.find('ul')
            if sub_ul:
                sub_items = sub_ul.find_all('li', class_='subitem1')
                for sub in sub_items:
                    opt_a = sub.find('a')
                    if not opt_a: continue
                    
                    chan_name = str(opt_a.contents[0]).strip() if opt_a.contents else "Opción"
                    href = opt_a.get('href', '')

                    if "/en-vivo/" in href or "/canal/" in href:
                        deep_chans = get_tvlibre_deep_sources(href)
                        if deep_chans:
                            for dc in deep_chans:
                                options_for_event.append({
                                    "name": f"TVL: {chan_name} - {dc['name']}",
                                    "url": dc['url'],
                                    "type": dc['type'],
                                    "drm": dc.get('drm')
                                })
                        else:
                            # FALLBACK: Si no encuentra botones ni iframes
                            options_for_event.append({
                                "name": f"TVL: {chan_name}",
                                "url": BASE_URL_TVLIBRE + href if href.startswith('/') else href,
                                "type": "iframe",
                                "drm": None
                            })
                        time.sleep(0.3)
                        
                    elif "?r=" in href or "?embed=" in href:
                        try:
                            parsed = urlparse(href)
                            params = parse_qs(parsed.query)
                            raw_val = params.get('r', params.get('embed', [None]))[0]
                            
                            if raw_val:
                                # SOLUCIÓN: Reparador matemático de Padding Base64
                                raw_val += "=" * ((4 - len(raw_val) % 4) % 4)
                                decoded_url = base64.b64decode(raw_val).decode('utf-8')
                                resolved = resolve_url(decoded_url)
                                
                                options_for_event.append({
                                    "name": f"TVL: {chan_name}",
                                    "url": resolved['url'],
                                    "type": resolved['type'],
                                    "drm": resolved.get('drm')
                                })
                        except Exception as e:
                            # FALLBACK SEGURO: Si el Base64 viene dañado y falla la decodificación
                            # Pasamos la URL original en bruto para que el Sniffer la analice
                            full_href = BASE_URL_TVLIBRE + href if href.startswith('/') else href
                            options_for_event.append({
                                "name": f"TVL: {chan_name}",
                                "url": full_href,
                                "type": "iframe",
                                "drm": None
                            })
                    elif href and href != "#":
                        # Cualquier otro enlace directo
                        full_href = BASE_URL_TVLIBRE + href if href.startswith('/') else href
                        options_for_event.append({
                            "name": f"TVL: {chan_name}",
                            "url": full_href,
                            "type": "iframe",
                            "drm": None
                        })

            if options_for_event:
                order_counter += 1
                events.append({
                    "title": title, "time": final_time, "date": current_date,
                    "league": league_name, "image": image_url,
                    "channels": options_for_event, "order": order_counter 
                })
    except Exception as e:
        print(f"❌ Error crítico en TvLibre: {e}")
    return events

def get_deportelibre_events(current_date):
    print("⚽ Extrayendo eventos de Deporte Libre...")
    events = []
    try:
        resp = scraper.get(DL_AGENDA_URL)
        if resp.status_code != 200:
            print(f"⚠️ Error accediendo a Deporte Libre: Status {resp.status_code}")
            return []
            
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        list_items = soup.find_all('li')
        order_counter = 0

        for li in list_items:
            if 'subitem1' in li.get('class', []): continue
            
            link_tag = li.find('a')
            if not link_tag: continue
            
            time_span = link_tag.find('span', class_='t')
            if not time_span: continue
            
            time_text_raw = time_span.get_text(strip=True)
            time_span.decompose() 
            final_time = fix_spain_to_arg_time(time_text_raw)
            
            i_tag = link_tag.find('i')
            if i_tag: i_tag.decompose()
            
            title = link_tag.get_text(" ", strip=True).strip()
            if not title: continue
            
            image_url = "" 
            league_name = "Deporte Libre"
            options_for_event = []
            
            sub_ul = li.find('ul')
            if sub_ul:
                sub_items = sub_ul.find_all('li', class_='subitem1')
                for sub in sub_items:
                    opt_a = sub.find('a')
                    if not opt_a: continue
                    
                    chan_name = str(opt_a.contents[0]).strip() if opt_a.contents else "Opción DL"
                    href = opt_a.get('href', '')

                    if ".php" in href or "/en-vivo/" in href:
                        deep_chans = get_deporte_libre_sources(href)
                        if deep_chans:
                            for dc in deep_chans:
                                options_for_event.append({
                                    "name": f"DL: {chan_name.strip()} - {dc['name']}",
                                    "url": dc['url'],
                                    "type": dc['type'],
                                    "drm": dc.get('drm')
                                })
                        else:
                            full_href = BASE_URL_DL + href if href.startswith('/') else href
                            options_for_event.append({
                                "name": f"DL: {chan_name.strip()}",
                                "url": full_href,
                                "type": "iframe",
                                "drm": None
                            })
                        time.sleep(0.3)
                        
                    elif "?r=" in href or "?embed=" in href:
                        try:
                            parsed = urlparse(href)
                            params = parse_qs(parsed.query)
                            raw_val = params.get('r', params.get('embed', [None]))[0]
                            
                            if raw_val:
                                raw_val += "=" * ((4 - len(raw_val) % 4) % 4)
                                decoded_url = base64.b64decode(raw_val).decode('utf-8')
                                resolved = resolve_url(decoded_url)
                                options_for_event.append({
                                    "name": f"DL: {chan_name.strip()}",
                                    "url": resolved['url'],
                                    "type": resolved['type'],
                                    "drm": resolved.get('drm')
                                })
                        except:
                            full_href = BASE_URL_DL + href if href.startswith('/') else href
                            options_for_event.append({
                                "name": f"DL: {chan_name.strip()}",
                                "url": full_href,
                                "type": "iframe",
                                "drm": None
                            })
                    elif href and href != "#":
                        full_href = BASE_URL_DL + href if href.startswith('/') else href
                        options_for_event.append({
                            "name": f"DL: {chan_name.strip()}",
                            "url": full_href,
                            "type": "iframe",
                            "drm": None
                        })

            if options_for_event:
                order_counter += 1
                events.append({
                    "title": title, "time": final_time, "date": current_date,
                    "league": league_name, "image": image_url,
                    "channels": options_for_event, "order": order_counter 
                })
    except Exception as e:
        print(f"❌ Error crítico en Deporte Libre: {e}")
    return events

def merge_events(tvlibre_events, deportelibre_events):
    print("🔄 Fusionando eventos de ambas agendas...")
    merged = list(tvlibre_events)
    
    for dl_ev in deportelibre_events:
        found_match = False
        dl_words = set(dl_ev['title'].lower().replace('.', '').split())
        
        for tv_ev in merged:
            if dl_ev['time'] == tv_ev['time']:
                tv_words = set(tv_ev['title'].lower().replace('.', '').split())
                
                dl_keywords = {w for w in dl_words if len(w) > 3}
                tv_keywords = {w for w in tv_words if len(w) > 3}
                
                if len(dl_keywords.intersection(tv_keywords)) >= 2:
                    tv_ev['channels'].extend(dl_ev['channels'])
                    if not tv_ev['image'] and dl_ev['image']:
                        tv_ev['image'] = dl_ev['image']
                    found_match = True
                    break
        
        if not found_match:
            merged.append(dl_ev)
            
    merged_sorted = sorted(merged, key=lambda x: x['time'])
    for i, ev in enumerate(merged_sorted):
        ev['order'] = i + 1
    return merged_sorted

def parse_agenda():
    print(f"📅 Iniciando Crawler de Agenda Integrada...")
    current_date = get_current_arg_date()
    print(f"🕒 Fecha para base de datos: {current_date}")

    tv_events = get_tvlibre_events(current_date)
    dl_events = get_deportelibre_events(current_date)
    
    final_events = merge_events(tv_events, dl_events)

    for ev in final_events:
        print(f"   ⚽ [{ev['time']}] {ev['title']} | Opciones: {len(ev['channels'])}")

    if final_events:
        print(f"📤 Enviando {len(final_events)} eventos consolidados a Go...")
        try:
            r = requests.post(API_GO_URL, json={"events": final_events})
            if r.status_code == 200:
                print("✅ Agenda actualizada correctamente en la base de datos.")
            else:
                print(f"⚠️ El servidor respondió con código HTTP: {r.status_code}")
        except Exception as e:
            print(f"❌ Error de conexión al servidor Go: {e}")
    else:
        print("⚠️ No se encontraron eventos válidos para fusionar.")

if __name__ == "__main__":
    parse_agenda()
