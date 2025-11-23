#!/bin/bash
# Script de utilidad para ejecutar pruebas del NLPService
# Uso: ./run_nlp_tests.sh [opción]

set -e

PROJECT_ROOT=$(cd "$(dirname "$0")" && pwd)
VENV="${PROJECT_ROOT}/.venv"
PYTHON="${VENV}/bin/python"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones auxiliares
print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ $1${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Verificar virtualenv
check_venv() {
    if [ ! -f "$PYTHON" ]; then
        print_error "Virtual environment no encontrado en $VENV"
        echo "Ejecuta primero: python -m venv .venv"
        exit 1
    fi
    print_success "Virtual environment encontrado"
}

# Ejecutar pytest tests
run_unit_tests() {
    print_header "EJECUTANDO UNIT TESTS"
    cd "$PROJECT_ROOT"
    "$PYTHON" -m pytest tests/test_nlp_service.py -v --tb=short
    print_success "Unit tests completados"
}

# Ejecutar pruebas interactivas
run_interactive_tests() {
    print_header "EJECUTANDO PRUEBAS INTERACTIVAS"
    cd "$PROJECT_ROOT"
    "$PYTHON" test_nlp_service_interactive.py
    print_success "Pruebas interactivas completadas"
}

# Ejecutar benchmarking
run_benchmark() {
    print_header "EJECUTANDO BENCHMARKING"
    cd "$PROJECT_ROOT"
    "$PYTHON" test_nlp_service_benchmark.py
    print_success "Benchmarking completado"
}

# Ejecutar análisis estático
run_linting() {
    print_header "EJECUTANDO ANÁLISIS ESTÁTICO"
    cd "$PROJECT_ROOT"
    
    if command -v flake8 &> /dev/null; then
        print_info "Ejecutando flake8..."
        "$PYTHON" -m flake8 app/services/nlp_service.py --max-line-length=100 --ignore=E501,W503 || true
    else
        print_info "flake8 no instalado, saltando..."
    fi
    
    if command -v black &> /dev/null; then
        print_info "Verificando formato con black..."
        "$PYTHON" -m black app/services/nlp_service.py --check --line-length=100 || true
    else
        print_info "black no instalado, saltando..."
    fi
    
    print_success "Análisis estático completado"
}

# Ejecutar todo
run_all() {
    print_header "EJECUTANDO SUITE COMPLETA DE PRUEBAS"
    
    run_unit_tests
    echo ""
    
    run_interactive_tests
    echo ""
    
    run_benchmark
    echo ""
    
    run_linting
    echo ""
    
    print_header "✨ TODAS LAS PRUEBAS COMPLETADAS ✨"
}

# Mostrar reporte
show_reports() {
    print_header "REPORTES DISPONIBLES"
    
    INTERACTIVE_REPORT="${PROJECT_ROOT}/nlp_service_test_report.json"
    BENCHMARK_REPORT="${PROJECT_ROOT}/nlp_service_benchmark_report.json"
    
    if [ -f "$INTERACTIVE_REPORT" ]; then
        print_success "Reporte de pruebas interactivas:"
        echo "  $INTERACTIVE_REPORT"
        print_info "Contenido:"
        "$PYTHON" -m json.tool "$INTERACTIVE_REPORT" | head -50
        echo "  ..."
    fi
    
    if [ -f "$BENCHMARK_REPORT" ]; then
        print_success "Reporte de benchmarking:"
        echo "  $BENCHMARK_REPORT"
        print_info "Contenido (resumen):"
        "$PYTHON" -m json.tool "$BENCHMARK_REPORT" | head -50
        echo "  ..."
    fi
}

# Mostrar ayuda
show_help() {
    echo ""
    print_header "NLP SERVICE TEST RUNNER"
    echo ""
    echo "Uso: $0 [opción]"
    echo ""
    echo "Opciones:"
    echo "  unit           Ejecutar unit tests (pytest)"
    echo "  interactive    Ejecutar pruebas interactivas"
    echo "  benchmark      Ejecutar benchmarking"
    echo "  lint           Ejecutar análisis estático"
    echo "  reports        Mostrar reportes generados"
    echo "  all            Ejecutar suite completa (por defecto)"
    echo "  help           Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 unit"
    echo "  $0 benchmark"
    echo "  $0 all"
    echo ""
}

# Main
check_venv

case "${1:-all}" in
    unit)
        run_unit_tests
        ;;
    interactive)
        run_interactive_tests
        ;;
    benchmark)
        run_benchmark
        ;;
    lint)
        run_linting
        ;;
    reports)
        show_reports
        ;;
    all)
        run_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Opción desconocida: $1"
        show_help
        exit 1
        ;;
esac

echo ""
