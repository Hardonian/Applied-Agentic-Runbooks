"""Static contract tests for production deployment hardening."""

from pathlib import Path


def test_helm_has_security_and_reliability_resources() -> None:
    templates = Path("deploy/k8s/helm/agent-factory/templates")
    expected = {
        "pdb.yaml",
        "networkpolicy.yaml",
        "serviceaccount.yaml",
        "pvc.yaml",
        "migration-job.yaml",
        "servicemonitor.yaml",
        "prometheusrule.yaml",
    }
    assert expected <= {path.name for path in templates.iterdir()}
    deployment = (templates / "deployment.yaml").read_text(encoding="utf-8")
    assert "readOnlyRootFilesystem" in Path(
        "deploy/k8s/helm/agent-factory/values.yaml"
    ).read_text(encoding="utf-8")
    assert "arena-artifacts" in deployment


def test_production_compose_uses_distributed_streams_and_migrations() -> None:
    compose = Path("deploy/docker-compose.production.yml").read_text(encoding="utf-8")
    assert "EVENT_BUS_BACKEND: redis" in compose
    assert "service_completed_successfully" in compose
    assert "read_only: true" in compose
    assert "jaeger:" in compose


def test_supply_chain_workflow_generates_sbom_and_scans_image() -> None:
    workflow = Path(".github/workflows/supply-chain.yml").read_text(encoding="utf-8")
    assert "anchore/sbom-action" in workflow
    assert "aquasecurity/trivy-action" in workflow
    assert "id-token: write" in workflow
