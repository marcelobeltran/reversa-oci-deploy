# 3. Administración y resolución de problemas

[Inicio](../README.md) · [Instalación](02-tenant-nuevo.md) · [Operación](operations.md)

**Objetivo:** entrar por SSH a la VM privada y comprobar qué está fallando.
Los pasos suponen que habilitaste Bastion y guardaste tu clave pública en la
VM al crearla, como indica la guía de instalación.

## Paso 1. Identificar la VM y la clave

**Dónde:** PowerShell de tu PC, raíz del clon de **ese tenant**.

```powershell
$out = Get-Content .\local\outputs.json -Raw | ConvertFrom-Json
$out.instance_ocid.value
$out.private_ip.value
Test-Path .\local\reversa-admin
Get-Content .\local\reversa-admin.pub
```

**Resultado esperado:** OCID de instancia, IP privada, `True` y clave **pública**.
No muestres el archivo sin `.pub`: es la clave privada. La VM es Ubuntu 24.04,
su usuario SSH es **`ubuntu`**. `opc` ejecuta la aplicación.

Si no tienes las salidas, el administrador puede buscar la VM `reversa-vm` en
`reversa-app`, y su IP privada en los detalles de red. Si no tienes la clave
privada correspondiente, no generes otra esperando que funcione: se requiere
recuperación de acceso con el administrador.

## Paso 2. Crear una sesión temporal de Bastion

**Dónde:** navegador, consola OCI del tenant y región correctos.

1. Busca el servicio **Bastion** y selecciona `reversa-operations`.
2. Abre `reversa-bastion`. Debe estar activo.
3. Comprueba que su lista de IP permitidas incluye la IP pública actual de tu PC
   como `/32`. Si cambió, actualiza `bastion_allowed_cidrs` mediante el mismo stack
   y su Plan/Apply. No abras `0.0.0.0/0`.
4. Crea una sesión tipo **SSH port forwarding**, destino la IP privada del paso
   1, puerto **22**, duración **3600 segundos**.
5. Proporciona el contenido de `local/reversa-admin.pub` como clave pública.
6. Espera estado **ACTIVE** y abre la opción de copiar el comando SSH de la sesión.

**Resultado esperado:** sesión activa con un comando para el host del servicio
Bastion. No crea una VM pública ni cambia el acceso web de la aplicación.

Alternativa para quien ya tiene CLI autenticada: `scripts/admin-session.py`
crea/reutiliza la sesión y guarda sus metadatos en `local/admin-session.private.json`.
La ruta por consola anterior permite copiar el comando preparado por OCI sin
interpretar manualmente los metadatos.

## Paso 3. Abrir el túnel y entrar a Ubuntu

**Dónde:** dos ventanas de PowerShell de tu PC, ambas en la raíz del mismo clon.

**Ventana A:** pega el comando copiado desde OCI, sustituyendo únicamente:

- `<privateKey>` por la ruta absoluta a `local/reversa-admin` de este clon.
- `<localPort>` por `2222`.

Usa la IP privada, el host, ID de sesión y puerto del servicio que entrega OCI.
**No pegues la clave privada dentro del comando.**

**Esperado en A:** el proceso sigue ejecutándose, normalmente sin mostrar texto
y sin devolver el prompt. Mantén esta ventana abierta.

**Ventana B:**

```powershell
ssh -i .\local\reversa-admin -p 2222 ubuntu@127.0.0.1
```

**Resultado esperado:** prompt de Ubuntu, por ejemplo `ubuntu@reversa:~$`.
Desde ese punto estás en la VM. `127.0.0.1:2222` es el túnel local, no la IP de
una VM pública. Si el túnel se cierra o expira la sesión, vuelve al paso 2.

## Paso 4. Comprobar la instalación dentro de la VM

**Dónde:** terminal **SSH de Ubuntu**, ventana B. Ejecuta cada bloque por separado.

```bash
sudo cloud-init status --wait
```

**Esperado:** termina en `done`. Puede tardar mientras descarga paquetes y espera
IAM. Si termina en error, revisa las últimas líneas:

```bash
sudo tail -n 60 /var/log/cloud-init-output.log
```

No repitas `cloud-init` ni el instalador completo sin resolver el error que aparece.

```bash
systemctl is-active nginx reversa-opencode reversa-portal
curl --fail --silent http://127.0.0.1:4096/global/health
```

**Esperado:** tres líneas `active` y JSON con `healthy: true`.
El puerto 4096 solo se consulta así **dentro de Ubuntu**, no desde tu PC.

```bash
systemctl is-active reversa-certificate.timer
sudo journalctl -u reversa-certificate.service -n 40 --no-pager
sudo /opt/reversa/certbot/bin/certbot certificates
```

**Esperado:** timer `active`, emisión/renovación correcta y certificado con la IP
pública correcta y fecha futura. El servicio oneshot puede figurar `inactive`
después de terminar bien; lo importante es el resultado del último job y el timer.

