import os
import json
import re

type_map = {
    'string': 'str',
    'integer': 'int',
    'number': '(int, float)',
    'boolean': 'bool'
}

def sanitize_name(name):
    return re.sub(r'[^0-9a-zA-Z_]', '_', name)

def solicitar_ruta():
    ruta = input('Ruta de archivos JSON (enter = actual): ').strip()
    return ruta or '.'

def listar_json(ruta):
    try:
        return [f for f in os.listdir(ruta) if f.lower().endswith('.json')]
    except OSError:
        print(f'Error al acceder a la ruta {ruta}')
        return []

def seleccionar_archivo(lista):
    for i, nombre in enumerate(lista, 1):
        print(f'{i}. {nombre}')
    indice = int(input('Selecciona un número: '))
    return lista[indice - 1]

def cargar_json(ruta, archivo):
    with open(os.path.join(ruta, archivo), 'r', encoding='utf-8') as f:
        return json.load(f)

def resolve_ref(ref, spec):
    parts = ref.lstrip('#/').split('/')
    result = spec
    for part in parts:
        result = result.get(part, {})
    return result

def generate_validator(ruta, seleccionado, spec, payload_structure, grouped_by_tag, ref_definitions):
    lines = []
    lines.append("import json")
    lines.append("import re")
    lines.append("")
    lines.append("class ValidationError(Exception): pass")
    lines.append("")
    path_spec = os.path.join(ruta, seleccionado).replace("\\", "\\\\")
    lines.append(f"with open(r'{path_spec}', 'r', encoding='utf-8') as f:")
    lines.append("    spec = json.load(f)")
    lines.append("")
    lines.append("payload_structure = " + repr(payload_structure))
    lines.append("grouped_by_tag = " + repr(grouped_by_tag))
    lines.append("")
    for ref_name, schema in ref_definitions.items():
        fn = sanitize_name(ref_name)
        lines.append(f"def validate_{fn}(obj):")
        lines.append("    if not isinstance(obj, dict):")
        lines.append(f"        raise ValidationError('Expected object for {fn}')")
        for prop in schema.get('required', []):
            lines.append(f"    if '{prop}' not in obj:")
            lines.append(f"        raise ValidationError('Missing {prop} in {fn}')")
        for prop, ps in schema.get('properties', {}).items():
            if 'type' in ps:
                py = type_map.get(ps['type'], 'str')
                lines.append(f"    if '{prop}' in obj and not isinstance(obj['{prop}'], {py}):")
                lines.append(f"        raise ValidationError('{prop} must be of type {ps['type']}')")
            if 'enum' in ps:
                lines.append(f"    if '{prop}' in obj and obj['{prop}'] not in {ps['enum']}:")
                lines.append(f"        raise ValidationError('{prop} must be one of {ps['enum']}')")
        lines.append("    return True")
        lines.append("")
    for tag, fields in grouped_by_tag.items():
        tfn = sanitize_name(tag)
        for field_name, fs in fields.items():
            ffn = sanitize_name(field_name)
            ref = fs.get('$ref_name')
            lines.append(f"def validate_{tfn}_{ffn}(value):")
            if ref:
                rfn = sanitize_name(ref)
                lines.append(f"    return validate_{rfn}(value)")
            else:
                if 'type' in fs:
                    py = type_map.get(fs['type'], 'str')
                    lines.append(f"    if not isinstance(value, {py}):")
                    lines.append(f"        raise ValidationError('Field {field_name} must be {fs['type']}')")
                if 'maxLength' in fs:
                    lines.append(f"    if hasattr(value, '__len__') and len(value) > {fs['maxLength']}:")
                    lines.append(f"        raise ValidationError('Field {field_name} max length is {fs['maxLength']}')")
                if 'minLength' in fs:
                    lines.append(f"    if hasattr(value, '__len__') and len(value) < {fs['minLength']}:")
                    lines.append(f"        raise ValidationError('Field {field_name} min length is {fs['minLength']}')")
                if 'enum' in fs:
                    lines.append(f"    if value not in {fs['enum']}:")
                    lines.append(f"        raise ValidationError('Field {field_name} must be one of {fs['enum']}')")
                lines.append("    return True")
            lines.append("")
    for tag, fields in grouped_by_tag.items():
        tfn = sanitize_name(tag)
        headers = [n for n, s in fields.items() if s.get('in') == 'header']
        paths   = [n for n, s in fields.items() if s.get('in') == 'path']
        lines.append(f"def validate_structure_headers_{tfn}(headers):")
        lines.append(f"    expected = {headers}")
        lines.append("    missing = [f for f in expected if f not in headers]")
        lines.append("    if missing:")
        lines.append("        raise ValidationError(f'Missing headers: {missing}')")
        lines.append("    extra = [f for f in headers if f not in expected]")
        lines.append("    if extra:")
        lines.append("        raise ValidationError(f'Unexpected headers: {extra}')")
        lines.append("    return True")
        lines.append("")
        lines.append(f"def validate_structure_path_{tfn}(path_params):")
        lines.append(f"    expected = {paths}")
        lines.append("    missing = [f for f in expected if f not in path_params]")
        lines.append("    if missing:")
        lines.append("        raise ValidationError(f'Missing path params: {missing}')")
        lines.append("    extra = [f for f in path_params if f not in expected]")
        lines.append("    if extra:")
        lines.append("        raise ValidationError(f'Unexpected path params: {extra}')")
        lines.append("    return True")
        lines.append("")
        lines.append(f"def validate_headers_{tfn}(headers):")
        lines.append(f"    validate_structure_headers_{tfn}(headers)")
        for h in headers:
            sh = sanitize_name(h)
            lines.append(f"    validate_{tfn}_{sh}(headers['{h}'])")
        lines.append("    return True")
        lines.append("")
        lines.append(f"def validate_path_{tfn}(path_params):")
        lines.append(f"    validate_structure_path_{tfn}(path_params)")
        for p in paths:
            sp = sanitize_name(p)
            lines.append(f"    validate_{tfn}_{sp}(path_params['{p}'])")
        lines.append("    return True")
        lines.append("")
    validator_path = os.path.join(ruta, 'validator.py')
    with open(validator_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'Validator generado en {validator_path}')

