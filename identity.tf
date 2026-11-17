resource "oci_identity_compartment" "reversa" {
  provider       = oci.home
  compartment_id = var.tenancy_ocid
  name           = var.prefix
  description    = "Reversa: instalación reproducible"
  enable_delete  = false
}
resource "oci_identity_compartment" "area" {
  provider       = oci.home
  for_each       = toset(["network", "app", "security", "ai", "operations"])
  compartment_id = oci_identity_compartment.reversa.id
  name           = "${var.prefix}-${each.key}"
  description    = "Reversa ${each.key}"
  enable_delete  = false
}
resource "oci_identity_dynamic_group" "vm" {
  provider       = oci.home
  compartment_id = var.tenancy_ocid
  name           = "${var.prefix}-vm"
  description    = "Solo instancias del compartimento de aplicación Reversa"
  matching_rule  = "ALL {instance.compartment.id = '${oci_identity_compartment.area["app"].id}'}"
}
resource "oci_identity_policy" "secrets" {
  provider       = oci.home
  count          = var.genai_secret_ocid != "" && var.web_secret_ocid != "" ? 1 : 0
  compartment_id = oci_identity_compartment.reversa.id
  name           = "${var.prefix}-read-runtime-secrets"
  description    = "La VM puede leer únicamente sus dos secretos"
  statements = [for id in [var.genai_secret_ocid, var.web_secret_ocid] :
    "Allow dynamic-group ${oci_identity_dynamic_group.vm.name} to read secret-bundles in compartment id ${oci_identity_compartment.area["security"].id} where target.secret.id = '${id}'"
  ]
}
resource "oci_identity_policy" "genai" {
  provider       = oci.home
  count          = var.genai_api_key_ocid != "" ? 1 : 0
  compartment_id = oci_identity_compartment.reversa.id
  name           = "${var.prefix}-genai-chat"
  description    = "Chat directo con API key GenAI específica de Reversa"
  statements = [
    "Allow any-user to use generative-ai-chat in compartment id ${oci_identity_compartment.area["ai"].id} where all {request.principal.type='generativeaiapikey', request.principal.id='${var.genai_api_key_ocid}'}"
  ]
}
