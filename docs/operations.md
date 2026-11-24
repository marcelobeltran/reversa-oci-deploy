# Operación y mantenimiento

[Inicio](../README.md) · [Entrar por SSH y diagnosticar](03-administracion.md)

Para la primera instalación sigue [Tenant nuevo](02-tenant-nuevo.md). Para usar
la app sigue [Primer uso](01-primer-uso.md). Esta página se consulta una vez
operativa la instalación.

Para revisar la cuota del modelo o pedir más capacidad, sigue
[Límites de Generative AI](limites-genai.md): procedimiento en la consola OCI,
valor propuesto de 1.500.000 TPM para Grok 4.6 en Chicago y justificación.

## Revisar certificados IP

Certbot 5.4+ usa perfil `shortlived` y `--ip-address`. El timer comprueba renovación
cada seis horas y recarga Nginx incluso cuando solo se renueva el certificado.
Si el LB todavía no enruta durante la primera emisión, el servicio reintenta
cada cinco minutos, con un máximo de tres arranques por hora. El timer conserva
su comprobación cada seis horas. No reintentar manualmente en un bucle.

**Dónde:** terminal SSH de Ubuntu, tras completar [Administración](03-administracion.md).

Para un reintento tras corregir conectividad:

```bash
sudo systemctl start reversa-certificate.service
sudo /opt/reversa/certbot/bin/certbot certificates
sudo /opt/reversa/certbot/bin/certbot renew --dry-run
```

**Resultado esperado:** el servicio termina correctamente, Certbot muestra el
certificado de la IP con vigencia futura y el dry-run confirma renovación simulada.
Si falla, revisar journalctl antes de continuar.

El dry-run debe ejecutarse después de la primera emisión real. En un ensayo previo
usar el servidor staging de Let's Encrypt, sin cargar ese certificado en producción.
No usar `--force-renewal` en un bucle: puede agotar límites de emisión.

El certificado tiene vigencia de aproximadamente seis días. Un timer instalado
no demuestra renovación exitosa: vigilar fecha de vencimiento externamente y
alertar con al menos 48 horas restantes. Esta entrega no configura un destino de
alertas porque no se proporcionó correo o canal. Si la VM se recrea se necesita
preservar/restaurar `/etc/letsencrypt` o emitir otro certificado para la misma IP.

## Cambiar la contraseña web

**Dónde:** consola web OCI, Vault del compartment `reversa-security`.

1. Abre el secreto `reversa-web`.
2. Crea una nueva versión con un JSON de campos `username` y `password`. El usuario
   debe usar letras/números/guion/guion bajo, y la contraseña al menos 20 caracteres.
3. Confirma que la nueva versión sea `CURRENT`.
4. Después, en **SSH de Ubuntu**, ejecuta:

```bash
sudo /opt/reversa/venv/bin/python /opt/reversa/configure.py
sudo nginx -t
sudo systemctl reload nginx
```

**Resultado esperado:** configuración válida y acceso con la credencial nueva
en una ventana privada del navegador. El navegador anterior puede conservar
credenciales básicas en caché. `configure.py` también regenera la configuración
OpenCode desde `/etc/reversa/config.json`: tenlo en cuenta si la editaste manualmente.

## Rotar la clave GenAI y respaldar datos

**Dónde:** consola OCI para la clave GenAI y Vault; SSH de Ubuntu para reiniciar.

1. Antes de los 90 días, renueva la clave secundaria de la API key GenAI de Reversa.
2. Guarda su valor como nueva versión CURRENT del secreto `reversa-genai`.
3. En SSH de Ubuntu, ejecuta:

```bash
sudo systemctl restart reversa-opencode
systemctl is-active reversa-opencode
curl --fail --silent http://127.0.0.1:4096/global/health
```

4. En el navegador, abre OpenCode y realiza la prueba de lectura/escritura de
   [Primer uso, paso 5](01-primer-uso.md#paso-5-comprobar-lectura-y-escritura).
5. Solo después de esa inferencia correcta, retira la clave anterior según la
   política de la organización y registra el próximo vencimiento.

**Resultado esperado:** servicio activo e inferencia real correcta con el secreto
nuevo. El health check solo no prueba la validez de la nueva clave. El script
`smoke-genai.py` utiliza el checkpoint local inicial, no consulta automáticamente
Vault; después de una rotación no lo uses para certificar la clave nueva.
Nunca pegues valores secretos en variables Terraform o en la consola del plan.

**Dónde:** estrategia de backup OCI y restauración administrada desde Ubuntu.

Respaldar `/home/opc/proyectos`, `/home/opc/.local/share/opencode`, configuración
de servicio y `/etc/letsencrypt` de forma cifrada. El boot volume se preserva al
eliminar la VM, pero eso no equivale a un backup independiente. Restaurar en VM
aislada y verificar ZIP, sesiones y documentos antes de declarar recuperado.

## Actualizar una instalación existente

**Dónde:** mismo stack de Resource Manager para infraestructura; SSH para cambios
de runtime. Esta sección no ordena ejecutar una actualización ahora.

No realizar `terraform destroy` como procedimiento de actualización. Reaplicar
el mismo estado es idempotente; no cambiar prefijo/compartimentos para simular
una actualización. cloud-init es de primer arranque: los cambios de user_data no
se reaplican solos. Para actualización de runtime usar un procedimiento probado
con copia previa o reemplazo/restauración planificado.
