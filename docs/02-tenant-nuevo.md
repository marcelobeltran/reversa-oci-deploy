# 2. Instalar Reversa en OCI

[Inicio](../README.md) · [Primer uso](01-primer-uso.md) · [Alternativa PowerShell](02-tenant-nuevo-terminal.md)

Esta guía describe la instalación de Reversa en un tenant nuevo mediante
Resource Manager y Cloud Shell. Al finalizar tendrás una URL HTTPS para acceder
a la aplicación y cargar tu primer proyecto.

## Requisitos y lugares de trabajo

- Un tenant limpio y un usuario con permisos administrativos para red, IAM, VM,
  Vault, GenAI, Resource Manager y acceso a Cloud Shell.
- Chicago habilitada y capacidad/cuota para E5 Flex y Grok 4.6. La prueba del paso
  8 comprobará el acceso real al modelo.
- Un navegador y el ZIP de la publicación de este repositorio.

| Dónde | Para qué lo usarás |
| --- | --- |
| GitHub en el navegador | Descargar los ZIP ya construidos |
| Consola web OCI | Crear stack, revisar Plan, ejecutar Apply y ver recursos |
| Cloud Shell dentro de OCI | Dos acciones guiadas: preparar Vault/referencias y probar GenAI |
| Reversa en el navegador | Probar carga y análisis al terminar |

Cloud Shell es una terminal Linux en el navegador de OCI, autenticada con tu
sesión. Los comandos de preparación se ejecutan en esa terminal.

El asistente de Cloud Shell prepara los secretos en Vault y actualiza sus OCID
en el stack. Los planes y su aplicación se revisan y ejecutan en Resource Manager.

## Paso 1. Entrar al tenant correcto

**Dónde:** navegador, consola OCI.

1. Inicia sesión con el usuario administrador del tenant destino.
2. En **Tenancy details**, copia el OCID `ocid1.tenancy...` y anota su home region.
3. En el selector superior elige **US Midwest (Chicago), us-chicago-1**.

**Esperado:** tenant y región destino identificados. El OCID `ocid1.domain...`
no reemplaza el OCID del tenant. El despliegue crea recursos facturables.

## Paso 2. Descargar el ZIP listo para Resource Manager

**Dónde:** GitHub, en el navegador.

