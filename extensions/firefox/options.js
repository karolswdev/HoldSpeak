async function load() {
  const stored = await browser.storage.local.get("runtimeUrl");
  document.getElementById("runtimeUrl").value = stored.runtimeUrl || "http://127.0.0.1:64524";
}

document.getElementById("save").addEventListener("click", async () => {
  const url = document.getElementById("runtimeUrl").value.trim();
  await browser.storage.local.set({ runtimeUrl: url });
  const saved = document.getElementById("saved");
  saved.hidden = false;
  setTimeout(() => { saved.hidden = true; }, 1400);
});

load();
