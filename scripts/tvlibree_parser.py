from bs4 import BeautifulSoup
import re

def parse_tvlibree_channel(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    sources = []

    # 1. Buscar en los botones del nav
    nav = soup.find('nav', class_='server-links')
    buttons = nav.find_all('a') if nav else []

    for btn in buttons:
        btn_text = btn.get_text().strip()
        # Buscamos en 'onclick' y en 'href' por si acaso
        content_to_search = str(btn.get('onclick', '')) + " " + str(btn.get('href', ''))
        
        # BUSQUEDA MAESTRA: Buscamos cualquier cosa que tenga get= seguido de letras y numeros
        # Esto captura: /html/fl/?get=VG9kb05vdGljaWFz
        match_get = re.search(r"get=([a-zA-Z0-9+=]+)", content_to_search)
        
        if match_get:
            code = match_get.group(1)
            # Construimos la URL de Nebunexa que SI entendemos
            nebu_url = f"https://www.nebunexa.life/cvatt.html?get={code}&lang=1"
            sources.append({
                "name_display": f"{btn_text} (Nebu)",
                "raw_url": nebu_url
            })
        
        # Si no hay 'get=', buscamos una URL de YouTube o HTTP normal
        else:
            match_http = re.search(r"src=['\"](http.*?)['\"]", content_to_search)
            if not match_http: # Intentamos buscar link pelado sin src=
                match_http = re.search(r"['\"](http.*?)['\"]", content_to_search)
            
            if match_http:
                sources.append({
                    "name_display": btn_text,
                    "raw_url": match_http.group(1)
                })

    return sources
