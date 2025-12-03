from typing_extensions import Annotated, Doc

from fastapi import FastAPI, Request, params
import asyncio
import uvicorn
from typing import Mapping, Any

def Injects(  # noqa: N802
    dependency: Annotated[
        str,
        Doc("The name of dependency, defined in State, that will be injected in the router."),
    ],
    *,
    use_cache: Annotated[
        bool,
        Doc(
            """
                By default, after a dependency is called the first time in a request, if
                the dependency is declared again for the rest of the request (for example
                if the dependency is needed by several dependencies), the value will be
                re-used for the rest of the request.

                Set `use_cache` to `False` to disable this behavior and ensure the
                dependency is called again (if declared more than once) in the same request.
                """
        ),
    ] = True,
) -> Any:
    def _inject_from_state(request: Request) -> Any:
        return getattr(request.state, dependency)

    return params.Depends(dependency=_inject_from_state, use_cache=use_cache)

class CounterService:
    def __init__(self):
        self.count = 0
    
    def increment(self):
        self.count += 1
        return self.count

class AppDependencies(Mapping):
    def __init__(self, /, **kwargs: Any):
        self.db: str = ""
        self.config: dict = {}
        self.counter = CounterService()
        self.__dict__.update(kwargs)

    def __getitem__(self, item):
        return self.__dict__[item]

    def __iter__(self):
        return self.__dict__.__iter__()

    def __len__(self):
        return self.__dict__.__len__()


class MyInitializer:
    def __init__(self, app: FastAPI):
        self.app = app
        self.deps = AppDependencies()

    async def _setup_db(self):
        # Giả lập khởi tạo database connection
        print("Setting up database...")
        await asyncio.sleep(1)
        return "DatabaseConnection"
    
    async def __aenter__(self):
        # Khởi tạo dependencies
        self.deps.db = await self._setup_db()
        self.deps.config = {"env": "test"}
        
        return self.deps
    
    async def _cleanup(self):
        # Giả lập dọn dẹp resources
        print("Cleaning up resources...")
        await asyncio.sleep(1)
        print("Resources cleaned up.")

    async def __aexit__(self, *args):
        await self._cleanup()

app = FastAPI(lifespan=MyInitializer)

@app.get("/test")
async def test_request_state(
    counter: CounterService = Injects("counter"),
    config: dict = Injects("config")):
    return {
        "counter": counter.increment(),
        "config": config,
    }

if __name__ == "__main__":
    uvicorn.run( app, host="127.0.0.1", port=8000)
