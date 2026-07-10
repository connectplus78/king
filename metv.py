import os
import json
import requests
import concurrent.futures
import shutil

def get_league_urls(page_url, league_name, org_id):
    urls_to_fetch = []
    try:
        response = requests.get(page_url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        import re
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text, re.DOTALL)
        if not match: return []
        data = json.loads(match.group(1))
        highlights_data = data.get("props", {}).get("pageProps", {}).get("initialReduxState", {}).get("highlights", {}).get("data", [])
        
        for league_info in highlights_data:
            if league_info.get("id") == org_id:
                for season in league_info.get("seasons", []):
                    season_name = season.get("name").replace('/', '-')
                    file_name = f"{league_name}_{season_name}.m3u"
                    for round_info in season.get("rounds", []):
                        url = f"https://beinsports.com.tr/api/highlights/events?sp=1&o={org_id}&s={season.get('id')}&r={round_info.get('round')}&st={round_info.get('st', 0)}"
                        urls_to_fetch.append((url, file_name))
        return urls_to_fetch
    except Exception as e:
        print(f"Hata: {e}")
        return []

def fetch_and_parse(url_info):
    url, file_name = url_info
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        data = response.json()
        events = data.get('Data', {}).get('events', [])
        result = []
        for event in events:
            video_url = event.get('highlightVideoUrl')
            if video_url:
                title = f"{event.get('homeTeam',{}).get('name')} {event.get('homeTeam',{}).get('matchScore')} - {event.get('awayTeam',{}).get('matchScore')} {event.get('awayTeam',{}).get('name')}"
                result.append((file_name, f"#EXTINF:-1,{title}\n{video_url}\n"))
        return result
    except: return []

def main():
    output_folder = 'metv'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print("Klasör oluşturuldu.")
    
    urls = get_league_urls("https://www.beinsports.com.tr/mac-ozetleri-goller/ingiltere-premier-ligi", "Premier_Lig", 135)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_and_parse, urls)
        for result_list in results:
            for file_name, content in result_list:
                with open(os.path.join(output_folder, file_name), 'a', encoding='utf-8') as f:
                    if f.tell() == 0: f.write("#EXTM3U\n\n")
                    f.write(content)
    print("İşlem tamamlandı, dosyalar oluşturuldu.")

if __name__ == "__main__":
    main()
