localStorage.openpages = Date.now();
var onLocalStorageEvent = function (e) {
  if (e.key == "openpages") {
    // Listen if anybody else is opening the same page!
    localStorage.page_available = Date.now();
    alert("Another Tally Ninja tab is open! Proceed with caution!");
  }
  if (e.key == "page_available") {
    alert("Another Tally Ninja tab is open! Proceed with caution!");
  }
};
window.addEventListener("storage", onLocalStorageEvent, false);
