from time import sleep

import urwid

from irc_client import IRCClient

# Global lists for demo purposes. In a real application, these would be dynamically updated.
channels = ['#general']
users = []
current_channel = '#general'

class MessageEdit(urwid.Edit):
    def __init__(self, irc_client, chat_body, user_box, channel_list_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.irc_client = irc_client
        self.chat_body = chat_body
        self.user_box = user_box
        self.channel_list_widget = channel_list_widget

    def keypress(self, size, key):
        if key == 'enter':
            message = self.get_edit_text().strip()
            if message.startswith("/join "):
                channel = message.split("/join ", 1)[1]
                # Validate the channel name
                if not self.is_valid_channel_name(channel):
                    self.chat_body.body.append(urwid.Text(f"Invalid channel name: {channel}"))
                elif self.irc_client.join_channel(channel):
                    global current_channel
                    current_channel = channel
                    self.chat_body.body.clear()
                    self.chat_body.body.append(urwid.Text(f"Joined {channel}"))
                    self.irc_client.request_user_list(channel)
                    self.channel_list_widget.append(urwid.AttrMap(urwid.Text(channel), 'channel'))
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



def on_send_button_pressed(irc_client, message_edit, chat_body, button):
    message = message_edit.get_edit_text().strip()
    if message:
        irc_client.send_message(current_channel, message)
        chat_body.body.append(urwid.Text((f"You: {message}")))
        message_edit.set_edit_text('')


def setup_ui(irc_client):
    palette = [('header', 'light cyan,bold', 'black'), ('chat', 'white', 'black'),
               ('footer', 'light gray', 'black'), ('channel', 'dark cyan', 'black'),
               ('user', 'dark green', 'black'), ]
    header = urwid.AttrMap(urwid.Text("IRC Client", align='center'), 'header')
    chat_body = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.Text("Simple PyIRC")]))
    chat_view = urwid.BoxAdapter(SafeFrame(body=chat_body), height=20)

    channel_list_widget = urwid.SimpleFocusListWalker([urwid.AttrMap(urwid.Text(chan), 'channel') for chan in channels])
    channel_list = urwid.ListBox(channel_list_widget)
    channel_box = urwid.LineBox(channel_list, title='Channels')

    user_list = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.AttrMap(urwid.Text(user), 'user') for user in users]))
    user_box = urwid.LineBox(user_list, title='Users')

    # Pass user_box and channel_list_widget to MessageEdit
    message_edit = MessageEdit(irc_client, chat_body, user_box, channel_list_widget, "Message: ")

    send_button = urwid.Button("Send")
    urwid.connect_signal(send_button, 'click', on_send_button_pressed,
                         user_args=[irc_client, message_edit, chat_body])

    footer = urwid.AttrMap(urwid.Columns([message_edit, send_button]), 'footer')

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
    irc_client = IRCClient("localhost", 32855, "Test User")
    if irc_client.connect():
        irc_client.register("TestUser")
        sleep(1)
        irc_client.join_channel("#general")
        sleep(1)
        loop = setup_ui(irc_client)
        irc_client.request_user_list("#general")
        loop.run()

