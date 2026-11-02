# Sorora

Directorio de refugios y señal de alerta para mujeres en situación de violencia. **Demo:** [sorora.fuken404.dev](https://sorora.fuken404.dev)

> **La demo no avisa a nadie y sus albergues son inventados.** Si estás en peligro en Colombia, llama al **155** (orientación a mujeres) o al **123** (emergencias).

## Qué hace

- Muestra albergues en un mapa, ordenados por distancia a un punto, con sus cupos.
- Ante una alerta sugiere los tres más cercanos **con cupo**.
- Tiene dos modos, y el seguro es el predeterminado:

| | `MODE=demo` (por defecto) | `MODE=live` |
|---|---|---|
| Ubicación | Un punto de ejemplo: el panel no la pide | La del dispositivo, con permiso |
| Se guarda la alerta | No | Sí, con su resultado |
| Aviso por Telegram | No | Sí, con reintentos |
| Requiere llave | No | Sí, `X-Alert-Key` |
| Si el aviso falla | No aplica | Responde `502` y `notified: false`: nunca dice que se envió |

## Decisiones

- **Una API modular, no microservicios.** Dos dominios pequeños no justifican desplegar y coordinar varios servicios.
- **Sin datos reales.** La ubicación de un albergue real es información protegida; aquí solo hay ejemplos.
- **Sin clave en el mapa.** Leaflet y OpenStreetMap evitan publicar una llave en el frontend.
- **El token no llega a los logs.** Telegram lleva el token en la URL, así que no se registran URLs ni excepciones crudas.
- **Escribir exige llave.** Crear, editar o borrar albergues requiere `X-Admin-Key`; sin llave configurada, esas rutas quedan cerradas.

Modo `live` es una base para una instancia privada, no un servicio de emergencias listo para usar: necesitaría acompañamiento de organizaciones especializadas y datos verificados.

## Correr en local

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
STORAGE=memory uvicorn app.main:app --reload
```

Abre <http://127.0.0.1:8000> y la API en `/api/docs`. Con MongoDB incluido:

```bash
docker compose up --build
```

## Pruebas

```bash
pytest
```

## Stack

Python 3.12 · FastAPI · MongoDB · Leaflet · Docker · Vercel · GitHub Actions
