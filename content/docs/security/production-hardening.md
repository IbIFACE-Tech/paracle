# Production Security Hardening Guide

**Last Updated**: 2026-01-18
**Version**: 1.0
**Audience**: Security Engineers, DevOps Teams

---

## Overview

Comprehensive security hardening measures for Paracle production deployments beyond application-level security.

**Security Layers**:

1. **Network Layer** - VPC, subnets, security groups, WAF
2. **Transport Layer** - SSL/TLS, certificate management, HSTS
3. **Application Layer** - Rate limiting, DDoS protection, input validation
4. **Data Layer** - Encryption at rest/transit, key management
5. **Access Layer** - IAM, RBAC, audit logging

**Compliance Targets**:

- OWASP Top 10 protection
- ISO 27001 / 42001 compliance
- SOC2 Type II requirements
- GDPR data protection

---

## Network Security

### VPC Design (AWS)

**Multi-Tier Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                      Internet Gateway                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Public Subnets                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   NAT GW     │  │   NAT GW     │  │   ALB        │      │
│  │   AZ-a       │  │   AZ-b       │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Private Subnets                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Pods    │  │  API Pods    │  │  Worker Pods │      │
│  │  AZ-a        │  │  AZ-b        │  │  AZ-c        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Database Subnets                          │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  RDS Primary │  │  RDS Replica │                        │
│  │  AZ-a        │  │  AZ-b        │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

**Terraform Configuration**:

```hcl
# VPC with 3-tier architecture
resource "aws_vpc" "paracle" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "paracle-prod-vpc"
    Environment = "production"
  }
}

# Public subnets (ALB, NAT Gateway)
resource "aws_subnet" "public" {
  count             = 3
  vpc_id            = aws_vpc.paracle.id
  cidr_block        = "10.0.${count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "paracle-public-${count.index + 1}"
    Tier = "public"
  }
}

# Private subnets (API, Workers)
resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.paracle.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "paracle-private-${count.index + 1}"
    Tier = "private"
  }
}

# Database subnets (RDS)
resource "aws_subnet" "database" {
  count             = 3
  vpc_id            = aws_vpc.paracle.id
  cidr_block        = "10.0.${count.index + 20}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "paracle-database-${count.index + 1}"
    Tier = "database"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.paracle.id

  tags = {
    Name = "paracle-igw"
  }
}

# NAT Gateways (one per AZ for HA)
resource "aws_eip" "nat" {
  count  = 3
  domain = "vpc"

  tags = {
    Name = "paracle-nat-eip-${count.index + 1}"
  }
}

resource "aws_nat_gateway" "main" {
  count         = 3
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "paracle-nat-${count.index + 1}"
  }
}
```

### Security Groups

**Layered Security Groups**:

```hcl
# ALB Security Group (Internet-facing)
resource "aws_security_group" "alb" {
  name        = "paracle-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.paracle.id

  # HTTPS from internet
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from internet"
  }

  # HTTP (redirect to HTTPS)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP redirect to HTTPS"
  }

  # Egress to API pods
  egress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
    description     = "To API pods"
  }

  tags = {
    Name = "paracle-alb-sg"
  }
}

# API Security Group
resource "aws_security_group" "api" {
  name        = "paracle-api-sg"
  description = "Security group for API pods"
  vpc_id      = aws_vpc.paracle.id

  # From ALB only
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "From ALB"
  }

  # To database
  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.database.id]
    description     = "To PostgreSQL"
  }

  # To Redis
  egress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.redis.id]
    description     = "To Redis"
  }

  # To internet (LLM APIs)
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "To LLM providers"
  }

  tags = {
    Name = "paracle-api-sg"
  }
}

# Database Security Group
resource "aws_security_group" "database" {
  name        = "paracle-database-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.paracle.id

  # From API only
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
    description     = "From API pods"
  }

  # No egress (database doesn't need outbound)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = []
    description = "No outbound traffic"
  }

  tags = {
    Name = "paracle-database-sg"
  }
}

# Redis Security Group
resource "aws_security_group" "redis" {
  name        = "paracle-redis-sg"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.paracle.id

  # From API only
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
    description     = "From API pods"
  }

  tags = {
    Name = "paracle-redis-sg"
  }
}
```

### Network Policies (Kubernetes)

**Zero-Trust Network Policies**:

