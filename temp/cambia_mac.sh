#!/usr/bin/env bash
INTERFAZ="$1"
if [[ $EUID -ne 0 ]]; then
    echo "Debes ejecutar este script como root."
    exit 1
fi
if [[ -z "$INTERFAZ" ]]; then
    echo "Uso: $0 <interfaz>"
    exit 1
fi
ip link set "$INTERFAZ" down
MAC_ANTERIOR=$(macchanger -s "$INTERFAZ" | awk '/Current MAC:/ {print $3}')
MAC_NUEVA=$(macchanger -r "$INTERFAZ" | awk '/New MAC:/ {print $3}')
ip link set "$INTERFAZ" up
echo "MAC anterior: $MAC_ANTERIOR"
echo "MAC nueva:    $MAC_NUEVA"
