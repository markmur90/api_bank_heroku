import os
import zipfile
import ast
from datetime import datetime
def obtener_rutas():
    rutas_str = input("Ingresa la ruta de los archivos ZIP (separadas por coma): ")
    rutas = [r.strip() for r in rutas_str.split(",") if r.strip()]
    for r in rutas:
        if not os.path.isfile(r) or not r.lower().endswith(".zip"):
            print(f"Error: '{r}' no es un ZIP válido.")
            exit(1)
    return rutas
def extraer_funciones(ruta_zip):
    funciones_por_archivo = {}
    with zipfile.ZipFile(ruta_zip) as z:
        for nombre in z.namelist():
            if nombre.lower().endswith(".py"):
                with z.open(nombre) as f:
                    try:
                        contenido = f.read().decode("utf-8", "ignore")
                        arbol = ast.parse(contenido)
                        funciones = [n.name for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)]
                        funciones_por_archivo[nombre] = funciones
                    except Exception:
                        funciones_por_archivo[nombre] = []
    return funciones_por_archivo
def funciones_comunes_internas(funciones_por_archivo):
    mapa = {}
    for archivo, funcs in funciones_por_archivo.items():
        for fn in funcs:
            mapa.setdefault(fn, []).append(archivo)
    return {fn: archivos for fn, archivos in mapa.items() if len(archivos) > 1}
def reporte():
    rutas = obtener_rutas()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datos = {}
    for ruta in rutas:
        funciones_por_archivo = extraer_funciones(ruta)
        comunes = funciones_comunes_internas(funciones_por_archivo)
        todas = set(fn for funcs in funciones_por_archivo.values() for fn in funcs)
        datos[ruta] = {
            "funciones_por_archivo": funciones_por_archivo,
            "comunes": comunes,
            "todas": todas
        }
    print(f"\nInforme de correlación — {ahora}\n" + "-"*50)
    for ruta, info in datos.items():
        total_py = len(info["funciones_por_archivo"])
        total_funcs = sum(len(funcs) for funcs in info["funciones_por_archivo"].values())
        print(f"\nZIP: {ruta}")
        print(f"  Archivos .py analizados: {total_py}")
        print(f"  Total de funciones encontradas: {total_funcs}")
        if info["comunes"]:
            print("  Funciones comunes internas:")
            for fn, archivos in info["comunes"].items():
                print(f"    - {fn}: {archivos}")
        else:
            print("  No hay funciones duplicadas internas.")
    zips = list(datos.keys())
    conjuntos = [datos[z]["todas"] for z in zips]
    global_comunes = set.intersection(*conjuntos) if conjuntos else set()
    print("\nFunciones comunes en TODOS los ZIPs:")
    if global_comunes:
        for fn in sorted(global_comunes):
            print(f"  - {fn}")
    else:
        print("  Ninguna.")
    print("\nFunciones comunes por pares de ZIPs:")
    n = len(zips)
    for i in range(n):
        for j in range(i+1, n):
            a, b = zips[i], zips[j]
            comun = datos[a]["todas"].intersection(datos[b]["todas"])
            etiqueta = f"{os.path.basename(a)} ↔ {os.path.basename(b)}"
            if comun:
                print(f"  {etiqueta}: {sorted(comun)}")
            else:
                print(f"  {etiqueta}: Ninguna")
if __name__ == "__main__":
    reporte()
