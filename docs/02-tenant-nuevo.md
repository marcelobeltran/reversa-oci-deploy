# 2. Instalación paso a paso en un tenant nuevo

[Inicio](../README.md) · [Primer uso](01-primer-uso.md) · [Administración](03-administracion.md)

**Objetivo:** crear base, permisos y aplicación en ese orden. El resultado es una
URL HTTPS y credenciales para continuar con Primer uso.

Esta es una **primera instalación en un tenant limpio**, con un clon nuevo por
tenant. No ejecutes esta secuencia sobre la instalación existente: el paso que
fija `enable_compute=false` es únicamente anterior a la primera VM.

## Mapa del recorrido

| Pasos | Dónde | Resultado |
| --- | --- | --- |
| 1–4 | PC, PowerShell 7 | Herramientas, sesión OCI y ZIP |
| 5 | Navegador, consola OCI | Stack vacío, sin Apply automático |
| 6–7 | PC, PowerShell | Referencias y base creada sin VM |
| 8–10 | PC, PowerShell | Secretos, IAM y prueba real de GenAI |
| 11–12 | PC, PowerShell | VM, URL y credenciales |
| 13 | SSH a Ubuntu | Bootstrap, servicios y certificado verificados |
| 14–15 | Navegador y PC | Prueba funcional y registro |

Los comandos PowerShell se ejecutan **desde la carpeta que contiene README.md**.
Conserva la misma ventana para mantener `$Py`, `$Oci`, `$Region` y otras variables.
No pegues bloques PowerShell en Cloud Shell, en el chat de OpenCode o en Ubuntu.

## Paso 1. Comprobar los requisitos

**Dónde:** PowerShell **7** en tu PC Windows.

```powershell
$PSVersionTable.PSVersion
git --version
py -3.12 --version
ssh -V
```

**Resultado esperado:** PowerShell 7.x, Git, Python 3.12 y OpenSSH disponibles.
Si falta alguno, instálalo antes de seguir:

