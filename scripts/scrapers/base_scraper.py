from abc import ABC, abstractmethod

# Esta clase define las reglas del juego
class BaseScraper(ABC):
    
    @abstractmethod
    def get_site_name(self):
        """Nombre del sitio (ej: 'La14HD')"""
        pass

    @abstractmethod
    def scrape(self):
        """
        Debe devolver una lista de diccionarios con este formato EXACTO:
        [
            {
                "channel_name": "ESPN",
                "url": "https://...",
                "type": "m3u8", # o "iframe"
                "headers": {...} # Opcional
            },
            ...
        ]
        """
        pass
