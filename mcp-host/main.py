from mcp_host_factory import McpHostFactoy


def main():
    host = McpHostFactoy.construct_host()
    host.run()


if __name__ == "__main__":
    main()
