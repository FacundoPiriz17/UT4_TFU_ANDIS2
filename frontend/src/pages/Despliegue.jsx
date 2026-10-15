import { useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';
import { Boton, Card, Comando, ComoFunciona, EncabezadoPatron, Estado } from '../components/ui';

export default function Despliegue() {
  const [instancias, setInstancias] = useState([]);
  const [eventos, setEventos] = useState([]);
  const [activo, setActivo] = useState(true);
  const previo = useRef({});

  useEffect(() => {
    if (!activo) return undefined;
    let vivo = true;
    const consultar = async () => {
      const r = await api('/health/live', { auth: false, silencioso: true });
      if (!vivo) return;
      const lista = r.ok ? r.data.instancias : [{ host: 'gateway', status: 'down' }];
      setInstancias(lista);
      const nuevos = [];
      for (const i of lista) {
        const firma = `${i.status}|${i.version ?? '—'}`;
        if (previo.current[i.host] !== firma) {
          if (previo.current[i.host] !== undefined) {
            nuevos.push({ t: new Date(), host: i.host, status: i.status, version: i.version });
          }
          previo.current[i.host] = firma;
        }
      }
      if (nuevos.length) setEventos((e) => [...nuevos, ...e].slice(0, 30));
    };
    consultar();
    const t = setInterval(consultar, 1500);
    return () => { vivo = false; clearInterval(t); };
  }, [activo]);

  return (
    <div className="page">
      <EncabezadoPatron id="deploy" atributo="Facilidad de despliegue">
        Cada versión se construye como una imagen inmutable etiquetada (<code>api:1.0</code>, <code>api:2.0</code>…). El despliegue
        reemplaza las réplicas por la nueva imagen y espera sus health checks; si la versión nueva no queda sana, se vuelve
        automáticamente a la imagen anterior, que se conserva. La base de datos no se recrea.
      </EncabezadoPatron>

      <div className="toolbar">
        <Boton variante={activo ? 'ghost' : 'primary'} onClick={() => setActivo((v) => !v)}>
          {activo ? '❚❚ Pausar observación' : '▶ Observar despliegue'}
        </Boton>
        <span className="muted small">Consulta /health/live cada 1,5 s y registra cada cambio de versión o estado.</span>
      </div>

      <div className="grid grid-2">
        <Card titulo="Versión en cada réplica">
          <div className="replicas">
            {instancias.map((i) => (
              <div key={i.host} className={`replica replica-${i.status}`}>
                <div className="replica-host mono">{i.host}</div>
                <div className="replica-version">{i.version ? `v${i.version}` : '—'}</div>
                <Estado valor={i.status} />
              </div>
            ))}
          </div>
        </Card>
        <Card titulo="Eventos detectados" subtitulo="Cambios de versión / estado durante la observación">
          {eventos.length === 0 ? (
            <div className="empty">Sin cambios todavía. Ejecutá un deploy o la demo de rollback.</div>
          ) : (
            <ul className="events">
              {eventos.map((e, i) => (
                <li key={i}>
                  <span className="mono muted">{e.t.toLocaleTimeString()}</span>
                  <span className="mono">{e.host}</span>
                  <Estado valor={e.status} />
                  <span className="mono">{e.version ? `v${e.version}` : ''}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <div className="grid grid-2">
        <Card titulo="Flujo de despliegue">
          <div className="pipeline">
            {[
              ['Build', 'imagen api:X con API_VERSION'],
              ['Verificar', 'la versión actual está sana'],
              ['Reemplazar', 'api1 y api2 con la nueva imagen'],
              ['Health check', '/health de cada réplica'],
              ['Confirmar', 'o rollback a la imagen previa'],
            ].map(([t, d], i) => (
              <div key={t} className="pipe-step">
                <span className="pipe-n">{i + 1}</span>
                <b>{t}</b>
                <span className="muted small">{d}</span>
              </div>
            ))}
          </div>
          <ComoFunciona items={[
            'Las imágenes versionadas hacen los despliegues reproducibles y reversibles: volver atrás es cambiar la etiqueta.',
            'El health check es la puerta de calidad: una versión que no responde /health no queda en producción.',
            <>Con <code>FORCE_UNHEALTHY=true</code> se fabrica una versión defectuosa para comprobar el rollback de forma controlada.</>,
          ]} />
        </Card>
        <Card titulo="Prueba empírica" subtitulo="Con este panel abierto, en otra terminal">
          <p className="small">Demo completa: construye <code>2.0-broken</code>, la despliega, detecta el fallo y restaura la versión anterior.</p>
          <Comando>.\scripts\demo_rollback.ps1</Comando>
          <Comando>bash scripts/demo_rollback.sh</Comando>
          <p className="small">Despliegue de una versión sana:</p>
          <Comando>.\scripts\build_version.ps1 2.0; .\scripts\deploy.ps1 2.0</Comando>
          <p className="small muted">El historial de despliegues queda en <code>deployment_logs/deployment.log</code>.</p>
        </Card>
      </div>
    </div>
  );
}
