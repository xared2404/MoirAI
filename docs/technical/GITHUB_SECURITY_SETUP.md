# 🔐 Configuración de Seguridad para GitHub

## 📋 ACCIONES INMEDIATAS DESPUÉS DE SUBIR AL REPOSITORIO

### 1. Configurar GitHub Secrets
Vaya a `Settings > Secrets and variables > Actions` y configure:

```
# Secretos para CI/CD
SECRET_KEY=<generar_clave_secura_32_caracteres>
DATABASE_URL=<url_base_datos_produccion>
JSEARCH_API_KEY=<clave_api_jsearch>

# Para Docker Compose en CI/CD
POSTGRES_DB=moirai_db
POSTGRES_USER=moirai_user
POSTGRES_PASSWORD=<password_seguro>
PGADMIN_EMAIL=admin@unrc.edu.mx
PGADMIN_PASSWORD=<password_admin_seguro>
```

### 2. Habilitar Dependabot
Crear archivo `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    reviewers:
      - "usuario-responsable"
    assignees:
      - "usuario-responsable"
```

### 3. Configurar Security Advisories
- Ir a `Settings > Security & analysis`
- Habilitar:
  - [x] Dependency graph
  - [x] Dependabot alerts
  - [x] Dependabot security updates
  - [x] Code scanning alerts

### 4. Branch Protection Rules
En `Settings > Branches > Add rule`:

```
Branch name pattern: main
☑️ Require a pull request before merging
  ☑️ Require approvals (1)
  ☑️ Dismiss stale PR approvals when new commits are pushed
☑️ Require status checks to pass before merging
  ☑️ Require branches to be up to date before merging
☑️ Require conversation resolution before merging
☑️ Do not allow bypassing the above settings
```

### 5. Configurar Code Scanning
Crear archivo `.github/workflows/codeql.yml`:

```yaml
name: "CodeQL"

on:
  push:
    branches: [ "main", "develop" ]
  pull_request:
    branches: [ "main" ]
  schedule:
    - cron: '22 5 * * 1'

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'python' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: ${{ matrix.language }}

    - name: Autobuild
      uses: github/codeql-action/autobuild@v2

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
      with:
        category: "/language:${{matrix.language}}"
```

## 🛡️ CONFIGURACIONES ADICIONALES DE SEGURIDAD

### 6. Análisis de Vulnerabilidades en CI
Crear archivo `.github/workflows/security.yml`:

```yaml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install bandit safety
        pip install -r requirements.txt
    
    - name: Run Bandit Security Lint
      run: bandit -r app/ -f json -o bandit-report.json || true
    
    - name: Run Safety Check
      run: safety check --json --output safety-report.json || true
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json
```

### 7. Configurar Issue Templates
Crear `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: 'bug'
assignees: ''
---

## Security Notice
⚠️ **Do NOT include sensitive information** (passwords, API keys, personal data) in this issue.

## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear description of what you expected to happen.

## Environment
- OS: [e.g. macOS, Windows, Linux]
- Python version: [e.g. 3.11]
- FastAPI version: [e.g. 0.104.1]
```

### 8. Configurar Pull Request Template
Crear `.github/pull_request_template.md`:

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Security Checklist
- [ ] No sensitive information (passwords, keys, personal data) included
- [ ] Dependencies updated and vulnerability-free
- [ ] Code follows security best practices
- [ ] No hardcoded secrets or credentials

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated

## Screenshots/Logs (if applicable)
Attach screenshots or relevant logs here
```

## 🚨 MONITOREO CONTINUO

### 9. Configurar Notificaciones
- Settings > Notifications
- Configurar alertas para:
  - Security advisories
  - Dependabot alerts
  - Failed workflows

### 10. Revisiones Periódicas
- **Semanal**: Revisar alertas de Dependabot
- **Mensual**: Revisar logs de auditoría
- **Trimestral**: Análisis completo de seguridad
- **Anual**: Rotación de secrets y keys

## ✅ CHECKLIST POST-DEPLOY

- [ ] Secrets configurados en GitHub
- [ ] Dependabot habilitado
- [ ] Branch protection activo
- [ ] Code scanning configurado
- [ ] Workflows de seguridad funcionando
- [ ] Issue/PR templates creados
- [ ] Notificaciones configuradas
- [ ] Documentación actualizada
- [ ] Equipo notificado sobre prácticas de seguridad

---

**📝 Nota**: Este proyecto ahora cumple con las mejores prácticas de seguridad para repositorios de código abierto. Mantenga estas configuraciones actualizadas y revise regularmente las alertas de seguridad.
