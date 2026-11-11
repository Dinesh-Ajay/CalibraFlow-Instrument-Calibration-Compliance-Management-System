import re
import json

path = r'c:\Users\P.DINESH AJAY\Downloads\Calibration Control – Full UI (2).html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

print('File size:', len(content))

# Look for bundled scripts or manifest
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
print(f'Total script tags: {len(scripts)}')

for i, s in enumerate(scripts):
    s_clean = s.strip()
    if 'manifest' in s_clean[:200].lower() or s_clean.startswith('{') or s_clean.startswith('['):
        print(f'Script {i} looks like manifest/json. Length: {len(s_clean)}')
        try:
            data = json.loads(s_clean)
            print(f'Parsed JSON in script {i}. Keys: {list(data.keys()) if isinstance(data, dict) else len(data)}')
            if isinstance(data, dict) and 'files' in data:
                print('Files in manifest:', list(data['files'].keys()))
        except Exception as e:
            print(f'Script {i} JSON parse error: {e}')
            print('Preview:', s_clean[:300])

# Also check for __bundler tags
bundler_tags = re.findall(r'<script[^>]+type=["\']__bundler/([^"\']+)["\'][^>]*>(.*?)</script>', content, re.DOTALL)
print(f'Bundler tags found: {len(bundler_tags)}')
for b_type, b_content in bundler_tags:
    print(f'Type: {b_type}, length: {len(b_content)}')
    if b_type == 'manifest':
        try:
            m_data = json.loads(b_content)
            print('Manifest keys:', list(m_data.keys()))
            if 'files' in m_data:
                for fname, fmeta in m_data['files'].items():
                    print(f' - {fname}: {fmeta}')
        except Exception as e:
            print('Manifest error:', e)
