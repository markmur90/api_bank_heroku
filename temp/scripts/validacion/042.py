import os
import json

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

def guardar_esquema(ruta, nombre_original, esquema):
    base, _ = os.path.splitext(nombre_original)
    nombre_salida = f'{base}_schema.json'
    with open(os.path.join(ruta, nombre_salida), 'w', encoding='utf-8') as f:
        json.dump(esquema, f, ensure_ascii=False, indent=4)
    print(f'Esquema generado en {os.path.join(ruta, nombre_salida)}')

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
                        schema = resolve_ref(schema['$ref'], spec)
                    field_schema = {
                        'in': p.get('in'),
                        'type': schema.get('type', p.get('type')),
                        'format': schema.get('format'),
                        'maxLength': schema.get('maxLength'),
                        'minLength': schema.get('minLength'),
                        'enum': schema.get('enum'),
                        'required': p.get('required', False)
                    }
                    if schema.get('properties'):
                        field_schema['properties'] = schema['properties']
                        field_schema['required'] = schema.get('required', [])
                    entries.append({'name': p.get('name'), 'schema': field_schema})
            if 'requestBody' in operation:
                content = operation['requestBody']['content'].get('application/json', {})
                schema_body = content.get('schema', {})
                if '$ref' in schema_body:
                    schema_body = resolve_ref(schema_body['$ref'], spec)
                for name, prop in schema_body.get('properties', {}).items():
                    prop_schema = resolve_ref(prop['$ref'], spec) if '$ref' in prop else prop
                    field_schema = prop_schema.copy()
                    entries.append({'name': name, 'schema': field_schema})
            payload_structure[route][method] = {'parameters': entries}
            for tag in operation.get('tags', ['Default']):
                grouped_by_tag.setdefault(tag, {})
                for field in entries:
                    grouped_by_tag[tag][field['name']] = field['schema']

    result = {
        'payload_structure': payload_structure,
        'grouped_by_tag': grouped_by_tag
    }

    guardar_esquema(ruta, seleccionado, result)

if __name__ == '__main__':
    main()
