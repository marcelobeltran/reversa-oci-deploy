# Registro de entrega — 17 noviembre 2026

Tenant destino observado: workshoprever, home region Chicago. No se publican
credenciales, OCIDs del cliente ni direcciones de acceso en este documento.

- Repositorio GitHub nuevo creado: marcelobeltran/reversa-oci-deploy.
- Terraform: `validate` correcto con proveedor oracle/oci 9.13.0.
- GitHub Actions: primera ejecución completa correcta (44164215383).
- Stack `reversa-stack` creado en Resource Manager, estado Active; todavía sin Apply.
- Job `reversa-foundation-plan` enviado: último estado observado Accepted (en cola).
- La consulta posterior del job mostró «Request not completed within 15000 ms».
  No hay Plan completo ni aprovisionamiento confirmado todavía.
- Después falló el control de la ventana OCI: «Accessibility state unavailable
  for window 1378226», incluso tras recuperar la ventana y reiniciar la sesión
  de control. No se ejecutó Apply. El job enviado no se duplicó ni se canceló.
- El ZIP del stack OCI corresponde a la primera versión de esta entrega. Antes
  del Apply definitivo, actualizar su configuración desde la versión actual de
  GitHub: contiene correcciones del arranque del portal, firewall y cloud-init.
- Portal recuperado: 33 pruebas ejecutadas, correctas; una omitida en Windows.
- Preparación de credenciales: cuatro pruebas offline correctas con SDK OCI
  2.191.0, incluyendo reintento sin duplicación y rechazo de checkpoint ajeno.
- Scripts de shell: sintaxis verificada con Bash.
- Paquete Resource Manager generado por lista explícita.
- Aplicación cloud: pendiente de registrar los resultados reales del stack.
- TLS, renovación y prueba funcional GenAI: pendientes en tenant destino.

No interpretar estas comprobaciones locales como una instalación cloud terminada.

Para continuar se necesita recuperar el control de la consola OCI o disponer de
una sesión OCI CLI autenticada. No se necesita enviar claves privadas por chat.
Consultar el job existente antes de volver a ejecutar Plan. Conservar el mismo
stack y su estado; no crear otra infraestructura duplicada desde Terraform local.
