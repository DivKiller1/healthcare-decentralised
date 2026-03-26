# Healthcare Multi‑Portal SaaS – Technical Design Document

## 1. Purpose of This Document

This document acts as the **single source of truth** for your project implementation. It defines:

* Kubernetes service breakdown
* Database schema & data models
* API grouping & responsibilities
* Entity relationships
* User roles & allowed functions

Once this document is followed, **no architectural confusion or redesign should be needed**.

---

## 2. System Overview (High Level)

The platform is a **public SaaS** with three major portals:

1. Public / Citizen Portal
2. Government Portal (Employee + Govt Admin)
3. Platform / Clinic Admin Portal

All portals talk to **one backend system**, with behavior controlled by **role & permissions**.

---

## 3. Kubernetes Architecture Breakdown

### 3.1 Kubernetes Cluster Responsibility

Single primary Kubernetes cluster (multi‑cloud aware) hosting all core services.

### 3.2 Services (Pods / Deployments)

#### 1. Auth Service

**Responsibility:**

* Login
* OTP verification
* Token issuance
* Role extraction

Runs as a stateless service.

---

#### 2. User & Role Service

**Responsibility:**

* User profile
* Role management
* Region assignment

---

#### 3. Facility Service

**Responsibility:**

* Clinic / hospital / blood bank registration
* Facility profile updates
* Verification status

---

#### 4. Request Service

**Responsibility:**

* Create requests (citizen & clinic)
* Auto‑expiry after 14 days
* Close / archive logic
* Category‑based grouping

---

#### 5. Government Operations Service

**Responsibility:**

* Govt request view
* Acknowledge & close requests
* Route planning trigger

---

#### 6. Routing Service

**Responsibility:**

* Generate optimized visit paths
* Store route plans
* Provide route visualization data

---

#### 7. Metrics & Analytics Service

**Responsibility:**

* Savings calculations
* Demand clustering
* Historical analytics

Admin‑only access.

---

#### 8. Audit & Logging Service

**Responsibility:**

* Track sensitive actions
* Maintain immutable audit logs

---

#### 9. Frontend Gateway / API Gateway

**Responsibility:**

* Single entry point
* Auth validation
* Rate limiting

---

## 4. Database Schema (Logical)

### 4.1 User Table

* user_id (PK)
* name (optional)
* mobile_number (mandatory)
* address (optional)
* role (citizen / clinic / govt_employee / govt_admin / admin)
* region_id (FK)
* created_at

---

### 4.2 Region Table

* region_id (PK)
* region_name (Dehradun)

---

### 4.3 Facility Table

* facility_id (PK)
* name
* facility_type (hospital / clinic / blood_bank / diagnostic)
* address
* latitude
* longitude
* contact_number
* verification_status (approved / rejected)
* region_id (FK)
* created_by (user_id)

---

### 4.4 Service Table

* service_id (PK)
* service_name (Polio, TB, Blood, etc.)
* category

---

### 4.5 Facility_Service Mapping

* facility_id (FK)
* service_id (FK)

---

### 4.6 Request Table

* request_id (PK)
* created_by (user_id)
* service_id (FK)
* category
* latitude
* longitude
* contact_number
* status (active / closed / expired)
* region_id (FK)
* created_at
* expires_at

---

### 4.7 Route_Plan Table

* route_id (PK)
* created_by (govt user_id)
* category
* start_lat
* start_long
* created_at

---

### 4.8 Route_Plan_Nodes

* route_id (FK)
* request_id (FK)
* visit_order

---

### 4.9 Metrics_Snapshot

* metric_id (PK)
* metric_type (cloud_savings / demand / efficiency)
* metric_value
* calculated_at

---

### 4.10 Audit_Log

* log_id (PK)
* actor_id (user_id)
* action_type
* entity_type
* entity_id
* timestamp

---

## 5. Entity Relationships

* User → Region (many‑to‑one)
* Facility → Region (many‑to‑one)
* Facility → Services (many‑to‑many)
* Request → Service (many‑to‑one)
* Request → User (many‑to‑one)
* RoutePlan → Requests (one‑to‑many)
* Metrics → Derived from Requests & Facilities
* AuditLog → User actions

---

## 6. API Responsibility Mapping

