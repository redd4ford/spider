class IncorrectProxyFormatError(Exception):
    def __init__(self, proxy_host=None):
        self.message = (
            f'Your proxy `{proxy_host}` did not match the required format. '
            'Proxy should come as a URL, e.g. `http://proxy_server_ip:proxy_server_port`'
        )
        super().__init__(self.message)

    def __str__(self):
        return self.message
