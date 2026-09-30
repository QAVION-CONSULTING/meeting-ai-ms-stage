(() => {
  "use strict";

  const cfg = window.MEETING_LINKS_CONFIG || {};
  const teams = window.microsoftTeams;
  const el = (id) => document.getElementById(id);
  const setStatus = (id, text) => { el(id).textContent = text || ""; };

  function isHttps(url) {
    try {
      return new URL(url).protocol === "https:";
    } catch {
      return false;
    }
  }

  async function openExternal(url) {
    if (!isHttps(url)) throw new Error("Es sind nur HTTPS-Links erlaubt.");
    if (teams?.app?.openLink) {
      try {
        await teams.app.openLink(url);
        return;
      } catch (_) {
        // Manche Clients lehnen openLink für externe URLs ab – dann window.open.
      }
    }
    const w = window.open(url, "_blank", "noopener,noreferrer");
    if (!w) throw new Error("Der Link konnte nicht geöffnet werden (Popup blockiert?).");
  }

  function bindLinkButton(buttonId, item) {
    const button = el(buttonId);
    if (!item?.url) {
      button.hidden = true;
      return;
    }
    button.textContent = item.label || item.url;
    button.addEventListener("click", async () => {
      setStatus("status", "");
      try {
        await openExternal(item.url);
      } catch (err) {
        setStatus("status", err?.message || "Link konnte nicht geöffnet werden.");
      }
    });
  }

  function showStageView() {
    el("title").textContent = cfg.title || "Meeting Links";
    el("subtitle").textContent = cfg.subtitle || "";
    bindLinkButton("button1", cfg.button1);
    bindLinkButton("button2", cfg.button2);
    el("stageView").hidden = false;
  }

  async function canShareToStage() {
    try {
      const caps = await new Promise((resolve, reject) =>
        teams.meeting.getAppContentStageSharingCapabilities((err, result) =>
          err ? reject(err) : resolve(result)
        )
      );
      return !!caps?.doesAppHaveSharePermission;
    } catch {
      return false;
    }
  }

  function shareToStage() {
    setStatus("launcherStatus", "Wird auf die Meeting-Bühne geteilt …");
    const stageUrl = new URL("index.html?view=stage", window.location.href).href;
    teams.meeting.shareAppContentToStage((err, result) => {
      if (err) {
        setStatus("launcherStatus", `Teilen fehlgeschlagen: ${err.message || err.errorCode || "Unbekannter Fehler"}`);
        return;
      }
      setStatus("launcherStatus", result ? "Die Links werden jetzt auf der Meeting-Bühne angezeigt." : "Teilen wurde nicht bestätigt.");
    }, stageUrl);
  }

  async function showLauncher() {
    el("launcher").hidden = false;
    const shareButton = el("shareStage");
    shareButton.addEventListener("click", shareToStage);
    if (!(await canShareToStage())) {
      shareButton.disabled = true;
      setStatus("launcherStatus", "Teilen auf die Bühne ist nur für Organisatoren/Referenten im Teams-Desktop- oder Web-Client möglich.");
    }
  }

  async function init() {
    if (!teams?.app) {
      showStageView();
      setStatus("status", "TeamsJS konnte nicht geladen werden.");
      return;
    }
    try {
      await teams.app.initialize();
    } catch {
      showStageView();
      setStatus("status", "Außerhalb von Teams geöffnet – Links funktionieren trotzdem.");
      return;
    }

    const context = await teams.app.getContext();
    const frameContext = context?.page?.frameContext;
    document.body.dataset.frame = frameContext || "";
    document.body.dataset.theme = context?.app?.theme || "default";
    teams.app.registerOnThemeChangeHandler?.((theme) => { document.body.dataset.theme = theme; });

    if (frameContext === "sidePanel") {
      await showLauncher();
    } else {
      showStageView();
    }
    teams.app.notifySuccess?.();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
