import os
import re
import json
import requests
from dotenv import load_dotenv

# === Load env variables ===
load_dotenv()
SOURCE_URL = os.environ.get("SOURCE_URL")
CHANNEL_GROUPS_RAW = os.getenv("CHANNEL_GROUPS")

if not SOURCE_URL or not CHANNEL_GROUPS_RAW:
    print("❌ SOURCE_URL or CHANNEL_GROUPS not set in .env")
    exit()

# Convert CHANNEL_GROUPS JSON string to dict
try:
    channel_groups = json.loads(CHANNEL_GROUPS_RAW)
except json.JSONDecodeError as e:
    print(f"❌ Invalid CHANNEL_GROUPS format: {e}")
    exit()

# Create lowercase lookup for allowed channels
allowed_channels = {}
for group, channels in channel_groups.items():
    for name in channels:
        allowed_channels[name.lower()] = group

# === Your custom EXTINF replacements ===
custom_channel_data = {
  "aaj tak": {
    "tvg-id": "ts689",
    "tvg-name": "Aaj Tak",
    "tvg-logo": "https://jiotvimages.cdn.jio.com/dare_images/images/Aaj_Tak.png",
    "display-name": "Aaj Tak"
  },
  "zee news": {
    "tvg-id": "ts259",
    "tvg-name": "Zee News",
    "tvg-logo": "https://jiotvimages.cdn.jio.com/dare_images/images/Zee_News.png",
    "display-name": "Zee News"
  },
  "zee tv hd": {
    "tvg-id": "ts63",
    "tvg-name": "Zee TV HD",
    "tvg-logo": "https://watchindia.net/images/channels/hindi/Zee_TV.png",
    "display-name": "Zee TV HD"
  },
  "&tv hd": {
    "tvg-id": "ts40",
    "tvg-name": "& TV HD",
    "tvg-logo": "https://watchindia.net/images/channels/hindi/And_TV_HD.png",
    "display-name": "&TV HD"
  },
  "zee anmol": {
    "tvg-id": "ts523",
    "tvg-name": "Zee Anmol",
    "tvg-logo": "https://jiotvimages.cdn.jio.com/dare_images/images/Zee_Anmol.png",
    "display-name": "Zee Anmol"
  },
  "zee cinema hd": {
    "tvg-id": "ts503",
    "tvg-name": "Zee Cinema HD",
    "tvg-logo": "https://watchindia.net/images/channels/hindi/Zee_Cinema_HD.png",
    "display-name": "Zee Cinema HD"
  },
  "&pictures hd": {
    "tvg-id": "ts267",
    "tvg-name": "& Pictures HD",
    "tvg-logo": "https://watchindia.net/images/channels/hindi/AndPictures_HD.png",
    "display-name": "&Pictures HD"
  },
  "zee bollywood": {
    "tvg-id": "441321",
    "tvg-name": "Zee Bollywood",
    "tvg-logo": "https://jiotv.catchup.cdn.jio.com/dare_images/images/Zee_Classic.png",
    "display-name": "Zee Bollywood"
  },
  "&pictures": {
    "tvg-id": "441329",
    "tvg-name": "&Pictures",
    "tvg-logo": "https://jiotvimages.cdn.jio.com/dare_images/images/And_Pictures.png",
    "display-name": "&Pictures"
  },
  "zee cinema": {
    "tvg-id": "441401",
    "tvg-name": "Zee Cinema",
    "tvg-logo": "https://jiotvimages.cdn.jio.com/dare_images/images/Zee_Cinema.png",
    "display-name": "Zee Cinema"
  },
  "zee tv": {
    "tvg-id": "ts557",
    "tvg-name": "Zee TV",
    "tvg-logo": "https://jiotvimages.cdn.jio.com/dare_images/images/Zee_TV.png",
    "display-name": "Zee TV"
  },
  "zee classic": {
    "tvg-id": "411574",
    "tvg-name": "Zee Classic",
    "tvg-logo": "https://jiotvimages.cdn.jio.com/dare_images/images/Zee_Classic.png",
    "display-name": "Zee Classic"
  }
}


# === Fetch playlist ===
print(f"📥 Fetching playlist from: {SOURCE_URL}")
try:
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()
except Exception as e:
    print(f"❌ Error fetching playlist: {e}")
    exit()

# === Process 3-line blocks ===
output_blocks = []
i = 0
while i + 2 < len(lines):
    if lines[i].startswith("#EXTINF:") and lines[i+1].startswith("#EXTVLCOPT:") and lines[i+2].startswith("http"):
        extinf = lines[i]
        channel_name = extinf.split(",")[-1].strip()
        group = allowed_channels.get(channel_name.lower())

        if group:
            channel_key = channel_name.lower()
            custom_info = custom_channel_data.get(channel_key)

            if custom_info:
                updated_extinf = (
                    f'#EXTINF:-1 '
                    f'tvg-id="{custom_info.get("tvg-id", "")}" '
                    f'tvg-name="{custom_info.get("tvg-name", "")}" '
                    f'tvg-logo="{custom_info.get("tvg-logo", "")}" '
                    f'group-title="{group}",' 
                    f'{custom_info.get("display-name", channel_name)}'
                )
            else:
                # fallback: only update group-title
                if 'group-title="' in extinf:
                    updated_extinf = re.sub(r'group-title=".*?"', f'group-title="{group}"', extinf)
                else:
                    updated_extinf = extinf.replace(",", f' group-title="{group}",', 1)

            block = "\n".join([updated_extinf, lines[i+1], lines[i+2]])
            output_blocks.append(block)
        i += 3
    else:
        i += 1

# === Write output ===
output_file = "Zee.m3u"
if output_blocks:
    print(f"✅ Found {len(output_blocks)} categorized channels.")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n# Updated By Himanshu\n\n")
        for block in output_blocks:
            f.write(block + "\n")
else:
    print("⚠️ No matching channels found.")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n# No matching channels found\n")

os.chmod(output_file, 0o666)
print(f"✅ '{output_file}' written successfully.")
