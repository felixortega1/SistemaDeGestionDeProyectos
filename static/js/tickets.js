/* Panel lateral "Tickets diarios": abrir y cerrar (se recuerda) y lista de personas según la empresa. */
(function () {
  var KEY = "ticketsOpen";
  var toggle = document.getElementById("tickets-toggle");
  var aside = document.getElementById("tickets-aside");

  function stored() {
    try { return window.localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function save(value) {
    try { window.localStorage.setItem(KEY, value); } catch (e) { /* sin almacenamiento: no se recuerda */ }
  }
  function setOpen(open, remember) {
    document.body.classList.toggle("tickets-open", open);
    if (toggle) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("title", open ? "Reducir Tickets diarios" : "Desplegar Tickets diarios");
    }
    if (aside) aside.setAttribute("aria-hidden", open ? "false" : "true");
    if (remember) save(open ? "1" : "0");
  }

  if (toggle && aside) {
    var saved = stored();
    setOpen(saved === null ? window.innerWidth >= 1280 : saved === "1", false);
    toggle.addEventListener("click", function () {
      setOpen(!document.body.classList.contains("tickets-open"), true);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && document.body.classList.contains("tickets-open") && window.innerWidth < 1100) {
        setOpen(false, true);
      }
    });
  }

  // "Asignar a": solo si soy responsable en la empresa elegida, y solo las personas de esa empresa.
  function syncAssignee(form) {
    var company = form.querySelector("[name=company]");
    var field = form.querySelector(".assignee-field");
    var select = form.querySelector("[name=assignee]");
    if (!company || !field || !select) return;
    var managers = (form.dataset.managers || "").split(",").filter(Boolean);
    var isManager = managers.indexOf(company.value) !== -1;
    field.hidden = !isManager;
    Array.prototype.forEach.call(select.options, function (opt) {
      if (!opt.value) return;
      var ok = (opt.dataset.companies || "").split(",").indexOf(company.value) !== -1;
      opt.hidden = !ok;
      opt.disabled = !ok;
    });
    if (!isManager || (select.selectedOptions[0] && select.selectedOptions[0].disabled)) select.value = "";
  }
  function syncAll(root) {
    (root || document).querySelectorAll("form[data-managers]").forEach(syncAssignee);
  }
  document.addEventListener("change", function (e) {
    if (e.target && e.target.name === "company" && e.target.form && e.target.form.dataset.managers !== undefined) {
      syncAssignee(e.target.form);
    }
  });
  document.addEventListener("htmx:load", function (e) { syncAll(e.target); });
  document.addEventListener("DOMContentLoaded", function () { syncAll(document); });
})();
