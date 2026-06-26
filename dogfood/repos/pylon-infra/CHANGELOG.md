# Changelog

All notable changes to pylon-infra. Format follows
[Keep a Changelog](https://keepachangelog.com/), and the estate is
versioned per shipped stage.

## [Unreleased]

### Planned
- Cluster autoscaler migration for prod node pools (PI-215, Stage 5).
- Rewrite of the pod-eviction-storm runbook (PI-220).
- Provision Grafana dashboards from Terraform (PI-231).

## [0.4.0] - 2026-04-30

### Added
- cert-manager for auto-renewing TLS certificates.
- sealed-secrets controller; secrets now committed as ciphertext only.

### Security
- Removed the last plaintext secret references from `k8s/base/`.

## [0.3.0] - 2026-03-25

### Added
- Prometheus + Grafana observability stack.
- SLO dashboards and alerting (availability, p99 latency, budget burn).

## [0.2.0] - 2026-02-18

### Added
- GitHub Actions CI: fmt/validate/plan on PRs, apply-on-main pipeline.
- Manual approval gate for prod applies.

## [0.1.0] - 2026-01-22

### Added
- Base cluster via Terraform: dev/staging/prod, three AZs, general +
  spot node pools, remote locked state.
