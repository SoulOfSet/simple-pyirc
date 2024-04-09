from time import sleep

from irc_client import IRCClient

userinfo = "Test User for IRC"


def main():
    client = IRCClient("localhost", 32791, userinfo)
    if client.connect():
        client.register("Timmy")
        # Wait for registration to complete
        sleep(1)

        # Join the test channel
        client.join_channel("#Test")
        client.send_message("#Test", "Hello!!!")
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        print("Failed to connect to IRC server.")

    client.disconnect()

if __name__ == "__main__":
    main()
