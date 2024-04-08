from client import IRCClient  # Make sure this matches the name of your IRC client file


def main():
    # Test code. Will eventually be replaced
    client = IRCClient("localhost", 6667)
    if client.connect():
        if client.send_ping():
            print("Ping sent successfully.")
        else:
            print("Failed to send ping.")
    else:
        print("Failed to connect to IRC server.")

    client.disconnect()


if __name__ == "__main__":
    main()
