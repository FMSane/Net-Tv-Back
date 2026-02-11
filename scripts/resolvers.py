import re
import base64
import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper()

# --- BASE DE DATOS DE LLAVES (Extraída de tu JS) ---
# Clave: El código en Base64 (getURL)
# Valor: {keyId, key}
NEBUNEXA_DRM_MAP = {
    "RVNQTjJIRA": {"kid": "e884b711ab111beb8a7ba1e7bcbdc9bf", "k": "cb89ee3961599e3e648a5aad60895f34"}, # ESPN 2 HD
    "U3lGeQ==": {"kid": "9cd99cbb466c42e5b33e7a2ef7e2c7df", "k": "18d9faccdaf2d15807d0a3f713e8b2a4"}, # SyFy
    "VW5pdmVyc2FsX0NpbmVtYQ==": {"kid": "f6ae2e17173055e4ca69dc18963406ae", "k": "5a955c29eb88a0b4c9a2538cc4b3aea2"}, # Universal Cinema
    "VW5pdmVyc2FsX0NvbWVkeQ==": {"kid": "062c5d25105a3a935b67e36923c73f28", "k": "88c2d4cec420f18d2477152c66c7870d"}, # Univ Comedy
    "dW5pdmVyc2FsX0NyaW1l": {"kid": "1efd7edf60e1514f775dd13d046ae708", "k": "c2ef1abbd945c62c11b1375eaaa50f0d"}, # Univ Crime
    "VW5pdmVyc2FsX1ByZW1pZXJl": {"kid": "0eb20b51ad13b58ad417f11318e588b3", "k": "ad5d29a33d73d21187157802de8e6097"}, # Univ Premiere
    "VW5pdmVyc2FsX1JlYWxpdHk=": {"kid": "cedd9c1a5c2ae43f80ee3197212016d6", "k": "bf47a3c39e164a97ea6adc4c8dd57435"}, # Univ Reality
    "RXZlbnRvc19IRF9VeQ==": {"kid": "48d0e34c8797c5c2a742d2630a8fb975", "k": "fb5d12b9d8febe836e5670abd003ddca"}, # Eventos 1 UY
    "Rm94U3BvcnRzMl9VWQ==": {"kid": "5fc7b662e69c0fbf8d39691166b1c919", "k": "89157cdd25df25d56f1ecccee3850888"}, # Fox Sports 2 UY
    "Rm94U3BvcnRzM19VWQ==": {"kid": "5fc7b662e69c0fbf8d39691166b1c919", "k": "89157cdd25df25d56f1ecccee3850888"}, # Fox Sports 3 UY
    "RVNQTjQ=": {"kid": "24f2b3e741f0d9e9a8d516faff38bddc", "k": "bbd3fd02fb104e1463ac528a13f67e4a"}, # ESPN 4
    "TkJBX1RW": {"kid": "d0c38de3c9844e4e9f975dffb3eff8ad", "k": "141ca0fdf6ebadfa7107576b8e09e117"}, # NBA TV
    "SFRW": {"kid": "daecef5fe32f4ce083c6a0c692755d6a", "k": "d4227f24389a9ba77293214b93eb0d7d"}, # HTV
    "RXZlbnRvc18yX0hE": {"kid": "e54e9ea87a634658fbba0e380aa701a7", "k": "4e486d25d7d0e7d131743b285963c643"}, # Flow Sports 2 (EL QUE BUSCABAS)
    "VlRWX1BsdXNfSEQ": {"kid": "da8a49a594160cc0059f07b9f71cd39a", "k": "37ca91dd799b351a02445151c7f61070"}, # VTV Plus
    "SEJPSEQ=": {"kid": "5317283f4110fac3fb3a0becd9f648bc", "k": "0754a03c926b1247216e01d9dbcfac28"}, # HBO
    # ... (Puedes agregar el resto de la lista gigante aquí poco a poco) ...
}

