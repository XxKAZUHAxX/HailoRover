"""FrameQueue: FIFO order, drop-oldest at capacity, never blocks."""

from hailo_layer.domain.frame_queue import FrameQueue


def test_fifo_order():
    q = FrameQueue(maxsize=3)
    q.push(1)
    q.push(2)
    q.push(3)
    assert q.pop_nowait() == 1
    assert q.pop_nowait() == 2
    assert q.pop_nowait() == 3
    assert q.pop_nowait() is None


def test_drop_oldest_when_full():
    q = FrameQueue(maxsize=2)
    q.push("a")
    q.push("b")
    q.push("c")  # full → "a" dropped
    assert q.qsize() == 2
    assert q.pop_nowait() == "b"
    assert q.pop_nowait() == "c"


def test_empty_pop_returns_none():
    q = FrameQueue(maxsize=2)
    assert q.pop_nowait() is None


def test_clear_discards_all():
    q = FrameQueue(maxsize=5)
    for i in range(5):
        q.push(i)
    q.clear()
    assert q.pop_nowait() is None
    assert q.qsize() == 0
