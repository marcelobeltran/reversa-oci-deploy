# Reversa en OCI: empieza aquí

Elige un recorrido antes de ejecutar comandos:

| Quiero… | Empiezo en… | Dónde trabajaré |
| --- | --- | --- |
| Probar Reversa que ya está instalado | [1. Primer uso](docs/01-primer-uso.md) | Navegador y chat de OpenCode |
| Instalarlo en un tenant nuevo | [2. Instalación paso a paso](docs/02-tenant-nuevo.md) | Navegador, consola OCI y Cloud Shell |
| Entrar a la VM o resolver un problema | [3. Administración](docs/03-administracion.md) | Consola OCI, PowerShell y SSH a Ubuntu |

**Si ya tienes la URL y quieres analizar un proyecto, comienza por
[Primer uso](docs/01-primer-uso.md).**

## Cómo leer las instrucciones

Cada paso indica **dónde** trabajar, la **acción**, el **resultado esperado** y
qué revisar **si falla**. Ejecuta los pasos en orden y continúa únicamente cuando
obtengas el resultado indicado.

- `/reversa` y `/reversa-docs`: chat de OpenCode en el navegador.
- `python3 scripts/cloud-shell.py`: Cloud Shell dentro del navegador OCI.
- PowerShell local: solo si eliges la ruta alternativa.
- `sudo` y `systemctl`: dentro de la VM Ubuntu, después de entrar por SSH.

## Descargar los paquetes listos

En [Releases](https://github.com/marcelobeltran/reversa-oci-deploy/releases/latest),
sección **Assets**:

- [ZIP para Resource Manager](https://github.com/marcelobeltran/reversa-oci-deploy/releases/latest/download/reversa-resource-manager.zip).
- [ZIP de ejemplo para el portal](https://github.com/marcelobeltran/reversa-oci-deploy/releases/latest/download/reversa-prueba.zip).

Descarga los paquetes desde Assets de la publicación y sigue
[la guía de instalación](docs/02-tenant-nuevo.md). La preparación se ejecuta en
Cloud Shell y el despliegue se administra en Resource Manager.

## Qué contiene este repositorio

Crea la red y seguridad antes de una VM Ubuntu privada. Un balanceador público
con IP reservada entrega HTTPS. OpenCode usa directamente OCI Generative AI.
El portal agregado permite cargar ZIP y consultar resultados. La base fija
Reversa **1.3.4** y OpenCode **1.19.0**.

La instalación recomendada utiliza **un stack de OCI Resource Manager**.
Resource Manager ejecuta Terraform y conserva el estado de la infraestructura.
No ejecutes `scripts/deploy.py` ni `terraform apply` local contra recursos de ese
stack, porque administrarías otro estado independiente.

## Orden de prueba

1. Aplicación existente: [crear el proyecto de ejemplo y probar lectura/escritura](docs/01-primer-uso.md#paso-1-preparar-un-zip-de-prueba).
2. Tenant limpio: completar [la instalación](docs/02-tenant-nuevo.md) hasta obtener URL y credenciales.
3. En ese tenant, repetir [Primer uso](docs/01-primer-uso.md).
4. Registrar el resultado con [la lista de aceptación](docs/02-tenant-nuevo.md#paso-15-registrar-la-prueba).

El despliegue crea recursos facturables OCI. Consulta el
[registro de aceptación](docs/acceptance.md) para conocer las comprobaciones
y el alcance de la instalación de referencia.

## Referencias, después del paso a paso

| Documento | Para qué sirve |
| --- | --- |
| [Arquitectura](docs/architecture.md) | Diagrama, versiones y componentes |
| [Operación](docs/operations.md) | Certificados, secretos, backups y actualización |
| [Límites de Generative AI](docs/limites-genai.md) | Revisar errores 429 y solicitar ampliación; valor sugerido: 5.000.000 TPM |
| [Problemas frecuentes](docs/03-administracion.md#problemas-frecuentes) | Diagnóstico según el error |
| [Aceptación del 18/11/2026](docs/acceptance.md) | Evidencia y límites de la instalación original |
| [Registro del despliegue](docs/deployment-status.md) | Historia técnica, no es el punto de partida |
| [Decisiones e historia](docs/history.md) | Motivos de la configuración |
| [Fuentes](docs/sources.md) | Referencias externas |

`local/` contiene referencias y credenciales privadas de **un solo tenant**.
No se publica en GitHub ni se incluye en el ZIP del stack. En la ruta recomendada
está dentro de tu carpeta de Cloud Shell. Para el tenant/stack siguiente, extrae
el paquete en otra carpeta vacía. La [ruta PowerShell local](docs/02-tenant-nuevo-terminal.md)
es opcional y mantiene un clon independiente por tenant.

Licencia: [MIT](LICENSE).
