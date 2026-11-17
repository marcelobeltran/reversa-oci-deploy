output "compartments" {
  value = merge({ root = oci_identity_compartment.reversa.id }, { for k, v in oci_identity_compartment.area : k => v.id })
}
output "public_ip" { value = oci_core_public_ip.reversa.ip_address }
output "url" { value = "https://${oci_core_public_ip.reversa.ip_address}/" }
output "private_subnet_ocid" { value = oci_core_subnet.private.id }
output "load_balancer_ocid" { value = oci_load_balancer_load_balancer.reversa.id }
output "vault" {
  value = {
    id     = oci_kms_vault.reversa.id
    key_id = oci_kms_key.reversa.id
  }
}
output "instance_ocid" { value = try(oci_core_instance.reversa[0].id, null) }
output "private_ip" { value = try(oci_core_instance.reversa[0].private_ip, null) }
output "phase" { value = var.enable_compute ? "VM creada; verificar bootstrap, TLS y prueba funcional" : "Infraestructura sin VM; preparar GenAI/Vault antes de habilitar compute" }

output "genai_project_ocid" { value = oci_generative_ai_project.reversa.id }
