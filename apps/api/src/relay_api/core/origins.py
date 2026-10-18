from urllib.parse import urlsplit

def origin_allowed(origin: str, configured_origin: str) -> bool:
    if origin == configured_origin:
        return True
    try:
        actual = urlsplit(origin)
        expected = urlsplit(configured_origin)
        loopback_names = {"localhost", "127.0.0.1"}
        return (
            actual.scheme == expected.scheme == "http"
            and actual.hostname in loopback_names
            and expected.hostname in loopback_names
            and actual.port == expected.port
            and not actual.username
            and not actual.password
            and not actual.path
            and not actual.query
            and not actual.fragment
        )
    except ValueError:
        return False
