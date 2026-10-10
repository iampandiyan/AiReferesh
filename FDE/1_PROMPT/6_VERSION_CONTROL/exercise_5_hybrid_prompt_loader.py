"""Exercise 5: prompt-store -> Git-tag -> disk fallback with TTL and source metrics.

Run independently with `python -m pip install pyyaml`. No API key or Together call is
needed. The store outage is simulated; the tag and disk stores are in-memory/local demo
fixtures, so this script does not require the output of Exercise 3.

Lesson: impose a timeout on remote prompt stores, cache successful loads with their source
label, and retain a local committed prompt as the last-resort availability floor.
"""

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml


@dataclass
class PromptHit:
    spec: dict
    source: str


class HybridPromptLoader:
    def __init__(self, store_client=None, tag_loader=None, disk_root: Path | None = None,
                 store_timeout_s: float = 0.5, ttl_s: float = 60):
        self.store = store_client
        self.tag_loader = tag_loader
        self.disk_root = disk_root
        self.timeout = store_timeout_s
        self.ttl = ttl_s
        self._cache: dict[tuple[str, str], tuple[float, dict, str]] = {}
        self.counter = {"store": 0, "tag": 0, "disk": 0}

    def _call_store_with_timeout(self, name: str, version: str) -> dict:
        if self.store is None:
            raise RuntimeError("No prompt store configured")
        done = threading.Event()
        outcome: dict = {}

        def worker() -> None:
            try:
                outcome["spec"] = self.store.fetch(name, version)
            except Exception as error:
                outcome["error"] = error
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        if not done.wait(self.timeout):
            raise TimeoutError(f"Prompt store exceeded {self.timeout:.3f}s timeout")
        if "error" in outcome:
            raise outcome["error"]
        return outcome["spec"]

    def load(self, name: str, version: str) -> PromptHit:
        key = (name, version)
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and now - cached[0] < self.ttl:
            _, spec, source = cached
            self.counter[source] += 1
            return PromptHit(spec=spec, source=source)

        if self.store is not None:
            try:
                spec = self._call_store_with_timeout(name, version)
                return self._remember(key, spec, "store")
            except Exception as error:
                print(f"[fallback] store miss: {error}")
        if self.tag_loader is not None:
            try:
                spec = self.tag_loader(name, version)
                return self._remember(key, spec, "tag")
            except Exception as error:
                print(f"[fallback] tag miss: {error}")
        if self.disk_root is not None:
            path = self.disk_root / name / f"{version}.yaml"
            if path.is_file():
                with path.open(encoding="utf-8") as stream:
                    spec = yaml.safe_load(stream)
                return self._remember(key, spec, "disk")
        raise FileNotFoundError(f"No prompt source resolved for {name}@{version}")

    def _remember(self, key: tuple[str, str], spec: dict, source: str) -> PromptHit:
        self._cache[key] = (time.monotonic(), spec, source)
        self.counter[source] += 1
        return PromptHit(spec=spec, source=source)


class SlowFailedStore:
    def fetch(self, name: str, version: str) -> dict:
        time.sleep(0.8)
        raise ConnectionError("simulated prompt-store outage")


def main() -> None:
    with TemporaryDirectory(prefix="hybrid_prompt_demo_") as temp_dir:
        root = Path(temp_dir)
        prompt_dir = root / "lending-advisor"
        prompt_dir.mkdir()
        spec = {"name": "lending-advisor", "version": "v1", "model": "openai/gpt-oss-120b",
                "body": "Synthetic lending advisor prompt."}
        (prompt_dir / "v1.yaml").write_text(yaml.safe_dump(spec), encoding="utf-8")

        tag_specs = {("lending-advisor", "v1"): {**spec, "body": "Immutable demo tag prompt."}}
        def tag_loader(name: str, version: str) -> dict:
            key = (name, version)
            if key not in tag_specs:
                raise KeyError(f"No tag for {name}@{version}")
            return tag_specs[key]

        loader = HybridPromptLoader(
            store_client=SlowFailedStore(),
            tag_loader=tag_loader,
            disk_root=root,
            store_timeout_s=0.5,
            ttl_s=60,
        )
        started = time.perf_counter()
        first = loader.load("lending-advisor", "v1")
        elapsed = time.perf_counter() - started
        second = loader.load("lending-advisor", "v1")
        assert first.source == "tag" and second.source == "tag"
        assert elapsed < 0.7, f"Store timeout was not bounded: {elapsed:.3f}s"
        print(f"First load: source={first.source}; elapsed={elapsed:.3f}s")
        print(f"Cached load: source={second.source}; counts={loader.counter}")

        disk_loader = HybridPromptLoader(
            store_client=SlowFailedStore(),
            tag_loader=lambda _name, _version: (_ for _ in ()).throw(KeyError("tag absent")),
            disk_root=root,
            store_timeout_s=0.05,
        )
        disk_hit = disk_loader.load("lending-advisor", "v1")
        assert disk_hit.source == "disk"
        print(f"Tag outage fallback: source={disk_hit.source}; model={disk_hit.spec['model']}")


if __name__ == "__main__":
    main()