def main():
    ruta = solicitar_ruta()
    archivos = listar_json(ruta)
    if not archivos:
        print('No hay archivos JSON en la ruta indicada.')
        return
    seleccionado = seleccionar_archivo(archivos)
    spec = cargar_json(ruta, seleccionado)
    payload_structure = {}
    grouped_by_tag = {}
    ref_definitions = {}
    for route, methods in spec.get('paths', {}).items():
        payload_structure[route] = {}
        for method, operation in methods.items():
            if method.lower() not in ['get','post','put','delete','patch','options','head']:
                continue
            entries = []
            if 'parameters' in operation:
                for p in operation['parameters']:
                    schema = p.get('schema', {})
                    if '$ref' in schema:
                        ref = schema['$ref']
                        name = ref.split('/')[-1]
                        resolved = resolve_ref(ref, spec)
                        ref_definitions[name] = resolved
                        fschema = resolved.copy()
                        fschema['$ref_name'] = name
                    else:
                        fschema = schema.copy()
                    field_schema = {
                        'in': p.get('in'),
                        'type': fschema.get('type'),
                        'format': fschema.get('format'),
                        'maxLength': fschema.get('maxLength'),
                        'minLength': fschema.get('minLength'),
                        'enum': fschema.get('enum'),
                        '$ref_name': fschema.get('$ref_name')
                    }
                    entries.append({'name': p.get('name'), 'schema': field_schema})
            if 'requestBody' in operation:
                content = operation['requestBody']['content'].get('application/json', {})
                schema_body = content.get('schema', {})
                if '$ref' in schema_body:
                    ref = schema_body['$ref']
                    schema_body = resolve_ref(ref, spec)
                for name, prop in schema_body.get('properties', {}).items():
                    if '$ref' in prop:
                        ref = prop['$ref']
                        rname = ref.split('/')[-1]
                        resolved = resolve_ref(ref, spec)
                        ref_definitions[rname] = resolved
                        prop_schema = {'$ref_name': rname}
                    else:
                        prop_schema = prop.copy()
                    entries.append({'name': name, 'schema': prop_schema})
            payload_structure[route][method] = {'parameters': entries}
            for tag in operation.get('tags', ['Default']):
                grouped_by_tag.setdefault(tag, {})
                for field in entries:
                    grouped_by_tag[tag][field['name']] = field['schema']
    generate_validator(ruta, seleccionado, spec, payload_structure, grouped_by_tag, ref_definitions)

if __name__ == '__main__':
    main()
