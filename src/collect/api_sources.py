import os


class Work24Source:
    """Reserved adapter for the official Work24 Open API.

    Collection remains disabled until the user supplies an official API key and
    the endpoint contract is verified against current official documentation.
    """

    def collect(self) -> list[dict]:
        if not os.getenv("WORK24_AUTH_KEY"):
            raise RuntimeError("WORK24_AUTH_KEY가 없어 Work24 수집을 보류합니다.")
        raise RuntimeError("Work24 adapter가 아직 활성화되지 않았습니다.")

