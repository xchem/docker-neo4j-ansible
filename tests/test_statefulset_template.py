"""Tests for the graph role's StatefulSet template.

The template is rendered with the role's defaults and vars
and the resulting manifest is checked.
"""
from pathlib import Path

import jinja2
import yaml

ROLE_DIR = Path(__file__).parent.parent / "roles" / "graph"


def render_statefulset(**overrides):
    """Renders the StatefulSet template, returning the manifest as a dictionary."""
    variables = {}
    for vars_file in ("defaults/main.yaml", "vars/main.yaml"):
        variables.update(yaml.safe_load((ROLE_DIR / vars_file).read_text()))
    variables.update(overrides)

    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(ROLE_DIR / "templates")),
        undefined=jinja2.StrictUndefined,
    )
    template = environment.get_template("statefulset.yaml.j2")
    return yaml.safe_load(template.render(**variables))


def graph_container(manifest):
    containers = manifest["spec"]["template"]["spec"]["containers"]
    return next(c for c in containers if c["name"] == "graph")


def test_graph_readiness_probe_is_a_tcp_check_on_the_bolt_port():
    # The probe must not depend on the contents of Neo4j's (rotated) debug log.
    probe = graph_container(render_statefulset())["readinessProbe"]

    assert "exec" not in probe
    assert probe["tcpSocket"] == {"port": 7687}


def test_graph_readiness_probe_is_a_tcp_check_when_bolt_tls_is_enabled():
    probe = graph_container(render_statefulset(graph_ssl_enabled=True))["readinessProbe"]

    assert probe["tcpSocket"] == {"port": 7687}
