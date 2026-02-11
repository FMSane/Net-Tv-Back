import requests
import re
from base_scraper import BaseScraper

class La14HDScraper(BaseScraper):
    def get_site_name(self):
        return "La14HD"

    def scrape(self):
        results = []
        # Mapa de canales que te interesan de este sitio
        urls_to_scan = {
            "ESPN": "https://la14hd.com/ver-espn-vivo-online",
            "TyC Sports": "https://la14hd.com/ver-tyc-sports-online"
        }

        for channel, url in urls_to_scan.items():
            try:
                # LÓGICA ESPECÍFICA DE ESTE SITIO
                # 1. Obtenemos el HTML
                headers = {'User-Agent': 'Mozilla/5.0...'}
                html = requests.get(url, headers=headers).text
                
                # 2. Buscamos el m3u8 (esto cambia según el sitio)
                # Supongamos que La14HD pone el link en una variable 'source:'
                match = re.search(r'source:\s*"(.*?\.m3u8)"', html)
                
                if match:
                    m3u8_link = match.group(1)
                    results.append({
                        "channel_name": channel,
                        "url": m3u8_link,
                        "type": "direct_m3u8",
                        "headers": {"Referer": "https://la14hd.com/"} # Clave para que funcione
                    })
            except Exception as e:
                print(f"Error scraping {channel} en La14HD: {e}")
        
        return results
