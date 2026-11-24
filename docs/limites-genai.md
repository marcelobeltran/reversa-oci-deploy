# Solicitar ampliación de límites de OCI Generative AI

[Inicio](../README.md) · [Operación](operations.md) · [Administración](03-administracion.md)

## Límite definido para Reversa

| Campo | Valor |
| --- | --- |
| Servicio | Generative AI |
| Región | US Midwest (Chicago), `us-chicago-1` |
| Modelo | Grok 4.6 |
| Nombre del límite | `grok-4-6-tokens-per-minute-count` |
| Nuevo valor total a solicitar | **1.500.000 tokens por minuto (TPM)** |
| Ámbito | Regional |

El valor se propuso el **23 de octubre de 2026** al revisar una exportación de
sesión de OpenCode. El pico estimado fue de **879.486 tokens en una ventana de
60 segundos**, agrupando por inicio de solicitud, con cinco solicitudes. De ese
total, **859.136 tokens correspondían a caché**. La propuesta de 1.500.000 TPM
incorpora margen sobre ese pico. La exportación no demuestra cómo OCI contabiliza
la caché para aplicar la cuota; esa consulta forma parte de la justificación.

**Estado documental al 24 de noviembre de 2026:** propuesta y justificación
preparadas. El historial revisado no confirma el envío ni la aprobación de la
solicitud. El valor de esta página es el objetivo solicitado, no una cuota
aprobada ni una medición de la cuota actual del tenant destino.

Como antecedente, el 20 de octubre de 2026 (hora de Chile) se verificaron
**200.000 TPM para Grok 4.3**, límite `grok-4-3-tokens-per-minute-count`,
en Chicago. Es un límite distinto; no se registró un nuevo valor acordado para
Grok 4.3.

## Paso 1. Revisar el límite del tenant destino

**Dónde:** navegador, consola OCI.

1. Entra al tenant donde Reversa realiza las llamadas a Generative AI.
2. Selecciona **US Midwest (Chicago), `us-chicago-1`**.
3. Busca **Limits, Quotas and Usage** en la consola.
4. Filtra por servicio **Generative AI** y compartment raíz del tenant.
5. Busca `grok-4-6-tokens-per-minute-count` y registra el límite actual y el uso
   disponible que muestre la consola.

**Esperado:** límite del modelo y región correctos identificado. Las cuotas deben
revisarse en cada tenant; el valor histórico de otro modelo no determina el
límite de Grok 4.6.

## Paso 2. Crear la solicitud

**Dónde:** consola OCI, menú **Ayuda (`?`) → Request a limit increase**,
dentro de **Targeted help**.

1. En **General information**, usa un nombre como
   `Reversa - Grok 4.6 - 1500000 TPM - Chicago` y pega la justificación siguiente.
   Si el formulario solicita una suscripción, selecciona la correspondiente al
   despliegue. Pulsa **Next**.
2. En **Requested items**, pulsa **Add**.
3. Selecciona **Service: Generative AI** y el límite
   **`grok-4-6-tokens-per-minute-count`**.
4. Confirma **`us-chicago-1`** como región e introduce **`1500000`** como nuevo
   valor total del límite.
5. Pulsa **Add → Next**, revisa los datos y envía con **Submit**.

### Justificación para copiar

> Solicitamos aumentar a 1.500.000 tokens por minuto el límite
> grok-4-6-tokens-per-minute-count de Grok 4.6 en us-chicago-1 para análisis y
> documentación de código con Reversa y OpenCode. Una sesión registró un pico
> estimado de 879.486 tokens en una ventana móvil de 60 segundos, con cinco
> solicitudes; 859.136 tokens correspondían a entrada en caché. Necesitamos
> margen para los flujos de análisis y documentación. Solicitamos confirmar cómo
> se contabilizan los tokens en caché para esta cuota.

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

Ruta del formulario verificada en la documentación oficial el **24 de noviembre
de 2026**. Los datos de consumo y la propuesta proceden del historial del proyecto
Reversa, conversación «Retomar configuración de Reversa en», del 23 de octubre
de 2026.
