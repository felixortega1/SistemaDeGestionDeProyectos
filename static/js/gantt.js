/* Gantt de solo lectura con frappe-gantt. Los datos llegan con json_script. */
(function () {
  var holder = document.getElementById("gantt-data");
  var container = document.getElementById("gantt-container");
  if (!holder || !container || typeof Gantt === "undefined") return;

  var data = JSON.parse(holder.textContent);
  var tasks = data.tasks.map(function (t) {
    var classes = [];
    if (t.is_late) classes.push("gantt-late");
    if (t.conflict) classes.push("gantt-conflict");
    var item = {
      id: String(t.id),
      name: t.title,
      start: t.start,
      end: t.end,
      progress: 0,
      dependencies: t.depends_on.map(String).join(","),
    };
    if (classes.length) item.custom_class = classes.join(" ");
    return item;
  });

  // Los hitos se dibujan como barras de un día con una clase propia.
  data.milestones.forEach(function (m) {
    tasks.push({
      id: "m" + m.id,
      name: "◆ " + m.name,
      start: m.date,
      end: m.date,
      progress: 0,
      custom_class: "gantt-milestone",
    });
  });

  container.innerHTML = "";
  if (!tasks.length) {
    container.textContent = "No hay tareas con fechas para dibujar.";
    return;
  }

  var first = Math.min.apply(null, tasks.map(function (t) { return new Date(t.start).getTime(); }));
  var last = Math.max.apply(null, tasks.map(function (t) { return new Date(t.end).getTime(); }));
  var totalDays = (last - first) / 86400000;
  var initial = totalDays > 120 ? "Month" : totalDays > 28 ? "Week" : "Day";

  var gantt = new Gantt(container, tasks, {
    readonly: true,
    readonly_dates: true,
    readonly_progress: true,
    view_mode: initial,
    language: "es",
    bar_height: 28,
    padding: 22,
    popup_on: "hover",
  });

  var buttons = document.querySelectorAll(".zoom-btn");
  function mark(mode) {
    buttons.forEach(function (b) {
      b.classList.toggle("active", b.dataset.mode === mode);
    });
  }
  mark(initial);
  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      gantt.change_view_mode(b.dataset.mode);
      mark(b.dataset.mode);
    });
  });
})();
