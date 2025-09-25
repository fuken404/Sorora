"""
Módulo principal de la API Sorora 🚨

Este archivo configura la aplicación FastAPI, incluyendo middlewares,
routers, documentación y un health check básico.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Agregar las rutas de los microservicios al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ms_albergues.app.routes import shelters_routes  # pylint: disable=wrong-import-position
from ms_alertas.app.routes import alerts_route  # pylint: disable=wrong-import-position


DESCRIPTION = """
# Sorora API 🚨

API unificada para el sistema Sorora de alerta y protección para mujeres.

## Funcionalidades

### Albergues 🏠

* **Listar albergues** - Obtener todos los albergues disponibles
* **Buscar albergue** - Encontrar albergue por ID
* **Crear albergue** - Registrar nuevo albergue
* **Actualizar albergue** - Modificar información de albergue
* **Eliminar albergue** - Dar de baja un albergue

### Alertas SOS 🆘

* **Crear alerta** - Enviar señal de auxilio con ubicación
* **Notificaciones** - Envío automático a servicios de emergencia
* **Seguimiento** - Monitoreo de alertas activas

## Ambiente

* **Desarrollo** - `http://localhost:10000`
* **Producción** - [URL_PRODUCCION]

## Notas

* Todas las respuestas incluyen códigos HTTP estándar
* La autenticación es requerida para endpoints sensibles
* Los datos de ubicación usan coordenadas geográficas (latitud/longitud)
"""

app = FastAPI(
    title="Sorora API",
    description=DESCRIPTION,
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    contact={
        "name": "Equipo Sorora",
        "url": "https://github.com/tuorganizacion/sorora",
        "email": "soporte@sorora.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ En producción, cambiar por orígenes específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los routers
app.include_router(
    shelters_routes.router,
    prefix="/shelters",
    tags=["shelters"],
)

app.include_router(
    alerts_route.router,
    prefix="/alerts",
    tags=["alerts"],
)


@app.get("/health", tags=["health"])
async def health_check():
    """
    Verifica el estado básico del servicio y sus microservicios.
    """
    return {"status": "ok", "services": ["shelters", "alerts"]}


if __name__ == "__main__":
    import uvicorn  # pylint: disable=import-outside-toplevel

    uvicorn.run(app, host="0.0.0.0", port=10000)
