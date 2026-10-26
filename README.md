# Caudo – Tu aliado financiero

Plataforma web de finanzas personales (Angular · NestJS · PostgreSQL · n8n · Docker).

## Estructura
- `backend/` API REST en NestJS (JWT, TypeORM, Swagger en `/api/docs`).
- `frontend/` aplicación Angular 21 con SSR.
- `docker-compose.yml` PostgreSQL + API + web + n8n.

## Módulos
| Módulo | Qué hace | Endpoints principales |
|---|---|---|
| Autenticación y perfil | Registro con consentimiento, JWT, perfil, cambio de contraseña | `/auth/*`, `/users/*` |
| Transacciones | Ingresos y gastos, categorización automática, comprobantes validados | `/transactions`, `/categories/suggest`, `/files/upload` |
| Presupuestos y alertas | Tope mensual por categoría; alertas al 80 % y 100 % | `/budgets`, `/budgets/alerts` |
| Metas de ahorro | Aportes, avance y proyección de cumplimiento | `/goals` |
| Créditos | Obligaciones, % del ingreso comprometido, evaluación de un crédito nuevo, simulador de abono a capital y de compra de cartera | `/credits/*` |
| Análisis | Patrones de gasto, gastos hormiga, recomendaciones por reglas | `/insights/*` |
| Resumen | Balance mensual consolidado | `/dashboard` |

Las recomendaciones se calculan con reglas en el backend. Opcionalmente, un flujo de n8n puede reescribir su redacción:
importa `n8n/workflows/recomendaciones.json` en n8n, actívalo y define `N8N_RECOMMENDATIONS_WEBHOOK=http://n8n:5678/webhook/caudo-recomendaciones`.
Solo se envían los textos ya calculados, nunca transacciones ni datos del usuario.
### Integración opcional con n8n (solo Docker)
n8n es opcional: sin él, las recomendaciones se entregan con el texto calculado por las reglas.
1. Con el sistema levantado, abra http://localhost:5678 y cree la cuenta local de n8n.
2. Importe el flujo: menú `...` del editor → Importar desde archivo → `n8n/workflows/recomendaciones.json`.
3. Publique el flujo (botón Publicar).
4. En el `.env` agregue `N8N_RECOMMENDATIONS_WEBHOOK=http://n8n:5678/webhook/caudo-recomendaciones` y guárdelo.
5. Reinicie el backend: `docker compose up -d --force-recreate backend`.
6. Compruebe en el panel de administración (Estado del sistema) que n8n aparezca como disponible.

En el despliegue en la nube (Render) n8n no está desplegado; allí las recomendaciones usan las reglas y, si hay clave, Gemini.

## Roles y panel de administración

Hay dos roles, según el documento de actores: **Usuario final** y **Administrador**.

- El registro público siempre crea un *usuario*. Los administradores solo se crean con las variables `ADMIN_EMAIL` / `ADMIN_PASSWORD` (al arrancar) o desde el panel por otro administrador.
- Si el correo de `ADMIN_EMAIL` ya existe, no se cambia su contraseña: solo se asegura el rol `admin` y que esté activa.
- El rol y el estado se leen de la base en cada petición: suspender una cuenta cierra su acceso de inmediato.
- El administrador entra a `/admin` y puede: gestionar cuentas (crear, editar, suspender, reactivar), administrar las categorías globales, ver métricas agregadas de uso, y monitorear auditoría, errores 5xx de la API y estado de n8n/webhooks. No ve las transacciones ni la información financiera de las personas (Ley 1581 de 2012).
- Reglas de seguridad: un admin no puede suspenderse ni cambiarse el rol a sí mismo; "Otros Gastos" y "Otros Ingresos" no se renombran ni eliminan; una categoría en uso no se elimina.
- API: todo bajo `/api/admin/*` (ver Swagger en `/api/docs`, etiqueta `admin`), con 403 para quien no sea admin.

## Recomendaciones del módulo de crédito (reglas)

- **Abono a capital:** se calcula en las dos modalidades (reducir plazo / reducir cuota) y se recomienda la que más intereses ahorra, explicando la contrapartida.
- **Qué deuda abonar primero:** con 2+ créditos activos se aplica la estrategia de avalancha (mayor tasa E.A. primero; si empatan, menor saldo), con aviso de conservar un fondo de emergencia.
- **Compra de cartera:** además del veredicto, un mensaje explica si baja la cuota pero se paga más en total.
- Limitaciones: el veredicto de endeudamiento usa solo el % del ingreso comprometido (umbrales de referencia 30 % / 40 %, configurables en `credit-math.ts`, sin fuente normativa), y las tarjetas se modelan como cuota fija.