# --- LÓGICA DE SERVIDORES (Replica el if/else de 'number') ---
def get_server_number(code):
    """Determina si va al servidor c3, c4, c5, c6 o c7"""
    
    # Grupo 7
    group_7 = ["QTNfQ2luZQ==", "Rmxvd19NdXNpY19YUA==", "Rmxvd19NdXNpY18x", "Rmxvd19NdXNpY18y", "Rmxvd19NdXNpY18z", "QUVIRA==", 
               "SG9sYV9UVg==", "QVhOSEQ=", "TVRWMDA=", "V2FybmVySEQ=", "R0VOX1RW", "Rm94X1Nwb3J0c19QcmVtaXVuX0hE", "VG9kb05vdGljaWFz", 
               "VHlDU3BvcnQ", "QW1lcmljYTI0", "QzVO", "TGFfTmFjaW9u", "Q3JvbmljYVRW", "Q2FuYWxfOF9UdWN1bWFu", "UGFyYWd1YXlfVFY=", 
               "UGFyYW1vdW50", "Q29tZWR5Q2VudHJhbA", "Qm9vbWVyYW5n", "RHJlYW13b3Jrcw==", "QW5pbWFsUGxhbmV0", "SGlzdG9yeUhE", "SUQ=", 
               "QnJhdm9UVg==", "U29ueUhE", "VHJ1VFY=", "SEJPX1BPUA==", "RGlzY292ZXJ5VHVyYm8=", "RGlzbmV5SnI=", "SW52ZXN0aWdhY2lvbl9QZXJpb2Rpc3RpY2E=", 
               "Rm94U3BvcnRzMl9VWQ==", "RVNQTjQ=", "Rm94U3BvcnRzM19VWQ==", "RXZlbnRvc19IRF9VeQ==", "VGVsZW11bmRvX0hE", "RVNQTjNfVXktUHk=", 
               "QTNfU2VyaWVz", "VVNBX05ldHdvcms="]
    
    # Grupo 6
    group_6 = ["RVNQTjJfQXJn", "Q2luZW1heA==", "RXZlbnRvc18yX0hE", "Q2FuYWxfOF9DQkE", "MjZfVFZfSEQ", "RGlwdXRhZG9zX1RW", "QXJnZW50aW5pc2ltYQ", 
               "TWV0cm8", "QkJDX1dvcmxkX05ld3M", "VGhlYXRlcl9IRA==", "R2xpdHo=", "UXVpZXJvX0hE", "RGlzY292ZXJ5X1dvcmxkX0hE", "RXVyb2NoYW5uZWw=", 
               "RGlzY292ZXJ5X1NjaWVuY2U=", "SU5DQUFfVHY=", "VFY1X01vbmRl", "TVRWX0hpdHM=", "TVRWX0hE", "Tmlja19Kcg==", "VFZfRXNwYW5h", "V09CSQ==", 
               "Vm9sdmVy", "VGVsZXN1cg==", "TGlmZXRpbWU=", "QW50ZW5hXzM=", "Rm94X05ld3M=", "VHZfQ2hpbGU=", "QU1DX1Nlcmllcw==", "U3R1ZGlvX1VuaXZlcnNhbA==", 
               "SVNBVA==", "U3VuX0NoYW5uZWw=", "UkFJ", "VmVudXM=", "U2V4dHJlbWU", "UGxheWJveQ", "VE5UX1Nwb3J0c19IRA", "VGVsZWZlSEQ=", "Q2FuYWw3", 
               "RW5jdWVudHJv", "VGVsZW1heA", "TmV0X1RW", "Q2FuYWxfMTJfQ0JB", "RWxfR2FyYWdl", "RmlsbV9BcnRz", "VW5pdmVyc2FsX0NoYW5uZWxfSEQ=", 
               "RXVyb3BhX0V1cm9wYQ", "RXVyb25ld3M=", "Rm9vZF9OZXR3b3Jr", "RV9FbnRlcnRhaW5tZW50X1RlbGV2aXNpb24=", "Q00=", "UEFLQV9QQUtB", 
               "SGlzdG9yeV8y", "U3lGeQ==", "VEJT", "VENN", "SEJPXzI=", "SEJPX1BsdXM=", "SEJPX0ZhbWlseQ==", "SEJPX0V4dHJlbWU=", "SEJPX011bmRp", 
               "SEJPX1NpZ25hdHVyZQ==", "Q2FuYWxfUnVyYWw=", "VExD", "Q2FuYWxfZGVfbGFfY2l1ZGFk", "RGlzY292ZXJ5X0tpZHM=", "SFRW", "TkJBX1RW", 
               "VW5pdmVyc2FsX0NpbmVtYQ==", "VW5pdmVyc2FsX0NvbWVkeQ==", "dW5pdmVyc2FsX0NyaW1l", "VW5pdmVyc2FsX1ByZW1pZXJl", "VW5pdmVyc2FsX1JlYWxpdHk=", 
               "Q2FuYWxfZGVfbGFzX2VzdHJlbGxhcw==", "S1pP", "R29sZGVu"]
    
    # Grupo 5
    group_5 = ["QzlOX0M0"]
    
    # Grupo 4
    group_4 = ["Q2FuYWxfNV9Sb3Nhcmlv", "VEVMRUZVVFVST19DNA==", "VGVsZWZlX05ldXF1ZW4=", "VGVsZWZlX1NhbHRh", "U05UX0M0", "UEFSQVZJU0lPTl9DNA==", 
               "Tk9USUNJQVNfUFlfQzQ=", "TEFfVEVMRV9DNA==", "U1VSX1RWX0M0", "Q2FuYWwxMlVSVQ==", "RGlzY292ZXJ5SG9tZUhlYWx0aEhE", "Q2FuYWw0X1VSVQ==", 
               "SEJPSEQ=", "Q2FuYWwxMF9VUlU=", "UlBDX0M0", "RVNQTjJfVVk=", "RVNQTl9VWQ=="]

    if code in group_7: return 7
    if code in group_6: return 6
    if code in group_5: return 5
    if code in group_4: return 4
    return 3 # Default del "else" final