### Auth APIs

* Login, OTP verification, role resolution

### Public APIs

* Facility discovery
* Blood bank lookup
* Create & view own requests

### Facility APIs

* Register facility
* Update services
* Update blood availability
* Create requests

### Government APIs

* View clustered requests
* Plan routes
* Close requests

### Government Admin APIs

* Approve / reject facilities
* Oversight on requests

### Admin APIs

* View savings metrics
* Platform analytics
* Audit logs

---

## 7. User Roles & Allowed Functions

### Citizen

* View facilities & blood banks
* Create requests
* Track own requests

---

### Clinic User

* Register facility
* Update facility services
* Update blood status
* Create requests

---

### Govt Employee

* View requests
* Plan visit routes
* Close requests

---

### Govt Admin

* Everything govt employee can do
* Approve / reject facilities
* Governance actions

---

### Platform Admin

* View metrics & savings
* Audit system actions
* No govt execution access

---

## 8. Design Guarantees

* No medical records stored
* No public exposure of requests
* Region‑restricted visibility
* Mandatory contact verification
* Immutable audit trail

---

## 9. Implementation Readiness

With this document:

* Backend APIs can be implemented directly
* Database schemas can be created without ambiguity
* Kubernetes services are clearly separated
* Resume & interview explanations are straightforward

**This document marks the official transition from design to execution.**

---

## 10. Repository Structure (Production-Ready)

```
healthcare-saas/
│
├── frontend/
│   ├── public-portal/
│   ├── govt-portal/
│   └── admin-portal/
│
├── backend/
│   ├── auth-service/
│   ├── user-service/
│   ├── facility-service/
│   ├── request-service/
│   ├── govt-ops-service/
│   ├── routing-service/
│   ├── metrics-service/
│   └── audit-service/
│
├── infra/
│   ├── k8s/
│   │   ├── namespaces/
│   │   ├── deployments/
│   │   ├── services/
│   │   ├── ingress/
│   │   ├── configmaps/
│   │   └── secrets/
│   └── terraform/
│
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   └── data-model.md
│
└── README.md
```

---

## 11. Kubernetes Namespaces

* public
* govt
* admin
* backend
* monitoring

Namespaces enforce logical isolation between portals.

---

## 12. Kubernetes Deployments (Logical)

Each backend service runs as its own Deployment:

* auth-deployment
* user-deployment
* facility-deployment
* request-deployment
* govt-ops-deployment
* routing-deployment
* metrics-deployment
* audit-deployment

All deployments are stateless and horizontally scalable.

---

## 13. Kubernetes Services

Each Deployment is exposed internally via a ClusterIP Service:

* auth-svc
* user-svc
* facility-svc
* request-svc
* govt-ops-svc
* routing-svc
* metrics-svc
* audit-svc

---

## 14. Ingress Strategy

Single Ingress Controller with path-based routing:

* /api/auth → auth-svc
* /api/users → user-svc
* /api/facilities → facility-svc
* /api/requests → request-svc
* /api/govt → govt-ops-svc
* /api/routes → routing-svc
* /api/metrics → metrics-svc
* /api/audit → audit-svc

This keeps a single public endpoint while preserving service boundaries.

---

## 15. Configuration & Secrets

### ConfigMaps

* Environment configs
* Feature flags
* Region configuration (Dehradun)

### Secrets

* Database credentials
* JWT signing keys
* API keys (maps)

Secrets are never committed to Git.

---

## 16. Scaling & Reliability Rules

* Horizontal Pod Autoscaling enabled for:

  * request-service
  * govt-ops-service
  * routing-service

* Metrics-service scales independently

* Auth-service kept lightweight

---

## 17. Week-1 Execution Guidance

Day 1–2:

* Repo setup
* Kubernetes namespaces
* Auth + User service skeleton

Day 3–4:

* Facility service
* Basic request service

Day 5:

* Ingress + service wiring
* Health checks

---

## 18. Final Note

With this structure:

* You can develop services independently
* You can deploy incrementally
* You can explain every architectural decision clearly

This concludes the infrastructure and execution foundation.

---

## 19. README.md (Project Root File)

Below is the **complete, production-grade README** you should place in the root of the repository as `README.md`.

