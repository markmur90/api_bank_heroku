import os
import json
import re

def solicitar_ruta():
    ruta = input('Ruta de archivos JSON (enter = actual): ').strip()
    return ruta or '.'

def listar_json(ruta):
    return [f for f in os.listdir(ruta) if f.lower().endswith('.json')]

def seleccionar_archivo(lista):
    for i, nombre in enumerate(lista, 1):
        print(f'{i}. {nombre}')
    indice = int(input('Selecciona un número: '))
    return lista[indice - 1]

def cargar_json(ruta, archivo):
    with open(os.path.join(ruta, archivo), 'r', encoding='utf-8') as f:
        return json.load(f)

def detectar_format(valor):
    if isinstance(valor, str):
        iso = r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)?$'
        if re.match(iso, valor):
            return 'date-time'
    return None

def recorrer(obj, prefijo, acumulador):
    if isinstance(obj, dict):
        for clave, val in obj.items():
            nuevo_prefijo = f'{prefijo}/{clave}' if prefijo else clave
            recorrer(val, nuevo_prefijo, acumulador)
    elif isinstance(obj, list):
        tipo_items = None
        if obj:
            tipo_items = type(obj[0]).__name__
        acumulador.append({
            'path': prefijo,
            'in': 'body',
            'type': 'array',
            'itemsType': tipo_items,
            'required': True
        })
        for val in obj:
            recorrer(val, prefijo + '[]', acumulador)
    else:
        entrada = {
            'path': prefijo,
            'in': 'body',
            'type': type(obj).__name__,
            'required': True
        }
        fmt = detectar_format(obj)
        if fmt:
            entrada['format'] = fmt
        if isinstance(obj, str):
            entrada['minLength'] = len(obj)
            entrada['maxLength'] = len(obj)
        if isinstance(obj, list):
            entrada['enum'] = obj
        acumulador.append(entrada)

def generar_esquema(data):
    propiedades = []
    recorrer(data, '', propiedades)
    tag = data.get('tag', 'default') if isinstance(data, dict) else 'default'
    return { tag: propiedades }

def guardar_esquema(ruta, nombre_original, esquema):
    base, _ = os.path.splitext(nombre_original)
    nombre_salida = f'{base}_schema.json'
    with open(os.path.join(ruta, nombre_salida), 'w', encoding='utf-8') as f:
        json.dump(esquema, f, ensure_ascii=False, indent=2)
    print(f'Esquema guardado en {nombre_salida}')

def main():
    ruta = solicitar_ruta()
    archivos = listar_json(ruta)
    if not archivos:
        print('No hay archivos JSON en la ruta indicada.')
        return
    seleccionado = seleccionar_archivo(archivos)
    data = cargar_json(ruta, seleccionado)
    esquema = generar_esquema(data)
    guardar_esquema(ruta, seleccionado, esquema)

if __name__ == '__main__':
    main()
