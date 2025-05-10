#!/usr/bin/env bash

# Array de atributos y su descripción
declare -A ATRIBUTOS=(
  [0]="reset"
  [1]="bold"
  [2]="dim"
  [4]="underline"
  [5]="blink"
  [7]="reverse"
  [8]="hidden"
)

# Colores de primer plano
declare -A COLORES_FG=(
  [30]="Negro"
  [31]="Rojo"
  [32]="Verde"
  [33]="Amarillo"
  [34]="Azul"
  [35]="Magenta"
  [36]="Cyan"
  [37]="Blanco"
  [90]="GrisOscuro"
  [91]="RojoClaro"
  [92]="VerdeClaro"
  [93]="AmarilloClaro"
  [94]="AzulClaro"
  [95]="MagentaClaro"
  [96]="CyanClaro"
  [97]="BlancoIntenso"
)

for attr in "${!ATRIBUTOS[@]}"; do
  for fg in "${!COLORES_FG[@]}"; do
    nombre_atributo=${ATRIBUTOS[$attr]}
    nombre_color=${COLORES_FG[$fg]}
    echo -e "\033[${attr};${fg}m[${nombre_atributo};${nombre_color}] Ejemplo de texto en ${nombre_color}\033[0m"
  done
done
