# 🗄️ CONFIGURACIÓN DE BASE DE DATOS

## Problema Detectado

```
FATAL: database "moirai" does not exist
```

La base de datos PostgreSQL aún no está creada. Necesitamos configurarla antes de continuar.

---

## ✅ Solución: Crear Base de Datos

### Paso 1: Conectarse a PostgreSQL
```bash
psql -U postgres
```

Si pide contraseña, ingresa la que configuraste durante instalación de PostgreSQL.

### Paso 2: Crear la base de datos
```sql
CREATE DATABASE moirai;
```

### Paso 3: Conectarse a la BD nueva
```sql
\c moirai
```

### Paso 4: Crear tablas (ejecutar migraciones)
```bash
# Salir de psql primero
\q

# Luego ejecutar las migraciones de Alembic
cd /Users/sparkmachine/MoirAI
alembic upgrade head
```

Si `alembic` no está disponible, instalar:
```bash
pip install alembic
```

### Paso 5: Verificar que se crearon las tablas
```bash
psql moirai -U postgres -c "\dt"
```

Debe mostrar las tablas, incluyendo `job_positions`.

---

## 🚀 Alternativa: Usar Script de Setup

Si existe un script de setup en el proyecto:
```bash
cd /Users/sparkmachine/MoirAI
python manage_admin.py  # O el script equivalente
```

O ejecutar main.py que puede tener setup incluido:
```bash
python main.py --init-db
```

---

## ✅ Verificar que la BD está lista

```bash
# Conectarse a la BD
psql moirai -U postgres

# Ver las tablas
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

# Salir
\q
```

Debe mostrar al menos:
```
 table_name
-------------------
 job_positions
 users
 students
 companies
 ... (otras tablas)
```

---

## 📋 Pasos Completos de Setup

### 1. Instalar PostgreSQL (si no está)
```bash
# macOS
brew install postgresql

# Iniciar servicio
brew services start postgresql
```

### 2. Crear usuario (si no existe)
```bash
createuser -P postgres  # Crear con contraseña
```

### 3. Crear BD
```bash
createdb -U postgres moirai
```

### 4. Ejecutar migraciones
```bash
cd /Users/sparkmachine/MoirAI

# Instalar dependencias si es necesario
pip install -r requirements.txt

# Ejecutar migraciones de Alembic
alembic upgrade head
```

### 5. Verificar
```bash
psql moirai -U postgres -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
```

Debe retornar un número > 0.

---

## 🧪 Después de Configurar BD

Una vez que la BD esté creada y con tablas, ejecutar:

```bash
# Verificar que todo funciona
./verify-cache-storage.sh
```

Ahora debe mostrar:
```
✅ Empleos activos y vigentes: 0
✅ No hay duplicados
... (todos los tests pasando)
```

---

## 🆘 Si Sigue Sin Funcionar

### Verificar variables de entorno
```bash
# Mostrar configuración actual
echo $DATABASE_URL
echo $DB_NAME
echo $DB_USER
```

Deben estar configuradas. Si no, editar `.env`:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/moirai
DB_NAME=moirai
DB_USER=postgres
```

### Verificar puerto de PostgreSQL
```bash
# PostgreSQL corre en puerto 5432 por defecto
psql -U postgres -c "SELECT version();"
```

Si dice "psql: error: connection to server ... failed", PostgreSQL no está corriendo:
```bash
# Iniciar PostgreSQL
brew services start postgresql

# O verificar si ya está corriendo
brew services list | grep postgresql
```

### Verificar credenciales
```bash
# Probar conexión con contraseña
psql -U postgres -W -c "SELECT 1;"

# Probar sin contraseña (si se configuró así)
psql -U postgres -c "SELECT 1;"
```

---

## ✅ Checklist Final

- [ ] PostgreSQL está instalado
- [ ] PostgreSQL está corriendo (en puerto 5432)
- [ ] Base de datos "moirai" existe
- [ ] Tablas se crearon (via alembic o manual)
- [ ] Puedo conectarme: `psql moirai -U postgres`
- [ ] Script `verify-cache-storage.sh` pasa todos los tests
- [ ] Backend puede iniciar: `python main.py`

---

## 📞 Comandos de Referencia Rápida

```bash
# Crear BD (una sola vez)
createdb -U postgres moirai

# Conectarse
psql -U postgres moirai

# Ver tablas
psql moirai -U postgres -c "\dt"

# Ver cantidad de registros en job_positions
psql moirai -U postgres -c "SELECT COUNT(*) FROM job_positions;"

# Ejecutar migraciones
alembic upgrade head

# Resetear BD (CUIDADO: borra datos)
dropdb -U postgres moirai
createdb -U postgres moirai
alembic upgrade head
```

---

## 🎯 Siguiente Paso

Una vez que la BD esté configurada:

1. **Iniciar backend:**
   ```bash
   cd /Users/sparkmachine/MoirAI
   python main.py
   ```

2. **Hacer búsqueda de prueba:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/job-scraping/search \
     -H 'Content-Type: application/json' \
     -H 'X-API-Key: tu_api_key' \
     -d '{"keyword":"python","detailed":true}'
   ```

3. **Verificar que se guardó:**
   ```bash
   psql moirai -U postgres -c "SELECT COUNT(*) FROM job_positions WHERE source='occ';"
   ```

4. **Ejecutar script de verificación:**
   ```bash
   ./verify-cache-storage.sh
   ```

---

**Status:** ⚠️ **PENDIENTE CONFIGURACIÓN DE BD**

Una vez completados estos pasos, la reparación del cache estará **completamente funcional**.
