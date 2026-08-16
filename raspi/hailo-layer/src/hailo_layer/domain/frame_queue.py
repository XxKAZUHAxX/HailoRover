"""Bounded thread-safe queue with drop-oldest semantics.

Used between the GStreamer pipeline thread (producer) and the server's asyncio
broadcast loop (consumer). Drop-oldest keeps end-to-end latency low: the
consumer always sees the freshest frame, never a backlog.
"""

from __future__ import annotations

import queue
from typing import Generic, TypeVar

T = TypeVar("T")


class FrameQueue(Generic[T]):
    """Never-blocking FIFO that evicts the oldest item when full."""

    def __init__(self, maxsize: int = 2) -> None:
        self._q: queue.Queue[T] = queue.Queue(maxsize=maxsize)

    def push(self, item: T) -> None:
        """Add an item, dropping the oldest if full."""
        try:
            self._q.put_nowait(item)
        except queue.Full:
            try:
                self._q.get_nowait()  # drop oldest
            except queue.Empty:
                pass
            try:
                self._q.put_nowait(item)
            except queue.Full:
                pass

    def pop_nowait(self) -> T | None:
        """Return the oldest item, or None if empty."""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    def clear(self) -> None:
        """Discard all pending items."""
        while self.pop_nowait() is not None:
            pass

    def qsize(self) -> int:
        return self._q.qsize()
