from bs4 import BeautifulSoup

BASE_URL = "https://tvlibree.com"

# 1. Filtros por CATEGORÍA (Badges)
BLACKLIST_BADGES = ["Paraguay", "Adultos (+18)"]

# 2. Filtros por NOMBRE EXACTO DEL CANAL (Nuevo)
BLACKLIST_TITLES = ["Adult Swim", "Venus", "Playboy"]

def parse_home_grid(html_content):
    """
    Recibe el HTML de la portada y devuelve una lista limpia de canales.
    """
    # Forzamos decodificación si viene en bytes, aunque lo ideal es hacerlo en el request
    if isinstance(html_content, bytes):
        html_content = html_content.decode('utf-8', errors='ignore')

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
                # print(f"   🚫 Filtrando canal prohibido: {name}")
                continue

            # --- C. CONSTRUCCIÓN DE URLS ---
            href = card.get('href')
            if href.startswith('/'):
                full_url = f"{BASE_URL}{href}"
            else:
                full_url = href
            
            # Logo
            img_tag = card.find('img')
            logo_url = ""
            if img_tag:
                src = img_tag.get('src')
                if src.startswith('//'):
                    logo_url = "https:" + src
                else:
                    logo_url = src
            
            # Categoría Principal
            category = "General"
            paises_ignorar = ["Argentina", "México", "Colombia", "España", "Uruguay", "Estados Unidos", "Chile", "Perú"]
            
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
