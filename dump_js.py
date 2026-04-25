import re
content = open('app/tabs/tab_van_chuyen.py', encoding='utf-8').read()
js = re.search(r'<script>(.*?)</script>', content, re.DOTALL).group(1)
# Remove the f-string replacements to make it pure JS
js = js.replace('{data_json_str}', '[]').replace('{{', '{').replace('}}', '}')
with open('js_test.js', 'w', encoding='utf-8') as f:
    f.write(js)
