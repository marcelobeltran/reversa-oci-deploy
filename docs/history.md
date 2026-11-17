# Decisiones e historia revisada

Revisión: 17 noviembre 2026. Fuentes: chat del proyecto «Retomar configuración de
Reversa en», documentos del repositorio local anterior y exportaciones auditadas.

La base auditada es Reversa 1.3.4, commit upstream
524c64e5d8e11edd617f9207cd118bec8671b6ad. OpenCode observado: 1.19.0. El nuevo
despliegue conserva estas versiones para separar reinstalación de actualización.
La web de upstream muestra versiones posteriores; no se adoptan sin revisar.

La instalación anterior incluía LiteLLM, callbacks Gemini, un puente temporal,
guardias, prompts de pruebas y reglas globales. Las auditorías encontraron
problemas de integración y ensayos que sustituían el prompt base. No hay evidencia
para afirmar que un único componente causó todos los fallos ni que varios modelos
fueran incapaces de ejecutar Reversa.

La exportación más reciente analizada registra proveedor `oci`, Grok 4.6 y
solicitudes directas a Oracle Chicago `/openai/v1/chat/completions`, con lecturas,
escrituras y edición reales. También registra 404 de autorización y límites de
tokens. Un flujo de herramienta mínimo o un sitio generado no certifican exactitud
del análisis ni el despliegue nuevo.

Se elige conexión directa, una sola identidad visible de proveedor, modelos por ID
real, habilidades originales y proyectos nuevos. No se habilitan silenciosamente
fallbacks a otros modelos o proveedores. Las extensiones MD01/MD02 anteriores no se
instalan por defecto porque su eficacia no quedó certificada.

La API key de OCI GenAI es distinta de la pareja RSA de firma IAM, de una clave
SSH y de las Virtual Keys de LiteLLM. Cada tenant requiere sus propias claves,
políticas y comprobación de región/modelo. Crear la API key no le concede permisos:
se incluye política acotada por OCID y principal `generativeaiapikey`.

El LB usa TCP 443 con TLS hasta la VM. Esta decisión permite renovar certificados
IP cortos sin dar a la VM permiso para cambiar el LB. La VM solo puede leer dos
secretos y no necesita credenciales IAM de usuario ni permisos de administración.

No se versionan proyectos analizados, datos bancarios, sesiones o logs del piloto.
El portal se recuperó mediante lista explícita desde el código de integración
anterior; el inicializador conserva las rutas de ese código para compatibilidad.
