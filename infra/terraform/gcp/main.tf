# infra/terraform/gcp/main.tf
provider "google" {
  project = var.project_id
  region  = var.region
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = "healthcare-saas-cluster"
  location = var.region
  
  initial_node_count = 1
  
  node_config {
    machine_type = "e2-medium"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# Cloud SQL (PostgreSQL)
resource "google_sql_database_instance" "main" {
  name             = "healthcare-db-instance"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier = "db-f1-micro"
  }
}

# Cloud Memorystore (Redis)
resource "google_redis_instance" "main" {
  name           = "healthcare-cache"
  memory_size_gb = 1
  region         = var.region
}

# Workload Identity for K8s -> GCP IAM
resource "google_service_account" "k8s_sa" {
  account_id   = "healthcare-k8s-sa"
  display_name = "K8s Service Account"
}
