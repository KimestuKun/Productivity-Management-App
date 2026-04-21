/* TaskFlow PMA — Custom JavaScript */
(function () {
  'use strict';

  /* ── Bootstrap form validation ──
     Adds .was-validated class on submit to trigger Bootstrap's
     built-in validation styles on required fields. */
  document.querySelectorAll('form[novalidate]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!form.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
      }
      form.classList.add('was-validated');
    });
  });

  /* ── Set min date on date inputs to today ──
     Prevents selecting past dates on create/edit forms. */
  document.querySelectorAll('input[type="date"]').forEach(function (input) {
    if (!input.value) {
      input.min = new Date().toISOString().split('T')[0];
    }
  });

})();

/* ── Status select — color coding + auto-submit ──
   Applies a CSS class to each .status-select based on the currently
   selected value, then submits the form when the user picks a new status.
   Classes (.s-pending, .s-progress, .s-done) are styled in style.css. */
function applyStatusColor(sel) {
  sel.classList.remove('s-pending', 's-progress', 's-done');
  if (sel.value === '0')      sel.classList.add('s-pending');
  else if (sel.value === '1') sel.classList.add('s-progress');
  else                        sel.classList.add('s-done');
}

document.querySelectorAll('.status-select').forEach(function (sel) {
  applyStatusColor(sel);  /* color on page load */
  sel.addEventListener('change', function () {
    applyStatusColor(sel);
    sel.form.submit();    /* auto-submit on change */
  });
});

/* ── Delete confirmation ──
   Called from the delete button's onclick attribute.
   Returns false to cancel navigation if user clicks Cancel. */
function confirmDelete(taskTitle) {
  return window.confirm(
    'Delete "' + taskTitle + '"?\n\nThis action cannot be undone.'
  );
}
