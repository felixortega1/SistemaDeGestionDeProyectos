/* Tablero: arrastrar tarjetas con SortableJS y pedir el movimiento al servidor con HTMX.
   Toda la regla de negocio vive en el servidor; aquí solo se resalta y se envía. */
(function () {
  function allowedIds(card) {
    return (card.dataset.allowed || "").split(" ").filter(Boolean);
  }

  var pending = null; // { taskId, counts } del último arrastre, para animar tras el reemplazo

  function readCounts() {
    var counts = {};
    document.querySelectorAll("#board .column").forEach(function (c) {
      var el = c.querySelector(".count");
      if (el) counts[c.dataset.columnId] = el.textContent.trim();
    });
    return counts;
  }

  function clearHighlights() {
    document.querySelectorAll("#board .column").forEach(function (c) {
      c.classList.remove("allowed", "forbidden");
    });
  }

  function initBoard() {
    var board = document.getElementById("board");
    if (!board || typeof Sortable === "undefined") return;
    board.querySelectorAll(".cards").forEach(function (list) {
      if (list._sortable) list._sortable.destroy();
      list._sortable = new Sortable(list, {
        group: "board",
        draggable: ".task-card",
        filter: ".move-form, .card-comments",
        preventOnFilter: false,
        animation: 150,
        delay: 150,
        delayOnTouchOnly: true,
        onStart: function (evt) {
          var ok = allowedIds(evt.item);
          board.querySelectorAll(".column").forEach(function (col) {
            var id = col.dataset.columnId;
            var isOrigin = id === evt.from.dataset.columnId;
            col.classList.add(isOrigin || ok.indexOf(id) !== -1 ? "allowed" : "forbidden");
          });
        },
        onMove: function (evt) {
          var target = evt.to.dataset.columnId;
          return target === evt.from.dataset.columnId || allowedIds(evt.dragged).indexOf(target) !== -1;
        },
        onEnd: function (evt) {
          clearHighlights();
          if (evt.to === evt.from) return;
          pending = { taskId: evt.item.dataset.taskId, counts: readCounts() };
          htmx.ajax("POST", evt.item.dataset.moveUrl, {
            target: "#board",
            swap: "outerHTML",
            values: { column_id: evt.to.dataset.columnId },
          });
        },
      });
    });
  }

  // HTMX reemplaza el tablero entero: hay que volver a crear las instancias.
  document.addEventListener("htmx:load", initBoard);
  document.addEventListener("DOMContentLoaded", initBoard);

  // 409 y 422 traen el tablero redibujado con el mensaje; cualquier otra respuesta recarga.
  document.addEventListener("htmx:beforeSwap", function (evt) {
    var status = evt.detail.xhr && evt.detail.xhr.status;
    if (status === 409 || status === 422) {
      evt.detail.shouldSwap = true;
      evt.detail.isError = false;
    } else if (status !== 200) {
      evt.detail.shouldSwap = false;
      window.location.reload();
    }
  });
  // Tras reemplazar el tablero: solo se agregan clases; el CSS hace la animación.
  document.addEventListener("htmx:afterSwap", function (evt) {
    var board = document.getElementById("board");
    if (!pending || !board) return;
    var status = evt.detail.xhr && evt.detail.xhr.status;
    var card = board.querySelector('[data-task-id="' + pending.taskId + '"]');
    if (status === 200) {
      if (card) card.classList.add("settle");
      board.querySelectorAll(".column").forEach(function (c) {
        var el = c.querySelector(".count");
        if (el && pending.counts[c.dataset.columnId] !== el.textContent.trim()) el.classList.add("bump");
      });
    } else if (status === 409 || status === 422) {
      board.classList.add("rejected");
      if (card) card.classList.add("rejected");
    }
    pending = null;
  });
  document.addEventListener("htmx:sendError", function () {
    window.location.reload();
  });
})();
