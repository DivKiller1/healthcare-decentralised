# infra/terraform/gcp/variables.tf
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

# infra/terraform/gcp/outputs.tf
output "gke_cluster_name" {
  value = google_container_cluster.primary.name
}

output "db_instance_address" {
  value = google_sql_database_instance.main.ip_address.0.ip_address
}

output "redis_instance_host" {
  value = google_redis_instance.main.host
}
