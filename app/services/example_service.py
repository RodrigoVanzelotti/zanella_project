from typing import Dict


class ExampleService:
    """A small example service to demonstrate wiring and testing.

    In real projects this would be an interface to DBs, external APIs, etc.
    """

    def fetch(self) -> Dict[str, str]:
        # Placeholder for an external call or business logic
        return {"message": "hello from ExampleService"}


service = ExampleService()
