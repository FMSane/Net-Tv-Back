from bs4 import BeautifulSoup

BASE_URL = "https://tvlibree.com"

# 1. Filtros por CATEGORÍA (Badges)
BLACKLIST_BADGES = ["Paraguay", "Adultos (+18)"]

# 2. Filtros por NOMBRE EXACTO DEL CANAL
BLACKLIST_TITLES = ["Adult Swim", "Venus", "Playboy"]

def parse_home_grid(html_content):
    """
    Recibe el HTML de la portada y devuelve una lista limpia de canales.
    Maneja la corrección de codificación (UTF-8 vs Latin-1).
    """

    # --- BLOQUE DE CORRECCIÓN DE CODIFICACIÓN ---
    # Si viene en bytes (response.content), decodificamos explícitamente a UTF-8
    if isinstance(html_content, bytes):
        try:
            html_content = html_content.decode('utf-8')
        except UnicodeDecodeError:
            html_content = html_content.decode('iso-8859-1')
    
    # Si viene en string (response.text) y ya está roto (ej: "AmÃ©rica"), intentamos arreglarlo
    elif isinstance(html_content, str):
        try:
            # El truco: Invertir la decodificación incorrecta (Latin1) y re-decodificar como UTF-8
            # Esto transforma "AmÃ©rica" -> "América"
            html_content = html_content.encode('iso-8859-1').decode('utf-8')
        except Exception:
            # Si falla (porque no estaba roto), lo dejamos tal cual
            pass

    # --- PARSEO ---
    soup = BeautifulSoup(html_content, 'html.parser')
    
    grid = soup.find('section', id='grid')
    if not grid:
        print("❌ No se encontró la grilla de canales.")
        return []

    clean_channels = []
    cards = grid.find_all('a', class_='canal')

    print(f"🔍 Analizando {len(cards)} tarjetas...")

    for card in cards:
        try:
            # --- A. EXTRACCIÓN DE DATOS ---
            
            # Nombre (Limpiamos espacios extra)
            title_tag = card.find('h2', class_='title')
            name = title_tag.get_text(strip=True) if title_tag else "Desconocido"

            # Badges (Categorías)
            badges_tags = card.find_all('span', class_='badge')
            badges_text = [b.get_text(strip=True) for b in badges_tags]

            # --- B. FILTRADO (Badges + Títulos) ---
            
            # 1. Filtro por Badges (Categoría prohibida)
            if any(bad in badges_text for bad in BLACKLIST_BADGES):
                continue 

            # 2. Filtro por Título (Canal específico prohibido)
            if any(forbidden.lower() == name.lower() for forbidden in BLACKLIST_TITLES):
                continue

            # --- C. CONSTRUCCIÓN DE URLS ---
            href = card.get('href')
            if href and href.startswith('/'):
                full_url = f"{BASE_URL}{href}"
            else:
                full_url = href or ""
            
            # Logo
            img_tag = card.find('img')
            logo_url = ""
            if img_tag:
                src = img_tag.get('src')
                if src:
                    if src.startswith('//'):
                        logo_url = "https:" + src
                    elif src.startswith('/'):
                         logo_url = f"{BASE_URL}{src}"
                    else:
                        logo_url = src
            
            # Categoría Principal
            category = "General"
            paises_ignorar = ["Argentina", "México", "Colombia", "España", "Uruguay", "Estados Unidos", "Chile", "Perú", "Ecuador", "Venezuela"]
            
            for b in badges_text:
                if b not in paises_ignorar:
                    category = b
                    break

            # --- D. GUARDADO ---
            clean_channels.append({
                "name": name,
                "url": full_url,
                "logo": logo_url,
                "category": category
            })

        except Exception as e:
            print(f"⚠️ Error parseando una tarjeta: {e}")

    print(f"✅ Canales válidos encontrados: {len(clean_channels)}")
    return clean_channels
