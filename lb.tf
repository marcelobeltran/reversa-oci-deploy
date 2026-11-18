resource "oci_core_public_ip" "reversa" {
  compartment_id = local.network_compartment
  lifetime       = "RESERVED"
  display_name   = "${var.prefix}-public-ip"
  # The load balancer service owns the private-IP attachment after reservation.
  lifecycle { ignore_changes = [private_ip_id] }
}
resource "oci_load_balancer_load_balancer" "reversa" {
  compartment_id             = local.network_compartment
  display_name               = "${var.prefix}-lb"
  shape                      = "flexible"
  is_private                 = false
  subnet_ids                 = [oci_core_subnet.public.id]
  network_security_group_ids = [oci_core_network_security_group.lb.id]
  reserved_ips { id = oci_core_public_ip.reversa.id }
  shape_details {
    minimum_bandwidth_in_mbps = 10
    maximum_bandwidth_in_mbps = 100
  }
}
resource "oci_load_balancer_backend_set" "reversa" {
  for_each         = toset(["80", "443"])
  load_balancer_id = oci_load_balancer_load_balancer.reversa.id
  name             = "${var.prefix}-${each.key}"
  policy           = "ROUND_ROBIN"
  health_checker {
    protocol          = "HTTP"
    port              = 80
    url_path          = "/healthz"
    return_code       = 200
    interval_ms       = 10000
    timeout_in_millis = 3000
    retries           = 3
  }
}
resource "oci_load_balancer_listener" "reversa" {
  for_each                 = toset(["80", "443"])
  load_balancer_id         = oci_load_balancer_load_balancer.reversa.id
  name                     = "${var.prefix}-${each.key}"
  default_backend_set_name = oci_load_balancer_backend_set.reversa[each.key].name
  port                     = tonumber(each.key)
  protocol                 = "TCP"
  connection_configuration { idle_timeout_in_seconds = 3600 }
}
resource "oci_load_balancer_backend" "reversa" {
  for_each         = var.enable_compute ? toset(["80", "443"]) : toset([])
  load_balancer_id = oci_load_balancer_load_balancer.reversa.id
  backendset_name  = oci_load_balancer_backend_set.reversa[each.key].name
  ip_address       = oci_core_instance.reversa[0].private_ip
  port             = tonumber(each.key)
  weight           = 1
}
