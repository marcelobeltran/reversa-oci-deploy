# Fuentes primarias consultadas

Consultadas el 17 noviembre 2026. Las políticas, disponibilidad y versiones pueden cambiar.

- [Reversa upstream, base auditada](https://github.com/sandeco/reversa/tree/524c64e5d8e11edd617f9207cd118bec8671b6ad)
- [OpenCode: proveedores personalizados](https://opencode.ai/docs/providers/#custom-provider)
- [OpenCode: servidor](https://opencode.ai/docs/server/)
- [OCI OpenAI-compatible endpoints](https://docs.oracle.com/en-us/iaas/Content/generative-ai/openai-compatible-api.htm)
- [API keys GenAI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/api-keys.htm)
- [Permisos de API key](https://docs.oracle.com/en-us/iaas/Content/generative-ai/add-api-permission.htm)
- [Grok 4.6 y límites](https://docs.oracle.com/en-us/iaas/Content/generative-ai/xai-grok-4-6.htm)
- [Terraform Load Balancer e IP reservada](https://docs.oracle.com/en-us/iaas/tools/terraform-provider-oci/latest/docs/r/load_balancer_load_balancer.html)
- [Certbot: certificados IP y perfil corto](https://letsencrypt.org/2026/03/11/shorter-certs-certbot)
- [Disponibilidad general de certificados IP](https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability)

Además se verificó el esquema del proveedor oficial oracle/oci 9.13.0 mediante
`terraform providers schema -json`, y los modelos CreateApiKeyDetails, KeyDetails,
ApiKey/ApiKeyItem del SDK Python OCI 2.191.0 publicado por Oracle.
