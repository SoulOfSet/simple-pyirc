import argparse
from time import sleep
import urwid
from irc_client import IRCClient


def parse_arguments():
    """
    Parses command-line arguments for IRC client configuration.

    Returns:
        Namespace: An argparse.Namespace object containing the values for configured options.
    """
    parser = argparse.ArgumentParser(description='Simple IRC Client')
    parser.add_argument('--host', required=True, help='IRC server hostname')
    parser.add_argument('--port', type=int, required=True, help='IRC server port')
    parser.add_argument('--userinfo', required=True, help='User info for IRC registration')
    parser.add_argument('--nickname', required=True, help='Nickname for the IRC session')
    parser.add_argument('--default-channel', required=True, help='Default channel to join')
    return parser.parse_args()


# Global lists for demo purposes. In a real application, these would be dynamically updated.
channels = []
users = []
current_channel = '#general'


class MessageEdit(urwid.Edit):
    """
    Custom Edit widget for handling IRC messages and commands.

    Args:
        irc_client (IRCClient): The IRC client to send messages.
        chat_body (urwid.ListBox): Widget where chat messages will be displayed.
        user_box (urwid.LineBox): Widget displaying the list of users.
        channel_list_widget (urwid.SimpleFocusListWalker): Widget displaying the list of channels.
    """

    def __init__(self, irc_client, chat_body, user_box, channel_list_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.irc_client = irc_client
        self.chat_body = chat_body
        self.user_box = user_box
        self.channel_list_widget = channel_list_widget
        self.channel_widgets = {}

    def keypress(self, size, key):
        """
        Handles keypress events to process IRC commands and message sending.

        Args:
            size (tuple): Size of the widget.
            key (str): The key pressed.
        """
        if key == 'enter':
            message = self.get_edit_text().strip()
            if message.startswith("/join "):
                channel = message.split("/join ", 1)[1]
                # Validate the channel name
                if not self.is_valid_channel_name(channel):
                    self.chat_body.body.append(urwid.Text(f"Invalid channel name: {channel}"))
                elif channel in self.irc_client.channels:
                    self.switch_channel(channel)  # Switch to the channel if it already exists
                elif self.irc_client.join_channel(channel):
                    self.update_current_channel(channel)
                self.set_edit_text('')
            elif message.startswith("/switch "):
                channel = message.split("/switch ", 1)[1]
                if channel in self.irc_client.channels:
                    self.switch_channel(channel)
                else:
                    self.chat_body.body.append(urwid.Text(f"Not in channel: {channel}"))
                self.set_edit_text('')
            elif message.startswith("/whisp "):
                try:
                    command, username, private_message = message.split(' ', 2)
                    self.irc_client.send_message(username, private_message)
                    self.chat_body.body.append(urwid.Text(f"You whispered to {username}: {private_message}"))
                except ValueError:
                    self.chat_body.body.append(urwid.Text("Incorrect whisper format. Use /whisp username message"))
                self.set_edit_text('')
            elif message:
                self.irc_client.send_message(current_channel, message)
                self.chat_body.body.append(urwid.Text((f"You: {message}")))
                self.set_edit_text('')
        else:
            super().keypress(size, key)

    def is_valid_channel_name(self, channel_name):
        """
        Validates IRC channel names based on predefined criteria.

        Args:
            channel_name (str): The channel name to validate.

        Returns:
            bool: True if the channel name is valid, False otherwise.
        """
        return channel_name.startswith('#') and ' ' not in channel_name and 1 < len(channel_name) <= 50

    def update_current_channel(self, channel):
        """
        Updates the current IRC channel. Clears the chat body, appends a join message, requests the user list, and updates the UI to reflect the current channel.

        Args:
            channel (str): The channel to set as the current channel.

        Returns:
            None
        """
        global current_channel
        current_channel = channel
        self.chat_body.body.clear()
        self.chat_body.body.append(urwid.Text(f"Joined {channel}"))
        self.irc_client.request_user_list(channel)
        if channel not in self.channel_widgets:
            channel_widget = urwid.AttrMap(urwid.Text(channel), 'channel', 'current_channel')
            self.channel_widgets[channel] = channel_widget
            self.channel_list_widget.append(channel_widget)
        self.highlight_current_channel(channel)

    def switch_channel(self, channel):
        """
        Switches the user's view to another channel. Clears the chat body, appends a switch message, requests the user list for the new channel, and updates the UI to highlight the new channel.

        Args:
            channel (str): The new channel to switch to.

        Returns:
            None
        """
        global current_channel
        current_channel = channel
        self.chat_body.body.clear()
        self.chat_body.body.append(urwid.Text(f"Switched to {channel}"))
        self.irc_client.request_user_list(channel)
        self.highlight_current_channel(channel)

    def highlight_current_channel(self, channel):
        """
        Highlights the current channel in the channel list to visually indicate which channel is active.

        Args:
            channel (str): The channel to highlight as the current active channel.

        Returns:
            None
        """
        # Reset all channels to default look
        for chan, widget in self.channel_widgets.items():
            widget.set_attr_map({None: 'channel'})
        # Highlight the current channel
        if channel in self.channel_widgets:
            self.channel_widgets[channel].set_attr_map({None: 'current_channel'})


class SafeFrame(urwid.Frame):
    def mouse_event(self, size, event, button, col, row, focus):
        if self.footer is not None:
            return super().mouse_event(size, event, button, col, row, focus)
        # Else, ignore mouse events in the footer area
        return False


def update_chat_body(sender, channel_or_user, message, chat_body, loop):
    """
    Updates the chat body with new messages. It is triggered by the message event from the IRC client.

    Args:
        sender (str): The sender of the message.
        channel_or_user (str): The channel or user from which the message was received.
        message (str): The content of the message.
        chat_body (urwid.ListBox): The ListBox widget where the chat messages are displayed.
        loop (urwid.MainLoop): The main event loop of the application.

    Returns:
        None
    """
    if channel_or_user == 'private':
        chat_body.body.append(urwid.Text(f"Private from {sender}: {message}"))
    else:
        chat_body.body.append(urwid.Text(f"{sender}: {message}"))
    loop.draw_screen()


def update_user_list(channel, user_box, loop, irc_client):
    """
    Updates the list of users in the user box when a user joins, leaves, or is listed in a channel.

    Args:
        channel (str): The channel for which the user list is updated.
        user_box (urwid.LineBox): The LineBox containing the user list.
        loop (urwid.MainLoop): The main event loop of the application.
        irc_client (IRCClient): The IRC client instance to fetch user information.

    Returns:
        None
    """
    global current_channel  # Refer to the global variable
    if channel == current_channel:  # Compare with the global variable
        user_list_widget = user_box.base_widget  # Assuming user_box is a LineBox around a ListBox
        user_list_widget.body.clear()  # Clear the current list

        # Re-populate the list with updated users
        updated_users = sorted(irc_client.channel_users.get(channel, []))
        for user in updated_users:
            user_list_widget.body.append(urwid.Text(user))

        loop.draw_screen()  # Ensure the UI is updated


def setup_ui(irc_client, default_channel):
    """
    Sets up the user interface for the IRC client using the urwid library.

    Args:
        irc_client (IRCClient): The IRC client to interact with.
        default_channel (str): The default channel to join upon starting the client.

    Returns:
        urwid.MainLoop: The main loop configured with the IRC client UI.
    """
    palette = [
        ('header', 'light cyan,bold', 'black'),
        ('chat', 'white', 'black'),
        ('footer', 'light gray', 'black'),
        ('channel', 'dark cyan', 'black'),
        ('user', 'dark green', 'black'),
        ('current_channel', 'white', 'dark blue'),  # New attribute for highlighting the current channel
    ]
    header = urwid.AttrMap(urwid.Text("IRC Client", align='center'), 'header')
    chat_body = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.Text("Simple PyIRC")]))
    chat_view = urwid.BoxAdapter(SafeFrame(body=chat_body), height=20)

    channel_list_widget = urwid.SimpleFocusListWalker([urwid.AttrMap(urwid.Text(chan), 'channel') for chan in channels])
    channel_list = urwid.ListBox(channel_list_widget)
    channel_box = urwid.LineBox(channel_list, title='Channels')

    user_list = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.AttrMap(urwid.Text(user), 'user') for user in users]))
    user_box = urwid.LineBox(user_list, title='Users')

    # Initialize message_edit with irc_client, chat_body, user_box, and channel_list_widget
    message_edit = MessageEdit(irc_client, chat_body, user_box, channel_list_widget, "Message: ")

    # Initialize the channel_widgets dictionary for the initial channel
    initial_channel_widget = urwid.AttrMap(urwid.Text(default_channel), 'channel', 'current_channel')
    message_edit.channel_widgets[default_channel] = initial_channel_widget
    channel_list_widget.append(initial_channel_widget)

    footer = urwid.AttrMap(urwid.Columns([message_edit]), 'footer')

    columns = urwid.Columns([
        ('weight', 1, channel_box),
        ('weight', 4, chat_view),
        ('weight', 1, user_box),
    ])
    layout = SafeFrame(body=columns, header=header, footer=footer)

    loop = urwid.MainLoop(layout, palette)

    irc_client.message_event.subscribe(
        lambda sender, channel, message: update_chat_body(sender, channel, message, chat_body, loop))
    irc_client.user_event.subscribe(lambda user, channel, action: update_user_list(channel, user_box, loop, irc_client))
    irc_client.names_event.subscribe(lambda channel, names: update_user_list(channel, user_box, loop, irc_client))

    return loop


if __name__ == "__main__":
    # Parse command-line arguments to get configuration for the IRC client.
    args = parse_arguments()
    irc_client = IRCClient(args.host, args.port, args.userinfo)
    current_channel = args.default_channel

    # Attempt to connect to the IRC server using the host and port provided.
    if irc_client.connect():
        irc_client.register(args.nickname)
        sleep(2)
        # Join the default channel specified in the command line arguments.
        irc_client.join_channel(current_channel)
        sleep(2)

        # Set up the user interface using the 'urwid' library and pass the irc_client and current_channel.
        loop = setup_ui(irc_client, current_channel)
        message_edit = loop.widget.footer.original_widget[0]
        message_edit.highlight_current_channel(current_channel)
        irc_client.request_user_list(current_channel)

        # Start the urwid main loop to run the interactive UI.
        loop.run()
    else:
        # If connection to the server fails, print an error message.
        print("Unable to connect to server")

