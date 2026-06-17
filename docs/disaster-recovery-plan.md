# EcoChain Exchange - Disaster Recovery Plan

## 1. Purpose
This document defines the recovery strategy for the EcoChain Exchange carbon
credit trading platform in the event of infrastructure failure, data loss, or
a regional outage. Because the platform handles regulatory and audit-critical
trading data, recovery objectives are intentionally conservative.

## 2. Recovery Objectives
| Metric | Target |
|---|---|
| Recovery Time Objective (RTO) | 30 minutes |
| Recovery Point Objective (RPO) | 5 minutes |

## 3. Backup Strategy
- **Database (PostgreSQL / RDS):** Automated daily snapshots with a 7-day
  retention window, plus continuous write-ahead log (WAL) archiving for
  point-in-time recovery (RPO of 5 minutes).
- **Application configuration & secrets:** Stored in HashiCorp Vault, which
  is itself backed by periodic snapshot (`vault operator raft snapshot save`).
- **Container images:** Immutable, versioned images stored in ECR with a
  retention policy of the last 10 builds, so any previous release can be
  redeployed instantly.
- **Infrastructure definitions:** All infrastructure is defined in Terraform
  and stored in the GitHub repository, enabling complete environment
  recreation from code.

## 4. Failure Scenarios & Response

### 4.1 Application Pod Crash
- Kubernetes liveness/readiness probes on `/health` automatically restart
  unhealthy pods.
- The Horizontal Pod Autoscaler maintains a minimum of 2 replicas, so a
  single pod failure does not cause downtime.

### 4.2 Node Failure
- The EKS managed node group automatically replaces failed worker nodes.
- Pods are rescheduled onto healthy nodes by the Kubernetes scheduler.

### 4.3 Database Failure
- Restore the most recent automated RDS snapshot into a new instance.
- Apply WAL logs up to the point of failure for point-in-time recovery.
- Update the `DATABASE_URL` secret in Vault / Kubernetes Secret and restart
  the application deployment to pick up the new endpoint.

### 4.4 Full Region Outage
1. Re-run `terraform apply` against a secondary AWS region using the same
   configuration (region is a variable, `var.aws_region`).
2. Restore the latest RDS snapshot (cross-region snapshot copy) into the new
   region.
3. Redeploy the application via the Jenkins pipeline, pointing `kubectl` at
   the new cluster's kubeconfig.
4. Update DNS records to point to the new ingress endpoint.

### 4.5 Secret Compromise
- Revoke the affected Vault token/policy immediately.
- Rotate the compromised credential (DB password, app secret key) in Vault.
- Roll the Kubernetes Deployment (`kubectl rollout restart deployment/ecochain-app`)
  so pods pick up the new secret.

## 5. Monitoring & Alerting
- Prometheus scrapes `/metrics` from the application every 15 seconds.
- Grafana dashboards visualize request rate, latency, and error rate.
- Alerts (configured in Alertmanager / Grafana) notify the on-call engineer
  if the application is down (`up == 0`) for more than 1 minute, or if
  error rate exceeds 5% over 5 minutes.

## 6. Testing the Plan
- Quarterly disaster recovery drills:
  1. Simulate a pod failure (`kubectl delete pod <pod>`) and confirm
     automatic recovery.
  2. Simulate a database failure by restoring a snapshot to a test instance
     and validating data integrity.
  3. Perform a full `terraform destroy` / `terraform apply` cycle in a
     staging environment to validate infrastructure-as-code recovery.

## 7. Roles & Responsibilities
| Role | Responsibility |
|---|---|
| DevOps Lead | Coordinates recovery effort, executes Terraform/Jenkins runbooks |
| Database Administrator | Restores database snapshots, validates data integrity |
| Compliance Officer | Confirms audit trail integrity post-recovery |
| On-call Engineer | First responder to monitoring alerts |
