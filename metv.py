import os
import requests
import concurrent.futures

# Premier Lig için ID'ler ve sezonlar (Süper Lig tarzı manuel garanti)
premier_sezonlar = {
    3950: '2025-2026',
    3792: '2024-2025',
    3613: '2023-2024',
    3466: '2022-2023'
}

def fetch_and_parse(url_info):
    url, group_title = url_info
    try:
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        data = response.json()
        events = data.get('Data', {}).get('events', [])
        result = []
        for event in events:
            video_url = event.get('highlightVideoUrl')
            if video_url:
                title = f"{event.get('homeTeam',{}).get('name')} {event.get('homeTeam',{}).get('matchScore')}-{event.get('awayTeam',{}).get('matchScore')} {event.get('awayTeam',{}).get('name')}"
                line1 = f'#EXTINF:-1 group-title="{group_title}",{title}\n'
                line2 = f"{video_url}\n"
                result.append((group_title, line1, line2))
        return result
    except: return []

def main():
    output_folder = 'metv'
    os.makedirs(output_folder, exist_ok=True)
    
    all_urls = []
    # Premier Lig (org_id: 135)
    for s_id, s_adi in premier_sezonlar.items():
        group_title = f"Premier_Lig_{s_adi}"
        # Sezon içindeki haftaları dolaş (1'den 38'e kadar)
        for hafta in range(1, 39):
            url = f"https://www.beinsports.com.tr/api/highlights/events?sp=1&o=135&s={s_id}&r={hafta}&st=0"
            all_urls.append((url, group_title))

    grouped_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for result_list in executor.map(fetch_and_parse, all_urls):
            for group_title, line1, line2 in result_list:
                grouped_results.setdefault(group_title, []).append((line1, line2))

    # Süper Lig kodundaki gibi klasörle ve yaz
    for group_title, lines in grouped_results.items():
        folder_path = os.path.join(output_folder, group_title)
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{group_title}.m3u")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n\n")
            for line1, line2 in lines:
                f.write(line1 + line2)

if __name__ == "__main__":
    main()
