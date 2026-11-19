/* Detalles de interfaz: aviso de carga de HTMX y cierre automático de avisos de éxito. */
(function () {
  document.addEventListener("htmx:beforeRequest", function () { document.body.classList.add("loading"); });
  document.addEventListener("htmx:afterRequest", function () { document.body.classList.remove("loading"); });

  document.querySelectorAll(".messages li.success").forEach(function (li) {
    setTimeout(function () {
      li.classList.add("leaving");
      setTimeout(function () { li.remove(); }, 240);
    }, 5000);
  });
})();
