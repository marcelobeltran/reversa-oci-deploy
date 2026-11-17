resource "oci_generative_ai_project" "reversa" {
  compartment_id = oci_identity_compartment.area["ai"].id
  display_name   = "${var.prefix}-genai"
  description    = "Proyecto para inferencia directa de Reversa"
}
