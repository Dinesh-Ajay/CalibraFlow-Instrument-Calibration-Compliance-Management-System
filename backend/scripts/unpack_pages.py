import re
import json
import base64
import gzip
import os

path = r'c:\Users\P.DINESH AJAY\Downloads\Calibration Control – Full UI (2).html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

m_match = re.search(r'<script type=["\']__bundler/manifest["\'][^>]*>(.*?)</script>', content, re.DOTALL)
p_order = re.search(r'<script type=["\']__bundler/page_order["\'][^>]*>(.*?)</script>', content, re.DOTALL)

manifest = json.loads(m_match.group(1))
order = json.loads(p_order.group(1))

os.makedirs('extracted_ui', exist_ok=True)

titles = [
    "01_Dashboard",
    "02_Workflow_Board",
    "03_Instruments",
    "04_Plans_and_Events",
    "05_Certificates",
    "06_Work_Orders",
    "07_Production_Use",
    "08_Alerts",
    "09_Audit_Trail",
    "10_Data_Quality"
]

for idx, uuid in enumerate(order):
    entry = manifest.get(uuid, {})
    raw_data = entry.get('data', '')
    compressed = entry.get('compressed', False)
    mime = entry.get('mime', 'text/html')

    decoded = base64.b64decode(raw_data)
    if compressed:
        try:
            unpacked_bytes = gzip.decompress(decoded)
        except Exception:
            # maybe zlib
            import zlib
            unpacked_bytes = zlib.decompress(decoded, 16 + zlib.MAX_WBITS)
    else:
        unpacked_bytes = decoded

    text = unpacked_bytes.decode('utf-8', errors='ignore')

    # Try to find page title inside text
    title_match = re.search(r'<title>(.*?)</title>', text, re.I)
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.I)
    page_name = titles[idx] if idx < len(titles) else f"page_{idx+1}"
    if title_match:
        page_name += f"_{title_match.group(1).strip()}"
    elif h1_match:
        page_name += f"_{re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()}"

    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', page_name)[:50]
    out_file = f"extracted_ui/{safe_name}.html"
    with open(out_file, 'w', encoding='utf-8') as out:
        out.write(text)

    print(f"[{idx+1}/10] Unpacked {uuid} -> {out_file} ({len(text)} bytes, mime: {mime})")

print("\nSuccessfully unpacked all reference UI screens!")
