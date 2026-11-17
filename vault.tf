resource "oci_kms_vault" "reversa" {
  compartment_id = oci_identity_compartment.area["security"].id
  display_name   = "${var.prefix}-vault"
  vault_type     = "DEFAULT"
}
resource "oci_kms_key" "reversa" {
  compartment_id      = oci_identity_compartment.area["security"].id
  display_name        = "${var.prefix}-secrets-key"
  management_endpoint = oci_kms_vault.reversa.management_endpoint
  protection_mode     = "SOFTWARE"
  key_shape {
    algorithm = "AES"
    length    = 32
  }
}
