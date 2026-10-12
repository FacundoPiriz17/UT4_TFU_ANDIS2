"""Operaciones compartidas por los launchers PowerShell y Bash (Python 3.10+)."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
SERVICES = ("db", "api1", "api2", "nginx")
EXPECTED = {"api1.0", "api2.0"}
STATE = ROOT / ".deploy/current_version"


def run(*args, capture=False, env=None):
    result = subprocess.run(args, cwd=ROOT, env=env, text=True,
                            stdout=subprocess.PIPE if capture else None, check=True)
    return result.stdout.strip() if capture else None


def compose(*args, capture=False):
    return run("docker", "compose", "-f", str(ROOT / "docker-compose.yaml"),
               *args, capture=capture)


def prepare():
    run("docker", "info", capture=True)
    run("docker", "compose", "version", capture=True)
    if not (ROOT / ".env").exists():
        shutil.copyfile(ROOT / ".env.example", ROOT / ".env")
    STATE.parent.mkdir(exist_ok=True)
    (ROOT / "deployment_logs").mkdir(exist_ok=True)
    if STATE.exists():
        os.environ["API_IMAGE"] = "api:" + STATE.read_text().strip()


def http(path, data=None, token=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(BASE + path, data=json.dumps(data).encode() if data is not None else None,
                  headers=headers, method=method)
    with urlopen(req, timeout=15) as response:
        raw = response.read()
        body = json.loads(raw) if raw and "json" in response.headers.get("Content-Type", "") else raw
        return body, response.headers.get("X-Instance-ID"), response.status


def health(service):
    ids = compose("ps", "-a", "-q", service, capture=True).splitlines()
    if len(ids) != 1:
        return "missing"
    state = json.loads(run("docker", "inspect", ids[0], capture=True))[0]["State"]
    return state.get("Health", {}).get("Status", state["Status"])


def wait(services=SERVICES, timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        states = {s: health(s) for s in services}
        if all(v == "healthy" for v in states.values()):
            print(states)
            return
        if any(v in ("unhealthy", "exited", "dead") for v in states.values()):
            raise RuntimeError(f"Servicios fallidos: {states}")
        time.sleep(2)
    raise RuntimeError(f"Timeout esperando servicios: {states}")


def scaling(version=None, verbose=True):
    seen = set()
    for i in range(10):
        body, instance, _ = http("/instance")
        if body["instance"] != instance:
            raise RuntimeError("Header e identidad no coinciden")
        if version and body["version"] != version:
            raise RuntimeError(f"Version inesperada: {body}")
        seen.add(instance)
        if verbose:
            print(f"Peticion {i + 1} -> {instance} -> {body['version']}")
    if seen != EXPECTED:
        raise RuntimeError(f"No se observaron las dos instancias: {seen}")


def login():
    body, instance, _ = http("/auth/login", {
        "email": "demo@adaii.local", "contrasena": "Demo123!"})
    token = body.get("access_token")
    if not token:
        raise RuntimeError("Login sin JWT")
    print(f"LOGIN -> {instance} -> JWT obtenido")
    return token


def stateless():
    token = login()
    seen = set()
    # Auditoria es un GET autenticado ya existente en el dominio.
    for i in range(10):
        _, instance, status = http("/auditoria", token=token)
        print(f"GET /auditoria -> {instance} -> {status}")
        seen.add(instance)
    if seen != EXPECTED:
        raise RuntimeError(f"JWT no comprobado en ambas instancias: {seen}")


def ready(version=None):
    wait()
    compose("exec", "-T", "nginx", "nginx", "-t")
    http("/health")
    scaling(version, verbose=False)


def build(version="1.0", broken="false"):
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", version):
        raise ValueError("Version no valida para una etiqueta Docker")
    if broken not in ("true", "false"):
        raise ValueError("ForceUnhealthy debe ser true o false")
    run("docker", "build", "-f", "dockerfile", "--build-arg", "API_VERSION=" + version,
        "--build-arg", "FORCE_UNHEALTHY=" + broken, "-t", "api:" + version, ".")


def start():
    build()
    os.environ["API_IMAGE"] = "api:1.0"
    compose("up", "-d", "--no-build")
    wait(("db", "api1", "api2"))
    compose("restart", "nginx")
    ready("1.0")
    STATE.write_text("1.0\n")
    compose("ps")
    print("API: http://localhost:8000\nSwagger: http://localhost:8000/docs")
    print("Usuario demo: demo@adaii.local / Demo123!")


def log(message):
    line = f"{datetime.now(timezone.utc).isoformat()} | {message}"
    print(line)
    with (ROOT / "deployment_logs/deployment.log").open("a", encoding="utf-8") as out:
        out.write(line + "\n")


def switch(version):
    os.environ["API_IMAGE"] = "api:" + version
    compose("up", "-d", "--no-deps", "--no-build", "--force-recreate", "api1", "api2")
    wait(("api1", "api2"))
    compose("restart", "nginx")
    ready(version)


def deploy(version):
    run("docker", "image", "inspect", "api:" + version, capture=True)
    if not STATE.exists():
        raise RuntimeError("Falta version anterior verificada; ejecutar start primero")
    previous = STATE.read_text().strip()
    if previous == version:
        raise RuntimeError("Usar una etiqueta distinta para preservar la imagen de rollback")
    run("docker", "image", "inspect", "api:" + previous, capture=True)
    ready(previous)
    log(f"DEPLOY_START previous={previous} new={version}")
    try:
        switch(version)
        STATE.write_text(version + "\n")
        log(f"DEPLOY_SUCCESS current={version}")
        return 0
    except Exception as exc:
        log(f"DEPLOY_FAILED {exc}")
        try:
            compose("logs", "--tail", "50", "api1", "api2", "nginx")
        except Exception as log_error:
            log(f"LOGS_UNAVAILABLE {log_error}")
    log(f"ROLLBACK_START target={previous}")
    try:
        switch(previous)
        STATE.write_text(previous + "\n")
        log(f"ROLLBACK_SUCCESS current={previous}")
        return 1
    except Exception as exc:
        log(f"ROLLBACK_FAILED {exc}")
        return 2


def rollback_demo():
    if not STATE.exists():
        start()
    previous = STATE.read_text().strip()
    ready(previous)
    db_id = compose("ps", "-q", "db", capture=True)
    build("2.0-broken", "true")
    if deploy("2.0-broken") != 1:
        raise RuntimeError("Se esperaba deploy fallido con rollback exitoso")
    ready(previous)
    if STATE.read_text().strip() != previous or compose("ps", "-q", "db", capture=True) != db_id:
        raise RuntimeError("Estado anterior o contenedor MySQL alterado")
    print("Rollback verificado en ambas APIs; MySQL no fue recreado.")


def acid():
    compose("exec", "-T", "api1", "python", "-m", "scripts.acid_check")


def tactics():
    token = login()
    games = []
    try:
        for policy, expected in (("normal", 100), ("invierno", 50)):
            game, _, _ = http("/juegos", {"nombre": "Demo tacticas " + policy}, token)
            game_id = game["id_juego"]
            games.append((game_id, False))
            body, _, _ = http("/compras", {"email_persona": "demo@adaii.local",
                "id_juego": game_id, "costo_base": 100, "politica": policy}, token)
            games[-1] = (game_id, True)
            if body["costo_compra"] != expected:
                raise RuntimeError(f"Costo incorrecto: {body}")
            print(f"Strategy {policy}: {body['costo_compra']}")
        # Mutaciones desde ambas replicas usando un unico JWT.
        seen = set()
        for _ in range(10):
            _, instance, _ = http(f"/juegos/{games[0][0]}", {"nombre": "Demo auditada"}, token, "PUT")
            seen.add(instance)
        if seen != EXPECTED:
            raise RuntimeError("No se auditaron operaciones de ambas replicas")
        # Verificar desde las dos APIs los mismos registros recien escritos.
        query = (
            "from app.database import SessionLocal; from app.models import Compra; "
            "import json; "
            "db=SessionLocal(); "
            f"rows=db.query(Compra).filter(Compra.IdJuego.in_({[g[0] for g in games]!r})).all(); "
            "print(json.dumps(sorted((r.IdJuego,r.CostoCompra) for r in rows))); db.close()"
        )
        rows = [json.loads(compose("exec", "-T", s, "python", "-c", query, capture=True))
                for s in ("api1", "api2")]
        expected = [[games[0][0], 100], [games[1][0], 50]]
        if rows[0] != expected or rows[1] != expected:
            raise RuntimeError(f"Las APIs no comparten las compras esperadas: {rows}")
        print("Ambas APIs leen las mismas compras en MySQL.")
        body, _, _ = http("/auditoria", token=token)
        if not any("GENERAR_COMPRA | OK" in line for line in body["lineas"]):
            raise RuntimeError("Auditoria sin compras")
        paths = [compose("exec", "-T", s, "cat", "/app/logs/operaciones.txt", capture=True)
                 for s in ("api1", "api2")]
        if not paths[0] or paths[0] != paths[1]:
            raise RuntimeError("Auditoria no compartida")
        compose("restart", "api1", "api2")
        wait(("api1", "api2"))
        compose("restart", "nginx")
        ready()
        after = compose("exec", "-T", "api2", "cat", "/app/logs/operaciones.txt", capture=True)
        if not after.startswith(paths[0]):
            raise RuntimeError("Auditoria perdida tras reinicio")
        print("Auditoria compartida y persistente verificada.")
    finally:
        for game_id, purchased in reversed(games):
            if purchased:
                http(f"/compras/demo@adaii.local/{game_id}", token=token, method="DELETE")
            http(f"/juegos/{game_id}", token=token, method="DELETE")


def status():
    compose("ps")
    ready()
    print("Entorno listo para la demo.")


def menu():
    actions = {"1": start, "2": status, "3": scaling, "4": stateless,
               "5": acid, "6": tactics, "7": rollback_demo,
               "8": lambda: compose("logs", "--tail", "100", *SERVICES),
               "9": lambda: compose("down")}
    while True:
        print("\n1 Iniciar entorno\n2 Ver estado\n3 Demo balanceo / escalabilidad horizontal"
              "\n4 Demo stateless / JWT\n5 Demo ACID\n6 Demo tacticas TFU 2"
              "\n7 Demo rollback de despliegue\n8 Ver logs\n9 Detener entorno\n0 Salir")
        choice = input("> ").strip()
        if choice == "0":
            return
        try:
            if choice in actions:
                actions[choice]()
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "stop", "status", "build_version", "deploy",
        "demo_scaling", "demo_stateless", "demo_acid", "demo_tacticas", "demo_rollback", "menu"])
    parser.add_argument("version", nargs="?", default="1.0")
    parser.add_argument("broken", nargs="?", default="false")
    parser.add_argument("--clean", action="store_true", help="Elimina tambien los volumenes")
    args = parser.parse_args()
    try:
        prepare()
        actions = {"start": start, "status": status, "demo_scaling": scaling,
            "demo_stateless": stateless, "demo_acid": acid, "demo_tacticas": tactics,
            "demo_rollback": rollback_demo, "menu": menu,
            "build_version": lambda: build(args.version, args.broken),
            "deploy": lambda: deploy(args.version),
            "stop": lambda: compose("down", *(["-v", "--remove-orphans"] if args.clean else []))}
        return actions[args.action]() or 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.action in ("start", "deploy", "demo_rollback"):
            try:
                compose("logs", "--tail", "80", *SERVICES)
            except Exception:
                pass
        return 2


if __name__ == "__main__":
    sys.exit(main())