## IA generativa (Gemini, opcional)

Las cifras, alertas y simulaciones salen siempre de reglas en el backend. La IA es un complemento:

- **Redacción de recomendaciones:** con `GEMINI_API_KEY`, el backend le pide a Gemini que reescriba el texto de cada recomendación ya calculada. Solo se envía título y mensaje (sin identificadores ni transacciones). Si el texto devuelto cambia, omite o inventa una cifra, o es demasiado largo, se descarta y se usa el texto de las reglas.
- **Clasificación de transacciones (opt-in):** con `AI_CATEGORIZATION=true`, cuando las palabras clave no reconocen la descripción se le pregunta a Gemini; la respuesta se valida contra la lista de categorías. Esto envía la descripción de la transacción a Google, así que debe estar cubierto por el consentimiento y la política de datos. Por defecto está apagado.
- **Plan B:** sin clave, ante un error, un límite de uso o un tiempo agotado, el sistema responde con las reglas (la IA se pausa 60 s tras un fallo).
- La capa gratuita de Google puede usar el contenido enviado para mejorar sus productos; revisa las condiciones vigentes en https://ai.google.dev/gemini-api/docs/pricing antes de usar datos reales.
- El panel de administración muestra si la IA está activa y registra cada llamada (éxito, duración, error).

## Ejecución con Docker
```bash
cp .env.example .env      # edita DB_PASSWORD, JWT_SECRET y N8N_PASSWORD
docker compose up --build
```
| Servicio | URL |
|---|---|
| Web | http://localhost:4200 |
| API / Swagger | http://localhost:3000/api/docs |
| n8n | http://localhost:5678 |

Las migraciones se aplican solas al arrancar la API (`NODE_ENV=production`).

## Desarrollo local
```bash
# Backend (requiere PostgreSQL; copia backend/.env.example a backend/.env)
cd backend && npm install && npm run start:dev
# Frontend
cd frontend && npm install && npm start     # http://localhost:4200
```
En desarrollo el esquema se sincroniza automáticamente (`synchronize`).

## Migraciones
```bash
cd backend
npm run migration:generate -- src/database/migrations/NombreCambio
npm run migration:run
npm run migration:revert
```
Si ya tienes una base creada con `synchronize` (por ejemplo la de Supabase), registra la migración inicial como aplicada en lugar de ejecutarla:
`INSERT INTO migrations(timestamp, name) VALUES (1791843527342, 'InitialSchema1791843527342');` (la migración `FinanceModules` sí debe ejecutarse: solo crea las tablas nuevas) y aplica antes a mano las columnas nuevas de `users` (`ingreso_mensual`, `acepta_politica`, `fecha_consentimiento`) y `transactions` (`origen_categoria`).
## Despliegue en la nube (Render + Supabase)

El sistema también se despliega sin Docker: la base de datos en Supabase (PostgreSQL gestionado) y la API y el frontend como dos *Web Services* de Render.

**1. Base de datos (Supabase).** Crear un proyecto y copiar los datos de conexión del *Session pooler* (host, usuario y puerto 5432). No hay que crear las tablas: el backend aplica las migraciones al arrancar.

**2. Backend (Render).** Web Service con `Root Directory: backend`, build `npm install --include=dev && npm run build` y start `npm run start:prod`. Variables de entorno:

| Variable | Valor |
|---|---|
| `NODE_VERSION`, `NODE_ENV` | `22.12.0`, `production` |
| `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_NAME`, `DB_SSL` | datos del pooler de Supabase, `5432`, usuario `postgres.<id-del-proyecto>`, `postgres`, `true` |
| `DB_PASSWORD` | contraseña del proyecto de Supabase |
| `JWT_SECRET` | cadena larga y aleatoria |
| `APP_URL`, `CORS_ORIGINS` | URL del backend y URL del frontend |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | cuenta inicial del administrador |
| `GEMINI_API_KEY`, `AI_CATEGORIZATION` | opcional (IA); `false` por defecto |

**3. Frontend (Render).** Web Service con `Root Directory: frontend`, build `npm install --include=dev && npm run build` y start `npm run serve:ssr:CaudoFront`. La dirección del backend se define en `frontend/src/environments/environment.prod.ts` (`apiUrl`).

**4. Verificación.** Swagger en `<url-backend>/api/docs`; las 10 tablas deben aparecer en el *Table Editor* de Supabase. En el plan gratuito, los servicios se duermen tras un tiempo sin uso y tardan cerca de un minuto en responder.

Nota de seguridad: las tablas deben tener RLS activado (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`); el backend se conecta con el rol `postgres`, que no se ve afectado.


## Pruebas
```bash
cd backend && npm test && npm run test:e2e
```
