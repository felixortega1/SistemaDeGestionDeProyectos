from apps.backlog.models import Task, TaskDependency


def effective_dates(task, sprint):
    """Fechas efectivas de una tarea. Devuelve un dict con `start`, `end` y sus fuentes,
    o `{"undated": motivo}` si no se puede dibujar. Función pura."""
    if task.start_date:
        start, start_source = task.start_date, "task"
    elif sprint is not None and sprint.start_date:
        start, start_source = sprint.start_date, "sprint"
    else:
        start, start_source = None, None
    if task.due_date:
        end, end_source = task.due_date, "task"
    elif sprint is not None and sprint.end_date:
        end, end_source = sprint.end_date, "sprint"
    else:
        end, end_source = None, None

    if start is None and end is None:
        return {"undated": "sin fechas"}
    if start is None or end is None:
        return {"undated": "una sola fecha"}
    if end < start:
        return {"undated": "fin anterior al inicio"}
    return {"start": start, "end": end, "start_source": start_source, "end_source": end_source}


def build_gantt(project, today):
    """Arma la estructura del Gantt. Solo lee."""
    tasks = list(Task.objects.filter(project=project, kind=Task.TASK).select_related("sprint", "column").order_by("id"))
    drawn, undated = {}, []
    for t in tasks:
        eff = effective_dates(t, t.sprint)
        if "undated" in eff:
            undated.append({"id": t.pk, "title": t.title, "reason": eff["undated"]})
            continue
        eff["task"] = t
        eff["is_late"] = t.column is not None and not t.column.is_done and eff["end"] < today
        eff["conflict"] = False
        eff["depends_on"] = []
        drawn[t.pk] = eff

    for dep in TaskDependency.objects.filter(task__project=project):
        succ, pred = drawn.get(dep.task_id), drawn.get(dep.depends_on_id)
        if succ is None or pred is None:
            continue
        succ["depends_on"].append(dep.depends_on_id)
        same_sprint_inherited = (
            succ["start_source"] == succ["end_source"] == pred["start_source"] == pred["end_source"] == "sprint"
            and succ["task"].sprint_id == pred["task"].sprint_id
        )
        if not same_sprint_inherited and succ["start"] <= pred["end"]:
            succ["conflict"] = True

    return {
        "tasks": [
            {
                "id": pk,
                "title": e["task"].title,
                "start": e["start"].isoformat(),
                "end": e["end"].isoformat(),
                "start_source": e["start_source"],
                "end_source": e["end_source"],
                "is_late": e["is_late"],
                "conflict": e["conflict"],
                "depends_on": e["depends_on"],
            }
            for pk, e in drawn.items()
        ],
        "undated": undated,
        "milestones": [
            {"id": m.pk, "name": m.name, "date": m.date.isoformat()} for m in project.milestones.all()
        ],
    }
