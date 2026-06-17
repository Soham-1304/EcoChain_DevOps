# EcoChain Exchange - Carbon Credit Trading Platform

**Case Study 74: Project EcoChain - Global Carbon Credit Exchange Platform**

A small but functional carbon-credit trading web application, built to
demonstrate a complete DevOps lifecycle: containerization, CI/CD,
infrastructure as code, orchestration, monitoring, logging, and secret
management.

## Repository Structure

```
ecochain/
├── app/                    # Flask application source code
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── templates/
│   └── static/
├── docker-compose.yml      # Full local stack (app + db + monitoring + logging + vault)
├── Jenkinsfile              # CI/CD pipeline definition
├── terraform/               # AWS infrastructure as code (VPC, EKS, ECR, RDS)
├── k8s/                      # Kubernetes manifests
├── monitoring/               # Prometheus + Grafana configuration
├── logging/                   # ELK stack configuration (Logstash, Filebeat)
├── vault/                      # HashiCorp Vault setup script
└── docs/
    ├── disaster-recovery-plan.md
    └── diagrams/                # Architecture diagrams
```

## Quick Start (Local)

```bash
cd app
pip install -r requirements.txt
python app.py
# Visit http://localhost:5000
```

## Quick Start (Full Stack with Docker Compose)

```bash
docker compose up -d --build
# App:        http://localhost:5000
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000  (admin/admin)
# Vault:      http://localhost:8200  (token: root)
# Kibana:     http://localhost:5601
```

See the accompanying **EcoChain DevOps Implementation Guide.docx** for full
step-by-step instructions covering every deliverable.
