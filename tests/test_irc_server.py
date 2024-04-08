import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from irc_client import IRCClient

irc_server = DockerContainer("inspircd/inspircd-docker")
userinfo = "Test User for IRC"


@pytest.fixture(scope="module", autouse=True)
def setup():
    irc_server.with_exposed_ports(6667).start()
    wait_for_logs(irc_server, "InspIRCd is now running as", timeout=30)  # Adjust the message accordingly
    yield irc_server
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
    client = IRCClient(host=host, port=int(port),
                       userinfo=userinfo)  # Initialize the IRCClient with the server's host and port

    # Assert that the client can connect to the IRC server
    assert client.connect(), "Client failed to connect to the IRC server."

    # Assert that the client can send a ping command and receive a response
    assert client.send_ping(), "Client failed to send PING to the IRC server."

    # Disconnect the client from the server
    client.disconnect()


def test_irc_client_registration_and_nickname_change():
    """
    Tests the IRCClient's ability to register a user with a nickname and user info on an IRC server,
    and then update the user's nickname after registration.

    This test ensures that the IRCClient class can not only establish a connection with an IRC server but also
    successfully register a user with initial nickname and user info. It further verifies the client's ability
    to update the user's nickname post-registration, as per IRC protocol specifications.

    The test uses a Docker container running an IRC server to simulate a real-world IRC environment. This isolated
    environment allows for a controlled test of the IRCClient's registration and nickname updating functionalities.

    Workflow:
    1. Connects to the IRC server running within a Docker container.
    2. Registers a user with an initial nickname and user info.
    3. Updates the user's nickname to a new value.
    4. Verifies that the nickname was successfully updated.

    Assertions:
    1. The client can connect to the IRC server.
    2. The client can register with the IRC server using the initial nickname and user info.
    3. The client can successfully update the nickname after registration.
    4. The updated nickname is correctly reflected within the client.

    If any of these operations fail, the test will indicate an issue with the IRCClient's implementation of
    the registration process or its ability to handle nickname updates as per IRC protocol.

    Note: This test assumes the IRC server responds appropriately to NICK and USER commands as per standard
    IRC protocol behavior. Adjustments may be needed based on the specific IRC server's implementation details.
    """
    host = irc_server.get_container_host_ip()
    port = irc_server.get_exposed_port(6667)

    client = IRCClient(host=host, port=int(port), userinfo=userinfo)

    # Connect to the IRC server
    assert client.connect(), "Client failed to connect to the IRC server."

    # Initial registration with a nickname
    initial_nickname = "testUser"
    assert client.register(initial_nickname), "Client failed to register with the IRC server."

    # Change the nickname
    new_nickname = "newTestUser"
    assert client.set_nickname(new_nickname), "Client failed to update the nickname."

    # Optionally, you can verify that the new nickname has been set correctly
    assert client.nickname == new_nickname, "The client's nickname was not updated correctly."

    # Disconnect the client from the server
    client.disconnect()


def test_irc_client_join_channel():
    """
    Tests the IRCClient's ability to join a channel on an IRC server.

    This test ensures that the IRCClient class can join a channel after establishing a connection with an IRC server.
    It verifies that the channel join attempt is made and that the internal state of the client is updated to reflect
    the joined channel.

    The test uses a Docker container running an IRC server to simulate a real-world IRC environment. This isolated
    environment allows for a controlled test of the IRCClient's channel joining functionality.

    Assertions:
    1. The client can connect to the IRC server.
    2. The client can successfully join a channel.
    3. The client's internal state is updated to include the joined channel.

    If any of these operations fail, the test will fail, indicating issues with the IRCClient's implementation of
    channel joining or state management.
    """
    host = irc_server.get_container_host_ip()
    port = irc_server.get_exposed_port(6667)
    client = IRCClient(host=host, port=int(port), userinfo=userinfo)

    assert client.connect(), "Client failed to connect to the IRC server."
    channel_name = "#testChannel"
    assert client.join_channel(channel_name), "Client failed to join the channel."
    assert channel_name in client.channels, "Channel was not added to the client's internal state."

    client.disconnect()


def test_irc_client_leave_channel():
    """
    Tests the IRCClient's ability to leave a channel on an IRC server.

    After joining a channel, this test ensures that the IRCClient can leave the channel and updates its internal
    state to reflect the channel has been left. It verifies the channel leave attempt is made and the client no
    longer tracks the channel as joined.

    The test uses a Docker container running an IRC server to simulate a real-world IRC environment, allowing for
    a controlled test of the IRCClient's channel leaving functionality.

    Assertions:
    1. The client can connect to the IRC server.
    2. The client can successfully leave a channel it had joined.
    3. The client's internal state is updated to remove the left channel.

    If any of these operations fail, the test will fail, indicating issues with the IRCClient's implementation of
    channel leaving or state management.
    """
    host = irc_server.get_container_host_ip()
    port = irc_server.get_exposed_port(6667)
    client = IRCClient(host=host, port=int(port), userinfo=userinfo)

    assert client.connect(), "Client failed to connect to the IRC server."
    channel_name = "#testChannel"
    # Ensure the client is part of the channel before attempting to leave
    client.join_channel(channel_name)
    assert client.leave_channel(channel_name), "Client failed to leave the channel."
    assert channel_name not in client.channels, "Channel was not removed from the client's internal state."

    client.disconnect()
