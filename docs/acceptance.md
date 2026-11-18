# Aceptación — 18 noviembre 2026

Verificaciones realizadas sobre la instalación real en Chicago. No se publican
IPs, OCIDs, contraseñas, tokens ni cuerpos de respuestas de clientes.

| Comprobación | Resultado |
| --- | --- |
| Orden de despliegue | Base, secretos/IAM y Bastion completados antes de la VM |
| Estado remoto | Un único stack Resource Manager; Apply de VM SUCCEEDED |
| VM | RUNNING, subnet privada y ninguna IP pública en sus VNIC |
| LB | Listeners 80/443; ambos backend sets OK |
| Bootstrap | cloud-init done; nginx, reversa-opencode y reversa-portal activos |
| Versiones | Reversa 1.3.4 y OpenCode 1.19.0 |
| GenAI | OCI directo, proveedor oci, modelo xai.grok-4.6, proyecto real |
| HTTPS | Cadena confiable Let's Encrypt YE2; SAN IP validado desde Internet |
| Renovación | certbot renew --dry-run correcto; timer activo cada seis horas |
| Autenticación | Sin credenciales: HTTPS 401; con credenciales: app y portal 200 |
| Portal | ZIP sintético de dos archivos cargado e inicializado mediante HTTPS |
| Herramientas | Dos read y un write completados por Grok; archivo confirmado en disco |
| Entregable | _reversa_sdd/validacion.md renderizado desde el portal HTTPS |
| Streaming | SSE 200 text/event-stream; evento recibido a través del LB |
| Habilidad | /reversa cargó skill oficial y leyó archivos/estado; sin errores |
| Idempotencia | Plan final SUCCEEDED: No changes |
| CI | GitHub Actions 44306566159 correcto, incluyendo pruebas Linux del portal |

Proyecto sintético conservado: `reversa-validacion`. Su sesión de aceptación
muestra el proveedor/modelo y las llamadas de herramientas. Se activó `/reversa`
hasta su primer punto oficial de interacción; no se ejecutó un análisis completo
de negocio ni sus cinco fases. La escritura de validación no sustituye esa prueba.

El primer ACME se inició antes de que el health check del LB se actualizara y
falló por conexión. Tras confirmar HTTP externo se emitió correctamente y se
verificó la renovación staging. El servicio incorpora reintentos limitados cada
cinco minutos para esa condición en nuevos tenants. También se corrigió el
lanzador del inicializador para ejecutar explícitamente Node con el archivo .mjs;
el bootstrap comprueba ahora sus módulos antes de continuar.

Los certificados IP tienen vigencia corta: el primero vence el 25 de noviembre
de 2026 y queda bajo renovación automática. La API key GenAI vence a los 90 días
de su creación y requiere la rotación documentada. No se probaron cargas grandes,
límites de tokens, recuperación de backups, alta disponibilidad ni generación
HTML completa por el modelo. La aplicación usa una sola VM; los backups y alertas
con destinatario deben configurarse según la operación de cada tenant.
