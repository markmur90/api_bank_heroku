#!/usr/bin/env bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# source "${BASE_DIR}/Opciones.sh"

do_update() {
    bash "${BASE_DIR}/00.sh" "$@"
}

setup_postgres() {
    bash "${BASE_DIR}/01Postgres.sh" "$@"
}

dump_database() {
    bash "${BASE_DIR}/02Bdd_dump.sh" "$@"
}

copy_and_backup() {
    bash "${BASE_DIR}/03copy_and_backup.sh" "$@"
}

sync_to_remote() {
    bash "${BASE_DIR}/06sync_to_remote.sh" "$@"
}

honeypot_server() {
    python3 "${BASE_DIR}/honeypot_server.py" "$@"
}

gunicon_honeypot() {
    bash "${BASE_DIR}/07script_completo.sh" "$@"
}

run_all() {
    do_update "$@"
    setup_postgres "$@"
    dump_database "$@"
    copy_and_backup "$@"
    sync_to_remote "$@"
    gunicon_honeypot "$@"
    honeypot_server "$@"
}

if [[ -n "$1" ]]; then
    case "$1" in
        honeypot)     shift; honeypot_server "$@" ;;
        update)       shift; do_update "$@" ;;
        postgres)     shift; setup_postgres "$@" ;;
        dump)         shift; dump_database "$@" ;;
        backup)       shift; copy_and_backup "$@" ;;
        sync)         shift; sync_to_remote "$@" ;;
        mozilla)      shift; gunicon_honeypot "$@" ;;
        all)          shift; run_all "$@" ;;
        *) echo "Uso: $0 {honeypot|update|postgres|dump|backup|mozilla|sync|all} [args]"; exit 1 ;;
    esac
else
    if type mostrar_menu &>/dev/null; then
        mostrar_menu
    else
        echo "Parámetros disponibles:"
        echo "  update     Ejecuta 00Update.sh"
        echo "  postgres   Ejecuta 01Postgres.sh"
        echo "  dump       Ejecuta 02Bdd_dump.sh"
        echo "  backup     Ejecuta 03copy_and_backup.sh"
        echo "  sync       Ejecuta 06sync_to_remote.sh"
        echo "  honeypot   Ejecuta honeypot_server.py"
        echo "  mozilla    Ejecuta 07script_completo.sh"
        echo "  all        Ejecuta todo en secuencia"
        echo ""
        echo "Ejemplo:"
        echo "  $0 all"
    fi
fi
