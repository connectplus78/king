import os
import re
import json
import requests
import concurrent.futures
import shutil

# --- PREMIER LİG İÇİN DİNAMİK URL ÇEKME ---
def get_league_urls(page_url, league_name, org_id):
    urls_to_fetch = []
    try:
        response = requests.get(page_url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text, re.DOTALL)
        if not match: return []
        data = json.loads(match.group(1))
        
        highlights_data = data.get("props", {}).get("pageProps", {}).get("initialReduxState", {}).get("highlights", {}).get("data", [])
        
        for league_info in highlights_data:
            if league_info.get("id") == org_id:
                for season in league_info.get("seasons", []):
                    season_name = season.get("name")
                    season_id = season.get("id")
                    # Her sezon için ayrı bir grup başlığı oluşturuyoruz
                    group_title = f"{league_name}_{season_name.replace('/', '-')}"
                    for round_info in season.get("rounds", []):
                        round_number = round_info.get("round")
                        st_code = round_info.get("st", 0)
                        if season_id and round_number:
                            url = f"https://beinsports.com.tr/api/highlights/events?sp=1&o={org_id}&s={season_id}&r={round_number}&st={st_code}"
                            urls_to_fetch.append((url, group_title))
        return urls_to_fetch
    except Exception as e:
        print(f"Veri çekme hatası: {e}")
        return []

def fetch_and_parse(url_info):
    url, group_title = url_info
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        data = response.json()
        events = data.get('Data', {}).get('events', [])
        result = []
        for event in events:
            home = event.get('homeTeam', {}).get('name', 'Ev Sahibi')
            home_score = event.get('homeTeam', {}).get('matchScore', '-')
            away = event.get('awayTeam', {}).get('name', 'Deplasman')
            away_score = event.get('awayTeam', {}).get('matchScore', '-')
            video_url = event.get('highlightVideoUrl')
            logo = event.get('highlightThumbnail', '')
            match_id = event.get('matchId', '')
            if video_url:
                title = f"{home} {home_score}-{away_score} {away}"
                line1 = f'#EXTINF:-1 tvg-id="{match_id}" tvg-logo="{logo}" group-title="{group_title}",{title}\n'
                line2 = f"{video_url}\n"
                result.append((group_title, line1, line2))
        return result
    except Exception:
        return []

def main():
    output_folder = 'metv'
    
    # Klasörü tamamen temizle (Eski dosyalar silinsin)
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)
    
    # Premier Lig verilerini çek
    urls = get_league_urls("https://www.beinsports.com.tr/mac-ozetleri-goller/ingiltere-premier-ligi", "Premier_Lig", 135)

    grouped_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_results = executor.map(fetch_and_parse, urls)
        for result_list in future_results:
            for group_title, line1, line2 in result_list:
                grouped_results.setdefault(group_title, []).append((line1, line2))

    # Dosyaları yaz
    for group_title, lines in grouped_results.items():
        folder_path = os.path.join(output_folder, group_title)
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{group_title}.m3u")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n\n")
            for line1, line2 in lines:
                f.write(line1)
                f.write(line2)

if __name__ == "__main__":
    main()