```yaml
# Deny all traffic by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-default
  namespace: paracle-prod
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress

---
# API pods can receive from ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-ingress-policy
  namespace: paracle-prod
spec:
  podSelector:
    matchLabels:
      app: paracle-api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000

---
# API pods can access database and Redis
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-egress-policy
  namespace: paracle-prod
spec:
  podSelector:
    matchLabels:
      app: paracle-api
  policyTypes:
    - Egress
  egress:
    # To PostgreSQL
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432

    # To Redis
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379

    # To DNS (kube-dns)
    - to:
        - namespaceSelector:
            matchLabels:
              name: kube-system
      ports:
        - protocol: UDP
          port: 53

    # To internet (LLM APIs) - port 443
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 443

---
# Database can only receive from API
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-policy
  namespace: paracle-prod
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: paracle-api
      ports:
        - protocol: TCP
          port: 5432
  # No egress allowed
  egress: []
```

---

## Web Application Firewall (WAF)

### AWS WAF

**Managed Rules + Custom Rules**:

```hcl
# AWS WAF Web ACL
resource "aws_wafv2_web_acl" "paracle" {
  name  = "paracle-prod-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  # AWS Managed Rules - Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"

        # Exclude rules causing false positives
        excluded_rule {
          name = "SizeRestrictions_BODY"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules - Known Bad Inputs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules - SQL Injection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLiRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # Rate limiting - 1000 requests per 5 minutes per IP
  rule {
    name     = "RateLimitRule"
    priority = 10

    action {
      block {
        custom_response {
          response_code = 429
          custom_response_body_key = "rate_limit_body"
        }
      }
    }

    statement {
      rate_based_statement {
        limit              = 1000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRuleMetric"
      sampled_requests_enabled   = true
    }
  }

  # Block known malicious IPs
  rule {
    name     = "BlockMaliciousIPs"
    priority = 20

    action {
      block {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.malicious_ips.arn
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BlockMaliciousIPsMetric"
      sampled_requests_enabled   = true
    }
  }

  # Geo-blocking (optional)
  rule {
    name     = "GeoBlocking"
    priority = 30

    action {
      block {}
    }

    statement {
      geo_match_statement {
        country_codes = ["KP", "IR", "SY"]  # North Korea, Iran, Syria
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "GeoBlockingMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "ParacleWAFMetric"
    sampled_requests_enabled   = true
  }

  tags = {
    Name        = "paracle-prod-waf"
    Environment = "production"
  }
}

# Custom response for rate limiting
resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.paracle.arn
}

# IP set for known malicious IPs
resource "aws_wafv2_ip_set" "malicious_ips" {
  name               = "paracle-malicious-ips"
  scope              = "REGIONAL"
  ip_address_version = "IPV4"

  addresses = [
    # Populated from threat intelligence feeds
    # Example: "192.0.2.0/24"
  ]
}
```

### Cloudflare WAF (Alternative)

**Cloudflare Configuration**:

```bash
# Enable Cloudflare WAF
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/settings/waf" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{"value":"on"}'

# Enable OWASP ModSecurity Core Rule Set
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/firewall/waf/packages/${OWASP_PACKAGE_ID}" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{"sensitivity":"high","action_mode":"challenge"}'

# Custom firewall rule - Block known attack patterns
curl -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/firewall/rules" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{
    "filter": {
      "expression": "(http.request.uri.path contains \"../\" or http.request.uri.path contains \"./\") or (http.user_agent eq \"\")"
    },
    "action": "block",
    "description": "Block path traversal and empty user agents"
  }'

# Rate limiting rule
curl -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/rate_limits" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{
    "threshold": 1000,
    "period": 300,
    "action": {
      "mode": "challenge",
      "timeout": 86400
    },
    "match": {
      "request": {
        "url": "api.paracle.com/*"
      }
    },
    "description": "Rate limit API requests"
  }'
```

---

## DDoS Protection

### AWS Shield Advanced

**Activation and Configuration**:

