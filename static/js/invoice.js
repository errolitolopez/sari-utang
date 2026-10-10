// Invoice page: print / save as PDF, and copy the text version.

const textBox = document.getElementById("invoice-text");
const copyMessage = document.getElementById("copy-message");

document.getElementById("print-button").addEventListener("click", () => window.print());

document.getElementById("copy-button").addEventListener("click", async () => {
  copyMessage.classList.add("d-none");

  // The modern clipboard only works on https or localhost. On a phone using
  // http://192.168.x.x it is missing, so fall back to selecting the text box.
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(textBox.value);
      copyMessage.classList.remove("d-none");
      return;
    } catch {
      // fall through to the fallback below
    }
  }

  textBox.classList.remove("d-none");
  textBox.focus();
  textBox.select();
  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch {
    copied = false;
  }
  copyMessage.textContent = copied
    ? "Copied! Paste it in Messenger or Viber."
    : "Select the text below and copy it.";
  copyMessage.classList.remove("d-none");
});
