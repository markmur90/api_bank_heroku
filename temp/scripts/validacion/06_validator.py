#!/usr/bin/env python3
import zipfile
import json
import re
import os

def flatten_schema(schema, parent_key=''):
    fields_map = {}
    lower_map = {}
    props = schema.get('properties', {})
    for key, subschema in props.items():
        full_key = f"{parent_key}.{key}" if parent_key else key
        fields_map[full_key] = subschema
        lower_map[full_key.lower()] = full_key
        t = subschema.get('type')
        if t == 'object' or 'properties' in subschema:
            fm, lm = flatten_schema(subschema, full_key)
            fields_map.update(fm)
            lower_map.update(lm)
        elif t == 'array' and 'items' in subschema:
            items = subschema['items']
            if 'properties' in items:
                fm, lm = flatten_schema(items, full_key)
                fields_map.update(fm)
                lower_map.update(lm)
    return fields_map, lower_map

def flatten_json(data, parent_key=''):
    flat_map = {}
    lower_map = {}
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                fm, lm = flatten_json(value, full_key)
                flat_map.update(fm)
                lower_map.update(lm)
            elif isinstance(value, list):
                found = False
                for item in value:
                    if isinstance(item, dict):
                        fm, lm = flatten_json(item, full_key)
                        flat_map.update(fm)
                        lower_map.update(lm)
                        found = True
                if not found:
                    flat_map[full_key] = value
                    lower_map[full_key.lower()] = full_key
            else:
                flat_map[full_key] = value
                lower_map[full_key.lower()] = full_key
    return flat_map, lower_map

def detect_type(value):
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, int):
        return 'integer'
    if isinstance(value, float):
        return 'number'
    if isinstance(value, str):
        return 'string'
    if isinstance(value, list):
        return 'array'
    if isinstance(value, dict):
        return 'object'
    if value is None:
        return 'null'
    return type(value).__name__

def analyze_zip():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = input("Ingrese la ruta donde está ubicado el esquema JSON (Enter para script): ").strip() or script_dir
    json_file = input("Ingrese el nombre del archivo JSON del esquema (Enter para 'fields_configuration.json'): ").strip() or "fields_configuration.json"
    zip_dir = input("Ingrese la ruta de los archivos ZIP (Enter para script): ").strip() or script_dir
    zip_files_input = input("ZIPs separados por coma (Enter para todos): ").strip()
    if not zip_files_input:
        zip_files = [f for f in os.listdir(zip_dir) if f.lower().endswith('.zip')]
    else:
        zip_files = [z.strip() for z in zip_files_input.split(',') if z.strip()]
    omit_files_input = input("Archivos ZIP a omitir (coma) (Enter para ninguno): ").strip()
    omit_files = [f.strip() for f in omit_files_input.split(',')] if omit_files_input else []
    omit_validators_input = input("Validadores a omitir (type,maxLength,minLength,pattern,enum) (coma) (Enter para ninguno): ").strip()
    omit_validators = [v.strip() for v in omit_validators_input.split(',')] if omit_validators_input else []

    schema_fullpath = os.path.join(json_path, json_file)
    try:
        with open(schema_fullpath, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except Exception as e:
        print(f"No se pudo leer el esquema JSON: {e}")
        return

    schema_map, schema_lower = flatten_schema(schema)
    schema_lower_set = set(schema_lower.keys())

    for zip_name in zip_files:
        if zip_name in omit_files:
            continue
        zip_path_full = os.path.join(zip_dir, zip_name)
        if not os.path.isfile(zip_path_full):
            print(f"Archivo ZIP no encontrado: {zip_path_full}")
            continue

        try:
            with zipfile.ZipFile(zip_path_full, 'r') as z:
                json_entries = [n for n in z.namelist() if n.lower().endswith('.json') and n not in omit_files]
                print(f"Analizando: {zip_path_full}")
                if not json_entries:
                    print("  No hay archivos JSON dentro del ZIP.")
                    continue
                for entry in json_entries:
                    with z.open(entry) as jf:
                        data = json.load(jf)
                    json_map, json_lower_map = flatten_json(data)
                    matching = schema_lower_set & set(json_lower_map.keys())
                    missing = schema_lower_set - matching
                    extra = set(json_lower_map.keys()) - matching
                    alias_map = {}

                    for j_lower in list(extra):
                        candidates = [s for s in missing if s in j_lower]
                        if len(candidates) == 1:
                            s = candidates[0]
                            matching.add(s)
                            missing.remove(s)
                            extra.remove(j_lower)
                            alias_map[s] = j_lower
                        elif len(candidates) > 1:
                            s = max(candidates, key=len)
                            matching.add(s)
                            missing.remove(s)
                            extra.remove(j_lower)
                            alias_map[s] = j_lower

                    print(f"  Archivo: {entry}")
                    print(f"    Campos encontrados: {len(matching)} de {len(schema_lower_set)}")
                    print("    Validaciones:")
                    for lower in sorted(matching):
                        orig = schema_lower[lower]
                        j_orig = alias_map.get(lower, json_lower_map.get(lower))
                        value = json_map.get(j_orig)
                        subschema = schema_map[orig]
                        details = []
                        if 'type' not in omit_validators:
                            actual = detect_type(value)
                            exp = subschema.get('type')
                            exp_list = exp if isinstance(exp, list) else [exp]
                            if actual not in exp_list:
                                details.append(f"Tipo inválido: esperado {exp_list}, obtenido {actual}")
                        if 'maxLength' in subschema and 'maxLength' not in omit_validators:
                            if isinstance(value, str) and len(value) > subschema['maxLength']:
                                details.append(f"Longitud > maxLength: {len(value)} > {subschema['maxLength']}")
                        if 'minLength' in subschema and 'minLength' not in omit_validators:
                            if isinstance(value, str) and len(value) < subschema['minLength']:
                                details.append(f"Longitud < minLength: {len(value)} < {subschema['minLength']}")
                        if 'pattern' in subschema and 'pattern' not in omit_validators:
                            if isinstance(value, str) and not re.fullmatch(subschema['pattern'], value):
                                details.append(f"No cumple patrón: {subschema['pattern']}")
                        if 'enum' in subschema and 'enum' not in omit_validators:
                            if value not in subschema['enum']:
                                details.append(f"Valor no está en enum: {value}")
                        print(f"      {orig}:")
                        if not details:
                            print("        - OK")
                        else:
                            for d in details:
                                print(f"        - {d}")

                    if missing:
                        print("    Faltantes:")
                        for lower in sorted(missing):
                            print(f"      {schema_lower[lower]}")
                    if extra:
                        print("    Extras:")
                        for lower in sorted(extra):
                            print(f"      {json_lower_map[lower]}")
                    print()
        except zipfile.BadZipFile as e:
            print(f"No es un ZIP válido: {zip_path_full} ({e})")

def main():
    analyze_zip()

if __name__ == '__main__':
    main()
