locals {
  network_compartment = oci_identity_compartment.area["network"].id
  tags                = { application = "reversa", managed_by = "terraform" }
}
resource "oci_core_vcn" "reversa" {
  compartment_id = local.network_compartment
  cidr_blocks    = [var.vcn_cidr]
  display_name   = "${var.prefix}-vcn"
  dns_label      = "reversa"
  freeform_tags  = local.tags
}
resource "oci_core_internet_gateway" "reversa" {
  compartment_id = local.network_compartment
  vcn_id         = oci_core_vcn.reversa.id
  display_name   = "${var.prefix}-igw"
  enabled        = true
}
resource "oci_core_nat_gateway" "reversa" {
  compartment_id = local.network_compartment
  vcn_id         = oci_core_vcn.reversa.id
  display_name   = "${var.prefix}-nat"
}
data "oci_core_services" "regional" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}
resource "oci_core_service_gateway" "reversa" {
  compartment_id = local.network_compartment
  vcn_id         = oci_core_vcn.reversa.id
  display_name   = "${var.prefix}-sgw"
  services { service_id = data.oci_core_services.regional.services[0].id }
}
resource "oci_core_route_table" "public" {
  compartment_id = local.network_compartment
  vcn_id         = oci_core_vcn.reversa.id
  display_name   = "${var.prefix}-public-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.reversa.id
  }
}
resource "oci_core_route_table" "private" {
  compartment_id = local.network_compartment
  vcn_id         = oci_core_vcn.reversa.id
  display_name   = "${var.prefix}-private-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_nat_gateway.reversa.id
  }
  route_rules {
    destination_type  = "SERVICE_CIDR_BLOCK"
    destination       = data.oci_core_services.regional.services[0].cidr_block
    network_entity_id = oci_core_service_gateway.reversa.id
  }
}
resource "oci_core_security_list" "empty" {
  compartment_id = local.network_compartment
  vcn_id         = oci_core_vcn.reversa.id
  display_name   = "${var.prefix}-empty-use-nsg"
}
resource "oci_core_subnet" "public" {
  compartment_id             = local.network_compartment
  vcn_id                     = oci_core_vcn.reversa.id
  cidr_block                 = var.public_cidr
  display_name               = "${var.prefix}-public-lb"
  dns_label                  = "public"
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.empty.id]
  prohibit_public_ip_on_vnic = false
}
resource "oci_core_subnet" "private" {
  compartment_id             = local.network_compartment
  vcn_id                     = oci_core_vcn.reversa.id
  cidr_block                 = var.private_cidr
  display_name               = "${var.prefix}-private-app"
  dns_label                  = "app"
  route_table_id             = oci_core_route_table.private.id
  security_list_ids          = [oci_core_security_list.empty.id]
  prohibit_public_ip_on_vnic = true
}
resource "oci_core_network_security_group" "lb" {
  compartment_id = local.network_compartment
  vcn_id         = oci_core_vcn.reversa.id
  display_name   = "${var.prefix}-lb-nsg"
}
resource "oci_core_network_security_group" "app" {
  compartment_id = local.network_compartment
  vcn_id         = oci_core_vcn.reversa.id
  display_name   = "${var.prefix}-app-nsg"
}
resource "oci_core_network_security_group_security_rule" "https" {
  for_each                  = toset(var.web_allowed_cidrs)
  network_security_group_id = oci_core_network_security_group.lb.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = each.value
  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}
resource "oci_core_network_security_group_security_rule" "acme" {
  network_security_group_id = oci_core_network_security_group.lb.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = "0.0.0.0/0"
  tcp_options {
    destination_port_range {
      min = 80
      max = 80
    }
  }
}
resource "oci_core_network_security_group_security_rule" "lb_to_app" {
  for_each                  = toset(["80", "443"])
  network_security_group_id = oci_core_network_security_group.lb.id
  direction                 = "EGRESS"
  protocol                  = "6"
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.app.id
  tcp_options {
    destination_port_range {
      min = tonumber(each.value)
      max = tonumber(each.value)
    }
  }
}
resource "oci_core_network_security_group_security_rule" "app_from_lb" {
  for_each                  = toset(["80", "443"])
  network_security_group_id = oci_core_network_security_group.app.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.lb.id
  tcp_options {
    destination_port_range {
      min = tonumber(each.value)
      max = tonumber(each.value)
    }
  }
}
resource "oci_core_network_security_group_security_rule" "app_https_egress" {
  network_security_group_id = oci_core_network_security_group.app.id
  direction                 = "EGRESS"
  protocol                  = "6"
  destination               = "0.0.0.0/0"
  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}
resource "oci_core_network_security_group_security_rule" "pmtu" {
  for_each                  = { lb = oci_core_network_security_group.lb.id, app = oci_core_network_security_group.app.id }
  network_security_group_id = each.value
  direction                 = "INGRESS"
  protocol                  = "1"
  source                    = "0.0.0.0/0"
  icmp_options {
    type = 3
    code = 4
  }
}
resource "oci_bastion_bastion" "reversa" {
  count                        = length(var.bastion_allowed_cidrs) > 0 ? 1 : 0
  bastion_type                 = "STANDARD"
  compartment_id               = oci_identity_compartment.area["operations"].id
  target_subnet_id             = oci_core_subnet.private.id
  client_cidr_block_allow_list = var.bastion_allowed_cidrs
  name                         = "${var.prefix}-bastion"
  max_session_ttl_in_seconds   = 10800
}
resource "oci_core_network_security_group_security_rule" "ssh_bastion" {
  count                     = length(var.bastion_allowed_cidrs) > 0 ? 1 : 0
  network_security_group_id = oci_core_network_security_group.app.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = "${oci_bastion_bastion.reversa[0].private_endpoint_ip_address}/32"
  tcp_options {
    destination_port_range {
      min = 22
      max = 22
    }
  }
}