```hcl
# AWS Shield Advanced subscription
resource "aws_shield_protection" "alb" {
  name         = "paracle-alb-ddos-protection"
  resource_arn = aws_lb.main.arn

  tags = {
    Name = "paracle-alb-shield"
  }
}

# CloudWatch alarms for DDoS attacks
resource "aws_cloudwatch_metric_alarm" "ddos_attack" {
  alarm_name          = "paracle-ddos-attack-detected"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DDoSDetected"
  namespace           = "AWS/DDoSProtection"
  period              = 300
  statistic           = "Sum"
  threshold           = 1

  alarm_description = "DDoS attack detected on ALB"
  alarm_actions     = [aws_sns_topic.security_alerts.arn]

  dimensions = {
    ResourceArn = aws_lb.main.arn
  }
}

# Shield Response Team (SRT) access
resource "aws_shield_drt_access_role_arn_association" "main" {
  role_arn = aws_iam_role.shield_drt.arn
}

resource "aws_iam_role" "shield_drt" {
  name = "ShieldResponseTeamAccess"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "drt.shield.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "shield_drt" {
  role       = aws_iam_role.shield_drt.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSShieldDRTAccessPolicy"
}
```

### Cloudflare DDoS Protection

**Automatic DDoS Mitigation** (included with Cloudflare):

```yaml
# Cloudflare Terraform configuration
resource "cloudflare_zone_settings_override" "paracle" {
  zone_id = var.cloudflare_zone_id

  settings {
    # Enable DDoS protection
    security_level = "high"

    # Enable browser integrity check
    browser_check = "on"

    # Challenge passage
    challenge_ttl = 1800

    # Enable automatic HTTPS rewrites
    automatic_https_rewrites = "on"

    # Enable opportunistic encryption
    opportunistic_encryption = "on"

    # TLS 1.3
    min_tls_version = "1.3"

    # HTTP/2
    http2 = "on"

    # HTTP/3 with QUIC
    http3 = "on"
  }
}

# Rate limiting (advanced)
resource "cloudflare_rate_limit" "api_protection" {
  zone_id = var.cloudflare_zone_id

  threshold = 1000
  period    = 60

  match {
    request {
      url_pattern = "api.paracle.com/api/*"
    }
  }

  action {
    mode    = "challenge"
    timeout = 3600
  }

  description = "Protect API endpoints from abuse"
}
```

---

## SSL/TLS Configuration

### Certificate Management

**AWS Certificate Manager (ACM)**:

```hcl
# Request SSL certificate
resource "aws_acm_certificate" "paracle" {
  domain_name       = "api.paracle.com"
  validation_method = "DNS"

  subject_alternative_names = [
    "*.paracle.com",
    "paracle.com"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "paracle-prod-cert"
  }
}

# DNS validation
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.paracle.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id = data.aws_route53_zone.main.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "paracle" {
  certificate_arn         = aws_acm_certificate.paracle.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}
```

### ALB HTTPS Configuration

**Secure TLS Settings**:

```hcl
# ALB HTTPS listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.paracle.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# HTTP listener - redirect to HTTPS
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# Additional certificates (SNI)
resource "aws_lb_listener_certificate" "wildcard" {
  listener_arn    = aws_lb_listener.https.arn
  certificate_arn = aws_acm_certificate.paracle.arn
}
```

### Nginx TLS Configuration

**Kubernetes Ingress with TLS**:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: paracle-ingress
  namespace: paracle-prod
  annotations:
    # Force HTTPS
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"

    # TLS configuration
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.2 TLSv1.3"
    nginx.ingress.kubernetes.io/ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
    nginx.ingress.kubernetes.io/ssl-prefer-server-ciphers: "true"

    # HSTS
    nginx.ingress.kubernetes.io/hsts: "true"
    nginx.ingress.kubernetes.io/hsts-max-age: "31536000"
    nginx.ingress.kubernetes.io/hsts-include-subdomains: "true"
    nginx.ingress.kubernetes.io/hsts-preload: "true"

    # Security headers
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "X-Frame-Options: DENY";
      more_set_headers "X-Content-Type-Options: nosniff";
      more_set_headers "X-XSS-Protection: 1; mode=block";
      more_set_headers "Referrer-Policy: strict-origin-when-cross-origin";
      more_set_headers "Permissions-Policy: geolocation=(), microphone=(), camera=()";

spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.paracle.com
        - "*.paracle.com"
      secretName: paracle-tls-secret

  rules:
    - host: api.paracle.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: paracle-api
                port:
                  number: 8000
```

### Certificate Rotation

**Automated Certificate Renewal (cert-manager)**:

```yaml
# Install cert-manager
apiVersion: v1
kind: Namespace
metadata:
  name: cert-manager

