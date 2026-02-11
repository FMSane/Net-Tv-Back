import requests
from sites.la14hd import La14HDScraper
from sites.streamtp10 import StreamTP10Scraper
# from sites.nebunexa import NebunexaScraper

API_GO_URL = "http://localhost:8080/api/tv/update-sources"

def main():
    # 1. Instanciamos nuestros scrapers
    scrapers = [
        La14HDScraper(),
        StreamTP10Scraper(),
        # NebunexaScraper()
    ]

    all_channels_data = {}

    # 2. Ejecutamos cada uno
    for scraper in scrapers:
        print(f"Scraping {scraper.get_site_name()}...")
        channels_found = scraper.scrape()
        
        # 3. Agrupamos por canal
        for item in channels_found:
            name = item['channel_name']
            
            if name not in all_channels_data:
                all_channels_data[name] = []
            
            # Formateamos para la API de Go
            source_entry = {
                "name": f"{scraper.get_site_name()} (Auto)",
                "url": item['url'],
                "type": item['type'],
                "priority": 1, # Podrías dar menos prioridad a sitios lentos
            }
            if "headers" in item:
                source_entry["headers"] = item["headers"]

            all_channels_data[name].append(source_entry)

    # 4. Enviamos a Go canal por canal
    for channel_name, sources in all_channels_data.items():
        payload = {
            "name": channel_name,
            "sources": sources
        }
        # Enviamos POST a tu API
        try:
            r = requests.post(API_GO_URL, json=payload)
            print(f"Actualizado {channel_name}: {r.status_code}")
        except Exception as e:
            print(f"Error enviando {channel_name} a API: {e}")

if __name__ == "__main__":
    main()