```
# Healthcare Multi-Portal SaaS Platform

A **public, multi-cloud, Kubernetes-based healthcare intelligence platform** designed to connect **citizens, clinics, and government health authorities** through a unified, secure, and scalable system.

This project focuses on **visibility, coordination, and cost-aware decision support** rather than clinical systems, making it safe, realistic, and enterprise-aligned.

---

## 🌍 Vision

Healthcare systems often struggle with:
- Poor visibility of nearby clinics and services
- Fragmented government service discovery
- Inefficient field visit planning
- Lack of operational and cost intelligence

This platform bridges the gap between **public users, healthcare facilities, and government authorities** by providing:
- Map-based discovery of verified clinics, hospitals, and blood banks
- Government service request and coordination system
- Route planning for field visits
- Operational and cloud cost savings intelligence for administrators

---

## 🧩 Portals

### 👤 Public Portal
- Discover nearby hospitals, clinics, and blood banks
- Search government health services (e.g., polio vaccination, TB screening)
- Raise service requests with location and contact verification

### 🏛️ Government Portal
- View and manage categorized service requests
- Identify demand clusters on the map
- Plan optimized visit routes using "Easy Mode"
- Close and acknowledge resolved requests

### 🧑‍💼 Admin Portal
- Approve and verify clinic and blood bank registrations
- Monitor platform usage and regional trends
- View cloud and operational savings metrics
- Access system audit logs

---

## 🏗️ High-Level Architecture

- **Frontend:** Web-based portals (Public, Government, Admin)
- **Backend:** Microservices (Python / FastAPI)
- **Orchestration:** Kubernetes
- **Cloud Strategy:**
  - AWS — Core compute, data, and platform services
  - Azure — Identity and governance services
  - GCP — Maps and AI/analytics services

---

## 🔐 Security & Data Principles

- No patient or medical records are stored
- Only minimal contact data is collected (mobile number & address)
- Role-based access for all system actions
- Requests are never publicly visible
- Facilities must be verified before appearing on the public map
- Immutable audit logs for administrative actions

---

## 🗺️ Key Features

- Interactive healthcare facility map
- Government service discovery and request system
- Blood bank availability visibility
- Request lifecycle management with expiry and archiving
- Route planning for government field teams
- Platform-wide operational and cost metrics

---

## 🧪 Project Status

**Phase:** Platform Skeleton & Infrastructure Setup

Current focus:
- Kubernetes cluster
- Microservice foundation
- Authentication and user management

---

## 📁 Repository Structure

```

healthcare-multicloud-saas/
│
├── frontend/
│   ├── public-portal/
│   ├── govt-portal/
│   └── admin-portal/
│
├── backend/
│   ├── auth-service/
│   ├── user-service/
│   ├── facility-service/
│   ├── request-service/
│   ├── govt-ops-service/
│   ├── routing-service/
│   ├── metrics-service/
│   └── audit-service/
│
├── infra/
│   ├── k8s/
│   │   ├── namespaces/
│   │   ├── deployments/
│   │   ├── services/
│   │   ├── ingress/
│   │   ├── configmaps/
│   │   └── secrets/
│   └── terraform/
│
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   └── data-model.md
│
└── README.md

````

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- Docker
- Kubernetes (kind / minikube)
- kubectl
- Git

### Setup

```bash
git clone https://github.com/<your-username>/healthcare-multicloud-saas.git
cd healthcare-multicloud-saas
````

Create local Kubernetes cluster:

```bash
kind create cluster --name healthcare-saas
kubectl apply -f infra/k8s/namespaces/namespaces.yaml
```

---

## 🧠 Design Philosophy

This project prioritizes:

* **System design before implementation**
* **Clear role separation**
* **Security-first architecture**
* **Cost-awareness and scalability**

It is built as a **portfolio-grade SaaS platform** rather than a feature demo.

---

## 📜 License

This project is open-source and available under the MIT License.

---

## ✍️ Author

**Divyanshu Gaur**
Cloud & Backend Engineering Portfolio Project

```

---

## 20. Usage Note

This README is intentionally written to:
- Be readable by recruiters
- Explain architectural decisions clearly
- Act as a walkthrough during interviews

It is part of the project’s **portfolio value**, not just documentation.

```
