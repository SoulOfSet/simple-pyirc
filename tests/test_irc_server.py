import pytest
from testcontainers.core.container import DockerContainer
from client import IRCClient

irc_server = DockerContainer("inspircd/inspircd-docker")


@pytest.fixture(scope="module", autouse=True)
def setup():
    irc_server.with_exposed_ports(6667).start()
    yield
    irc_server.stop()


def test_irc_client_connection():
    """
    Tests the IRCClient's ability to connect to an IRC server, send a ping, and then disconnect.

    This test ensures that the IRCClient class can establish a connection with an IRC server,
    successfully send a ping message to it, and then cleanly disconnect without errors.

    The test uses a Docker container running an IRC server for the testing environment. The
    `irc_server` fixture should start the container and expose the necessary port before this
    test runs.

    Assertions:
        1. The client can connect to the IRC server.
        2. The client can send a ping command to the server.
        3. Both assertions must pass for the test to succeed.

    If any of these operations fail, the test will fail, indicating issues with the IRCClient's
    implementation or its interaction with the specified IRC server.
    """
    host = irc_server.get_container_host_ip()  # Get the IRC server's host IP from the Docker container
    port = irc_server.get_exposed_port(6667)  # Get the exposed port from the Docker container
    client = IRCClient(host=host, port=int(port))  # Initialize the IRCClient with the server's host and port

    # Assert that the client can connect to the IRC server
    assert client.connect(), "Client failed to connect to the IRC server."

    # Assert that the client can send a ping command and receive a response
    assert client.send_ping(), "Client failed to send PING to the IRC server."

    # Disconnect the client from the server
    client.disconnect()
