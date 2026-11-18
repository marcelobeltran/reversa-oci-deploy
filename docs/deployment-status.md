# Registro de entrega — 17 noviembre 2026

Tenant destino observado: workshoprever, home region Chicago. No se publican
credenciales, OCIDs del cliente ni direcciones de acceso en este documento.

- Repositorio GitHub nuevo creado: marcelobeltran/reversa-oci-deploy.
- Terraform: `validate` correcto con proveedor oracle/oci 9.13.0.
- GitHub Actions: primera ejecución completa correcta (44164215383).
- Stack `reversa-stack` creado en Resource Manager, estado Active; todavía sin Apply.
- Tras reiniciar Chrome se confirmó que `reversa-foundation-plan` terminó
  **Succeeded**. No se había ejecutado Apply.
- Se actualizó el ZIP del mismo stack con las correcciones del arranque del portal,
  firewall y cloud-init, manteniendo `enable_compute=false`.
- Se envió `reversa-foundation-plan-current`. Último estado observado: Accepted.
- Chrome volvió a bloquearse al abrir la vista de Logs. Se está preparando el
  acceso por OCI CLI para consultar el mismo job y continuar sin esa vista.
- OCI CLI oficial 3.96.3 instalada en una carpeta aislada del proyecto. Login
  temporal de 60 minutos abierto; autenticación del titular pendiente.
- Portal recuperado: 33 pruebas ejecutadas, correctas; una omitida en Windows.
- Preparación de credenciales: cuatro pruebas offline correctas con SDK OCI
  2.191.0, incluyendo reintento sin duplicación y rechazo de checkpoint ajeno.
- Controlador de Resource Manager: cinco pruebas offline correctas de aislamiento
  por tenant/stack y rechazo de jobs duplicados; nueve junto a las de credenciales.
- Scripts de shell: sintaxis verificada con Bash.
- Paquete Resource Manager generado por lista explícita.
- Aplicación cloud: pendiente de registrar los resultados reales del stack.
- TLS, renovación y prueba funcional GenAI: pendientes en tenant destino.

No interpretar estas comprobaciones locales como una instalación cloud terminada.

Para continuar se necesita completar el login temporal OCI. No se necesita enviar
claves privadas ni contraseñas por chat.
Consultar el job existente antes de volver a ejecutar Plan. Conservar el mismo
stack y su estado; no crear otra infraestructura duplicada desde Terraform local.
