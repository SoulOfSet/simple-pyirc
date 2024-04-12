# Simple IRC Client

This repository contains the source code for a simple IRC client implemented in Python using the `urwid` library for the user interface. It's designed to connect to an IRC server, join channels, send messages, and handle real-time updates.

## Features

- Connect to an IRC server
- Register with a nickname
- Join and leave channels
- Send and receive messages
- Handle private messages
- Dynamically update user lists for channels
- Customizable through command line arguments

## Project Structure

- `irc_client.py`: Contains the core IRC client logic.
- `main.py`: The entry point of the application, handling user interface setup and main event loop.
- `Makefile`: Provides commands to start the client and run tests.
- `requirements.txt`: Lists dependencies for the project.

## Installation

Before running the IRC client, you must install the necessary dependencies. This project uses `urwid` for the GUI elements, and `pytest` for running tests.

```bash
pip install -r requirements.txt
```

## Running with `make`
To start the IRC client, use the following make command:

```bash
make start-client
```

This command will prompt you to enter the necessary details such as server host, port, userinfo, nickname, and default channel through command line arguments.

## Running from Python

The application accepts several command line arguments to configure the IRC client:

- `--host`: IRC server hostname
- `--port`: IRC server port
- `--userinfo`: User info for IRC registration
- `--nickname`: Nickname for the IRC session
- `--default-channel`: Default channel to join

Example:

```bash
python irc_app.py --host irc.example.com --port 6667 --userinfo "Python IRC Client" --nickname mynickname --default-channel #general
```

## IRC Commands

Once connected, you can interact with the IRC server and other users through various commands typed into the client:

 - `/join [channel]`: Joins the specified channel if it exists. Example: `/join #help`
 - `/switch [channel]`: Switches your current view to another channel you have joined. Example: `/switch #general`
 - `/whisp [username] [message]`: Sends a private message to the specified user. Example: `/whisp John Hello, John!`

These commands are input directly into the client's message field and processed upon pressing 'enter'. Errors or feedback are displayed within the chat interface.

## Testing

To run the unit tests for the IRC client, execute:

```bash
make test
```
This will run tests defined in the tests/ directory using pytest.

## Logging

Logs for the application are written to irc.log in the root directory, providing detailed output of operations and any errors encountered.