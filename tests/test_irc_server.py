from testcontainers.core.container import DockerContainer
import pytest

@pytest.fixture(scope="module")
def irc_server():
    with DockerContainer("inspircd/inspircd-docker") as container:
        container.with_exposed_ports(6667)  # default IRC port
        yield container

def test_irc_server_up(irc_server):
    assert irc_server.get_exposed_port(6667) is not None, "IRC server should expose port 6667"

