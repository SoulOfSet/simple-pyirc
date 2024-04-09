from time import sleep

import urwid

from irc_client import IRCClient

# Global lists for demo purposes. In a real application, these would be dynamically updated.
channels = ['#general', '#help', '#random']
users = ['user1', 'user2', 'user3']


def update_chat_body(sender, channel_or_user, message, chat_body, loop):
    chat_body.body.append(urwid.Text(f"{sender}: {message}"))
    loop.draw_screen()


def update_user_list(user, channel, action, user_box):
    # Placeholder for updating the user list based on join/part events
    pass


def on_send_button_pressed(button, irc_client, message_edit, chat_body):
    message = message_edit.get_edit_text()
    irc_client.send_message("#general", message)  # Placeholder for sending message logic
    chat_body.body.contents.append((urwid.Text(("chat", message)), chat_body.options()))
    message_edit.set_edit_text('')  # Clear the input field after sending


def setup_ui(irc_client):
    palette = [('header', 'light cyan,bold', 'black'), ('chat', 'white', 'black'),
               ('footer', 'light gray', 'black'), ('channel', 'dark cyan', 'black'),
               ('user', 'dark green', 'black'), ]
    header = urwid.AttrMap(urwid.Text("IRC Client", align='center'), 'header')
    chat_body = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.Text("Welcome to the IRC Client")]))
    chat_view = urwid.BoxAdapter(urwid.Frame(body=chat_body), height=20)
    message_edit = urwid.Edit("Message: ")
    send_button = urwid.Button("Send")
    urwid.connect_signal(send_button, 'click', on_send_button_pressed,
                         user_args=[irc_client, message_edit, chat_body])
    footer = urwid.AttrMap(urwid.Columns([message_edit, send_button]), 'footer')


    # Channel list
    channel_list = urwid.ListBox(
        urwid.SimpleFocusListWalker([urwid.AttrMap(urwid.Text(chan), 'channel') for chan in channels]))
    channel_box = urwid.LineBox(channel_list, title='Channels')

    # User list
    user_list = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.AttrMap(urwid.Text(user), 'user') for user in users]))
    user_box = urwid.LineBox(user_list, title='Users')

    # Layout
    columns = urwid.Columns([
        ('weight', 1, channel_box),
        ('weight', 4, chat_view),
        ('weight', 1, user_box),
    ])
    layout = urwid.Frame(body=columns, header=header, footer=footer)

    # Create loop to run the UI
    loop = urwid.MainLoop(layout, palette)

    # Subscribe to IRC client events
    irc_client.message_event.subscribe(
        lambda sender, channel, message: update_chat_body(sender, channel, message, chat_body, loop))
    irc_client.user_event.subscribe(lambda user, channel, action: update_user_list(user, channel, action, user_box))

    return loop


if __name__ == "__main__":
    irc_client = IRCClient("localhost", 32815, "Test User")
    if irc_client.connect():
        irc_client.register("TestUser")
        sleep(1)
        irc_client.join_channel("#general")
        loop = setup_ui(irc_client)  # Setup UI and keep loop reference
        loop.run()
