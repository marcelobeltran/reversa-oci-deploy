# 1. Primer uso: probar la aplicación instalada

[Inicio](../README.md) · [Instalar en otro tenant](02-tenant-nuevo.md)

**Objetivo:** cargar un proyecto, comprobar lectura/escritura y luego iniciar el
análisis. Esta ruta no cambia infraestructura.

## Antes de empezar

Necesitas la URL HTTPS y el usuario/contraseña de tu instalación. Los entrega
el administrador. Si acabas de instalar, salen del
[paso 12 de instalación](02-tenant-nuevo.md#paso-12-obtener-la-url-y-las-credenciales).
No se publican contraseñas en este repositorio.

| Lugar | Qué harás allí |
| --- | --- |
| GitHub en el navegador | Descargar el ZIP de ejemplo |
| Navegador, `https://TU_IP/proyectos/` | Cargar proyectos y consultar archivos |
| Navegador, `https://TU_IP/` | Abrir OpenCode y conversar con Reversa |

`TU_IP` es la IP pública reservada del balanceador de **tu** instalación.
No uses la IP privada de la VM ni añadas `:4096` o `:4100` a la URL.

## Paso 1. Preparar un ZIP de prueba

**Dónde:** GitHub, en el navegador. No necesitas instalar herramientas.

Descarga [reversa-prueba.zip](https://github.com/marcelobeltran/reversa-oci-deploy/releases/latest/download/reversa-prueba.zip)
desde **Assets** de [la publicación](https://github.com/marcelobeltran/reversa-oci-deploy/releases/latest).

**Resultado esperado:** el archivo en Descargas, con `README.md` y `calculadora.py`.
No lo descomprimas: el portal recibe el ZIP. No subas el ZIP de Resource Manager
como código de proyecto.

Si prefieres construirlo y ya tienes un clon, esta opción es **solo PowerShell
de tu PC**, desde la raíz del repositorio:

```powershell
Compress-Archive -Path .\examples\prueba-app\* -DestinationPath .\reversa-prueba.zip
```

Las fuentes están en [examples/prueba-app](../examples/prueba-app). Si ya existe
un ZIP con ese nombre, utiliza otro nombre en `-DestinationPath`.

## Paso 2. Entrar al portal

**Dónde:** navegador de tu PC.

1. Abre `https://TU_IP/proyectos/`.
2. Introduce el usuario y contraseña de la aplicación.

**Resultado esperado:** página **Proyectos**, con **Crear proyecto y cargar código**.
Si falla el certificado, no omitas su validación: ve a
[problemas frecuentes](03-administracion.md#problemas-frecuentes).

## Paso 3. Crear el proyecto

**Dónde:** página **Proyectos** del portal.

1. Abre **Crear proyecto y cargar código**.
2. Nombre: `reversa-prueba-01`.
3. Selecciona el ZIP del paso 1.
4. Pulsa **Crear y cargar proyecto**.

**Resultado esperado:** mensaje de proyecto creado y una entrada
`reversa-prueba-01`. El portal inicializa las habilidades y estado de Reversa.
Esto todavía **no ejecuta el análisis**.

Si ya existe, usa `reversa-prueba-02` y cambia el nombre en los siguientes pasos.
El portal evita sobrescribir otro proyecto.

## Paso 4. Abrir ese mismo proyecto en OpenCode

**Dónde:** navegador, OpenCode en `https://TU_IP/`.

1. Usa el enlace **OpenCode** del portal.
2. Abre/agrega la carpeta `/home/opc/proyectos/reversa-prueba-01`.
3. Crea una conversación dentro de ese proyecto.
4. Selecciona **Grok 4.6** del proveedor **Reversa OCI directo**, modelo probado
   con esta base.

**Resultado esperado:** conversas dentro del proyecto cargado, no en la carpeta
padre `/home/opc/proyectos`. El texto exacto del botón de apertura puede variar
con OpenCode. El catálogo visible no garantiza permiso/cuota para todos sus modelos.

## Paso 5. Comprobar lectura y escritura

**Dónde:** escribe este mensaje en el **chat de OpenCode** del proyecto:

```text
Prueba de instalación. Lee README.md y calculadora.py mediante herramientas.
Crea _reversa_sdd/prueba-instalacion.md con el propósito de la función sumar
y el resultado esperado de sumar(2, 3). Debe existir el archivo en disco.
No modifiques el código ni la configuración. Al terminar, informa su ruta.
```

**Resultado esperado:** llamadas reales de lectura/escritura y un documento que
indica el resultado **5**. Si pide un permiso, revisa que corresponda a esos
archivos y la escritura indicada. Esto verifica integración, no la calidad de
un análisis completo.

## Paso 6. Verificar el archivo fuera del chat

**Dónde:** portal, `https://TU_IP/proyectos/`.

1. Abre `reversa-prueba-01`.
2. Entra a **Análisis (Markdown)** y actualiza la vista.
3. Abre `prueba-instalacion.md`.

**Resultado esperado:** puedes leer el documento renderizado. Si falta, pide a
OpenCode releerlo y confirmar la ruta dentro del proyecto correcto. Un mensaje
en el chat no sustituye esta comprobación.

## Paso 7. Elegir cómo analizar

**Dónde:** chat de OpenCode, en el mismo proyecto.

| Escribe | Uso | Resultado esperado |
| --- | --- | --- |
| `/reversa` | Primera prueba guiada | Plan y decisiones entre etapas |
| `/reversa-autonomous` | Menos pausas | Entrevista inicial y señal de inicio |
| `/reversa-extract-soul` | Resumen del sistema | Propósito y entidades; requiere reconocimiento Scout |
| `/reversa-docs` | Mini sitio HTML | Usa el análisis existente y pide perfil/profundidad/estilo |
| `/reversa-migrate` | Preparar modernización | Comprueba artefactos e inicia entrevista |
| `/reversa-agents-help` | Catálogo de habilidades | Explica cada agente |

Empieza con **solo uno**: `/reversa` o `/reversa-autonomous`.

**Resultado esperado:** nombre correcto del proyecto y plan. Responde las opciones
de profundidad y organización de specs. En autónomo, escribe `INICIAR` **cuando
lo solicite**. Esperar esa respuesta forma parte de la preparación inicial.

## Paso 8. Comprobar el análisis

**Dónde:** portal, **Análisis (Markdown)** y **Todos los resultados**.

Consulta `_reversa_sdd/`. Los nombres y carpetas dependen de la organización
elegida. Comprueba que los documentos explican la función de ejemplo y citan
archivos reales. En el chat pide etapas terminadas y pendientes. Si se interrumpe,
vuelve al mismo proyecto y escribe `/reversa` para recuperar el estado.

**Resultado esperado:** entregables verificables. Una carpeta creada o un mensaje
de finalización no acreditan que terminaron todas las fases.

## Paso 9. Generar y consultar el HTML

**Dónde:** primero chat de OpenCode, después portal.

1. En el chat escribe `/reversa-docs`.
2. Elige perfil, profundidad y estilo cuando los solicite.
3. Responde `CONTINUAR` cuando corresponda y espera el resumen de páginas.
4. En el portal abre el proyecto y **Documentación (HTML)**.

**Resultado esperado:** archivos en `_reversa_docs/`, normalmente con `index.html`.
El visor del portal **bloquea JavaScript**: los gráficos interactivos y vistas 3D
pueden no funcionar allí. No significa automáticamente que falte análisis.
Esta guía no habilita scripts en el portal.

## Paso 10. Registrar tu prueba

- [ ] Entré por HTTPS con usuario y contraseña.
- [ ] Cargué el ZIP y apareció el proyecto.
- [ ] OpenCode leyó los dos archivos usando OCI.
- [ ] El Markdown de prueba existe y se ve en el portal.
- [ ] Reversa mostró el plan y respondí sus decisiones iniciales.
- [ ] Verifiqué entregables, si ejecuté el análisis completo.
- [ ] Identifiqué el límite del visor HTML, si generé el mini sitio.

**Siguiente paso:** cargar una copia de un proyecto real con otro nombre y repetir
desde el paso 3. Para problemas técnicos, ir a
[Administración](03-administracion.md#problemas-frecuentes).
