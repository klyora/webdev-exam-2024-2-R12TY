document.addEventListener("DOMContentLoaded", function () {
  if (typeof EasyMDE === "undefined") return;

  const textareas = document.querySelectorAll('textarea[data-markdown]');
  textareas.forEach((ta) => {
    if (ta._easyMDE) return;

    const easyMDE = new EasyMDE({
      element: ta,
      autoDownloadFontAwesome: false,
      spellChecker: false,
      status: false,
      autofocus: false,
      forceSync: true,          // <<< КЛЮЧЕВОЕ
      autosave: { enabled: false },
      renderingConfig: { singleLineBreaks: false },
      toolbar: [
        "bold", "italic", "strikethrough", "|",
        "heading", "quote", "unordered-list", "ordered-list", "|",
        "link", "code", "|",
        "preview", "guide"
      ]
    });

    ta._easyMDE = easyMDE;
  });
});