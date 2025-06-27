from Kekik.cli import konsol
from httpx import Client
from parsel import Selector
import re

class KralBetTV:
    def __init__(self, m3u_dosyasi):
        self.m3u_dosyasi = m3u_dosyasi
        self.httpx = Client(timeout=10, verify=False)
        self.base_url = "https://royalvipcanlimac.com/channels.php"

    def referer_domainini_al(self):
        referer_deseni = r'#EXTVLCOPT:http-referrer=(https?://[^/]*1029kralbettv[^/]*\.[^\s/]+)'
        with open(self.m3u_dosyasi, "r") as dosya:
            icerik = dosya.read()

        if eslesme := re.search(referer_deseni, icerik):
            return eslesme[1]
        else:
            raise ValueError("M3U dosyasında '1029kralbettv' içeren referer domain bulunamadı!")

    def get_stream_links(self):
        try:
            response = self.httpx.get(self.base_url)
            response.raise_for_status()
            
            selector = Selector(response.text)
            
            # Extract stream links - you'll need to adjust this based on the actual page structure
            stream_links = selector.xpath('//div[contains(@class, "stream-link")]/@data-url').getall()
            
            if not stream_links:
                # Alternative pattern if the above doesn't work
                stream_links = re.findall(r'player\.setup\({\s*source:\s*["\'](https?://[^"\']+)["\']', response.text)
            
            if not stream_links:
                raise ValueError("No stream links found on the page")
                
            return stream_links[0]  # Return the first stream link found
            
        except Exception as e:
            konsol.log(f"[red][!] Error getting stream links: {e}")
            raise

    def m3u_guncelle(self):
        eldeki_domain = self.referer_domainini_al()
        konsol.log(f"[yellow][~] Bilinen Domain : {eldeki_domain}")

        try:
            yeni_yayin_url = self.get_stream_links()
            konsol.log(f"[green][+] Yeni Yayın URL : {yeni_yayin_url}")

            with open(self.m3u_dosyasi, "r") as dosya:
                m3u_icerik = dosya.read()

            # Find and replace the old stream URL
            if not (eski_yayin_url := re.search(r'https?://[^\s]+\.m3u8', m3u_icerik)):
                raise ValueError("M3U dosyasında eski yayın URL'si bulunamadı!")

            eski_yayin_url = eski_yayin_url[0]
            konsol.log(f"[yellow][~] Eski Yayın URL : {eski_yayin_url}")

            yeni_m3u_icerik = m3u_icerik.replace(eski_yayin_url, yeni_yayin_url)
            yeni_m3u_icerik = yeni_m3u_icerik.replace(eldeki_domain, self.base_url)

            with open(self.m3u_dosyasi, "w") as dosya:
                dosya.write(yeni_m3u_icerik)

            konsol.log("[green][+] M3U dosyası başarıyla güncellendi!")

        except Exception as e:
            konsol.log(f"[red][!] Hata oluştu: {e}")
            raise

if __name__ == "__main__":
    guncelleyici = KralBetTV("KralBetTV.m3u")
    guncelleyici.m3u_guncelle()
