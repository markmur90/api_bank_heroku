import zipfile
import json
import ast
import re

def load_json_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {field["name"]: field for field in data["fields"]}

def extract_schema(code_str):
    match = re.search(r'sepa_credit_transfer_schema\s*=\s*({)', code_str)
    if not match:
        return None
    start = code_str.find('{', match.start())
    count = 0
    for i in range(start, len(code_str)):
        if code_str[i] == '{':
            count += 1
        elif code_str[i] == '}':
            count -= 1
            if count == 0:
                end = i + 1
                break
    literal = code_str[start:end]
    return ast.literal_eval(literal)

def flatten_props(props, prefix=""):
    items = []
    for key, val in props.items():
        path = f"{prefix}{key}"
        items.append(path)
        if val.get("type") == "object" and "properties" in val:
            nested = flatten_props(val["properties"], prefix=path + ".")
            items.extend(nested)
    return items

def analyze_zip(zip_path, config):
    with zipfile.ZipFile(zip_path, 'r') as z:
        schema_code = None
        for name in z.namelist():
            if name.endswith("schemas.py"):
                with z.open(name) as f:
                    schema_code = f.read().decode('utf-8')
                break
    schema_dict = extract_schema(schema_code)
    code_fields = []
    if schema_dict and "properties" in schema_dict:
        code_fields = flatten_props(schema_dict["properties"])
    expected = set(config.keys())
    actual = set(code_fields)
    missing = expected - actual
    extra = actual - expected
    print(f"\n=== Informe para {zip_path} ===")
    print(f"Campos encontrados: {len(actual)}")
    if missing:
        print("\nCampos faltantes en el código:")
        for m in sorted(missing):
            print(f"  - {m}")
    if extra:
        print("\nCampos extra en el código:")
        for e in sorted(extra):
            print(f"  - {e}")
    print("\nValidación de campos comunes:")
    for field in sorted(expected & actual):
        cfg = config[field]
        # Aquí podrías añadir comprobaciones more granuladas (tipo, maxLength, pattern...)
        print(f"  - {field}: OK")

def main():
    config = load_json_config("fields_configuration.json")
    for zip_file in ["gpt3.zip", "gpt4.zip"]:
        analyze_zip(zip_file, config)

if __name__ == "__main__":
    main()