- [PowerShell para Windows](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows): instalar PowerShell 7 y abrir esa aplicación, no Windows PowerShell 5.1.
- [Git para Windows](https://git-scm.com/downloads/win): instalar y volver a abrir la terminal.
- [Python para Windows](https://www.python.org/downloads/windows/): elegir Python 3.12 con su launcher `py`.
- [OpenSSH de Windows](https://learn.microsoft.com/windows-server/administration/openssh/openssh_install_firstuse): habilitar el cliente OpenSSH si no está disponible.

Vuelve a ejecutar las cuatro comprobaciones. No necesitas Terraform local para
esta ruta: Resource Manager lo ejecutará en OCI.

También necesitas acceso administrativo al **tenant destino**, permisos para
crear compartimentos/IAM, red, LB, VM, Vault y GenAI, y capacidad/cuota para esos
servicios. La base usa Chicago, E5 Flex y Grok 4.6. La prueba real del paso 10
confirmará el acceso al modelo. Cambiar de región/modelo exige revisar su
disponibilidad y los parámetros, no reutilizar OCID de Chicago.

## Paso 2. Crear un clon y las herramientas de ese tenant

**Dónde:** PowerShell de tu PC. Cambia `tenant-01` por otro nombre para cada tenant.

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\Documents\Reversa-tenants" | Out-Null
Set-Location "$env:USERPROFILE\Documents\Reversa-tenants"
git clone https://github.com/marcelobeltran/reversa-oci-deploy.git tenant-01
Set-Location .\tenant-01
py -3.12 -m venv .venv
$Py = (Resolve-Path .\.venv\Scripts\python.exe).Path
& $Py -m pip install oci-cli==3.96.3
$Oci = (Resolve-Path .\.venv\Scripts\oci.exe).Path
New-Item -ItemType Directory -Force .\local\oci | Out-Null
& $Oci --version
```

**Resultado esperado:** clon nuevo, carpeta `.venv`, carpeta `local` y CLI 3.96.3.
El SDK OCI viene como dependencia de la CLI. No copies `local/`, claves ni estados
Terraform desde otro tenant. Si ya existe `tenant-01`, elige otra carpeta para
una primera instalación o retoma el clon correcto, sin recrearlo.

## Paso 3. Identificar el tenant e iniciar sesión

**Dónde:** primero navegador en la consola OCI, después PowerShell.

1. En OCI, abre **Tenancy details / Detalles de arrendamiento**, copia su OCID y
   comprueba la **home region**. El OCID empieza por `ocid1.tenancy`, no por
   `ocid1.domain`.
2. Vuelve a PowerShell:

```powershell
$Tenancy = Read-Host 'OCID del tenant DESTINO (ocid1.tenancy...)'
$HomeRegion = Read-Host 'Home region del tenant (ejemplo us-chicago-1)'
$Region = 'us-chicago-1'
$Config = Join-Path (Resolve-Path .\local\oci).Path 'config'
$Sessions = Join-Path (Resolve-Path .\local\oci).Path 'sessions'
& $Oci session authenticate --region $Region --profile-name REVERSA --config-location $Config --token-location $Sessions --session-expiration-in-minutes 60
```

3. Completa usuario, contraseña y MFA en el navegador que abre la CLI, eligiendo
   **ese tenant**. No envíes las credenciales al chat.

**Resultado esperado:** la terminal confirma la autenticación y crea
`local/oci/config`, perfil `REVERSA`. El navegador por sí solo no basta.
No continúes si aparece `invalid state` o no se crea el perfil: ve a
[problemas frecuentes](03-administracion.md#problemas-frecuentes).

La sesión dura hasta 60 minutos. Si expira, repite la autenticación y elige
sobrescribir únicamente el perfil `REVERSA` de **este clon**. Conserva el resto
de `local/`, el stack y sus jobs.

## Paso 4. Generar el paquete para OCI

**Dónde:** PowerShell, raíz del clon.

```powershell
& $Py scripts/package.py
Get-Item .\reversa-resource-manager.zip
```

**Resultado esperado:** ZIP no vacío y un resumen con `stack_bytes` y
`stack_sha256`. El ZIP contiene Terraform y runtime, no `local/` ni claves.
No es el ZIP de código que se sube al portal de proyectos.

## Paso 5. Crear el stack, todavía sin desplegar

**Dónde:** navegador, consola OCI del tenant destino, región **Chicago**.

1. Busca **Resource Manager**, abre **Stacks** y pulsa **Create stack**.
2. Origen: **My configuration**, tipo **Zip file**. Sube el ZIP del paso 4.
3. Nombre: `reversa-stack`. Guarda el stack en el compartment raíz del tenant,
   porque los compartments de Reversa todavía no existen.
4. Elige una versión Terraform ofrecida por OCI compatible con `>=1.5, <2.0`.
5. En variables, completa esta tabla. Deja las demás con sus valores base:

| Variable | Qué ingresar |
| --- | --- |
| `tenancy_ocid` | El OCID del paso 3 |
| `region` | `us-chicago-1` |
| `home_region` | La home region real del paso 3 |
| `prefix` | `reversa` |
| `enable_compute` | `false` |

6. Revisa y **desmarca Run apply** si está seleccionado.
7. Crea el stack y copia su OCID, que empieza por `ocid1.ormstack`.

**Resultado esperado:** stack `ACTIVE`, sin job Apply. No existe VM todavía.
No ingreses contraseñas ni el valor de una API key en variables Terraform.
Referencia: [crear un stack desde ZIP](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Tasks/create-stack-local.htm).

## Paso 6. Vincular los scripts a ese mismo stack

**Dónde:** PowerShell, raíz del clon.

```powershell
$Stack = Read-Host 'OCID del stack creado (ocid1.ormstack...)'
$refs = @{ tenancy_ocid = $Tenancy; region = $Region; stack_ocid = $Stack }
$refs | ConvertTo-Json | Set-Content -Encoding utf8 .\local\deployment.private.json
& $Py scripts/resource-manager.py status
```

**Resultado esperado:** `[]` si el stack no tiene jobs. Si indica tenant incorrecto,
detente y corrige la sesión o las referencias. Este script verifica también el
`tenancy_ocid` de las variables del stack.

## Paso 7. Aplicar la base sin VM

**Dónde:** PowerShell. Ejecuta un comando a la vez y espera su resultado.

```powershell
& $Py scripts/resource-manager.py plan --wait
```

**Esperado:** termina `SUCCEEDED`. Entonces revisa el resumen:

```powershell
& $Py scripts/resource-manager.py logs
```

**Esperado:** altas de recursos, **cero destrucciones** y ninguna instancia
`oci_core_instance.reversa` en el plan. El log completo queda en
`local/reversa-plan.private.log`; puedes abrirlo con un editor local.
Si no coincide, detente antes de Apply.

```powershell
& $Py scripts/resource-manager.py apply --wait
```

**Esperado:** `SUCCEEDED`. Exporta las salidas:

```powershell
& $Py scripts/resource-manager.py outputs
$out = Get-Content .\local\outputs.json -Raw | ConvertFrom-Json
$out.phase.value
```

**Resultado esperado:** texto que indica infraestructura **sin VM**. En OCI ya
existen compartments, VCN/subnets, gateways, NSG, LB/IP, Vault y proyecto GenAI.
Es normal que el LB no tenga backends operativos antes de crear la VM.

## Paso 8. Crear las credenciales en Vault

**Dónde:** PowerShell, mismo clon y sesión.

```powershell
& $Py scripts/prepare-runtime.py --outputs local/outputs.json --config $Config --profile REVERSA --auth security_token --region $Region --prefix reversa
```

**Resultado esperado:** mensaje de credenciales guardadas en Vault y estos archivos:

| Archivo local | Contenido |
| --- | --- |
| `local/runtime.auto.tfvars.json` | OCID, imagen y AD; no contraseñas |
| `local/runtime.private.json` | Checkpoint privado con valores secretos |

No publiques el segundo archivo. Si el proceso falla, conserva ambos y reintenta
sobre el mismo clon. No crees otra clave manualmente ni borres el checkpoint.
Las API keys GenAI de esta base vencen a los 90 días.

## Paso 9. Preparar SSH/Bastion y aplicar permisos

**Dónde:** PowerShell. Este paso es anterior a la primera VM.

```powershell
ssh-keygen -t ed25519 -f .\local\reversa-admin -C reversa-admin
```

**Esperado:** clave privada `local/reversa-admin` y pública `.pub`. Responde las
preguntas de passphrase. No reemplaces una clave existente: para retomar, usa la
que corresponde a este tenant y omite su generación.

Ahora configura el acceso administrativo. La consulta a ipify obtiene únicamente
la IP pública de esta conexión; no es una llamada al modelo:

```powershell
$AdminIP = (Invoke-RestMethod 'https://api.ipify.org').Trim()
$runtime = Get-Content .\local\runtime.auto.tfvars.json -Raw | ConvertFrom-Json
$runtime | Add-Member -Force NoteProperty ssh_public_key ((Get-Content .\local\reversa-admin.pub -Raw).Trim())
$runtime | Add-Member -Force NoteProperty bastion_allowed_cidrs @("$AdminIP/32")
$runtime | Add-Member -Force NoteProperty enable_compute $false
$runtime | ConvertTo-Json -Depth 10 | Set-Content -Encoding utf8 .\local\runtime.auto.tfvars.json
& $Py scripts/resource-manager.py sync-source --variables local/runtime.auto.tfvars.json
```

**Esperado:** código/variables actualizados **sin ejecutar Apply**. Planifica:

```powershell
& $Py scripts/resource-manager.py plan --wait
& $Py scripts/resource-manager.py logs
```

**Esperado:** `SUCCEEDED`, sin destrucciones y sin VM. Debe agregar políticas y
Bastion/acceso SSH. Solo después:

```powershell
& $Py scripts/resource-manager.py apply --wait
```

**Resultado esperado:** `SUCCEEDED`. IAM y Bastion existen antes de la VM.
Si cambia tu IP por VPN/conexión, tendrás que actualizar el `/32` por el mismo
stack. El acceso web no usa ese túnel.

## Paso 10. Comprobar GenAI antes de crear la VM

**Dónde:** PowerShell. Hace una inferencia pequeña real, con consumo OCI.

```powershell
& $Py scripts/smoke-genai.py --region $Region --model xai.grok-4.6
```

**Resultado esperado:** JSON con `"success": true` y modelo `xai.grok-4.6`.
Si falla tras aplicar IAM, espera la propagación y vuelve a probar una vez.
Un 401/403/404 requiere revisar credencial, permiso/proyecto o modelo; un 429,
cuota/capacidad. No continúes a la VM hasta que funcione.

## Paso 11. Habilitar y crear la VM privada

**Dónde:** PowerShell.

```powershell
$runtime = Get-Content .\local\runtime.auto.tfvars.json -Raw | ConvertFrom-Json
$runtime.enable_compute = $true
$runtime | ConvertTo-Json -Depth 10 | Set-Content -Encoding utf8 .\local\runtime.auto.tfvars.json
& $Py scripts/resource-manager.py sync-source --variables local/runtime.auto.tfvars.json
& $Py scripts/resource-manager.py plan --wait
& $Py scripts/resource-manager.py logs
```

**Esperado:** plan exitoso de la instancia y los dos backends del LB, sin
destrucciones. En la instalación de referencia fueron **3 altas, 0 cambios,
0 destrucciones**. Una diferencia exige leer el plan antes de aplicarlo.

```powershell
& $Py scripts/resource-manager.py apply --wait
```

**Resultado esperado:** `SUCCEEDED`. Eso confirma infraestructura, no todavía
que cloud-init, la aplicación o el certificado hayan terminado.

## Paso 12. Obtener la URL y las credenciales

**Dónde:** PowerShell, solo en tu PC privado.

```powershell
& $Py scripts/resource-manager.py outputs
$out = Get-Content .\local\outputs.json -Raw | ConvertFrom-Json
$out.url.value
$out.private_ip.value
```

**Esperado:** URL `https://IP_PUBLICA/` y una IP privada distinta para SSH.
Para ver la credencial web generada, **sin mostrar la clave GenAI**:

```powershell
(Get-Content .\local\runtime.private.json -Raw | ConvertFrom-Json).web
```

**Esperado:** `username` y `password`. Guárdalos en tu gestor de contraseñas.
También están en OCI Vault, secreto `reversa-web` del compartment
`reversa-security`, versión `CURRENT`. No copies los valores a GitHub.

## Paso 13. Verificar bootstrap y HTTPS

**Dónde:** sigue [Administración, pasos 1–4](03-administracion.md#paso-1-identificar-la-vm-y-la-clave),
que te lleva desde PowerShell hasta una terminal SSH en Ubuntu.

**Esperado:** `cloud-init` termina, los tres servicios están activos y el certificado
es válido. Después, **en PowerShell de tu PC**, no en Ubuntu:

```powershell
$out = Get-Content .\local\outputs.json -Raw | ConvertFrom-Json
curl.exe --head $out.url.value
curl.exe "http://$($out.public_ip.value)/"
```

**Resultado esperado:** HTTPS devuelve **401** sin credenciales y valida el
certificado; HTTP raíz devuelve **404**. Son respuestas previstas. No uses `-k`
para omitir errores de certificado. Si aún no responde, revisa bootstrap y la
salud del LB, en lugar de repetir Apply o crear otra VM.

## Paso 14. Probar la aplicación e idempotencia

**Dónde:** navegador, siguiendo [Primer uso](01-primer-uso.md) desde el paso 1,
con la URL y credenciales del paso 12.

**Esperado:** carga del ZIP, lectura/escritura con OCI y Markdown visible.
Después, en **PowerShell**, con `enable_compute=true` conservado:

```powershell
& $Py scripts/resource-manager.py plan --wait
& $Py scripts/resource-manager.py logs
```

**Resultado esperado:** `No changes`. No hace falta Apply para un plan sin cambios.
No vuelvas a ejecutar la primera fase con `enable_compute=false` sobre esta VM.

## Paso 15. Registrar la prueba

Guarda este registro en tu documentación privada. No publiques identificadores o
direcciones de acceso en una incidencia pública junto con credenciales.

- [ ] Tenant y región comprobados; clon exclusivo para ese tenant.
- [ ] Un único stack y estado, sin Terraform Apply local.
- [ ] Base y políticas creadas antes de la VM.
- [ ] Inferencia mínima real `success: true` antes de habilitar compute.
- [ ] VM en subnet privada, sin IP pública en sus VNIC.
- [ ] Backends 80/443 del LB saludables.
- [ ] cloud-init terminado y servicios activos.
- [ ] HTTPS confiable y prueba de renovación correcta.
- [ ] ZIP de ejemplo y Markdown de lectura/escritura verificados.
- [ ] Plan final `No changes`.
- [ ] Copia segura de la clave SSH y fecha de rotación de la clave GenAI registradas.

**Siguiente paso:** [operación y mantenimiento](operations.md).
La evidencia histórica de otra ejecución está en [acceptance.md](acceptance.md);
tu nueva instalación debe producir su propio registro.

## Si cierras PowerShell y necesitas retomar

Si todavía no llegaste al paso 6, recupera las variables repitiendo el paso 3 y
continúa donde quedaste, conservando el stack si ya lo creaste. El bloque siguiente
supone que `local/deployment.private.json` ya existe.

Abre PowerShell 7, entra al **mismo clon**, y recupera las variables:

```powershell
Set-Location "$env:USERPROFILE\Documents\Reversa-tenants\tenant-01"
$Py = (Resolve-Path .\.venv\Scripts\python.exe).Path
$Oci = (Resolve-Path .\.venv\Scripts\oci.exe).Path
$Config = Join-Path (Resolve-Path .\local\oci).Path 'config'
$Sessions = Join-Path (Resolve-Path .\local\oci).Path 'sessions'
$Region = 'us-chicago-1'
& $Py scripts/resource-manager.py status
```

Si el token expiró, repite la autenticación del paso 3 con esas rutas. Consulta
el estado del job existente antes de emitir otro. No borres `local/`, no crees
otro stack y no repitas una fase ya aplicada por no haber visto la pantalla final.
