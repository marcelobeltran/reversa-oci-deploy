# Solicitar ampliación de límites de OCI Generative AI

[Inicio](../README.md) · [Operación](operations.md) · [Administración](03-administracion.md)

Si Reversa recibe un **HTTP 429** de OCI Generative AI con un mensaje que indica
que se alcanzó el límite de tokens del modelo, revisa la cuota y sigue estos pasos
para solicitar una ampliación cuando resulte insuficiente.

## Límite sugerido

| Campo | Valor |
| --- | --- |
| Servicio | Generative AI |
| Región | US Midwest (Chicago), `us-chicago-1` |
| Modelo | Grok 4.6 |
| Nombre del límite | `grok-4-6-tokens-per-minute-count` |
| Nuevo valor total sugerido | **5.000.000 tokens por minuto (TPM)** |
| Ámbito | Regional |

**5.000.000 TPM es un valor sugerido.** Ajusta la solicitud según el consumo y
la concurrencia previstos para tu instalación. La aprobación depende de OCI.

## Paso 1. Revisar el límite del tenant destino

**Dónde:** navegador, consola OCI.

1. Entra al tenant donde Reversa realiza las llamadas a Generative AI.
2. Selecciona **US Midwest (Chicago), `us-chicago-1`**.
3. Busca **Limits, Quotas and Usage** en la consola.
4. Filtra por servicio **Generative AI** y compartment raíz del tenant.
5. Busca `grok-4-6-tokens-per-minute-count` y registra el límite actual y el uso
   disponible que muestre la consola.

**Esperado:** límite del modelo y región correctos identificado. Las cuotas deben
revisarse en cada tenant, para el modelo y la región utilizados por la instalación.

## Paso 2. Crear la solicitud

**Dónde:** consola OCI, menú **Ayuda (`?`) → Request a limit increase**,
dentro de **Targeted help**.

1. En **General information**, usa un nombre como
   `Reversa - Grok 4.6 - 5000000 TPM - Chicago` y pega la justificación siguiente.
   Si el formulario solicita una suscripción, selecciona la correspondiente al
   despliegue. Pulsa **Next**.
2. En **Requested items**, pulsa **Add**.
3. Selecciona **Service: Generative AI** y el límite
   **`grok-4-6-tokens-per-minute-count`**.
4. Confirma **`us-chicago-1`** como región e introduce **`5000000`** como nuevo
   valor total sugerido del límite, o el valor que requiera tu instalación.
5. Pulsa **Add → Next**, revisa los datos y envía con **Submit**.

### Justificación para copiar

> Solicitamos aumentar a 5.000.000 tokens por minuto el límite
> grok-4-6-tokens-per-minute-count de Grok 4.6 en us-chicago-1 para análisis y
> documentación de código con Reversa y OpenCode. Estos flujos envían contexto
> de código y documentación en solicitudes sucesivas y requieren capacidad
> suficiente para el volumen de trabajo y la concurrencia previstos.
> Solicitamos confirmar cómo se contabilizan los tokens en caché para esta cuota.

**Esperado:** página de detalle de la solicitud con estado **In Progress**.
Guarda el identificador o enlace y la fecha de envío. El envío no equivale a la
aprobación.

## Paso 3. Registrar la resolución y comprobar

1. Consulta el detalle de la solicitud y cualquier requerimiento adicional de
   Oracle.
2. Cuando se apruebe, vuelve a **Limits, Quotas and Usage** y comprueba el valor
   efectivo de Grok 4.6 en Chicago.
3. Ejecuta una prueba de inferencia y luego el análisis habitual de Reversa.
4. Registra la fecha, estado y valor efectivamente aprobado en el registro
   operativo privado del tenant, junto con el identificador de solicitud.

Un HTTP 429 también puede relacionarse con limitación dinámica de capacidad.
Revisa el mensaje y conserva los reintentos con espera progresiva; la ampliación
de TPM no garantiza eliminar todos los rechazos. Aumentar la RAM de la VM no
amplía la cuota de Generative AI.

## Referencias

- [OCI: crear una solicitud de aumento de límite](https://docs.oracle.com/en-us/iaas/Content/General/service-limits/create-request.htm).
- [OCI: Grok 4.6 y límites](https://docs.oracle.com/en-us/iaas/Content/generative-ai/xai-grok-4-6.htm).
- [OCI: limitación dinámica](https://docs.oracle.com/en-us/iaas/Content/generative-ai/dynamic-throttling.htm).