def resolve_nebunexa_direct(url):
    try:
        # Extraer el código después de get=
        code_match = re.search(r"get=([a-zA-Z0-9+=]+)", url)
        if not code_match: return None
        code = code_match.group(1)
        
        # 1. ¿Tenemos la llave?
        drm_data = NEBUNEXA_DRM_MAP.get(code)
        
        if drm_data:
            # SI TENEMOS LLAVE: Generamos el .mpd directo
            decoded_id = base64.b64decode(code).decode('utf-8')
            server_num = get_server_number(code)
            mpd_url = f"https://cdn.cvattv.com.ar/live/c{server_num}eds/{decoded_id}/SA_Live_dash_enc_C/{decoded_id}.mpd"
            
            return {
                "url": mpd_url,
                "type": "dash",
                "drm": {
                    "clearkey": { "keyId": drm_data["kid"], "key": drm_data["k"] }
                }
            }
        else:
            # NO TENEMOS LLAVE: Forzamos IFRAME para que Nebunexa cargue su propio player
            # Esto evita que el front descargue archivos .mpd
            return {
                "url": url,
                "type": "iframe",
                "headers": {
                    "Referer": "https://tvlibree.com/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
            }
    except Exception as e:
        print(f"Error en resolver Nebunexa: {e}")
        return None


# --- FUNCIONES LEGACY (Las que ya tenías) ---
def resolve_generic(url):
    return {"url": url, "type": "iframe"}

def resolve_bolaloca(url):
    return {"url": url, "type": "iframe", "headers": {"Referer": "https://bolaloca.my/"}}

def resolve_la14hd(url):
    try:
        html = scraper.get(url).text
        m3u8 = re.search(r'source:\s*["\'](.*?\.m3u8.*?)["\']', html)
        if m3u8: return {"url": m3u8.group(1), "type": "m3u8"}
        iframe = BeautifulSoup(html, 'html.parser').find('iframe')
        if iframe and iframe.get('src'): return {"url": iframe['src'], "type": "iframe"}
        return None
    except: return None

def resolve_welivesports(url):
    try:
        html = scraper.get(url).text
        m3u8 = re.search(r'["\'](http.*?\.m3u8.*?)["\']', html)
        if m3u8: return {"url": m3u8.group(1), "type": "m3u8"}
        return {"url": url, "type": "iframe"}
    except: return None

RESOLVER_MAP = {
    "nebunexa.life": resolve_nebunexa_direct, # <--- USAMOS LA NUEVA FUNCIÓN
    "bolaloca.my": resolve_bolaloca,
    "la14hd.com": resolve_la14hd,
    "welivesports.shop": resolve_welivesports,
    "streamtp10.com": resolve_generic
}

def resolve_url(url):
    for domain, func in RESOLVER_MAP.items():
        if domain in url:
            return func(url)
    return resolve_generic(url)
