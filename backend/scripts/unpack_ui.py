import re
import json
import os

path = r'c:\Users\P.DINESH AJAY\Downloads\Calibration Control – Full UI (2).html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Get manifest
m_match = re.search(r'<script type=["\']__bundler/manifest["\'][^>]*>(.*?)</script>', content, re.DOTALL)
p_order = re.search(r'<script type=["\']__bundler/page_order["\'][^>]*>(.*?)</script>', content, re.DOTALL)
tmpl_match = re.search(r'<template id=["\']__bundler_entry["\'][^>]*>(.*?)</template>', content, re.DOTALL)

order = json.loads(p_order.group(1)) if p_order else []
print('Page order:', order)

manifest = json.loads(m_match.group(1)) if m_match else {}

os.makedirs('extracted_ui', exist_ok=True)

for pid in order:
    page_data = manifest.get(pid, {})
    title = page_data.get('title', pid)
    print(f"\n--- Page: {title} (ID: {pid}) ---")
    print("Keys in page_data:", list(page_data.keys()))
    html = page_data.get('html', '') or page_data.get('content', '') or ''
    print(f"Content length: {len(html)}")
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
    with open(f"extracted_ui/{safe_name}.html", "w", encoding="utf-8") as out_f:
        out_f.write(html if html else json.dumps(page_data, indent=2))
    print(f"Saved extracted_ui/{safe_name}.html")

print("\nDone extracting screens!")
