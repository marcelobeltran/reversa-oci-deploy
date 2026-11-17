resource "oci_core_instance" "reversa" {
  count               = var.enable_compute ? 1 : 0
  compartment_id      = oci_identity_compartment.area["app"].id
  availability_domain = var.availability_domain
  display_name        = "${var.prefix}-vm"
  shape               = var.shape
  shape_config {
    ocpus         = var.ocpus
    memory_in_gbs = var.memory_gbs
  }
  source_details {
    source_type             = "image"
    source_id               = var.image_ocid
    boot_volume_size_in_gbs = var.boot_volume_gbs
  }
  create_vnic_details {
    subnet_id        = oci_core_subnet.private.id
    assign_public_ip = false
    hostname_label   = "reversa"
    nsg_ids          = [oci_core_network_security_group.app.id]
  }
  instance_options { are_legacy_imds_endpoints_disabled = true }
  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64gzip(templatefile("${path.module}/cloud-init.yaml.tftpl", {
      runtime_b64 = filebase64("${path.module}/runtime.tar.gz")
      config_b64 = base64encode(jsonencode({
        region             = var.region
        public_ip          = oci_core_public_ip.reversa.ip_address
        lb_subnet_cidr     = var.public_cidr
        genai_project_ocid = oci_generative_ai_project.reversa.id
        genai_secret_ocid  = var.genai_secret_ocid
        web_secret_ocid    = var.web_secret_ocid
        model_id           = var.model_id
        model_context      = var.model_context
        model_output       = var.model_output
        opencode_version   = var.opencode_version
        certbot_version    = var.certbot_version
      }))
    }))
  }
  preserve_boot_volume = true
  freeform_tags        = local.tags
  depends_on = [
    oci_identity_policy.secrets, oci_identity_policy.genai,
    oci_core_route_table.private, oci_load_balancer_listener.reversa
  ]
  lifecycle {
    precondition {
      condition = alltrue([
        var.image_ocid != "", var.availability_domain != "",
        var.genai_secret_ocid != "", var.web_secret_ocid != "",
        var.genai_api_key_ocid != "", oci_generative_ai_project.reversa.id != ""
      ])
      error_message = "Antes de crear VM: ejecutar preparación GenAI/Vault y seleccionar imagen/AD verificadas."
    }
    ignore_changes = [metadata["user_data"]]
  }
}
