import eventlet
from eventlet import Timeout
from mock import create_autospec

from nameko.containers import ServiceContainer
from nameko.testing.utils import wait_for_call
from nameko.timer import Timer


def spawn_managed_thread(fn, identifier=None):
    return eventlet.spawn(fn)


def test_provider():
    container = create_autospec(ServiceContainer)
    container.service_name = "service"
    container.spawn_managed_thread = spawn_managed_thread

    timer = Timer(interval=0.1).bind(container, "method")
    timer.setup()
    timer.start()

    assert timer.interval == 0.1

    with wait_for_call(1, container.spawn_worker) as spawn_worker:
        with Timeout(1):
            timer.stop()

    # the timer should have stopped and should only have spawned
    # a single worker
    spawn_worker.assert_called_once_with(timer, (), {})
    assert timer.gt.dead


def test_stop_timer_immediately():
    container = create_autospec(ServiceContainer)
    container.service_name = "service"
    container.config = {}

    timer = Timer(interval=5).bind(container, "method")
    timer.setup()
    timer.start()

    eventlet.sleep(0.1)
    timer.stop()

    assert container.spawn_worker.call_count == 0
    assert timer.gt.dead


def test_kill_stops_timer():
    container = create_autospec(ServiceContainer)
    container.service_name = "service"
    container.spawn_managed_thread = spawn_managed_thread

    timer = Timer(interval=0).bind(container, "method")
    timer.setup()
    timer.start()

    with wait_for_call(1, container.spawn_worker):
        timer.kill()

    # unless the timer is dead, the following nap would cause a timer
    # to trigger
    eventlet.sleep(0.1)
    assert container.spawn_worker.call_count == 1
