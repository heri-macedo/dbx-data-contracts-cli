#!/bin/bash
# ============================================================================
# GitHub Secrets Manager
# Script para atualizar secrets do GitHub via CLI
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SECRETS_FILE=".secrets.env"
DRY_RUN=false
ENVIRONMENT=""

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) não está instalado."
        echo "Instale com: brew install gh"
        exit 1
    fi

    # Check if GH_TOKEN is set (for CI/CD or explicit token usage)
    if [ -n "$GH_TOKEN" ]; then
        print_info "Usando GH_TOKEN do ambiente"
        return 0
    fi

    # Check if authenticated via gh auth login
    if ! gh auth status &> /dev/null; then
        print_error "Você não está autenticado no GitHub CLI."
        echo ""
        echo "Opções de autenticação:"
        echo "  1. Execute: gh auth login"
        echo "  2. Ou exporte: export GH_TOKEN='seu-token-aqui'"
        echo "  3. Ou passe inline: GH_TOKEN='xxx' $0 [args]"
        exit 1
    fi
}

show_usage() {
    echo "Uso: $0 [OPTIONS]"
    echo ""
    echo "Opções:"
    echo "  -f, --file FILE       Arquivo com secrets (default: .secrets.env)"
    echo "  -e, --env ENV         Ambiente (dev|prod|all)"
    echo "  -s, --secret NAME     Atualizar um secret específico"
    echo "  -v, --value VALUE     Valor do secret (usado com -s)"
    echo "  -l, --list            Listar secrets existentes"
    echo "  -d, --dry-run         Simular execução sem fazer alterações"
    echo "  -h, --help            Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 --list                                    # Lista todos os secrets"
    echo "  $0 -f .secrets.env                           # Atualiza secrets do arquivo"
    echo "  $0 -e dev -f .secrets.dev.env                # Atualiza secrets de dev"
    echo "  $0 -s DATABRICKS_HOST_DEV -v 'https://...'   # Atualiza um secret específico"
    echo "  $0 --dry-run -f .secrets.env                 # Simula atualização"
    echo ""
}

list_secrets() {
    print_header "Secrets do Repositório"
    gh secret list
}

update_secret() {
    local name=$1
    local value=$2

    if [ "$DRY_RUN" = true ]; then
        print_info "[DRY-RUN] Atualizaria secret: $name"
    else
        echo -n "$value" | gh secret set "$name"
        print_success "Secret atualizado: $name"
    fi
}

update_secrets_from_file() {
    local file=$1

    if [ ! -f "$file" ]; then
        print_error "Arquivo não encontrado: $file"
        exit 1
    fi

    print_header "Atualizando Secrets de: $file"

    local count=0
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue

        # Skip GH_TOKEN (used for authentication, not a repo secret)
        [[ "$key" == "GH_TOKEN" ]] && continue

        # Remove quotes from value
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"

        # Filter by environment if specified
        if [ -n "$ENVIRONMENT" ] && [ "$ENVIRONMENT" != "all" ]; then
            case "$ENVIRONMENT" in
                dev)
                    [[ ! "$key" =~ _DEV$ ]] && continue
                    ;;
                prod)
                    [[ ! "$key" =~ _PROD$ ]] && continue
                    ;;
            esac
        fi

        update_secret "$key" "$value"
        ((count++))
    done < "$file"

    echo ""
    print_success "Total de secrets atualizados: $count"
}

# ============================================================================
# Main
# ============================================================================

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            SECRETS_FILE="$2"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--secret)
            SECRET_NAME="$2"
            shift 2
            ;;
        -v|--value)
            SECRET_VALUE="$2"
            shift 2
            ;;
        -l|--list)
            LIST_ONLY=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Opção desconhecida: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check prerequisites
check_gh_cli

# Execute based on options
if [ "$LIST_ONLY" = true ]; then
    list_secrets
    exit 0
fi

if [ -n "$SECRET_NAME" ]; then
    if [ -z "$SECRET_VALUE" ]; then
        print_error "Valor do secret não fornecido. Use -v ou --value"
        exit 1
    fi
    update_secret "$SECRET_NAME" "$SECRET_VALUE"
    exit 0
fi

# Default: update from file
update_secrets_from_file "$SECRETS_FILE"