Para comprobar renovación, después de la primera emisión correcta:

```bash
sudo /opt/reversa/certbot/bin/certbot renew --dry-run --no-random-sleep-on-renew
```

**Esperado:** simulación correcta. Utiliza staging y no reemplaza el certificado
real por uno de prueba. Si falla, revisa el error antes de reintentar.

Para volver a la guía de instalación, continúa en su
[paso 13](02-tenant-nuevo.md#paso-13-verificar-bootstrap-y-https), con las pruebas
externas desde PowerShell.

## Paso 5. Consultar registros según el servicio

**Dónde:** SSH de Ubuntu.

| Problema | Comando |
| --- | --- |
| OpenCode no responde o falla GenAI | `sudo journalctl -u reversa-opencode -n 60 --no-pager` |
| Error al cargar ZIP/inicializar proyecto | `sudo journalctl -u reversa-portal -n 60 --no-pager` |
| Nginx no inicia | `sudo nginx -t` |
| HTTPS no tiene certificado válido | `sudo journalctl -u reversa-certificate.service -n 40 --no-pager` |

**Resultado esperado:** error concreto del componente. Comparte solo el fragmento
necesario y quita credenciales o datos de proyectos. No vuelques archivos privados
de configuración para diagnosticar un problema de red.

## Paso 6. Cerrar la administración

**Dónde:** SSH de Ubuntu y PowerShell.

1. En B, escribe `exit` para salir de Ubuntu.
2. En A, pulsa `Ctrl+C` para cerrar el túnel.
3. En OCI, elimina la sesión temporal si ya no la necesitas, o deja que expire.

**Esperado:** ya no hay túnel administrativo. El acceso HTTPS sigue funcionando.

## Problemas frecuentes

| Síntoma | Dónde revisar | Qué hacer antes de continuar |
| --- | --- | --- |
| `py`, `git` o `ssh` no se reconoce | PowerShell, instalación paso 1 | Instalar la herramienta y abrir otra terminal |
| Autenticación `invalid state` / `state=undefined` | Terminal y navegador de CLI | Terminar el intento fallido, iniciar un login nuevo y usar únicamente su enlace. No reciclar el callback viejo ni asumir que el login web creó el perfil. Si se repite, detenerse y revisar con el administrador de OCI/CLI; no continuar con credenciales de otro tenant. Este fallo ocurrió en la instalación de referencia y la guía no promete resolverlo automáticamente |
| Token expirado / 401 al consultar Resource Manager | PowerShell | Reautenticar el perfil de ese clon, conservar el stack, consultar `status` y retomar el mismo job |
| Ya hay un job activo | Resource Manager o `resource-manager.py status` | Esperar ese job. No ejecutar Plan/Apply duplicados |
| Apply falló pero algunos recursos existen | Mismo stack, logs privados | Corregir la causa y crear otro Plan en el mismo estado. No borrar compartments ni duplicar stack |
| Error de capacidad E5 | Job Apply de OCI | Revisar capacidad de la AD/shape. Si cambia la shape, seleccionar imagen compatible antes de replanificar |
| HTTPS aún sin certificado | SSH, LB, timer | Esperar bootstrap, comprobar `/healthz` y backends del LB. Corregir conectividad y revisar el error ACME |
| HTTPS devuelve 401 sin usuario | Navegador/PowerShell | Es correcto: falta autenticación básica. Usar la credencial web |
| Credencial rechazada | Vault `reversa-web` | Verificar versión CURRENT y que Nginx tenga aplicado ese valor; ver Operación |
| 502 al abrir OpenCode | SSH, salud 4096 | Revisar servicio OpenCode y su acceso a Vault |
| GenAI 401/403/404 | Prueba mínima y permisos OCI | Revisar clave, política, proyecto, región e ID del modelo |
| GenAI 429 | Cuotas/capacidad OCI | Esperar y revisar límites. Aumentar RAM de la VM no aumenta cuota de tokens |
| SSH no conecta | Ventana A y Bastion | Revisar IP /32 actual, sesión ACTIVE, clave y destino privado correcto |
| SSH rechaza permisos de clave Windows | PC, propiedades del archivo privado | Quitar acceso a otros usuarios en Seguridad y conservar acceso de su propietario; no publicar la clave |
| Reversa espera organización o `INICIAR` | Chat OpenCode | Responder la entrevista del flujo autónomo |
| No encuentro Markdown | Portal y carpeta del proyecto | Verificar que conversación y carga usan el mismo nombre y pedir relectura del archivo |
| HTML sin gráficos/3D | Visor del portal | Bloquea JavaScript. Revisar los archivos generados antes de atribuirlo al modelo |

Para ajustes persistentes de infraestructura, usa variables y Plan/Apply del
**mismo stack**. Los cambios manuales en OCI pueden producir diferencias con
Terraform en el próximo Plan. Los comandos anteriores son de diagnóstico, salvo
crear/cerrar la sesión temporal de Bastion.
