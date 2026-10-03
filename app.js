(function () {
  "use strict";

  var DATA = window.WIKI_DATA || { meta: {}, sagas: [], characters: [], places: [] };
  var main = document.getElementById("main");
  var backBtn = document.getElementById("backBtn");
  var mainNav = document.getElementById("mainNav");
  var searchWrap = document.getElementById("searchWrap");
  var qInput = document.getElementById("q");
  var footerMeta = document.getElementById("footerMeta");

  var bySaga = {};
  var byChar = {};
  var byPlace = {};
  (DATA.sagas || []).forEach(function (s) { bySaga[s.id] = s; });
  (DATA.characters || []).forEach(function (c) { byChar[c.id] = c; });
  (DATA.places || []).forEach(function (p) { byPlace[p.id] = p; });

  footerMeta.textContent =
    (DATA.meta.sagaCount || DATA.sagas.length) + " sagas · " +
    (DATA.meta.characterCount || DATA.characters.length) + " chars · " +
    (DATA.meta.placeCount || DATA.places.length) + " places";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function paras(text) {
    var t = String(text || "").trim();
    if (!t) return '<p class="muted">—</p>';
    return t.split(/\n\s*\n/).map(function (p) {
      return "<p>" + esc(p) + "</p>";
    }).join("");
  }

  function markerChip(m) {
    var x = String(m || "").toUpperCase();
    var cls = "a";
    if (x.indexOf("A") >= 0 && x.indexOf("B") >= 0) cls = "ab";
    else if (x.indexOf("B") >= 0) cls = "b";
    return '<span class="chip ' + cls + '">' + esc(m || "?") + "</span>";
  }

  function setTab(tab) {
    mainNav.querySelectorAll("button").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-tab") === tab);
    });
  }

  function thumbImg(c) {
    var src = c && (c.portraitThumb || c.portrait);
    return src ? '<img class="card-thumb" src="' + esc(src) + '" alt="' + esc(c.name) + '" loading="lazy" decoding="async">' : "";
  }

  function portraitHtml(c) {
    return c && c.portrait
      ? '<figure class="portrait"><a href="' + esc(c.portrait) + '" target="_blank" rel="noopener"><img src="' + esc(c.portrait) + '" alt="Portrait of ' + esc(c.name) + '" decoding="async"></a></figure>'
      : "";
  }

  function charCard(id) {
    var c = byChar[id];
    if (!c) return "";
    var badge = (c.kind === "group" || (c.variants && c.variants.length) || (c.members && c.members.length))
      ? '<span class="chip group-chip">Group</span> '
      : "";
    return '<a class="mini-card" href="#/char/' + encodeURIComponent(c.id) + '"><strong>' +
      badge + esc(c.name) + "</strong><span>" + esc(c.role || c.uniqueTitle || "") + "</span></a>";
  }

  function placeCard(id) {
    var p = byPlace[id];
    if (!p) return "";
    return '<a class="mini-card" href="#/place/' + encodeURIComponent(p.id) + '"><strong>' +
      esc(p.name) + "</strong><span>" + esc(p.type || "") + "</span></a>";
  }

  function sagaCard(id) {
    var s = bySaga[id];
    if (!s) return "";
    return '<a class="mini-card" href="#/saga/' + esc(s.id) + '"><strong>#' + s.num + " " +
      esc(s.title) + "</strong><span>" + esc(s.markers) + "</span></a>";
  }

  function renderSagaList() {
    var list = DATA.sagas.slice().sort(function (a, b) { return a.num - b.num; });
    main.innerHTML =
      '<div class="list-tools"><span class="count">' + list.length + " sagas</span></div>" +
      '<div class="card-list">' +
      list.map(function (s) {
        return '<a class="card" href="#/saga/' + esc(s.id) + '">' +
          '<div class="num">#' + String(s.num).padStart(2, "0") + " · " + markerChip(s.markers) + "</div>" +
          "<h3>" + esc(s.title) + "</h3>" +
          '<div class="meta"><span>' + ((s.counts && s.counts.meatToilets) || 0) + " MT</span>" +
          "<span>" + ((s.counts && s.counts.places) || 0) + " places</span>" +
          "<span>" + ((s.counts && s.counts.messageCount) || 0) + " msgs</span></div></a>";
      }).join("") +
      "</div>";
  }

  function renderCharList() {
    var list = DATA.characters.slice().sort(function (a, b) {
      return a.name.localeCompare(b.name);
    });
    main.innerHTML =
      '<div class="list-tools"><span class="count">' + list.length + " characters</span></div>" +
      '<div class="card-list">' +
      list.map(function (c) {
        var inner = "<h3>" + ((c.kind === "group" || (c.variants && c.variants.length)) ? '<span class="chip group-chip">Group</span> ' : '') + esc(c.name) + "</h3>" +
          '<div class="meta"><span>' + esc(c.role || c.uniqueTitle || c.status || "—") + "</span>" +
          "<span>" + (c.sagaIds || []).length + " saga(s)</span></div>";
        if (thumbImg(c)) inner = thumbImg(c) + '<div class="card-body">' + inner + "</div>";
        return '<a class="card' + (c.portrait ? " has-thumb" : "") + '" href="#/char/' + encodeURIComponent(c.id) + '">' + inner + "</a>";
      }).join("") +
      "</div>";
  }

  function renderPlaceList() {
    var list = DATA.places.slice().sort(function (a, b) {
      return a.name.localeCompare(b.name);
    });
    main.innerHTML =
      '<div class="list-tools"><span class="count">' + list.length + " places</span></div>" +
      '<div class="card-list">' +
      list.map(function (p) {
        return '<a class="card" href="#/place/' + encodeURIComponent(p.id) + '">' +
          '<div class="num">' + esc(p.type || "other") + "</div><h3>" + esc(p.name) + "</h3>" +
          '<div class="meta"><span>' + (p.sagaIds || []).length + " saga(s)</span></div></a>";
      }).join("") +
      "</div>";
  }

  function renderSearch(q) {
    var qq = String(q || "").trim().toLowerCase();
    searchWrap.hidden = false;
    if (!qq) {
      main.innerHTML = '<div class="empty">Type to search sagas, characters, and places.</div>';
      return;
    }
    var sagas = DATA.sagas.filter(function (s) {
      return (s.title + " " + (s.shortSummary || "") + " " + (s.premise || "")).toLowerCase().indexOf(qq) >= 0;
    });
    var chars = DATA.characters.filter(function (c) {
      return (c.name + " " + (c.aliases || []).join(" ") + " " + (c.role || "") + " " + (c.biography || "")).toLowerCase().indexOf(qq) >= 0;
    });
    var places = DATA.places.filter(function (p) {
      return (p.name + " " + (p.summary || "") + " " + (p.details || "")).toLowerCase().indexOf(qq) >= 0;
    });
    main.innerHTML =
      '<div class="section"><h2>Sagas (' + sagas.length + ')</h2><div class="card-list">' +
      (sagas.slice(0, 30).map(function (s) {
        return '<a class="card" href="#/saga/' + esc(s.id) + '"><h3>' + esc(s.title) + "</h3></a>";
      }).join("") || '<p class="muted">None</p>') +
      '</div></div><div class="section"><h2>Characters (' + chars.length + ')</h2><div class="card-list">' +
      (chars.slice(0, 40).map(function (c) {
        var inner = "<h3>" + esc(c.name) + "</h3>" + '<div class="meta">' + esc(c.role || "") + "</div>";
        if (thumbImg(c)) inner = thumbImg(c) + '<div class="card-body">' + inner + "</div>";
        return '<a class="card' + (c.portrait ? " has-thumb" : "") + '" href="#/char/' + encodeURIComponent(c.id) + '">' + inner + "</a>";
      }).join("") || '<p class="muted">None</p>') +
      '</div></div><div class="section"><h2>Places (' + places.length + ')</h2><div class="card-list">' +
      (places.slice(0, 40).map(function (p) {
        return '<a class="card" href="#/place/' + encodeURIComponent(p.id) + '"><h3>' + esc(p.name) + "</h3></a>";
      }).join("") || '<p class="muted">None</p>') +
      "</div></div>";
  }

  function renderSaga(id) {
    var s = bySaga[id];
    if (!s) { main.innerHTML = '<div class="empty">Saga not found.</div>'; return; }
    var powers = (s.powers || []).map(function (p) { return "<li>" + esc(p) + "</li>"; }).join("") ||
      "<li class='muted'>None extracted</li>";
    var details = (s.importantDetails || []).map(function (d) { return "<li>" + esc(d) + "</li>"; }).join("") ||
      "<li class='muted'>See premise / progress</li>";
    var beats = (s.progress || []).map(function (b, i) {
      return '<div class="beat"><div class="beat-num">Beat ' + (i + 1) + "</div><h4>" + esc(b.title) +
        "</h4><p>" + esc(b.summary) + "</p></div>";
    }).join("") || '<p class="muted">No beats extracted.</p>';
    var mts = (s.meatToiletIds || []).map(charCard).join("") ||
      '<p class="muted">No linked meat toilets in cleaned roster (often marker-A / thin dump).</p>';
    var pls = (s.placeIds || []).map(placeCard).join("") ||
      '<p class="muted">No places linked for this saga.</p>';
    main.innerHTML =
      '<h1 class="page-title">' + esc(s.title) + "</h1>" +
      '<div class="badges">' + markerChip(s.markers) +
      '<span class="chip">' + ((s.counts && s.counts.meatToilets) || 0) + " MT</span>" +
      '<span class="chip">' + ((s.counts && s.counts.places) || 0) + " places</span>" +
      '<span class="chip">' + ((s.counts && s.counts.messageCount) || 0) + " msgs</span></div>" +
      '<div class="btn-row">' +
      '<a class="btn primary" href="#/saga/' + esc(s.id) + '/full">Read full saga</a>' +
      '<a class="btn" href="' + esc(s.url) + '" target="_blank" rel="noopener">Open on grok.com</a></div>' +
      '<div class="layout has-infobox"><aside class="infobox"><h2>Infobox</h2><dl>' +
      "<dt>Number</dt><dd>#" + s.num + "</dd>" +
      "<dt>Markers</dt><dd>" + esc(s.markers) + "</dd>" +
      '<dt>Chat file</dt><dd class="faint">' + esc(s.chatFile || (s.hex + ".md")) + "</dd>" +
      "<dt>Powers snapshot</dt><dd>" + esc((s.powers || []).slice(0, 6).join("; ") || "—") + "</dd>" +
      "<dt>MT count</dt><dd>" + ((s.counts && s.counts.meatToilets) || 0) + "</dd>" +
      "<dt>Place count</dt><dd>" + ((s.counts && s.counts.places) || 0) + "</dd>" +
      "<dt>Messages</dt><dd>" + ((s.counts && s.counts.messageCount) || 0) + "</dd>" +
      '</dl></aside><div class="content">' +
      '<section class="section"><h2>Short summary</h2><div class="prose">' + paras(s.shortSummary) + "</div></section>" +
      '<section class="section"><h2>How it started</h2><div class="prose">' + paras(s.premise || s.howItStarted) + "</div></section>" +
      '<section class="section"><h2>Progress / story arcs</h2>' + beats + "</section>" +
      '<section class="section"><h2>Powers / systems</h2><ul class="bullets">' + powers + "</ul></section>" +
      '<section class="section"><h2>Important details</h2><ul class="bullets">' + details + "</ul></section>" +
      '<section class="section"><h2>Meat toilets</h2><div class="grid-cards">' + mts + "</div></section>" +
      '<section class="section"><h2>Places</h2><div class="grid-cards">' + pls + "</div></section>" +
      (s.rawNotes ? '<section class="section"><h2>Notes</h2><div class="prose">' + paras(s.rawNotes) + "</div></section>" : "") +
      '<div class="btn-row"><a class="btn primary" href="#/saga/' + esc(s.id) + '/full">Read full saga transcript</a></div>' +
      "</div></div>";
  }

  function simpleMarkdown(md) {
    var lines = String(md || "").split(/\r?\n/);
    var out = [];
    var buf = [];
    function flush() {
      if (!buf.length) return;
      var t = buf.join("\n").replace(/\s+$/, "");
      if (t) out.push('<div class="md-p">' + esc(t) + "</div>");
      buf = [];
    }
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      var h = /^(#{1,3})\s+(.*)$/.exec(line);
      if (h) {
        flush();
        var lvl = h[1].length;
        var cls = lvl === 1 ? "md-h1" : lvl === 2 ? "md-h2" : "md-h3";
        var role = "";
        if (/^User$/i.test(h[2])) role = " role-user";
        if (/^Grok$/i.test(h[2])) role = " role-grok";
        out.push('<div class="' + cls + role + '">' + esc(h[2]) + "</div>");
        continue;
      }
      if (/^[-*]\s+/.test(line)) {
        flush();
        out.push('<div class="md-li">• ' + esc(line.replace(/^[-*]\s+/, "")) + "</div>");
        continue;
      }
      if (line.trim() === "") { flush(); continue; }
      buf.push(line);
    }
    flush();
    return out.join("");
  }

  function renderFullSaga(id) {
    var s = bySaga[id];
    if (!s) { main.innerHTML = '<div class="empty">Saga not found.</div>'; return; }
    main.innerHTML =
      '<h1 class="page-title">' + esc(s.title) + "</h1>" +
      '<p class="page-sub">Full transcript (offline markdown)</p>' +
      '<div class="btn-row">' +
      '<a class="btn" href="#/saga/' + esc(s.id) + '">← Saga page</a>' +
      '<a class="btn" href="transcripts/' + esc(s.hex) + '.md" download>Download .md</a></div>' +
      '<div class="transcript" id="transcriptBox"><p class="muted">Loading transcript…</p></div>';
    var path = s.fullTranscriptPath || ("transcripts/" + s.hex + ".md");
    function show(text) {
      document.getElementById("transcriptBox").innerHTML = simpleMarkdown(text);
    }
    function fail() {
      document.getElementById("transcriptBox").innerHTML =
        '<div class="warn">Browser blocked loading the transcript via fetch from file://. Open the markdown directly or use a tiny local server.</div>' +
        "<p><a href=\"transcripts/" + esc(s.hex) + '.md">Open transcripts/' + esc(s.hex) + ".md</a></p>" +
        '<p class="muted">Or run: <code>python3 -m http.server 8765</code> inside the wiki folder.</p>';
    }
    fetch(path).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.text();
    }).then(show).catch(function () {
      try {
        var xhr = new XMLHttpRequest();
        xhr.open("GET", path, true);
        xhr.onload = function () {
          if (xhr.status === 0 || (xhr.status >= 200 && xhr.status < 300)) show(xhr.responseText);
          else fail();
        };
        xhr.onerror = fail;
        xhr.send();
      } catch (e) { fail(); }
    });
  }

  function renderGroupSection(c) {
    var items = c.variants || c.members || [];
    if (c.kind !== "group" && !items.length) return "";
    var countLine = "";
    if (c.details && (c.details.count || c.details.breakdown)) {
      countLine = '<p class="group-count"><strong>Numbers:</strong> ' +
        esc(c.details.count || "") +
        (c.details.breakdown ? " — " + esc(c.details.breakdown) : "") +
        "</p>";
    }
    var cards = items.map(function (v) {
      var label = v.label || v.name || "Variant";
      var meta = [];
      if (v.count !== undefined && v.count !== null && v.count !== "") meta.push(String(v.count));
      if (v.summary) meta.push(v.summary);
      if (v.appearance) meta.push(v.appearance);
      if (v.notes) meta.push(v.notes);
      return '<div class="variant-card"><h4>' + esc(label) + "</h4><p>" +
        esc(meta.join(" · ")) + "</p></div>";
    }).join("");
    return '<section class="section group-section"><h2>Group</h2>' +
      countLine +
      (cards ? '<div class="variant-list">' + cards + "</div>" :
        '<p class="muted">Group entity — see biography for composition.</p>') +
      "</section>";
  }

  function renderChar(id) {
    var c = byChar[id];
    if (!c) { main.innerHTML = '<div class="empty">Character not found.</div>'; return; }
    var evo = (c.evolution || []).map(function (e, i) {
      return '<div class="beat"><div class="beat-num">Stage ' + (i + 1) + "</div><h4>" + esc(e.title) +
        "</h4><p>" + esc(e.summary) + "</p></div>";
    }).join("") || '<p class="muted">No evolution notes in sources.</p>';
    var sagasHtml = (c.sagaIds || []).map(sagaCard).join("") || '<p class="muted">—</p>';
    var placesHtml = (c.placesRelated || []).map(placeCard).join("") || '<p class="muted">—</p>';
    var details = Object.keys(c.details || {}).map(function (k) {
      return '<div class="k">' + esc(k) + "</div><div>" + esc(c.details[k]) + "</div>";
    }).join("");
    var excerpts = (c.sourceExcerpts || []).slice(0, 5).map(function (e) {
      return "<li>" + esc(e) + "</li>";
    }).join("");
    var isGroup = c.kind === "group" || (c.variants && c.variants.length) || (c.members && c.members.length);
    var groupHtml = renderGroupSection(c);
    main.innerHTML =
      '<h1 class="page-title">' + esc(c.name) + "</h1>" +
      '<p class="page-sub">' + esc(c.uniqueTitle || c.role || c.status || "") + "</p>" +
      (isGroup ? '<div class="badges"><span class="chip group-chip">Group entity</span></div>' : "") +
      '<div class="layout has-infobox"><aside class="infobox">' + portraitHtml(c) + '<h2>Infobox</h2><dl>' +
      "<dt>Name</dt><dd>" + esc(c.name) + "</dd>" +
      "<dt>Aliases</dt><dd>" + esc((c.aliases || []).join(", ") || "—") + "</dd>" +
      "<dt>Kind</dt><dd>" + esc(isGroup ? "group" : "character") + "</dd>" +
      "<dt>Role</dt><dd>" + esc(c.role || "—") + "</dd>" +
      "<dt>Status</dt><dd>" + esc(c.status || "—") + "</dd>" +
      "<dt>Relation to Eon</dt><dd>" + esc(c.relationshipToEon || "—") + "</dd>" +
      "<dt>Sagas</dt><dd>" + (c.sagaIds || []).length + "</dd></dl></aside><div class=\"content\">" +
      groupHtml +
      '<section class="section"><h2>Biography</h2><div class="prose">' + paras(c.biography) + "</div></section>" +
      '<section class="section"><h2>Appearance</h2><div class="prose">' + paras(c.appearance) + "</div></section>" +
      '<section class="section"><h2>Personality</h2><div class="prose">' + paras(c.personality) + "</div></section>" +
      '<section class="section"><h2>Powers / ownership / ranks</h2><div class="prose">' +
      paras([c.powers, c.ranks, c.status].filter(Boolean).join("\n\n")) + "</div></section>" +
      '<section class="section"><h2>Evolution / growth</h2>' + evo + "</section>" +
      '<section class="section"><h2>Related places</h2><div class="grid-cards">' + placesHtml + "</div></section>" +
      '<section class="section"><h2>Appears in</h2><div class="grid-cards">' + sagasHtml + "</div></section>" +
      (details ? '<section class="section"><h2>Extra details</h2><div class="kv">' + details + "</div></section>" : "") +
      (excerpts ? '<section class="section"><h2>Source excerpts</h2><ul class="bullets">' + excerpts + "</ul></section>" : "") +
      "</div></div>";
  }

  function renderPlace(id) {
    var p = byPlace[id];
    if (!p) { main.innerHTML = '<div class="empty">Place not found.</div>'; return; }
    var sagasHtml = (p.sagaIds || []).map(sagaCard).join("") || '<p class="muted">—</p>';
    var charsHtml = (p.relatedCharacterIds || []).map(charCard).join("") || '<p class="muted">—</p>';
    var facts = (p.notableFacts || []).map(function (f) { return "<li>" + esc(f) + "</li>"; }).join("");
    main.innerHTML =
      '<h1 class="page-title">' + esc(p.name) + "</h1>" +
      '<div class="badges"><span class="chip">' + esc(p.type || "other") + "</span></div>" +
      '<div class="layout has-infobox"><aside class="infobox"><h2>Infobox</h2><dl>' +
      "<dt>Type</dt><dd>" + esc(p.type || "other") + "</dd>" +
      "<dt>Sagas</dt><dd>" + (p.sagaIds || []).length + "</dd></dl></aside><div class=\"content\">" +
      '<section class="section"><h2>Summary</h2><div class="prose">' + paras(p.summary) + "</div></section>" +
      '<section class="section"><h2>Details</h2><div class="prose">' + paras(p.details) + "</div></section>" +
      (facts ? '<section class="section"><h2>Notable facts</h2><ul class="bullets">' + facts + "</ul></section>" : "") +
      '<section class="section"><h2>Related characters</h2><div class="grid-cards">' + charsHtml + "</div></section>" +
      '<section class="section"><h2>Sagas</h2><div class="grid-cards">' + sagasHtml + "</div></section>" +
      "</div></div>";
  }

  function route() {
    var raw = (location.hash || "#/sagas").replace(/^#/, "");
    var parts = raw.split("/").filter(Boolean);
    var view = parts[0] || "sagas";
    var detail = view === "saga" || view === "char" || view === "place";
    backBtn.classList.toggle("visible", detail);
    if (view === "sagas") { setTab("sagas"); searchWrap.hidden = true; renderSagaList(); return; }
    if (view === "chars") { setTab("chars"); searchWrap.hidden = true; renderCharList(); return; }
    if (view === "places") { setTab("places"); searchWrap.hidden = true; renderPlaceList(); return; }
    if (view === "search") { setTab("search"); renderSearch(qInput.value || ""); return; }
    if (view === "saga" && parts[1] && parts[2] === "full") {
      setTab("sagas"); searchWrap.hidden = true; renderFullSaga(parts[1]); return;
    }
    if (view === "saga" && parts[1]) { setTab("sagas"); searchWrap.hidden = true; renderSaga(parts[1]); return; }
    if (view === "char" && parts[1]) {
      setTab("chars"); searchWrap.hidden = true; renderChar(decodeURIComponent(parts[1])); return;
    }
    if (view === "place" && parts[1]) {
      setTab("places"); searchWrap.hidden = true; renderPlace(decodeURIComponent(parts[1])); return;
    }
    setTab("sagas"); searchWrap.hidden = true; renderSagaList();
  }

  mainNav.addEventListener("click", function (e) {
    var btn = e.target.closest("button[data-tab]");
    if (!btn) return;
    location.hash = "#/" + btn.getAttribute("data-tab");
  });
  backBtn.addEventListener("click", function () {
    if (history.length > 1) history.back();
    else location.hash = "#/sagas";
  });
  var timer = null;
  qInput.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () {
      if (location.hash.indexOf("#/search") !== 0) location.hash = "#/search";
      else renderSearch(qInput.value);
    }, 120);
  });
  window.addEventListener("hashchange", route);
  route();
})();
