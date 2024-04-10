import argparse
from time import sleep

import urwid

from irc_client import IRCClient


def parse_arguments():
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
    def __init__(self, irc_client, chat_body, user_box, channel_list_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.irc_client = irc_client
        self.chat_body = chat_body
        self.user_box = user_box
        self.channel_list_widget = channel_list_widget
        self.channel_widgets = {}

    def keypress(self, size, key):
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
            elif message:
                self.irc_client.send_message(current_channel, message)
                self.chat_body.body.append(urwid.Text((f"You: {message}")))
                self.set_edit_text('')
        else:
            super().keypress(size, key)

    def is_valid_channel_name(self, channel_name):
        """Validates IRC channel names. Must start with #, not contain spaces, and be 1-50 characters long."""
        return channel_name.startswith('#') and ' ' not in channel_name and 1 < len(channel_name) <= 50

    def update_current_channel(self, channel):
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
        global current_channel
        current_channel = channel
        self.chat_body.body.clear()
        self.chat_body.body.append(urwid.Text(f"Switched to {channel}"))
        self.irc_client.request_user_list(channel)
        self.highlight_current_channel(channel)

    def highlight_current_channel(self, channel):
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
    chat_body.body.append(urwid.Text(f"{sender}: {message}"))
    loop.draw_screen()


def update_user_list(channel, user_box, loop, irc_client):
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
    args = parse_arguments()

    # Use args to get command-line arguments
    irc_client = IRCClient(args.host, args.port, args.userinfo)
    current_channel = args.default_channel  # Set the global current_channel to the command-line argument

    if irc_client.connect():
        irc_client.register(args.nickname)
        sleep(2)
        irc_client.join_channel(current_channel)
        sleep(2)
        loop = setup_ui(irc_client, current_channel)
        message_edit = loop.widget.footer.original_widget[0]
        message_edit.highlight_current_channel(current_channel)
        irc_client.request_user_list(current_channel)
        loop.run()