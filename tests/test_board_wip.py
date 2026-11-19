import threading

import pytest
from django.db import connection

from apps.backlog import services
from apps.backlog.models import Task
from apps.core.exceptions import Conflict, Unprocessable

IS_SQLITE = connection.vendor == "sqlite"


def test_fourth_task_in_development_is_409(project, po, active_sprint, columns):
    sprint, tasks = active_sprint(4)
    dev = columns["En desarrollo"]
    for t in tasks[:3]:
        services.move_task(t, dev, po)
    with pytest.raises(Conflict) as exc:
        services.move_task(tasks[3], dev, po)
    assert "3 / 3" in exc.value.message


def test_invalid_targets_are_422(project, po, make_task, active_sprint, columns):
    sprint, (t, *_) = active_sprint(1)
    dev = columns["En desarrollo"]
    loose = make_task("suelta")
    story = make_task("hist", kind="story")
    with pytest.raises(Unprocessable):
        services.move_task(loose, dev, po)
    with pytest.raises(Unprocessable):
        services.move_task(story, dev, po)
    services.close_sprint(sprint)
    with pytest.raises(Unprocessable):
        services.move_task(t, dev, po)


def test_move_to_same_column_is_noop(project, po, active_sprint, columns):
    sprint, (t, *_) = active_sprint(1)
    assert services.move_task(t, columns["Por hacer"], po).column_id == columns["Por hacer"].pk


def test_wip_null_and_zero(project, po, active_sprint, columns):
    sprint, tasks = active_sprint(2)
    dev = columns["En desarrollo"]
    dev.wip_limit = None
    dev.save()
    services.move_task(tasks[0], dev, po)
    services.move_task(tasks[1], dev, po)
    other = columns["En revisión"]
    other.wip_limit = 0
    other.save()
    with pytest.raises(Conflict):
        services.move_task(tasks[0], other, po)


def test_lowering_limit_does_not_evict(project, po, active_sprint, columns):
    sprint, tasks = active_sprint(3)
    dev = columns["En desarrollo"]
    for t in tasks:
        services.move_task(t, dev, po)
    dev.wip_limit = 1
    dev.save()
    assert Task.objects.filter(column=dev).count() == 3


def test_validation_order_permission_first(project, make_user, active_sprint, columns):
    sprint, (t, *_) = active_sprint(1)
    from apps.core.exceptions import Forbidden

    with pytest.raises(Forbidden):
        services.move_task(t, columns["Hecho"], make_user())  # ni siquiera es miembro


def test_transition_checked_before_wip(project, po, active_sprint, columns):
    sprint, tasks = active_sprint(4)
    dev = columns["En desarrollo"]
    for t in tasks[:3]:
        services.move_task(t, dev, po)
    with pytest.raises(Unprocessable):  # Por hacer → Hecho: 422 aunque no haya WIP
        services.move_task(tasks[3], columns["Hecho"], po)


def test_service_rereads_stale_instance(project, po, active_sprint, columns):
    sprint, (t, *_) = active_sprint(1)
    stale = Task.objects.get(pk=t.pk)
    services.move_task(t, columns["En desarrollo"], po)
    # `stale` aún cree estar en "Por hacer" (donde "En revisión" no es contigua): solo funciona si se relee.
    assert stale.column_id == columns["Por hacer"].pk
    assert services.move_task(stale, columns["En revisión"], po).column_id == columns["En revisión"].pk


@pytest.mark.skipif(IS_SQLITE, reason="la concurrencia real exige MySQL (select_for_update)")
@pytest.mark.django_db(transaction=True)
def test_concurrent_moves_last_slot(project, po, active_sprint, columns):
    sprint, tasks = active_sprint(4)
    dev = columns["En desarrollo"]
    for t in tasks[:2]:
        services.move_task(t, dev, po)
    barrier = threading.Barrier(2)
    results = []

    def worker(task):
        try:
            barrier.wait()
            services.move_task(task, dev, po)
            results.append(200)
        except Conflict:
            results.append(409)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(t,)) for t in tasks[2:]]
    [th.start() for th in threads]
    [th.join() for th in threads]
    assert sorted(results) == [200, 409]
