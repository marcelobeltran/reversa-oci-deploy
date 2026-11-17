# Aceptación, operación y recuperación

## Antes de habilitar compute

- Confirmar tenancy, home region, estado de compartimentos, rutas y NSG.
- Comprobar LB activo, IP reservada y que no hay backend todavía.
- Verificar Vault y proyecto GenAI activos en los compartimentos correctos.
- Preparar claves por tenant, aplicar IAM y verificar disponibilidad de Grok 4.6.
- Consultar cuotas y límites: la referencia histórica tuvo un pico estimado de
  unos 880.000 tokens/min incluyendo caché. La forma de contabilizar caché debe
  confirmarse con OCI; no se promete resolver un 429 aumentando memoria de VM.
- Verificar imagen Ubuntu 24.04 x86_64 y capacidad E5 en la AD elegida.

## Después de habilitar compute

Entrar mediante OCI Bastion cuando esté habilitado. Comprobar:

```bash
sudo cloud-init status --wait
systemctl is-active nginx reversa-opencode reversa-portal
systemctl status reversa-certificate.timer --no-pager
sudo journalctl -u reversa-certificate.service -n 40 --no-pager
curl --fail http://127.0.0.1:4096/global/health
```

Desde otra red, `curl -I https://IP/` debe validar el certificado y responder 401
sin credenciales. `http://IP/` devuelve 404, no sirve proyectos. Probar el portal
autenticado y la conversación web; comprobar streaming y WebSocket. La VM no debe
tener IP pública y 4096/4100/22 no deben quedar expuestos a Internet.

Crear un proyecto sintético, subir dos archivos de ejemplo y activar `/reversa`.
Comprobar llamadas reales de lectura/escritura, checkpoints y entregables en
disco; exportar evidencia sanitizada del proveedor/modelo/endpoint. Confirmar que
no se seleccionó otro proveedor. La respuesta textual del modelo no basta.

## Certificados IP

Certbot 5.4+ usa perfil `shortlived` y `--ip-address`. El timer comprueba renovación
cada seis horas y recarga Nginx incluso cuando solo se renueva el certificado.
La primera emisión se reintenta en el siguiente timer si el LB aún no enruta.
Para un reintento tras corregir conectividad:

```bash
sudo systemctl start reversa-certificate.service
sudo /opt/reversa/certbot/bin/certbot certificates
sudo /opt/reversa/certbot/bin/certbot renew --dry-run
```

El dry-run debe ejecutarse después de la primera emisión real. En un ensayo previo
usar el servidor staging de Let's Encrypt, sin cargar ese certificado en producción.
No usar `--force-renewal` en un bucle: puede agotar límites de emisión.

El certificado tiene vigencia de aproximadamente seis días. Un timer instalado
no demuestra renovación exitosa: vigilar fecha de vencimiento externamente y
alertar con al menos 48 horas restantes. Esta entrega no configura un destino de
alertas porque no se proporcionó correo o canal. Si la VM se recrea se necesita
preservar/restaurar `/etc/letsencrypt` o emitir otro certificado para la misma IP.

## Credenciales y datos

Leer el secreto web en Vault con el usuario administrador. Su JSON incluye
`username` y `password`. Para cambiar contraseña: publicar una versión CURRENT
del secreto, ejecutar `sudo /opt/reversa/venv/bin/python /opt/reversa/configure.py`
y recargar Nginx. Para rotar GenAI, renovar la clave standby, cambiar CURRENT del
secreto GenAI y reiniciar `reversa-opencode`. Verificar una inferencia antes de
revocar la anterior. Nunca pegar valores en Terraform o en la consola del plan.

Respaldar `/home/opc/proyectos`, `/home/opc/.local/share/opencode`, configuración
de servicio y `/etc/letsencrypt` de forma cifrada. El boot volume se preserva al
eliminar la VM, pero eso no equivale a un backup independiente. Restaurar en VM
aislada y verificar ZIP, sesiones y documentos antes de declarar recuperado.

No realizar `terraform destroy` como procedimiento de actualización. Reaplicar
el mismo estado es idempotente; no cambiar prefijo/compartimentos para simular
una actualización. cloud-init es de primer arranque: los cambios de user_data no
se reaplican solos. Para actualización de runtime usar un procedimiento probado
con copia previa o reemplazo/restauración planificado.
