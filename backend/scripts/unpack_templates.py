import re
import json
import os

files = sorted(os.listdir('extracted_ui'))
os.makedirs('extracted_ui/templates', exist_ok=True)

for fname in files:
    if not fname.endswith('.html') or fname.startswith('template'):
        continue
    fpath = os.path.join('extracted_ui', fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        text = f.read()

    tmpl_match = re.search(r'<script type=["\']__bundler/template["\'][^>]*>(.*?)</script>', text, re.DOTALL)
    if tmpl_match:
        try:
            tmpl_str = json.loads(tmpl_match.group(1))
            out_name = f"extracted_ui/templates/{fname}"
            with open(out_name, 'w', encoding='utf-8') as out_f:
                out_f.write(tmpl_str)
            print(f"Extracted template for {fname} -> {out_name} ({len(tmpl_str)} chars)")
        except Exception as e:
            print(f"Error parsing template for {fname}: {e}")
    else:
        print(f"No template found in {fname}")

print("\nDone extracting inner HTML templates!")
