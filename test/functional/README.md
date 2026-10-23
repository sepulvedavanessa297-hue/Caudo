# Pruebas funcionales de Caudo (TC-01 a TC-40)

Script en Python 3 (solo librería estándar, no instala nada). Ejecuta 40 casos contra la API REST
y guarda el resultado en `results.json`.

## Ejecutar contra Docker local
1. Levante el proyecto: `docker compose up --build`
2. En esta carpeta (PowerShell):

```powershell
$env:API_URL="http://localhost:3000/api"
$env:ADMIN_EMAIL="admin@caudo.dev"
$env:ADMIN_PASSWORD="AdminDemo!2026"
py tc.py
```
(Use el correo y clave del administrador que defina en su `.env`: `ADMIN_EMAIL` / `ADMIN_PASSWORD`.)

Salida esperada: `40 / 40`.

## Variables
| Variable | Defecto | Uso |
|---|---|---|
| API_URL | http://localhost:3000/api | API a probar |
| ADMIN_EMAIL / ADMIN_PASSWORD | admin@caudo.test / Admin123! | cuenta admin (TC-34 a TC-40) |
| RESULTS | results.json | archivo de salida |

## Advertencia
Las pruebas crean usuarios y datos de prueba. Ejecútelas contra Docker local o un entorno de pruebas,
**no** contra la base de datos de demostración en la nube.
