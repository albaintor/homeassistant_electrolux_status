import os
import re

def fix_urls():
    translations_dir = 'custom_components/electrolux_status/translations'
    if not os.path.exists(translations_dir):
        print(f"Directory {translations_dir} not found")
        return
    files = os.listdir(translations_dir)
    print(f"Found {len(files)} files")
    for filename in files:
        if filename.endswith('.json'):
            filepath = os.path.join(translations_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content = re.sub(r'https://developer\.electrolux\.one/', '{url}', content)
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Fixed {filename}')
            else:
                print(f'No change in {filename}')

if __name__ == '__main__':
    fix_urls()