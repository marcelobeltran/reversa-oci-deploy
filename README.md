# Reversa en OCI: empieza aquí

Elige un recorrido antes de ejecutar comandos:

| Quiero… | Empiezo en… | Dónde trabajaré |
| --- | --- | --- |
| Probar Reversa que ya está instalado | [1. Primer uso](docs/01-primer-uso.md) | Navegador y chat de OpenCode |
| Instalarlo en un tenant nuevo | [2. Instalación paso a paso](docs/02-tenant-nuevo.md) | Windows PowerShell 7 y consola web OCI |
| Entrar a la VM o resolver un problema | [3. Administración](docs/03-administracion.md) | Consola OCI, PowerShell y SSH a Ubuntu |

**Si ya tienes la URL y quieres analizar un proyecto, comienza por
[Primer uso](docs/01-primer-uso.md). No necesitas instalar Terraform ni crear otra VM.**

## Cómo leer las instrucciones

Cada paso indica **dónde** trabajar, la **acción**, el **resultado esperado** y
qué revisar **si falla**. Ejecuta los pasos en orden y continúa únicamente cuando
obtengas el resultado indicado.

- `/reversa` y `/reversa-docs`: chat de OpenCode en el navegador.
- `python`, `git` y los scripts de instalación: PowerShell de tu PC.
- `sudo` y `systemctl`: dentro de la VM Ubuntu, después de entrar por SSH.

## Qué contiene este repositorio

Crea la red y seguridad antes de una VM Ubuntu privada. Un balanceador público
con IP reservada entrega HTTPS. OpenCode usa directamente OCI Generative AI.
El portal agregado permite cargar ZIP y consultar resultados. La base fija
Reversa **1.3.4** y OpenCode **1.19.0**.

La instalación recomendada utiliza **un stack de OCI Resource Manager**.
Terraform corre en OCI: para esa ruta no necesitas Terraform en tu PC.
No ejecutes `scripts/deploy.py` ni `terraform apply` local contra recursos de ese
stack, porque administrarías otro estado independiente.

## Orden de prueba

1. Aplicación existente: [crear el proyecto de ejemplo y probar lectura/escritura](docs/01-primer-uso.md#paso-1-preparar-un-zip-de-prueba).
2. Tenant limpio: completar [la instalación](docs/02-tenant-nuevo.md) hasta obtener URL y credenciales.
3. En ese tenant, repetir [Primer uso](docs/01-primer-uso.md).
4. Registrar el resultado con [la lista de aceptación](docs/02-tenant-nuevo.md#paso-15-registrar-la-prueba).

El despliegue crea recursos facturables OCI. Los comandos de esta guía se
contrastaron con los scripts. El registro cloud corresponde al **18/11/2026**,
no a una nueva instalación realizada al editar la documentación.

## Referencias, después del paso a paso

| Documento | Para qué sirve |
| --- | --- |
| [Arquitectura](docs/architecture.md) | Diagrama, versiones y componentes |
| [Operación](docs/operations.md) | Certificados, secretos, backups y actualización |
| [Problemas frecuentes](docs/03-administracion.md#problemas-frecuentes) | Diagnóstico según el error |
| [Aceptación del 18/11/2026](docs/acceptance.md) | Evidencia y límites de la instalación original |
| [Registro del despliegue](docs/deployment-status.md) | Historia técnica, no es el punto de partida |
| [Decisiones e historia](docs/history.md) | Motivos de la configuración |
| [Fuentes](docs/sources.md) | Referencias externas |

`local/` contiene referencias y credenciales privadas de **un solo tenant**.
No se publica en GitHub ni se incluye en el ZIP del stack. Para el tenant
siguiente, usa otro clon y repite la guía desde el principio.

Licencia: [MIT](LICENSE).
