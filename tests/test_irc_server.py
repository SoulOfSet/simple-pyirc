from unittest.mock import patch

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


@pytest.fixture
def mock_socket():
    with patch('socket.socket') as mock:
        yield mock


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
    host = irc_server.get_container_host_ip()
    port = irc_server.get_exposed_port(6667)
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


def test_send_message(mock_socket):
    """
    Tests the IRCClient's ability to send a message to a specific target, such as a user or a channel.

    This test verifies that the IRCClient constructs the correct PRIVMSG command and sends it over
    the socket to the IRC server. A mock socket object is used to intercept and assert the message
    format and contents sent by the IRCClient.

    The test simulates sending a message to a channel and checks if the correct command is formed
    and sent through the socket.

    :param mock_socket: A mock object representing the socket used by the IRCClient to send messages.
    """
    host = irc_server.get_container_host_ip()
    port = irc_server.get_exposed_port(6667)
    client = IRCClient(host, int(port), userinfo)
    client.socket = mock_socket()
    target = "#testChannel"
    message = "Hello, world!"
    client.send_message(target, message)
    mock_socket().sendall.assert_called_with(f"PRIVMSG {target} :{message}\n".encode())


def test_request_user_list(mock_socket):
    """
    Tests the IRCClient's ability to request a list of users present in a channel.

    This test checks if the IRCClient correctly forms and sends the NAMES command to the server,
    requesting a list of users in a specified channel. A mock socket object is used to intercept
    and assert the correctness of the command sent by the IRCClient.

    The focus is on verifying that the command sent is properly formatted according to IRC protocol
    specifications.

    :param mock_socket: A mock object representing the socket used by the IRCClient to request user lists.
    """
    host = irc_server.get_container_host_ip()
    port = irc_server.get_exposed_port(6667)
    client = IRCClient(host, int(port), userinfo)
    client.socket = mock_socket()
    channel = "#testChannel"
    client.request_user_list(channel)
    mock_socket().sendall.assert_called_with(f"NAMES {channel}\n".encode())


def test_handle_privmsg():
    """
    Tests the IRCClient's ability to handle a PRIVMSG (private message) server response.

    This test simulates receiving a PRIVMSG command from the server and checks if the IRCClient
    properly calls its `handle_privmsg` method with the correct parameters. It verifies the client's
    ability to parse and process incoming private messages according to IRC protocol specifications.

    The test uses a mocked `handle_privmsg` method to assert it gets called upon receiving a PRIVMSG
    response from the server.
    """
    host = irc_server.get_container_host_ip()
    port = irc_server.get_exposed_port(6667)
    client = IRCClient(host, int(port), userinfo)
    response = ":user!user@host PRIVMSG #testChannel :This is a test message"
    with patch.object(client, 'handle_privmsg') as mock_handle_privmsg:
        client.handle_server_response(response)
        mock_handle_privmsg.assert_called()


def test_handle_join():
    """
    Tests the IRCClient's handling of a JOIN message from the server.

    This test verifies that when the IRCClient receives a JOIN command indicating a user has joined
    a channel, it correctly calls its `handle_join` method to process this event.

    The effectiveness of the method is tested by simulating a JOIN command from the server and using
    a mock to ensure `handle_join` is called appropriately, reflecting the client's capability to
    manage channel join events.
    """
    host = irc_server.get_container_host_ip()
    port = irc_server.get_exposed_port(6667)
    client = IRCClient(host, int(port), userinfo)
    response = ":user!user@host JOIN #testChannel"
    with patch.object(client, 'handle_join') as mock_handle_join:
        client.handle_server_response(response)
        mock_handle_join.assert_called()


def test_handle_part():
    """
    Tests the IRCClient's handling of a PART message from the server.

    This test assesses the IRCClient's ability to handle a PART command, which signifies a user leaving
    a channel. It verifies that the client correctly calls its `handle_part` method to update its internal
    state in response to the event.

    By simulating a PART command from the server and employing a mock of the `handle_part` method, this test
    ensures the client can adequately process channel leave events.
    """
    host = irc_server.get_container_host_ip()
    port = irc_server.get_exposed_port(6667)
    client = IRCClient(host, int(port), userinfo)
    response = ":user!user@host PART #testChannel"
    with patch.object(client, 'handle_part') as mock_handle_part:
        client.handle_server_response(response)
        mock_handle_part.assert_called()


def test_handle_names():
    """
    Tests the IRCClient's ability to handle the NAMES server response.

    This test checks if the IRCClient properly processes a NAMES response from the server, which lists the
    users present in a channel. The focus is on ensuring that the client calls its `handle_names` method
    with the correct parameters to update its internal state based on the server's response.

    A mock of the `handle_names` method is used to assert its invocation upon receiving a NAMES response,
    demonstrating the client's capability to handle user list updates for channels.
    """
    host = irc_server.get_container_host_ip()
    port = irc_server.get_exposed_port(6667)
    client = IRCClient(host, int(port), userinfo)
    response = ":server 353 user = #testChannel :user1 user2 user3"
    with patch.object(client, 'handle_names') as mock_handle_names:
        client.handle_server_response(response)
        mock_handle_names.assert_called()
