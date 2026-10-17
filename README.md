# ANDIS TFU UT4 - API y consola de demostración

Aplicación de juegos que evoluciona las TFU anteriores. FastAPI, SQLAlchemy, MySQL,
Redis, Keycloak, React y Docker Compose. No requiere Kubernetes.

## Inicio

Con Docker Desktop iniciado, desde la raíz:

```powershell
docker compose up -d --build
```

Compose inicia el frontend, gateway, dos réplicas Blue, dos Green, MySQL, Redis y
Keycloak. Si no existe `.env`, copiar `.env.example` antes de iniciar.

| Servicio | Puerto predeterminado | Configuración |
|---|---|---|
| Frontend | http://localhost:3200 | `FRONTEND_PORT` |
| API / gateway | http://localhost:8000 | `API_PORT` |
| Swagger | http://localhost:8000/docs | `API_PORT` |
| Keycloak | http://localhost:8081 | `KEYCLOAK_PORT` |

El `.env` local puede usar otros puertos (por ejemplo API 18000 y Keycloak 18081).
Si se cambia el puerto de Keycloak, ajustar también `OIDC_ISSUER`, `KEYCLOAK_URL`
y `BASE_URL` cuando corresponda. Las APIs no publican puertos hacia el host.

| Cuenta de demostración | Contraseña | Rol |
|---|---|---|
| demo@adaii.local | Demo123! | user |
| segundo@adaii.local | Demo123! | user |
| admin@adaii.local | AdminDemo123! | admin |

El frontend usa Authorization Code + PKCE. La API valida tokens de Keycloak;
`POST /auth/login` permanece retirado (410).

Para una instalación previa de Keycloak, el archivo de importación no actualiza un
realm existente: verificar que el cliente público `andis-frontend` tenga como
redirect URI `http://localhost:3200/*`, origen `http://localhost:3200` y PKCE S256.
Actualizar ese cliente en la consola de administración sin borrar su volumen.

```powershell
docker compose ps
docker compose logs --tail=100
docker compose down
```

`down` conserva los datos. No agregar `-v` si se quieren preservar los volúmenes.

## Demos UT4

| Atributo | Patrón o estrategia | Prueba desde la consola |
|---|---|---|
| Disponibilidad | Health Endpoint Monitoring | Estado de réplicas del color que responde y readiness de dependencias. |
| Disponibilidad | Throttling | Ráfaga con 429 frente a tráfico a ritmo controlado. |
| Rendimiento | Cache-Aside | HIT/MISS, latencias e invalidación después del commit. |
| Rendimiento | CQRS | Comandos de compras y proyecciones de lectura y agregación. |
| Seguridad | Federated Identity | OIDC/PKCE, firma del token, identidad y roles; casos 200/401/403/410. |
| Seguridad / rendimiento | Gateway Offloading | gzip, estáticos y políticas centralizadas en Nginx. |
| Facilidad de modificación | External Configuration Store | Editar JSON externo compartido y observar el cambio sin rebuild ni reinicio. |
| Facilidad de despliegue | Blue/Green | Verificar y promover el otro color manteniendo estable el frontend. |

CQRS separa modelos dentro del mismo backend y MySQL: no implica que existan
despliegues de lectura y escritura independientes. Las mediciones del navegador
son demostraciones funcionales, no un benchmark exhaustivo.

## Demos antiguas

El menú del frontend contiene una sección desplegable **Demos antiguas**:

| Unidad | Demos |
|---|---|
| UT2 · Tácticas | Strategy y auditoría; rollback de imagen defectuosa. |
| UT3 · Soluciones | Componentes e interfaces / contenedores; escalabilidad horizontal; servicios sin estado; transacciones ACID. |

La clasificación sigue las propuestas de UT2 (tácticas) y UT3 (componentes,
escalabilidad, contenedores, ACID y stateless). El código heredado se adapta a la
identidad federada de UT4; no se reactiva el login local.

- Strategy y auditoría: compara políticas y genera/consulta una operación auditada.
- Escalabilidad y stateless: diez solicitudes reales entre réplicas del color activo.
- ACID: crea datos temporales, verifica commit y rollback desde otra sesión MySQL y
  limpia los datos de prueba. Requiere admin desde el navegador.
- Rollback histórico: ejecuta `.\scripts\demo_rollback.ps1` o
  `bash scripts/demo_rollback.sh` en una terminal. Reemplaza Blue con una imagen
  defectuosa y restaura la anterior; puede interrumpir temporalmente la API.
  Ejecutarlo separado de Blue/Green. Registra `deployment_logs/deployment.log`.

Referencias de la evolución:
[UT3](https://github.com/FacundoPiriz17/UT3_TFU_ANDIS2) y
[UT2](https://github.com/ThiagoAGarcia/adaII-UT2).

Los launchers `run.ps1` / `run.sh` también separan las demos actuales de las antiguas.
Los scripts CLI heredados que necesitan sesión aceptan `DEMO_ACCESS_TOKEN` con un
token vigente; las demos del frontend gestionan la sesión mediante Keycloak.

## Desarrollo y validación

```powershell
cd frontend
npm install
$env:GATEWAY_URL="http://localhost:18000"
$env:VITE_KEYCLOAK_URL="http://localhost:18081"
npm run dev
```

Vite queda en http://localhost:5173. Para los puertos predeterminados usar 8000 y
8081. El frontend de Compose permanece en 3200.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
docker compose config --quiet
```

Las pruebas cubren recarga del archivo, validación, concurrencia y protección de
la promoción ante destinos inválidos y errores de configuración Nginx.

Los diagramas UML de componentes originales se conservan en `docs/diagramas/`.
La partición es un backend modular replicado; contenerizar sus dependencias no lo
convierte en microservicios por dominio.
