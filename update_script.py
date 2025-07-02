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
            # Inject or update group-title
            if 'group-title="' in extinf:
                updated_extinf = re.sub(r'group-title=".*?"', f'group-title="{group}"', extinf)
            else:
                updated_extinf = extinf.replace(",", f' group-title="{group}",', 1)

            block = "\n".join([updated_extinf, lines[i+1], lines[i+2]])
            output_blocks.append(block)
        i += 3
    else:
        i += 1

# === Write output
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