---
# ClusterIssuer for Let's Encrypt
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: security@paracle.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
      - dns01:
          route53:
            region: us-east-1
            hostedZoneID: Z1234567890ABC

---
# Certificate resource
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: paracle-tls
  namespace: paracle-prod
spec:
  secretName: paracle-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - api.paracle.com
    - "*.paracle.com"

  # Auto-renewal 30 days before expiry
  renewBefore: 720h # 30 days
```

---

## Rate Limiting

### Application-Level Rate Limiting

**FastAPI with slowapi**:

```python
# packages/paracle_api/rate_limiting.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request

# Configure limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="redis://redis:6379/1",
    strategy="fixed-window-elastic-expiry",
)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits
@app.get("/api/v1/agents")
@limiter.limit("50/minute")
async def list_agents(request: Request):
    """List agents - 50 requests per minute."""
    return agents

@app.post("/api/v1/agents/run")
@limiter.limit("20/minute")
async def run_agent(request: Request, agent_request: AgentRequest):
    """Run agent - 20 requests per minute (expensive operation)."""
    return result

@app.get("/health")
@limiter.exempt  # No rate limit on health checks
async def health_check():
    return {"status": "healthy"}
```

**Advanced Rate Limiting with Redis**:

```python
# packages/paracle_api/advanced_rate_limiting.py
import time
from typing import Optional
from redis import Redis
from fastapi import HTTPException, Request

class AdvancedRateLimiter:
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)

    async def check_rate_limit(
        self,
        request: Request,
        limit: int,
        window: int,
        burst: Optional[int] = None,
    ) -> bool:
        """
        Token bucket rate limiting with burst support.

        Args:
            request: FastAPI request
            limit: Requests per window
            window: Time window in seconds
            burst: Optional burst capacity (default: limit * 2)
        """
        # Get client identifier
        client_id = self._get_client_id(request)
        key = f"rate_limit:{client_id}"

        # Token bucket parameters
        capacity = burst or (limit * 2)
        refill_rate = limit / window

        # Get current bucket state
        pipe = self.redis.pipeline()
        pipe.get(f"{key}:tokens")
        pipe.get(f"{key}:last_refill")
        tokens, last_refill = pipe.execute()

        now = time.time()
        tokens = float(tokens) if tokens else capacity
        last_refill = float(last_refill) if last_refill else now

        # Refill tokens
        elapsed = now - last_refill
        tokens = min(capacity, tokens + (elapsed * refill_rate))

        # Check if request allowed
        if tokens >= 1:
            tokens -= 1

            # Update bucket
            pipe = self.redis.pipeline()
            pipe.set(f"{key}:tokens", tokens, ex=window * 2)
            pipe.set(f"{key}:last_refill", now, ex=window * 2)
            pipe.execute()

            return True
        else:
            # Rate limit exceeded
            retry_after = int((1 - tokens) / refill_rate)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Retry after {retry_after}s",
                headers={"Retry-After": str(retry_after)},
            )

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"

        # Use IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0]}"

        return f"ip:{request.client.host}"

# Usage
rate_limiter = AdvancedRateLimiter("redis://redis:6379/1")

@app.post("/api/v1/agents/run")
async def run_agent(request: Request, agent_request: AgentRequest):
    # 20 requests per minute, burst up to 40
    await rate_limiter.check_rate_limit(request, limit=20, window=60, burst=40)
    return await execute_agent(agent_request)
```

### Nginx Rate Limiting

**Nginx Configuration**:

```nginx
# /etc/nginx/nginx.conf

