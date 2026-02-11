from bs4 import BeautifulSoup

BASE_URL = "https://tvlibree.com"

# Palabras prohibidas (Filtro)
BLACKLIST_BADGES = ["Paraguay", "Adultos (+18)"]

def parse_home_grid(html_content):
    """
    Recibe el HTML de la portada y devuelve una lista limpia de canales
    ignorando los de Paraguay y Adultos.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Buscamos el contenedor de la grilla
    grid = soup.find('section', id='grid')
    if not grid:
        print("❌ No se encontró la grilla de canales.")
        return []

    clean_channels = []
    
    # Buscamos cada tarjeta (son etiquetas <a> con clase 'canal')
    cards = grid.find_all('a', class_='canal')

    print(f"🔍 Analizando {len(cards)} tarjetas...")

    for card in cards:
        try:
            # --- 1. FILTRADO (La parte más importante) ---
            badges_tags = card.find_all('span', class_='badge')
            badges_text = [b.get_text(strip=True) for b in badges_tags]
            
            # Verificamos si alguna etiqueta prohibida está presente
            # Usamos intersección de conjuntos para ser rápidos
            if any(bad in badges_text for bad in BLACKLIST_BADGES):
                # print(f"   🚫 Ignorando: {card.find('h2').text} (Filtro: {badges_text})")
                continue # Salta al siguiente canal

            # --- 2. EXTRACCIÓN DE DATOS ---
            
            # Nombre
            title_tag = card.find('h2', class_='title')
            name = title_tag.get_text(strip=True) if title_tag else "Desconocido"

            # Link (href)
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
                # A veces vienen como "//bestleague.world...", hay que agregar https:
                if src.startswith('//'):
                    logo_url = "https:" + src
                else:
                    logo_url = src
            
            # Categoría (Tomamos la primera etiqueta que NO sea el país, si existe)
            category = "General"
            for b in badges_text:
                if b not in ["Argentina", "México", "Colombia", "España", "Uruguay", "Estados Unidos"]:
                    category = b
                    break

            # --- 3. GUARDADO ---
            clean_channels.append({
                "name": name,
                "url": full_url,   # URL de la página del canal (donde están los botones)
                "logo": logo_url,
                "category": category
            })

        except Exception as e:
            print(f"⚠️ Error parseando una tarjeta: {e}")

    print(f"✅ Canales válidos encontrados: {len(clean_channels)} (de {len(cards)})")
    return clean_channels
