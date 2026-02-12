from bs4 import BeautifulSoup
import re

def parse_tvlibree_channel(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    sources = []

    # --- ESTRATEGIA 1: BUSCAR BOTONES (La de siempre) ---
    nav = soup.find('nav', class_='server-links')
    
    if nav:
        buttons = nav.find_all('a')
        for btn in buttons:
            btn_text = btn.get_text().strip()
            # Combinamos onclick y href para buscar
            raw_string = str(btn.get('onclick', '')) + " " + str(btn.get('href', ''))
            
            # Buscamos patrón get=CODIGO
            match_get = re.search(r"get=([a-zA-Z0-9+=]+)", raw_string)
            
            if match_get:
                code = match_get.group(1)
                nebu_url = f"https://www.nebunexa.life/cvatt.html?get={code}&lang=1"
                sources.append({
                    "name_display": f"{btn_text} (Nebu)",
                    "raw_url": nebu_url
                })
            else:
                # Buscamos http normal
                match_http = re.search(r"src=['\"](http.*?)['\"]", raw_string)
                if not match_http: 
                    match_http = re.search(r"['\"](http.*?)['\"]", raw_string)
                
                if match_http:
                    sources.append({
                        "name_display": btn_text,
                        "raw_url": match_http.group(1)
                    })

    # --- ESTRATEGIA 2: BUSCAR IFRAME DIRECTO (Caso Flow Sports 2) ---
    # Si la Estrategia 1 falló o queremos asegurar, buscamos iframes en el cuerpo
    
    # Buscamos cualquier iframe cuyo SRC tenga 'get='
    direct_iframes = soup.find_all('iframe', src=re.compile(r'get='))
    
    for iframe in direct_iframes:
        src = iframe.get('src', '')
        # Extraemos el código
        match_get = re.search(r"get=([a-zA-Z0-9+=]+)", src)
        
        if match_get:
            code = match_get.group(1)
            nebu_url = f"https://www.nebunexa.life/cvatt.html?get={code}&lang=1"
            
            # Evitamos duplicados si el botón ya lo encontró
            if not any(s['raw_url'] == nebu_url for s in sources):
                sources.append({
                    "name_display": "Opción Directa",
                    "raw_url": nebu_url
                })
                
    # --- ESTRATEGIA 3: BUSCAR SCRIPTS (Caso extremo donde el iframe se escribe con JS) ---
    # A veces está oculto en: document.write('<iframe ... src="/html/fl/?get=..." ...')
    if not sources:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and "get=" in script.string:
                match_get = re.search(r"get=([a-zA-Z0-9+=]+)", script.string)
                if match_get:
                    code = match_get.group(1)
                    nebu_url = f"https://www.nebunexa.life/cvatt.html?get={code}&lang=1"
                    sources.append({
                        "name_display": "Opción Script",
                        "raw_url": nebu_url
                    })
                    break # Encontramos uno, suficiente

    return sources
