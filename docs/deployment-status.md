# Registro de despliegue — 18 noviembre 2026

[Inicio](../README.md) · Historia técnica. Para empezar usa
[Primer uso](01-primer-uso.md) o [Instalación](02-tenant-nuevo.md).

Destino: workshoprever, región principal Chicago. Este registro no publica
credenciales, OCIDs del cliente ni dirección de acceso.

- Repositorio: marcelobeltran/reversa-oci-deploy; infraestructura parametrizada,
  runtime y documentación versionados. Validación Terraform y CI correctas.
- Resource Manager: un único stack y estado remoto. Foundation Apply **SUCCEEDED**.
  Compartimentos, VCN, subnets pública/privada, rutas, gateways, NSG, IP reservada,
  balanceador, Vault/clave y proyecto GenAI creados antes de la VM.
- Credenciales GenAI y web creadas y almacenadas directamente en Vault. El estado
  Terraform contiene referencias; las claves no se empaquetan ni publican.
- Políticas de lectura de los dos secretos e inferencia por API key creadas.
- Inferencia real mínima con xai.grok-4.6 **correcta**, usando el endpoint Oracle
  OpenAI compatible y OpenAI-Project, sin proxy.
- Se corrigió el controlador OCI para usar los modelos Create* de solicitudes;
  siete pruebas cubren aislamiento y serialización real del SDK.
- OCI rechazó un intento de desasociar la IP que administra el LB. La IP siguió
  asociada; lifecycle.ignore_changes sobre private_ip_id evita ese cambio en
  siguientes planes. Se continuó sobre el mismo estado, sin duplicar recursos.
- Bastion administrativo restringido a una IP /32: Apply **SUCCEEDED** antes de
  crear la VM. Acceso temporal por port forwarding, sin VM bastión pública.
- Aplicación: Plan de tres altas, cero cambios y cero destrucciones; Apply
  **SUCCEEDED**. VM ejecutándose en subnet privada, sin IP pública. Ambos
  backend sets del LB reportan **OK**.
- cloud-init terminó correctamente. Nginx, OpenCode y portal están activos.
- Certificado IP de Let's Encrypt emitido; confianza y SAN de IP verificados
  externamente. Renovación simulada correcta; timer cada seis horas activo.
- Aceptación real: carga ZIP desde HTTPS, inicialización de 73 habilidades,
  lectura/escritura con Grok, Markdown visible en portal, streaming SSE y
  activación de la habilidad oficial mediante `/reversa`, sin errores.
- Runtime final sincronizado tanto en la VM como en el ZIP del mismo stack.
  El Plan final terminó **SUCCEEDED**, sin cambios de infraestructura.
- Evidencia y límites de aceptación: [acceptance.md](acceptance.md).

## Acceso temporal a OCI

Chrome se bloqueó repetidamente en Logs; las operaciones continúan mediante API.
El login de CLI 3.96.3 omitía state y OCI devolvía state=undefined. Se inició una
nueva autorización conservando public_key, nonce y callback del proceso oficial,
con state explícito igual al nonce. El titular completó contraseña/MFA y la CLI
confirmó autenticación, creó su perfil temporal y permitió consultar Resource
Manager. No se almacenan contraseñas de usuario en el repositorio.

No reutilizar un enlace de autorización después del callback ni publicar tokens.
Las sesiones y checkpoints se guardan exclusivamente en local/, excluido de Git.
