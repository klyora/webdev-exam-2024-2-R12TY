document.addEventListener("DOMContentLoaded", function () {
  const deleteModal = document.getElementById("deleteBookModal");
  if (!deleteModal) return;

  deleteModal.addEventListener("show.bs.modal", function (event) {
    const trigger = event.relatedTarget;
    if (!trigger) return;

    const bookId = trigger.getAttribute("data-book-id");
    const bookTitle = trigger.getAttribute("data-book-title") || "";

    const form = deleteModal.querySelector("#deleteBookForm");
    const titleSpan = deleteModal.querySelector("#deleteBookTitle");

    if (titleSpan) titleSpan.textContent = bookTitle;
    if (form) {
      form.setAttribute("action", `/books/${bookId}/delete`);
    }
  });
});