http {
    # Define rate limit zones

    # Zone 1: General API rate limiting (10 req/s per IP)
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    # Zone 2: Burst zone (50 req/s per IP, short burst)
    limit_req_zone $binary_remote_addr zone=api_burst:10m rate=50r/s;

    # Zone 3: Login endpoint (stricter - 5 req/minute per IP)
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

    # Zone 4: Per-user rate limiting (requires upstream to set header)
    limit_req_zone $http_x_user_id zone=user_limit:10m rate=100r/s;

    # Connection limiting
    limit_conn_zone $binary_remote_addr zone=addr_conn_limit:10m;

    server {
        listen 443 ssl http2;
        server_name api.paracle.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/paracle.crt;
        ssl_certificate_key /etc/nginx/ssl/paracle.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
        ssl_prefer_server_ciphers on;

        # Apply rate limits
        location /api/ {
            # General rate limit: 10 req/s, burst 20, delay after 10
            limit_req zone=api_limit burst=20 delay=10;

            # Connection limit: 10 concurrent connections per IP
            limit_conn addr_conn_limit 10;

            # Status for rate limit exceeded
            limit_req_status 429;
            limit_conn_status 429;

            proxy_pass http://paracle-api:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        location /api/v1/auth/login {
            # Stricter limit for login: 5 req/minute
            limit_req zone=login_limit burst=3 nodelay;

            proxy_pass http://paracle-api:8000;
        }

        location /api/v1/agents/run {
            # Burst zone for expensive operations
            limit_req zone=api_burst burst=10 nodelay;
            limit_req zone=user_limit burst=20;

            proxy_pass http://paracle-api:8000;
            proxy_read_timeout 300s;  # 5 minutes for long-running agents
        }

        location /health {
            # No rate limit for health checks
            access_log off;
            proxy_pass http://paracle-api:8000;
        }
    }
}
```

### AWS API Gateway Rate Limiting

**API Gateway Usage Plans**:

```hcl
# API Gateway REST API
resource "aws_api_gateway_rest_api" "paracle" {
  name = "paracle-api"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# Usage plan - Standard tier
resource "aws_api_gateway_usage_plan" "standard" {
  name = "paracle-standard-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.paracle.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }

  throttle_settings {
    burst_limit = 1000
    rate_limit  = 500  # 500 req/s
  }

  quota_settings {
    limit  = 1000000  # 1M requests per month
    period = "MONTH"
  }
}

# Usage plan - Premium tier
resource "aws_api_gateway_usage_plan" "premium" {
  name = "paracle-premium-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.paracle.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }

  throttle_settings {
    burst_limit = 5000
    rate_limit  = 2000  # 2000 req/s
  }

  quota_settings {
    limit  = 10000000  # 10M requests per month
    period = "MONTH"
  }
}

# API key
resource "aws_api_gateway_api_key" "customer_key" {
  name = "customer-${var.customer_id}"
}

# Associate key with usage plan
resource "aws_api_gateway_usage_plan_key" "main" {
  key_id        = aws_api_gateway_api_key.customer_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.standard.id
}
```

---

## Monitoring & Alerting

### Security Monitoring

**CloudWatch Alarms**:

```hcl
# WAF blocked requests
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  alarm_name          = "paracle-waf-high-blocked-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = 300
  statistic           = "Sum"
  threshold           = 1000
  alarm_description   = "High number of WAF blocked requests"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]

  dimensions = {
    WebACL = aws_wafv2_web_acl.paracle.name
    Region = var.aws_region
  }
}

# Rate limit exceeded
resource "aws_cloudwatch_metric_alarm" "rate_limit_exceeded" {
  alarm_name          = "paracle-high-rate-limit-rejections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "rate_limit_exceeded_total"
  namespace           = "Paracle/API"
  period              = 300
  statistic           = "Sum"
  threshold           = 500
  alarm_description   = "High number of rate limit rejections"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
}

