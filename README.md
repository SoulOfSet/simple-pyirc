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

## Usage
To start the IRC client, use the following make command:

```bash
make start-client
```

This command will prompt you to enter the necessary details such as server host, port, userinfo, nickname, and default channel through command line arguments.

## Command Line Arguments

The application accepts several command line arguments to configure the IRC client:

- `--host`: IRC server hostname
- `--port`: IRC server port
- `--userinfo`: User info for IRC registration
- `--nickname`: Nickname for the IRC session
- `--default-channel`: Default channel to join

Example:

```bash
python main.py --host irc.example.com --port 6667 --userinfo "Python IRC Client" --nickname mynickname --default-channel #general
```

## Testing

To run the unit tests for the IRC client, execute:

```bash
make test
```
This will run tests defined in the tests/ directory using pytest.

## Logging

Logs for the application are written to irc.log in the root directory, providing detailed output of operations and any errors encountered.