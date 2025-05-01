import zipfile
import json
import re
import io

def load_json_fields(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {field['name'] for field in data['fields']}

def find_functions(lines):
    funcs = []
    for idx, line in enumerate(lines):
        m = re.match(r'\s*def\s+([A-Za-z_]\w*)\s*\(', line)
        if m:
            funcs.append((idx, m.group(1)))
    return funcs

def function_for_line(functions, lineno):
    name = 'módulo'
    for idx, func in reversed(functions):
        if idx < lineno:
            name = func
            break
    return name

def analyze_zip(zip_path, expected_fields):
    occurrences = {field: [] for field in expected_fields}
    code_literals = {}
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            if not name.endswith('.py'):
                continue
            with z.open(name) as f:
                text = f.read().decode('utf-8', errors='ignore')
            lines = text.splitlines()
            functions = find_functions(lines)
            for i, line in enumerate(lines):
                for field in expected_fields:
                    if re.search(r'\b{}\b'.format(re.escape(field)), line):
                        func = function_for_line(functions, i)
                        occurrences[field].append((name, func, i+1))
                for lit in re.findall(r'["\']([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)["\']', line):
                    key = (name, function_for_line(functions, i), lit, i+1)
                    code_literals.setdefault(lit, []).append(key)
    missing = [f for f, occ in occurrences.items() if not occ]
    extras = {lit: locs for lit, locs in code_literals.items() if lit not in expected_fields}
    print(f"\n=== Informe para {zip_path} ===")
    print("\n-- Campos definidos en JSON encontrados:")
    for field, occ in occurrences.items():
        if occ:
            print(f"\n  • {field}:")
            for name, func, line in occ:
                print(f"      – archivo: {name}, función: {func}, línea: {line}")
    if missing:
        print("\n-- Campos definidos en JSON NO usados en el código:")
        for f in missing:
            print(f"  – {f}")
    if extras:
        print("\n-- Campos detectados en código NO definidos en JSON:")
        for lit, locs in extras.items():
            print(f"\n  • {lit}:")
            for name, func, field, line in locs:
                print(f"      – archivo: {name}, función: {func}, línea: {line}")
    print("\n========================================")

def main():
    expected = load_json_fields('fields_configuration.json')
    for zip_file in ['gpt3.zip', 'gpt4.zip']:
        analyze_zip(zip_file, expected)

if __name__ == '__main__':
    main()
