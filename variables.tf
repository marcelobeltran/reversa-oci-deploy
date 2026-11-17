variable "tenancy_ocid" {
  type        = string
  description = "OCID del tenant destino. No es el OCID de identity domain."
}
variable "region" {
  type    = string
  default = "us-chicago-1"
}
variable "home_region" {
  type        = string
  description = "Home region real del tenant para IAM."
}
variable "prefix" {
  type    = string
  default = "reversa"
  validation {
    condition     = can(regex("^reversa[a-z0-9-]*$", var.prefix)) && length(var.prefix) <= 30
    error_message = "El prefijo debe empezar por reversa, máximo 30 caracteres."
  }
}
variable "enable_compute" {
  type        = bool
  default     = false
  description = "Primera aplicación false: crea toda la base antes de la VM."
}
variable "vcn_cidr" {
  type    = string
  default = "10.80.0.0/16"
}
variable "public_cidr" {
  type    = string
  default = "10.80.0.0/24"
}
variable "private_cidr" {
  type    = string
  default = "10.80.10.0/24"
}
variable "web_allowed_cidrs" {
  type        = list(string)
  default     = ["0.0.0.0/0"]
  description = "Origen HTTPS. HTTP 80 queda público solo para ACME/health."
}
variable "bastion_allowed_cidrs" {
  type        = list(string)
  default     = []
  description = "CIDR /32 de administradores. Vacío: no crea Bastion ni abre SSH."
  validation {
    condition     = alltrue([for c in var.bastion_allowed_cidrs : can(cidrnetmask(c)) && c != "0.0.0.0/0"])
    error_message = "Usar CIDR IPv4 específicos; SSH administrativo no admite 0.0.0.0/0."
  }
}
variable "ssh_public_key" {
  type    = string
  default = ""
}
variable "image_ocid" {
  type        = string
  default     = ""
  description = "Imagen Ubuntu 24.04 x86_64 de la región, verificada con la shape."
}
variable "availability_domain" {
  type    = string
  default = ""
}
variable "shape" {
  type    = string
  default = "VM.Standard.E5.Flex"
}
variable "ocpus" {
  type    = number
  default = 2
}
variable "memory_gbs" {
  type    = number
  default = 16
}
variable "boot_volume_gbs" {
  type    = number
  default = 100
}
variable "genai_api_key_ocid" {
  type        = string
  default     = ""
  description = "OCID de la API key GenAI; nunca el secreto sk-."
}
variable "genai_secret_ocid" {
  type        = string
  default     = ""
  description = "Vault Secret cuyo contenido es la API key GenAI de este tenant."
}
variable "web_secret_ocid" {
  type        = string
  default     = ""
  description = "Vault Secret JSON: username, password. Nunca ingresar valores secretos en Terraform."
}
variable "model_id" {
  type    = string
  default = "xai.grok-4.6"
}
variable "model_context" {
  type    = number
  default = 1000000
}
variable "model_output" {
  type    = number
  default = 16384
}
variable "opencode_version" {
  type        = string
  default     = "1.19.0"
  description = "Versión observada en el proyecto anterior; validar antes de cambiar."
}
variable "certbot_version" {
  type    = string
  default = "5.4.0"
}