Abre [la última publicación](https://github.com/marcelobeltran/reversa-oci-deploy/releases/latest)
y, en **Assets**, descarga:

- [reversa-resource-manager.zip](https://github.com/marcelobeltran/reversa-oci-deploy/releases/latest/download/reversa-resource-manager.zip): infraestructura, runtime y asistente Cloud Shell.
- [reversa-prueba.zip](https://github.com/marcelobeltran/reversa-oci-deploy/releases/latest/download/reversa-prueba.zip): ejemplo para probar el portal al finalizar.
- `SHA256SUMS`, opcional, permite comprobar los archivos.

**Esperado:** ambos ZIP en Descargas. Utiliza `reversa-resource-manager.zip`
para el stack y conserva `reversa-prueba.zip` para la prueba del portal.
La opción Code > Download ZIP descarga el código fuente del repositorio; los
paquetes de instalación están en Assets de la publicación.

## Paso 3. Crear el stack sin Apply automático

**Dónde:** consola web OCI, Resource Manager > Stacks > Create stack.

1. Origen **My configuration**, tipo **Zip file**.
2. Sube `reversa-resource-manager.zip`, sin descomprimirlo en tu PC.
3. Nombre `reversa-stack`, compartment raíz del tenant.
4. Terraform: una versión ofrecida compatible con `>=1.5, <2.0`.
5. Completa únicamente estos valores de la base:

| Variable | Valor |
| --- | --- |
| `tenancy_ocid` | El OCID del paso 1 |
| `region` | `us-chicago-1` |
| `home_region` | La home region real del tenant |
| `prefix` | `reversa` |
| `enable_compute` | `false` |

6. Conserva las demás variables por defecto. No ingreses claves ni contraseñas.
7. En Review, **desmarca Run apply** y crea el stack.
8. Copia su OCID `ocid1.ormstack...`; lo pegarás en el asistente.

**Esperado:** stack ACTIVE sin VM. Conserva este mismo stack en todos los pasos.

## Paso 4. Crear la base antes de la VM

**Dónde:** detalle del stack en OCI.

1. Pulsa **Plan** y espera a que el job termine **SUCCEEDED**.
2. Revisa que agregue recursos, sin destrucciones y sin instancia
   `oci_core_instance.reversa`.
3. Pulsa **Apply**, selecciona el Plan exitoso anterior y espera **SUCCEEDED**.

**Esperado:** compartments `reversa-*`, VCN/subnets, gateways, NSG, LB e IP,
Vault/clave y proyecto GenAI. En Outputs, `phase` indica infraestructura sin VM.
El LB puede estar sin backends saludables en esta fase: todavía no existe servidor.

Si falla un job, revisa ese job en el mismo stack. No dupliques el stack ni
continúes a la siguiente fase. Si la vista Logs bloquea el navegador, vuelve a
la lista de jobs para consultar su estado y evita emitir un Apply duplicado.

## Paso 5. Abrir Cloud Shell y subir el mismo ZIP

**Dónde:** consola OCI, icono Cloud Shell/Code Editor en la barra superior.

1. Abre **Cloud Shell**, manteniendo Chicago seleccionada.
2. En su menú elige **Upload** y sube `reversa-resource-manager.zip` desde Descargas
   a tu directorio personal de Cloud Shell.
3. Ejecuta este bloque en **Cloud Shell**:

```bash
mkdir -p ~/reversa-tenant-01
cd ~/reversa-tenant-01
unzip -n ~/reversa-resource-manager.zip
python3 -c 'import oci; print("SDK OCI:", oci.__version__)'
```

**Esperado:** archivos `.tf`, `runtime.tar.gz`, carpeta `scripts/` y versión del SDK.
Si el archivo subido tiene otro nombre o está en otra carpeta, ajusta solo la ruta
que sigue a `unzip -n`. Para otro stack, usa **otra carpeta vacía**, por ejemplo
`~/reversa-tenant-02`. No copies `local/` entre carpetas.

Si el SDK falta o el asistente indica SDK antiguo, usa
[la solución de SDK/Python](#si-cloud-shell-no-tiene-el-sdk-necesario).

## Paso 6. Preparar credenciales y referencias con el asistente

**Dónde:** Cloud Shell, dentro de `~/reversa-tenant-01`.

```bash
python3 scripts/cloud-shell.py prepare
```

Pega **el OCID del stack del paso 3** cuando lo solicite. No introduzcas contraseñas.
El asistente utiliza la sesión autenticada de Cloud Shell.

**Qué hace:**

1. Comprueba tenant, región, último Apply correcto y ausencia de VM.
2. Crea la API key GenAI y los secretos `reversa-genai` y `reversa-web` en Vault.
3. Selecciona imagen Ubuntu/AD y crea una clave SSH administrativa en Cloud Shell.
4. Actualiza únicamente las referencias y la clave pública en el mismo stack.

**Esperado:** termina con `3/3 Referencias actualizadas...` y el siguiente paso.
No imprime secretos. No aplica Terraform ni habilita compute.

Los checkpoints quedan en `local/` dentro de esta carpeta de Cloud Shell. Si se
interrumpe, conserva la carpeta y vuelve a ejecutar el mismo comando. Sus guardas
rechazan otro tenant/stack, un job activo o una VM ya habilitada.

## Paso 7. Aplicar los permisos desde la consola

**Dónde:** Resource Manager, mismo stack en el navegador. Puedes minimizar Cloud Shell.

1. Actualiza la página y comprueba `enable_compute=false`.
2. En variables deben aparecer `genai_api_key_ocid`, `genai_secret_ocid`,
   `web_secret_ocid`, `image_ocid`, `availability_domain` y `ssh_public_key`.
3. Ejecuta **Plan**. Espera **SUCCEEDED** y revisa los cambios de IAM, sin VM ni
   destrucciones.
4. Ejecuta **Apply de ese Plan** y espera **SUCCEEDED**.

**Esperado:** permisos para leer los dos secretos y usar GenAI. Aún no hay VM.

## Paso 8. Comprobar GenAI desde Cloud Shell

**Dónde:** vuelve a Cloud Shell y a la misma carpeta.

```bash
python3 scripts/cloud-shell.py check
```

**Esperado:** JSON con `"success": true`, modelo `xai.grok-4.6`, y el siguiente
paso. Hace una inferencia pequeña real y puede generar consumo OCI.

Si falla inmediatamente después de IAM, espera su propagación y reintenta una
vez. Un 401/403/404 requiere revisar permisos, clave, proyecto o modelo; un 429,
cuotas. Si hay timeout, revisa también el modo de red de Cloud Shell. No crees
la VM hasta que la prueba funcione.

## Paso 9. Habilitar la VM desde Resource Manager

**Dónde:** consola OCI, mismo stack > Edit stack / variables.

1. Cambia **solo** `enable_compute` a `true` y guarda, sin Apply automático.
2. Ejecuta **Plan** y espera **SUCCEEDED**.
3. Revisa instancia privada y dos backends. En la referencia fueron 3 altas,
   0 cambios y 0 destrucciones. Si difiere, lee el Plan antes de aplicar.
4. Ejecuta **Apply de ese Plan** y espera **SUCCEEDED**.

**Esperado:** VM creada. No vuelvas a poner `enable_compute=false` sobre esta VM:
podría planificar su eliminación. La fase de preparación inicial ya terminó.

## Paso 10. Comprobar los recursos en OCI

**Dónde:** consola OCI.

| Dónde entrar | Qué comprobar |
| --- | --- |
| Compute > Instances, compartment `reversa-app` | `reversa-vm` RUNNING, subnet privada y sin IP pública |
| Load Balancers, compartment `reversa-network` | `reversa-lb` activo, IP reservada y backend sets 80/443 OK |
| Vault, compartment `reversa-security` | Secretos `reversa-web` y `reversa-genai` |
| Resource Manager > Outputs del último Apply | `url`, `public_ip`, `private_ip` e `instance_ocid` |

El bootstrap sigue trabajando dentro de Ubuntu después del Apply. Espera a que
los backends estén saludables. Si no avanzan, consulta diagnóstico; repetir
Apply no reinstala cloud-init.

## Paso 11. Conservar la clave de administración

**Dónde:** Cloud Shell, menú **Download**.

La clave privada está en `~/reversa-tenant-01/local/reversa-admin`, y la pública
termina en `.pub`. Puedes descargar una copia segura de la privada mediante ese
menú, indicando su ruta dentro de tu directorio personal. No la subas a GitHub.

La ruta básica no crea Bastion ni abre SSH público. La clave pública ya queda
en la VM para habilitar administración después. Si necesitas entrar, configura
`bastion_allowed_cidrs` con tu IP administrativa /32 en el mismo stack y aplica
su Plan antes de seguir [la guía de Bastion](03-administracion.md#paso-2-crear-una-sesión-temporal-de-bastion).

## Paso 12. Obtener la URL y las credenciales

**Dónde:** consola OCI, sin mostrar valores secretos en logs del stack.

1. En el último Apply de Resource Manager, copia el Output `url`.
2. En `reversa-security`, abre el secreto Vault `reversa-web` y su versión CURRENT.
3. Usa la opción para ver el contenido del secreto, un JSON con `username` y
   `password`. Si la consola lo presenta codificado, usa su opción de mostrarlo
   decodificado. Guárdalo en tu gestor de contraseñas.
4. En el navegador abre `https://IP_PUBLICA/proyectos/` e inicia sesión con esos valores.

**Esperado:** página **Proyectos**. La credencial GenAI es distinta y no sirve
para iniciar sesión en la web. No se publica ninguna contraseña en este repo.

## Paso 13. Verificar bootstrap y HTTPS

**Dónde:** navegador de tu PC y consola OCI.

- El navegador debe confiar en el certificado de la IP, sin omitir advertencias.
- Sin credenciales, HTTPS debe solicitar autenticación. Con ellas abre el portal.
- Abre OpenCode desde el portal: debe cargar y permitir una conversación.
- Ambos backends del LB deben estar OK.

**Esperado:** acceso HTTPS y aplicación operativa. Esto verifica externamente la
instalación, pero no certifica por sí solo que cloud-init terminó sin incidencias
ni que la renovación será correcta. Las comprobaciones internas y el dry-run del
certificado están en [Administración, paso 4](03-administracion.md#paso-4-comprobar-la-instalación-dentro-de-la-vm).
Se realizan por SSH cuando habilites la administración, no en Cloud Shell sin túnel.

El certificado inicial puede tardar por la propagación de health checks del LB;
el servicio tiene reintentos limitados. Ante un error persistente, consulta
[problemas frecuentes](03-administracion.md#problemas-frecuentes).

## Paso 14. Probar la aplicación

**Dónde:** navegador, [Primer uso](01-primer-uso.md).

Sube `reversa-prueba.zip`, descargado en el paso 2, crea un proyecto nuevo y
comprueba lectura/escritura real y Markdown visible. Luego, en Resource Manager,
ejecuta otro **Plan** manteniendo `enable_compute=true`.

**Esperado:** prueba funcional correcta y Plan `No changes`. No requiere otro
Apply cuando no hay cambios. No ejecutes Terraform local contra ese stack.

## Paso 15. Registrar la prueba

- [ ] Tenant, región y paquete identificados.
- [ ] Un solo stack con base e IAM antes de la VM.
- [ ] Asistente prepare completado sin imprimir secretos.
- [ ] GenAI check devuelve `success: true`.
- [ ] VM privada RUNNING y LB saludable.
- [ ] HTTPS confiable y acceso con la credencial Vault.
- [ ] Ejemplo ZIP y entregable Markdown verificados.
- [ ] Plan final sin cambios.
- [ ] Clave SSH y vencimiento de la API key guardados de forma segura.
- [ ] Comprobación interna y renovación verificadas, o registradas como pendientes si aún no habilitaste administración.

La base utiliza Reversa 1.3.4. La clave GenAI requiere rotación antes de 90 días;
consulta [Operación](operations.md).

## Si Cloud Shell no tiene el SDK necesario

**Dónde:** Cloud Shell. Primero mira `python3 --version`. El asistente requiere
Python 3.8 o superior y los modelos SDK de GenAI de OCI 2.191.0 o posterior.
Si falta Python compatible, `csruntimectl python list` muestra los runtimes de
OCI y `csruntimectl python set ALIAS` selecciona uno de esa lista.

Si debes actualizar solo el SDK, hazlo en un entorno aislado **dentro de OCI**:

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install oci==2.192.0
.venv/bin/python scripts/cloud-shell.py prepare
```

En ese caso usa también `.venv/bin/python scripts/cloud-shell.py check` en el
paso 8. El entorno mantiene la autenticación de Cloud Shell.

Para descargar paquetes PyPI puede ser necesario seleccionar **Public Network**
en Cloud Shell. Si no está permitido, el administrador debe habilitar el acceso
para el grupo correspondiente o proporcionar el SDK por la vía de la organización.

[Red de Cloud Shell](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cloudshellintro_topic-Cloud_Shell_Networking.htm).

## Si cierras Cloud Shell

Reábrelo en el mismo tenant/usuario/región y ejecuta `cd ~/reversa-tenant-01`.
Conserva `local/`: liga el checkpoint
al stack y evita duplicar credenciales. No uses `csreset -a` para retomar.
Si un job continúa activo, espera a que termine antes de ejecutar el asistente.

## Otras opciones de instalación

[Instalación desde PowerShell](02-tenant-nuevo-terminal.md): procedimiento para
administradores que ejecutan la preparación desde una estación Windows.
