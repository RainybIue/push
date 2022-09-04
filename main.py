import wechat


def main():
    w = wechat.WeChat("./config.json")
    w.send_message()

    pass


if __name__ == "__main__":
    main()
