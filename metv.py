import os
import requests
import concurrent.futures

# Premier Lig ID ve Sezonları
premier_sezonlar = {3950: '2025-2026', 3792: '2024-2025', 3613: '2023-2024'}

def fetch_and_parse(url_info):
    url, group_title, folder_path = url_info
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        data = response.json()
        events = data.get('Data', {}).get('events', [])
        lines = []
        for event in events:
            video_url = event.get('highlightVideoUrl')
            if video_url:
                title = f"{event.get('homeTeam',{}).get('name')} {event.get('homeTeam',{}).get('matchScore')}-{event.get('awayTeam',{}).get('matchScore')} {event.get('awayTeam',{}).get('name')}"
                lines.append(f'#EXTINF:-1 group-title="{group_title}",{title}\n{video_url}\n')
        return os.path.join(folder_path, f"{group_title}.m3u"), lines
    except: return None, []

def main():
    base_dir = os.getcwd()
    output_folder = os.path.join(base_dir, 'metv')
    os.makedirs(output_folder, exist_ok=True)
    
    tasks = []
    for s_id, s_adi in premier_sezonlar.items():
        group_title = f"Premier_Lig_{s_adi}"
        folder_path = os.path.join(output_folder, group_title)
        os.makedirs(folder_path, exist_ok=True)
        for hafta in range(1, 39):
            url = f"https://www.beinsports.com.tr/api/highlights/events?sp=1&o=135&s={s_id}&r={hafta}&st=0"
            tasks.append((url, group_title, folder_path))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for file_path, lines in executor.map(fetch_and_parse, tasks):
            if file_path and lines:
                with open(file_path, 'a', encoding='utf-8') as f:
                    if f.tell() == 0: f.write("#EXTM3U\n\n")
                    f.writelines(lines)

if __name__ == "__main__":
    main()
