# API ETL Tool

[English (README.md)](README.md)

Extrae datos de APIs REST paginadas a CSV/XLSX con autenticación, filtrado de campos y rate limiting automático.

**Características principales:**

- Maneja endpoints paginados con parámetro configurable
- Autenticación con Bearer token via variables de entorno
- Filtrado de campos para reducir tamaño de salida
- Reintentos automáticos en rate limit (HTTP 429)
- Soporte para parámetros de consulta adicionales

## Instalación

```bash
python -m venv .venv && source .venv/bin/activate
# En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Demo rápida con API pública

```bash
# No requiere autenticación
python api_etl.py \
  --url "https://jsonplaceholder.typicode.com/posts" \
  --output posts.csv \
  --fields "userId,id,title" \
  --max-pages 2
```

**Resultado esperado:**

- `posts.csv` con 20 filas (10 por página) y 3 columnas
- Logs en terminal mostrando progreso de paginación con timestamps

**Ejecutar todas las demos:**

```bash
cd examples
bash demo_public_api.sh
```

## Uso con autenticación

Para APIs que requieren autenticación:

```bash
# 1. Copiar plantilla de variables de entorno
cp .env.example .env

# 2. Editar .env y agregar tu token
# API_TOKEN=tu_token_real_aqui

# 3. Ejecutar extracción
python api_etl.py \
  --url "https://api.ejemplo.com/data" \
  --output output/datos.xlsx \
  --max-pages 5 \
  --token-env API_TOKEN
```

## Parámetros

```bash
python api_etl.py --help
```

**Requeridos:**

- `--url`: URL del endpoint de la API
- `--output`: Archivo de salida (`.csv` o `.xlsx`)

**Opcionales:**

- `--fields`: Campos a extraer separados por coma (default: todos)
- `--max-pages`: Cantidad de páginas a traer (default: 1)
- `--page-param`: Nombre del parámetro de paginación (default: `page`)
- `--params`: Parámetros de consulta adicionales en formato JSON
- `--token-env`: Nombre de variable de entorno con el token (default: `API_TOKEN`)
- `--auth-header`: Nombre del header de autorización (default: `Authorization`)
- `--sleep`: Segundos entre requests (default: 0.5)

## Ejemplos comunes

### API de GitHub (repos públicos)

```bash
python api_etl.py \
  --url "https://api.github.com/users/torvalds/repos" \
  --output torvalds_repos.csv \
  --fields "name,stargazers_count,language,updated_at" \
  --max-pages 1
```

### API con paginación personalizada

```bash
python api_etl.py \
  --url "https://api.ejemplo.com/registros" \
  --output registros.xlsx \
  --page-param "offset" \
  --params '{"limit":50,"status":"activo"}' \
  --max-pages 10
```

### Con autenticación y rate limiting

```bash
# Configurar API_TOKEN en archivo .env primero
python api_etl.py \
  --url "https://api.privada.com/datos" \
  --output datos.csv \
  --max-pages 20 \
  --sleep 1.0 \
  --token-env API_TOKEN
```

## Capturas de pantalla

### Salida en terminal durante extracción

![Salida de Terminal](images/terminal_output.png)

### Vista previa del resultado (CSV abierto en hoja de cálculo)

![Vista Previa](images/result_preview.png)

## Cómo funciona

1. **Autenticación**: Carga token desde archivo `.env` usando `python-dotenv`
2. **Paginación**: Incrementa automáticamente el parámetro de página en cada request
3. **Rate limiting**: Espera entre requests; reintenta en HTTP 429
4. **Filtrado de campos**: Extrae solo los campos especificados de respuestas JSON
5. **Exportación**: Convierte a DataFrame de pandas y guarda como CSV/XLSX

## Formatos de respuesta soportados

La herramienta maneja dos estructuras comunes de respuesta de API:

**Respuesta tipo array:**

```json
[
	{"id": 1, "name": "Item 1"},
	{"id": 2, "name": "Item 2"}
]
```

**Objeto con clave items:**

```json
{
	"items": [{"id": 1, "name": "Item 1"}],
	"total": 100
}
```

## Stack tecnológico

- **Python 3.9+**
- **pandas** - Manipulación de datos y exportación
- **requests** - Cliente HTTP con lógica de reintentos
- **python-dotenv** - Gestión de variables de entorno
- **openpyxl** - Escritura de archivos Excel

## Próximos pasos

Después de la extracción, podés:

- Cargar a base de datos (PostgreSQL, MySQL)
- Programar con cron para actualizaciones diarias
- Agregar validaciones y checks de calidad de datos
- Integrar con pipelines de datos (Airflow, Prefect)
