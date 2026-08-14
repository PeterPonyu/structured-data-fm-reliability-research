(function () {
  "use strict";
  document.documentElement.classList.add("js");

  function apply(value) {
    document.querySelectorAll("[data-key-panel]").forEach(function (el) {
      var match = el.getAttribute("data-key-panel") === value;
      el.hidden = !match;
    });
  }

  var radios = document.querySelectorAll('input[name="key-condition"]');
  if (!radios.length) {
    return;
  }
  radios.forEach(function (radio) {
    radio.addEventListener("change", function () {
      if (radio.checked) {
        apply(radio.value);
      }
    });
  });
  var checked = document.querySelector('input[name="key-condition"]:checked');
  apply(checked ? checked.value : "included");
})();
