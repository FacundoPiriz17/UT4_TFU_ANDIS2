// Catálogo de patrones de la UT4 implementados en el proyecto.
export const GRUPOS = {
  disponibilidad: { nombre: 'Disponibilidad', color: 'green' },
  rendimiento: { nombre: 'Rendimiento', color: 'blue' },
  seguridad: { nombre: 'Seguridad', color: 'violet' },
  despliegue: { nombre: 'Modificabilidad y despliegue', color: 'amber' },
};

export const PATRONES = [
  {
    id: 'health',
    nombre: 'Health Endpoint Monitoring',
    grupo: 'disponibilidad',
    resumen: 'Endpoints /health, /health/live y /health/ready exponen el estado de cada réplica y sus dependencias.',
    archivos: ['app/main.py', 'docker-compose.yaml (healthcheck)'],
  },
  {
    id: 'throttling',
    nombre: 'Throttling',
    grupo: 'disponibilidad',
    resumen: 'El gateway limita a 10 req/s por IP (burst 20) y rechaza el exceso con 429 para proteger a las APIs.',
    archivos: ['nginx/default.conf'],
  },
  {
    id: 'cache',
    nombre: 'Cache-Aside',
    grupo: 'rendimiento',
    resumen: 'Las lecturas consultan Redis primero; ante un MISS cargan de MySQL y guardan con TTL. Las escrituras invalidan.',
    archivos: ['app/cache.py', 'app/routers/juegos.py', 'app/routers/biblioteca.py'],
  },
  {
    id: 'cqrs',
    nombre: 'CQRS',
    grupo: 'rendimiento',
    resumen: 'Compras separa comandos (transacción + Strategy + invalidación) de consultas (proyecciones SQL a DTO).',
    archivos: ['app/services/compras_commands.py', 'app/services/compras_queries.py'],
  },
  {
    id: 'identity',
    nombre: 'Federated Identity',
    grupo: 'seguridad',
    resumen: 'Keycloak autentica (OIDC + PKCE). La API solo valida tokens RS256 vía JWKS y autoriza por roles.',
    archivos: ['security/oidc.py', 'security/dependencies.py', 'security/keycloak/realm-ut4.json'],
  },
  {
    id: 'offloading',
    nombre: 'Gateway Offloading',
    grupo: 'seguridad',
    resumen: 'Nginx asume compresión, estáticos, límite de tasa y balanceo, quitando esas tareas transversales a FastAPI.',
    archivos: ['nginx/default.conf', 'nginx/static/'],
  },
  {
    id: 'deploy',
    nombre: 'Despliegue con rollback',
    grupo: 'despliegue',
    resumen: 'Imágenes versionadas; si la nueva versión no pasa el health check, se vuelve automáticamente a la anterior.',
    archivos: ['scripts/manage.py (deploy / rollback_demo)', 'dockerfile (FORCE_UNHEALTHY)'],
  },
];

export const patron = (id) => PATRONES.find((p) => p.id === id);
