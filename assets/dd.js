// DDIA 第二版导读：共享脚本。注入顶栏、章头（原书和译本各在哪）、章末导航、页脚；
// 接管分节地图（打勾、节号、层级）、词条的「记下」和筛选、先预测和读后对照、选择题、本地笔记、首页目录和全书回顾。
// 骨架来自 Free to Choose 导读的 fc.js（再往前是 Creating Modern Capitalism 伴读、枪炮伴读），选择题来自 APOSD 精读站。
// localStorage 键一律带 dd- 前缀（全站各教程同一个域名）：dd-done-N、dd-sec-N-节号、dd-star-NN-词条、dd-note-…、dd-bet-…、dd-theme。
// 章节页自己的模拟器脚本可以用 window.DD 里的 h()。
(() => {
  const CH = window.DD_CHAPTERS || [], READY = new Set(window.DD_READY || []), PARTS = window.DD_PARTS || [];
  const SECS = window.DD_SECS || {};
  const ROOT = document.currentScript.src.replace(/assets\/dd\.js.*$/, "");
  const LS = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { v == null || v === "" ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} },
    keys(prefix) { try { return Object.keys(localStorage).filter((k) => k.startsWith(prefix)); } catch { return []; } },
  };
  const h = (tag, attrs = {}, ...kids) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) k === "class" ? (el.className = v) : k.startsWith("on") ? (el[k] = v) : el.setAttribute(k, v);
    el.append(...kids.filter((x) => x != null));
    return el;
  };
  const pad = (n) => String(n).padStart(2, "0");
  const chHref = (n) => `${ROOT}chapters/${pad(n)}.html`;
  const chLabel = (n) => (n === 0 ? "开读之前" : `第 ${n} 章`);
  const chTitle = (c) => (c.n === 0 ? "开读之前 · 序言与全书地图" : `${chLabel(c.n)} · ${c.t}`);
  const isDone = (n) => LS.get(`dd-done-${n}`) === "1";
  const secDone = (n, k) => LS.get(`dd-sec-${n}-${k}`) === "1";
  const meta = (n) => SECS[n] || { words: 0, secs: [] };
  const nSecs = (n) => meta(n).secs.length;
  const badges = (c) => [
    h("span", { class: "badge" }, c.topic),
    h("span", { class: "badge" }, `约 ${Math.round(meta(c.n).words / 100) * 100} 词 · ${nSecs(c.n)} 节`),
    c.sim ? h("span", { class: "badge b-sim" }, `模拟器：${c.sim}`) : null,
  ];

  const saved = LS.get("dd-theme");
  if (saved) document.documentElement.dataset.theme = saved;
  function themeBtn() {
    return h("button", { class: "btn", "aria-label": "切换深色/浅色", onclick() {
      const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
      const next = dark ? "light" : "dark";
      document.documentElement.dataset.theme = next; LS.set("dd-theme", next);
    } }, "深/浅");
  }
  const curN = () => (document.body.dataset.chapter == null ? null : Number(document.body.dataset.chapter));

  function mountChrome() {
    const n = curN(), c = CH.find((x) => x.n === n);
    document.body.prepend(h("div", { class: "topbar" }, h("div", { class: "topbar-inner" },
      h("a", { class: "home", href: `${ROOT}index.html` }, "DDIA 第二版 · 导读"),
      h("span", { class: "crumb" }, c ? chTitle(c) : ""),
      themeBtn())));
    document.body.append(h("footer", { class: "site-footer" },
      h("a", { href: "https://beian.miit.gov.cn/", target: "_blank", rel: "noopener" }, "京ICP备18057656号-1")));
    if (!c) return;
    const main = document.querySelector("main");
    document.title = `${chTitle(c)} · DDIA 导读`;
    main.prepend(h("div", { class: "chapter-head" },
      h("div", { class: "kicker" }, n === 0 ? "Preface" : `Chapter ${n} · ${c.en}`),
      h("h1", {}, n === 0 ? "开读之前" : `${chLabel(n)}　${c.t}`),
      h("dl", { class: "where" },
        h("dt", {}, "原书"), h("dd", {}, n === 0 ? "Preface（第一章之前）" : `Chapter ${n}, ${c.en}`),
        h("dt", {}, "译本"), h("dd", {}, n === 0 ? "前言" : `第 ${n} 章。分节地图里每节都给了本站译的中文意思，拿它去译本里对`)),
      h("div", { class: "badges" }, ...badges(c))));
    const prev = CH.find((x) => x.n === n - 1), next = CH.find((x) => x.n === n + 1);
    const done = h("button", { class: "btn" });
    const paint = () => { done.textContent = isDone(n) ? `✓ 已读完${n ? "这一章" : ""}` : `标记：${n ? "这一章" : "这一篇"}读完了`; done.setAttribute("aria-pressed", isDone(n)); };
    done.onclick = () => { LS.set(`dd-done-${n}`, isDone(n) ? null : "1"); paint(); };
    paint();
    main.append(h("div", { class: "chapter-end" }, done, h("div", { class: "nav" },
      prev && READY.has(prev.n) ? h("a", { class: "btn", href: chHref(prev.n) }, `← ${chLabel(prev.n)}`) : null,
      h("a", { class: "btn", href: `${ROOT}index.html` }, "目录"),
      next && READY.has(next.n) ? h("a", { class: "btn primary", href: chHref(next.n) }, `${chLabel(next.n)} →`) : null)));
  }

  // 词条：<div class="entry [trap]"><div class="en">…</div><div class="loc" data-p="段号">原句里的 4–7 个词</div><div class="zh">…</div><div class="note">…</div></div>
  function wireEntries() {
    const entries = [...document.querySelectorAll(".entry")];
    if (!entries.length) return;
    const n = pad(curN());
    const first = entries[0];
    const count = h("span", { class: "count" });
    const mk = (label, cls) => h("button", { class: "btn", "aria-pressed": String(!cls), onclick(e) {
      document.body.classList.remove("only-traps", "only-starred");
      if (cls) document.body.classList.add(cls);
      bar.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b === e.currentTarget)));
    } }, label);
    const bar = h("div", { class: "toolbar" }, mk("全部", ""), mk("只看「每个字都认识」", "only-traps"), mk("只看我记下的", "only-starred"), count);
    (first.previousElementSibling?.matches("h3.sec-head") ? first.previousElementSibling : first).before(bar, h("p", { class: "empty-note" }, "还没有记下任何词条。回到「全部」，点词条右边的「记下」。"));
    const refresh = () => {
      const k = entries.filter((e) => e.classList.contains("starred")).length;
      document.body.classList.toggle("none-starred", k === 0);
      count.textContent = `共 ${entries.length} 条 · 已记下 ${k}`;
    };
    for (const e of entries) {
      const en = e.querySelector(".en"), text = en.textContent.trim();
      const key = `dd-star-${n}-${text}`;
      if (e.classList.contains("trap")) en.append(h("span", { class: "tag" }, "每个字都认识"));
      const btn = h("button", { class: "btn star" });
      const paint = () => { btn.textContent = e.classList.contains("starred") ? "已记下" : "记下"; };
      if (LS.get(key)) e.classList.add("starred");
      btn.onclick = () => {
        const on = e.classList.toggle("starred");
        LS.set(key, on ? JSON.stringify({ zh: e.querySelector(".zh")?.textContent.trim() || "" }) : null);
        paint(); refresh();
      };
      paint(); en.after(btn);
    }
    refresh();
  }

  // 分节地图：<ol class="secmap"><li class="sit">第一次坐下 …</li><li data-sec="1.2"><b>原书小标题<span class="w">约 600 词</span></b><span class="cn">本站译的小标题</span><span class="what">…</span></li>…</ol>
  // 每节加：读过了的勾、§k、层级（一级小标题 lv1、二级 lv2）；有词条的节加「词条 ↓」。
  function wireSecmap() {
    const n = curN();
    for (const li of document.querySelectorAll(".secmap li[data-sec]")) {
      const k = li.dataset.sec, key = `dd-sec-${n}-${k}`;
      const s = meta(n).secs.find((x) => x.k === k);
      li.classList.add(s && s.lv === 2 ? "lv2" : "lv1");
      const box = h("input", { type: "checkbox", "aria-label": `第 ${k} 节读过了` });
      box.checked = secDone(n, k); li.classList.toggle("done", box.checked);
      box.onchange = () => { LS.set(key, box.checked ? "1" : null); li.classList.toggle("done", box.checked); };
      li.prepend(box, h("span", { class: "k" }, `§${k}`));
      if (document.getElementById(`s${k}`)) li.append(h("a", { class: "jump", href: `#s${k}` }, "词条 ↓"));
    }
  }
  const secProgress = (c) => {
    const k = meta(c.n).secs.filter((s) => secDone(c.n, s.k)).length;
    return k && !isDone(c.n) ? h("span", { class: "sp" }, `　已读 ${k} 节`) : null;
  };

  // 本地笔记：<input class="note" data-key="01-f1"> / <textarea class="note" data-key="01-oneline">，键 dd-note-01-f1
  function wireNotes() {
    for (const el of document.querySelectorAll("input.note, textarea.note")) {
      const key = `dd-note-${el.dataset.key}`;
      el.value = LS.get(key) || "";
      let tip = null;
      if (el.tagName === "TEXTAREA") { tip = h("div", { class: "note-tip" }, el.value ? "已保存在本机浏览器" : "写下来会自动保存在本机浏览器"); el.after(tip); }
      let t = null;
      el.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { LS.set(key, el.value.trim() ? el.value : null); if (tip) tip.textContent = "已保存在本机浏览器"; }, 400); });
    }
  }

  // 先下注：<div class="bet" data-key="01-a"><div class="q">…</div><div class="opts"><button>…</button>…</div><textarea class="note" data-key="01-a-bet"></textarea></div>
  // 读后对照：<div class="payoff" data-bet="01-a"><div class="mine"></div><p>…</p></div>，显示读者当初押了什么、写了什么。键 dd-bet-01-a（选项序号）
  function wireBets() {
    for (const bet of document.querySelectorAll(".bet")) {
      const key = `dd-bet-${bet.dataset.key}`;
      const btns = [...bet.querySelectorAll(".opts button")];
      const paint = () => { const v = LS.get(key); btns.forEach((b, k) => b.classList.toggle("sel", String(k) === v)); };
      btns.forEach((b, k) => (b.onclick = () => { LS.set(key, LS.get(key) === String(k) ? null : String(k)); paint(); fillPayoffs(); }));
      paint();
    }
    fillPayoffs();
  }
  function fillPayoffs() {
    for (const po of document.querySelectorAll(".payoff")) {
      const k = po.dataset.bet, mine = po.querySelector(".mine");
      if (!mine) continue;
      const bet = document.querySelector(`.bet[data-key="${k}"]`);
      const v = LS.get(`dd-bet-${k}`);
      const choice = bet && v != null ? bet.querySelectorAll(".opts button")[Number(v)] : null;
      const note = LS.get(`dd-note-${k}-bet`) || "";
      const q = bet?.querySelector(".q")?.textContent.trim();
      mine.textContent = [q ? `当初的问题：${q}` : "", choice ? `你猜的是：${choice.textContent.trim()}` : "", note ? `你写的理由：${note}` : ""].filter(Boolean).join("\n");
      if (!choice && !note) mine.dataset.empty = "1"; else delete mine.dataset.empty;
    }
  }

  // 选择题：<div class="mcq" data-answer="1"><div class="q">…</div><div class="opts"><button>…</button>…</div><div class="explain">…</div></div>
  // data-answer 是 0 起的下标。点一次就锁定，显示对错和解释；<p class="quiz-score"> 显示这一页的得分。
  function wireMcq() {
    for (const q of document.querySelectorAll(".mcq")) {
      const ans = Number(q.dataset.answer), btns = [...q.querySelectorAll(".opts button")];
      btns.forEach((b, k) => (b.onclick = () => {
        if (q.classList.contains("answered")) return;
        q.classList.add("answered");
        b.classList.add(k === ans ? "right" : "wrong");
        btns[ans]?.classList.add("right");
        q.dataset.correct = k === ans ? "1" : "0";
        score();
      }));
    }
    score();
  }
  function score() {
    const all = document.querySelectorAll(".mcq").length, done = document.querySelectorAll(".mcq.answered").length, right = document.querySelectorAll('.mcq[data-correct="1"]').length;
    for (const el of document.querySelectorAll(".quiz-score")) el.textContent = `已答 ${done} / ${all}，答对 ${right}`;
  }

  // 首页：目录、进度、我的词本
  function mountHome() {
    const toc = document.getElementById("toc");
    if (!toc) return;
    let part = null;
    for (const c of CH) {
      if (c.part !== part) { part = c.part; const P = PARTS.find((x) => x.k === part); if (P) toc.append(h("li", { class: "blk" }, P.t)); }
      const ready = READY.has(c.n);
      toc.append(h("li", {}, h("a", Object.assign({ class: (isDone(c.n) ? "done " : "") + (ready ? "" : "todo") }, ready ? { href: chHref(c.n) } : {}),
        h("span", { class: "n" }, isDone(c.n) ? "✓" : c.n === 0 ? "序" : String(c.n)),
        h("span", { class: "t" }, c.t, h("span", { class: "te" }, c.en)),
        h("span", { class: "b" }, ...(ready ? badges(c) : [h("span", { class: "badge" }, c.topic), h("span", { class: "badge" }, "待写")])),
        c.d ? h("span", { class: "d" }, c.d, secProgress(c)) : null)));
    }
    const parts = document.getElementById("parts");
    if (parts) for (const P of PARTS) parts.append(h("div", { class: `p${P.k}` }, h("b", {}, `${P.t}　第 ${P.ch[0]}${P.ch.length > 1 ? `–${P.ch[P.ch.length - 1]}` : ""} 章`), P.d));
    const doneN = CH.filter((c) => isDone(c.n)).length;
    const p = document.getElementById("progress");
    if (p) p.append(h("div", { class: "progress" }, Object.assign(h("i"), { style: `width:${(100 * doneN) / CH.length}%` })), h("p", { class: "lede" }, `已读完 ${doneN} / ${CH.length}`));
    const wb = document.getElementById("wordbook");
    if (wb) {
      const keys = LS.keys("dd-star-").sort();
      if (!keys.length) wb.append(h("p", { class: "lede" }, "还是空的。在章节页里点词条右边的「记下」，它们会汇总到这里。"));
      for (const k of keys) {
        const m = k.match(/^dd-star-(\d\d)-(.*)$/); if (!m) continue;
        let zh = ""; try { zh = JSON.parse(LS.get(k)).zh; } catch {}
        wb.append(h("div", {}, h("b", {}, m[2]), h("span", {}, zh), h("a", { href: chHref(Number(m[1])) }, chLabel(Number(m[1])))));
      }
    }
  }

  // 全书回顾（recap.html 的 #recap）：读各个已完成章节页的「精彩回顾」汇总。章节页改了，这里自动跟着变。
  async function mountRecap() {
    const box = document.getElementById("recap");
    if (!box) return;
    let shown = 0;
    for (const c of CH) {
      if (!READY.has(c.n)) continue;
      let doc;
      try { doc = new DOMParser().parseFromString(await (await fetch(chHref(c.n))).text(), "text/html"); } catch { continue; }
      const line = doc.querySelector(".recall-line"), items = doc.querySelector(".recall");
      if (!items) continue;
      for (const a of items.querySelectorAll(".sec")) a.replaceWith(h("a", { class: "sec", href: chHref(c.n) }, a.textContent));
      box.append(h("section", { class: "recap-ch" },
        h("h2", {}, h("a", { href: chHref(c.n) }, chTitle(c))),
        h("p", { class: "lede" }, c.en),
        line ? document.importNode(line, true) : null, document.importNode(items, true)));
      shown++;
    }
    if (!shown) box.append(h("p", { class: "lede" }, "还没有写好的章节。"));
  }

  document.addEventListener("DOMContentLoaded", () => { mountChrome(); wireSecmap(); wireEntries(); wireNotes(); wireBets(); wireMcq(); mountHome(); mountRecap(); });
  // 跨设备同步：模块在首页仓库里（/_home/sync.js），所有教程站共用。只在线上加载；本地预览要联调时设 localStorage["sync-dev"] = "1"
  // 上线前要把 dd- 加进 sync.js 的 PREFIXES 和 sync_server.py 的 KEY_RE，见 ~/tutorials-deploy/README.md。
  try { if (location.hostname === "t.miaowuao.cn" || localStorage.getItem("sync-dev")) document.head.append(Object.assign(document.createElement("script"), { src: "/_home/sync.js" })); } catch (e) {}
  window.DD = { h, LS, ROOT, chHref, chLabel, isDone };
})();
