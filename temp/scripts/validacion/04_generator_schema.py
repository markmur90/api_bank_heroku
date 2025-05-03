import json
import os

path = input("Ingrese la ruta donde está ubicado el archivo JSON: ").strip()
input_file = input("Ingrese el nombre del archivo JSON (incluya .json): ").strip()
output_file = input("Ingrese el nombre para el archivo JSON que se generará (incluya .json): ").strip()

input_path = os.path.join(path, input_file)
with open(input_path, 'r', encoding='utf-8') as f:
    spec = json.load(f)

def resolve_ref(ref, spec):
    parts = ref.lstrip('#/').split('/')
    result = spec
    for part in parts:
        result = result.get(part, {})
    return result

payload_structure = {}
grouped_by_tag = {}

for route, methods in spec.get("paths", {}).items():
    payload_structure[route] = {}
    for method, operation in methods.items():
        if method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
            continue
        entries = []
        if "parameters" in operation:
            for p in operation["parameters"]:
                schema = p.get("schema", {})
                if "$ref" in schema:
                    schema = resolve_ref(schema["$ref"], spec)
                entries.append({
                    "name": p.get("name"),
                    "in": p.get("in"),
                    "type": schema.get("type", p.get("type")),
                    "format": schema.get("format"),
                    "maxLength": schema.get("maxLength"),
                    "minLength": schema.get("minLength"),
                    "enum": schema.get("enum"),
                    "required": p.get("required", False)
                })
        if "requestBody" in operation:
            content = operation["requestBody"]["content"].get("application/json", {})
            schema = content.get("schema", {})
            if "$ref" in schema:
                schema = resolve_ref(schema["$ref"], spec)
            for name, prop in schema.get("properties", {}).items():
                prop_schema = resolve_ref(prop["$ref"], spec) if "$ref" in prop else prop
                entries.append({
                    "name": name,
                    "in": "body",
                    "type": prop_schema.get("type"),
                    "format": prop_schema.get("format"),
                    "maxLength": prop_schema.get("maxLength"),
                    "minLength": prop_schema.get("minLength"),
                    "enum": prop_schema.get("enum"),
                    "required": name in schema.get("required", [])
                })
        payload_structure[route][method] = {"parameters": entries}
        for tag in operation.get("tags", ["Default"]):
            grouped_by_tag.setdefault(tag, {})
            for field in entries:
                name = field["name"]
                props = {k: v for k, v in field.items() if k != "name"}
                grouped_by_tag[tag].setdefault(name, props)

result = {
    "payload_structure": payload_structure,
    "grouped_by_tag": grouped_by_tag
}

output_path = os.path.join(path, output_file)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print(f"Esquema generado en {output_path}")
