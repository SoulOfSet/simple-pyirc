from testcontainers.core.container import DockerContainer
import pytest
from testcontainers.core.waiting_utils import wait_for_logs

irc_server = DockerContainer("inspircd/inspircd-docker")


# Setup IRC server in testcontainers
@pytest.fixture(scope="module", autouse=True)
def setup():
    irc_server.with_exposed_ports(6667).start()


# Verify that IRC server comes up
def test_irc_server_up():
    assert irc_server.get_exposed_port(6667) is not None, "IRC server should expose port 6667"