# Invalid authentication attempts
resource "aws_cloudwatch_metric_alarm" "auth_failures" {
  alarm_name          = "paracle-high-auth-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "auth_failures_total"
  namespace           = "Paracle/API"
  period              = 300
  statistic           = "Sum"
  threshold           = 100
  alarm_description   = "High number of authentication failures (possible attack)"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
}
```

### Security Dashboards

**Grafana Dashboard JSON**:

```json
{
  "dashboard": {
    "title": "Paracle Security Dashboard",
    "panels": [
      {
        "title": "WAF Blocked Requests",
        "targets": [
          {
            "expr": "rate(aws_wafv2_blocked_requests_total[5m])",
            "legendFormat": "Blocked Requests/s"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Rate Limit Rejections",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=\"429\"}[5m])",
            "legendFormat": "Rate Limited/s"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Authentication Failures",
        "targets": [
          {
            "expr": "rate(auth_failures_total[5m])",
            "legendFormat": "Auth Failures/s"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Top Blocked IPs",
        "targets": [
          {
            "expr": "topk(10, sum by (source_ip) (rate(aws_wafv2_blocked_requests_total[1h])))",
            "legendFormat": "{{source_ip}}"
          }
        ],
        "type": "table"
      }
    ]
  }
}
```

---

## Security Headers

### FastAPI Middleware

**Comprehensive Security Headers**:

```python
# packages/paracle_api/middleware/security_headers.py
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Strict Transport Security
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.openai.com https://api.anthropic.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=()"
        )

        # Remove server header
        response.headers.pop("Server", None)

        return response

# Apply middleware
app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)
```

---

## Compliance & Auditing

### Audit Logging

**Comprehensive Audit Trail**:

```python
# packages/paracle_audit/audit_logger.py
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

class AuditEvent(BaseModel):
    timestamp: datetime
    event_type: str  # create, update, delete, access, auth, etc.
    user_id: Optional[str]
    resource_type: str  # agent, workflow, tool, etc.
    resource_id: str
    action: str
    status: str  # success, failure
    ip_address: str
    user_agent: str
    request_id: str
    changes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class AuditLogger:
    def __init__(self, db: Session):
        self.db = db

    def log_event(self, event: AuditEvent):
        """Log security-relevant event to audit trail."""
        # Store in database
        audit_record = AuditLog(
            timestamp=event.timestamp,
            event_type=event.event_type,
            user_id=event.user_id,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action,
            status=event.status,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            request_id=event.request_id,
            changes=json.dumps(event.changes) if event.changes else None,
            metadata=json.dumps(event.metadata) if event.metadata else None,
        )
        self.db.add(audit_record)
        self.db.commit()

        # Also log to CloudWatch for analysis
        logger.info(
            "AUDIT",
            extra={
                "event_type": event.event_type,
                "user_id": event.user_id,
                "resource": f"{event.resource_type}/{event.resource_id}",
                "action": event.action,
                "status": event.status,
                "ip": event.ip_address,
            },
        )

# Usage in API endpoints
@app.post("/api/v1/agents")
async def create_agent(
    agent: AgentCreate,
    request: Request,
    db: Session = Depends(get_db),
    audit: AuditLogger = Depends(get_audit_logger),
):
    # Create agent
    new_agent = Agent(**agent.dict())
    db.add(new_agent)
    db.commit()

    # Audit log
    audit.log_event(
        AuditEvent(
            timestamp=datetime.utcnow(),
            event_type="agent.created",
            user_id=request.state.user_id,
            resource_type="agent",
            resource_id=new_agent.id,
            action="create",
            status="success",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            request_id=request.state.request_id,
            metadata={"agent_name": new_agent.name},
        )
    )

    return new_agent
```

### Compliance Reports

**Automated Compliance Reporting**:

```python
# packages/paracle_governance/compliance.py
from datetime import datetime, timedelta
from typing import List

class ComplianceReporter:
    def generate_soc2_report(self, period_days: int = 30) -> Dict:
        """Generate SOC2 Type II compliance report."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        report = {
            "report_type": "SOC2 Type II",
            "period": f"{start_date.date()} to {end_date.date()}",
            "generated_at": datetime.utcnow().isoformat(),
            "controls": []
        }

        # CC6.1: Logical Access Controls
        report["controls"].append({
            "control_id": "CC6.1",
            "name": "Logical Access Controls",
            "status": "pass",
            "evidence": [
                f"Total auth events: {self.count_auth_events(start_date, end_date)}",
                f"Failed auth attempts: {self.count_failed_auth(start_date, end_date)}",
                f"MFA enabled users: {self.count_mfa_users()}",
            ],
        })

        # CC7.2: System Monitoring
        report["controls"].append({
            "control_id": "CC7.2",
            "name": "System Monitoring",
            "status": "pass",
            "evidence": [
                "CloudWatch alarms configured",
                "24/7 monitoring active",
                f"Security incidents: {self.count_incidents(start_date, end_date)}",
            ],
        })

        return report
```

---

## Related Documentation

- [monitoring-setup.md](../deployment/monitoring-setup.md) - Monitoring configuration
- [incident-response.md](../deployment/incident-response.md) - Security incident procedures
- [secrets-management.md](../deployment/secrets-management.md) - API key security
- [disaster-recovery.md](../deployment/disaster-recovery.md) - DR procedures

---

**Last Updated**: 2026-01-18
**Next Review**: 2026-02-18
**Owner**: Security Team (security@paracle.com)
