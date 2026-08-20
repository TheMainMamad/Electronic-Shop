(function () {
  var stored = localStorage.getItem("theme");
  var systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  var dark = stored ? stored === "dark" : systemDark;
  document.documentElement.classList.toggle("dark", dark);
})();
