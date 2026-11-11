import re

with open(r'c:\Users\P.DINESH AJAY\Downloads\Calibration Control – Full UI (2).html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

scripts = re.findall(r'<script>(.*?)</script>', text, re.DOTALL)
if scripts:
    with open('backend/scripts/bundler_script.js', 'w', encoding='utf-8') as out:
        out.write(scripts[0])
    print('Saved bundler_script.js! Length:', len(scripts[0]))
