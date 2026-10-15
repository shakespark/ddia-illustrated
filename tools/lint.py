#!/usr/bin/env python3
"""章节页结构检查：python3 tools/lint.py chapters/04.html …
查：小节标题和顺序、先预测和读后对照是否成对、骨架（SVG 和边读边填的表）、分节地图（每节一条、照抄原书小标题、词数、中文小标题、坐下分隔）、
先用中文过一遍（SVG、术语表）、模拟器（只在该有的章里、只有一个、脚本只在这里）、词条（.en 重复、.loc 是否在原文那一段里、是否在自己那一节的小标题下、
顺序、密度、trap 占比）、「先停下」的分界、引用块（数量、只引作者的正文）、判断题（题数、答案位置）、术语页链接、本站其他书的链接、
图片、理解检查的题数、精彩回顾、写死的颜色、直引号、原书材料的路径。通用的几项在 ~/tutorials-deploy/scripts/lint_common.py。
00.html（开读之前）用另一张小节表，见 SECS0。"""
import os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.expanduser("~/tutorials-deploy/scripts"))
from lint_common import norm, check_entries, check_quotes, check_images, check_markup, counts

SECS = ["这一章在做什么", "读之前：先预测", "这一章的骨架", "分节地图", "先用中文过一遍", "动手：模拟器", "词与短语",
        "读完：回到你的预测", "判断题：换成你来选", "和本站其他书对照", "值得停下来的句子", "检查一下理解", "精彩回顾"]
SECS0 = ["这本书讲什么", "全书地图", "怎么读", "第二版新在哪", "分节地图", "词与短语", "本站怎么用"]
OPTIONAL = {"和本站其他书对照"}
MAP0 = {"1", "2", "3", "4"}
SIM_CHAPTERS = {2, 4, 5, 6, 7, 8, 9, 10, 11, 12}
GLOSS = os.path.join(ROOT, "glossary.html")
SISTERS = {"ostep": "~/operating_systems_three_easy_pieces", "aposd": "~/aposd"}
han = lambda s: len(re.findall(r"[一-鿿]", re.sub(r"<[^>]+>", "", s)))

def load(src):
    """读 source/text/NN.txt。返回 paras {段号: 文字}、marks {段号: 标记}、secs [(节号, 小标题, 第一段, 最后一段, 正文词数)]。"""
    paras, marks, secs = {}, {}, []
    for line in open(src, encoding="utf-8").read().splitlines():
        m = re.match(r"## §(\S+) (.*)$", line)
        if m: secs.append([m.group(1), m.group(2), None, None, 0]); continue
        m = re.match(r"\[(\d+)\] (\{[A-Z]\} )?(.*)$", line)
        if m:
            p = int(m.group(1)); paras[p] = norm(m.group(3)); marks[p] = (m.group(2) or "").strip()
            s = secs[-1]; s[2] = s[2] or p; s[3] = p
            if marks[p] not in ("{C}", "{F}", "{T}", "{E}"): s[4] += len(m.group(3).split())
    return paras, marks, [tuple(s) for s in secs]

bad = 0
gloss_ids = set(re.findall(r'id="(g-[a-z0-9-]+)"', open(GLOSS, encoding="utf-8").read())) if os.path.exists(GLOSS) else set()
for path in sys.argv[1:]:
    t = open(path, encoding="utf-8").read(); errs = []
    nn = re.search(r"(\d\d)\.html$", path).group(1); N = int(nn)
    paras, marks, secs = load(os.path.join(ROOT, f"source/text/{nn}.txt"))
    if N == 0: secs = [x for x in secs if x[0] in MAP0]   # Preface 只给前四节，后面是出版社的套话和致谢
    want_secs = SECS0 if N == 0 else [s for s in SECS if s != "动手：模拟器" or N in SIM_CHAPTERS]
    if f'<body data-chapter="{N}">' not in t: errs.append(f'<body> 应写成 <body data-chapter="{N}">')
    def part(a):
        i = t.find(f"<h2>{a}</h2>")
        if i < 0: return ""
        ends = [e for e in (t.find("<h2>", i + 1), t.find('<div class="gate">', i + 1)) if e > i]
        return t[i:min(ends)] if ends else t[i:]

    # 小节标题和顺序
    present = [s for s in want_secs if f"<h2>{s}</h2>" in t]
    for s in want_secs:
        if s not in present and s not in OPTIONAL: errs.append(f"缺少小节：{s}")
    pos = [t.find(f"<h2>{s}</h2>") for s in present]
    if pos != sorted(pos): errs.append("小节顺序不对，应为：" + " → ".join(want_secs))
    for s in re.findall(r"<h2>(.*?)</h2>", t):
        if s not in want_secs: errs.append(f"多出来的小节标题：{s}（标题一个字都不能改；「动手：模拟器」只有第 {sorted(SIM_CHAPTERS)} 章有）")
    if N:
        g = re.search(r'<div class="gist">(.*?)</div>', t, flags=re.S)
        if not g: errs.append("「这一章在做什么」要有 <div class=\"gist\">")
        elif han(g.group(1)) > 200: errs.append(f"「这一章在做什么」{han(g.group(1))} 个汉字，超过 200")

    # 先预测 ↔ 读后对照
    if N:
        pre = part("读之前：先预测")
        bets = re.findall(r'<div class="bet" data-key="([^"]+)">', pre)
        if not 1 <= len(bets) <= 2: errs.append(f"「读之前：先预测」要有 1–2 个 <div class=\"bet\" data-key>，现在 {len(bets)} 个")
        for k in bets:
            if not k.startswith(f"{nn}-"): errs.append(f"预测的 data-key 要以 {nn}- 开头：{k}")
            if f'<div class="payoff" data-bet="{k}"><div class="mine"></div>' not in part("读完：回到你的预测"):
                errs.append(f"预测 {k} 在「读完：回到你的预测」里没有对应的 <div class=\"payoff\" data-bet=\"{k}\"><div class=\"mine\"></div>…")
            if f'<textarea class="note" data-key="{k}-bet"' not in pre: errs.append(f"预测 {k} 要带一个 <textarea class=\"note\" data-key=\"{k}-bet\">")
        if '<div class="crux">' not in pre: errs.append("「读之前」要有一个 <div class=\"crux\">")
        nq = len(re.findall(r"<li>", re.search(r'<ol class="qs">(.*?)</ol>', pre, flags=re.S).group(1))) if '<ol class="qs">' in pre else 0
        if not 2 <= nq <= 4: errs.append(f"「读之前」带着读的问题（<ol class=\"qs\">）应有 2–4 个，现在 {nq} 个")
    for k in re.findall(r'class="note" data-key="([^"]+)"', t):
        if not k.startswith(f"{nn}-"): errs.append(f"笔记的 data-key 要以 {nn}- 开头：{k}")

    # 骨架：SVG + 边读边填
    if N:
        sk = part("这一章的骨架")
        keys = re.findall(r'<input class="note" data-key="([^"]+)"', sk)
        if '<table class="findit">' not in sk or not 4 <= len(keys) <= 7: errs.append(f"「骨架」要有一张边读边填的表（<table class=\"findit\">），4–7 行，现在 {len(keys)} 行")
        if '<details class="reveal">' not in sk: errs.append("「骨架」的表后面要有 <details class=\"reveal\"> 对照")
        if "<svg" not in sk: errs.append("「骨架」要有一张自己画的 SVG")

    # 分节地图：每节一条，<b> 照抄小标题（§0 照抄第一段开头 4–7 个词），有 .cn 和 .what
    sm = part("分节地图")
    items = re.findall(r'<li data-sec="([0-9.]+)"><b>(.*?)<span class="w">约 (\d+) 词</span></b><span class="cn">(.*?)</span><span class="what">(.*?)</span></li>', sm, flags=re.S)
    want = [s[0] for s in secs]
    if [k for k, *_ in items] != want: errs.append(f"分节地图的节号应为 {want}，实际认出 {[k for k, *_ in items]}（写法照规范：<li data-sec><b>…<span class=\"w\">约 N 词</span></b><span class=\"cn\">…</span><span class=\"what\">…</span></li>）")
    for (k, b, w, cn, what), (sk_, title, p0, p1, words) in zip(items, secs):
        b = norm(re.sub(r"<[^>]+>", "", b)).strip("… ").strip()
        if title == "（开篇）":
            first = next((paras[p] for p in range(p0, p1 + 1) if p in paras and marks.get(p) != "{E}"), "")
            if not (first.startswith(b) and 4 <= len(b.split()) <= 7): errs.append(f"分节地图 §{k}：开篇没有小标题，<b> 照抄第一段（不算题词）开头 4–7 个词：{b!r}")
            if han(cn) == 0: errs.append(f"分节地图 §{k}：.cn 写「开篇」")
        else:
            if b != norm(title): errs.append(f"分节地图 §{k}：<b> 要一字不差地照抄小标题 {title!r}，现在是 {b!r}")
            if not 1 <= han(cn) <= 20: errs.append(f"分节地图 §{k}：.cn 要写本站译的中文小标题（不超过 20 个汉字），现在是 {cn!r}")
        want_w = max(100, round(words / 100) * 100)
        if abs(int(w) - want_w) > max(100, words * 0.1): errs.append(f"分节地图 §{k}：词数写的是 {w}，应为约 {want_w}")
        if not 1 <= han(what) <= 50: errs.append(f"分节地图 §{k}：说明（.what）{han(what)} 个汉字，要 1–50 个")
    # 坐下：每次 2000–5500 词，单独一节超过 5500 的除外
    total = sum(s[4] for s in secs)
    wmap = {s[0]: s[4] for s in secs}
    chunks, cur = [], None
    for m in re.finditer(r'<li class="sit">|<li data-sec="([0-9.]+)">', sm):
        if not m.group(1): cur = []; chunks.append(cur)
        elif cur is not None: cur.append(m.group(1))
    if N and total > 6000:
        if len(chunks) < 2: errs.append("分节地图要用 <li class=\"sit\"> 分成几次坐下")
        elif not sm.split('<li data-sec=')[0].count('<li class="sit">'): errs.append("分节地图的第一条要是 <li class=\"sit\">")
        for i, c in enumerate(chunks):
            ws = sum(wmap.get(k, 0) for k in c)
            single = len(c) == 1 or max((wmap.get(k, 0) for k in c), default=0) > 5500
            if ws > 5500 and not single: errs.append(f"第 {i + 1} 次坐下 {ws} 词，超过 5500")
            if ws < 2000 and i != len(chunks) - 1: errs.append(f"第 {i + 1} 次坐下只有 {ws} 词，不到 2000（只有最后一次可以少）")

    # 先用中文过一遍：SVG、术语表
    if N:
        pr = part("先用中文过一遍")
        if pr.count("<svg") < 2: errs.append(f"「先用中文过一遍」至少要两张自己画的 SVG，现在 {pr.count('<svg')} 张")
        tb = re.search(r'<table class="terms">(.*?)</table>', pr, flags=re.S)
        rows = len(re.findall(r"<tr>", tb.group(1))) - 1 if tb else 0
        if not 8 <= rows <= 15: errs.append(f"「先用中文过一遍」的术语表（<table class=\"terms\">）要有 8–15 行，现在 {rows} 行")
        if tb and "<th>英文</th><th>中文</th><th>一句话</th>" not in tb.group(1): errs.append("术语表的表头写 <th>英文</th><th>中文</th><th>一句话</th>")
        nsys = len(re.findall(r"<div><b>", re.search(r'<div class="sys">(.*?)</div>\s*(?:<h3|<div class="table-wrap"|<table)', pr, flags=re.S).group(1))) if '<div class="sys">' in pr else 0
        if nsys > 10: errs.append(f"「这一章点名的系统」不超过 10 个，现在 {nsys} 个")

    # 模拟器：该有的章有且只有一个；脚本只为它服务
    nsim = len(re.findall(r'<div class="sim" id="sim-', t))
    scripts = re.findall(r"<script(?![^>]*src=)[^>]*>.*?</script>", t, flags=re.S)
    styles = re.findall(r"<style[^>]*>.*?</style>", t, flags=re.S)
    if N in SIM_CHAPTERS:
        sp = part("动手：模拟器")
        if f'<div class="sim" id="sim-{nn}">' not in sp: errs.append(f"「动手：模拟器」里要有 <div class=\"sim\" id=\"sim-{nn}\">")
        if nsim != 1: errs.append(f"一页只有一个模拟器，现在 {nsim} 个")
        if len(scripts) != 1: errs.append(f"模拟器的脚本写在页面末尾一个 <script> 里，现在 {len(scripts)} 段")
        for st in styles:
            for sel in re.findall(r"(?:^|})\s*([^{}@]+)\{", re.sub(r"/\*.*?\*/", "", st[st.find(">") + 1:], flags=re.S)):
                if not all(x.strip().startswith(f"#sim-{nn}") for x in sel.split(",")): errs.append(f"页面 <style> 里的选择器要以 #sim-{nn} 开头：{sel.strip()[:40]}")
            if re.search(r"#[0-9a-fA-F]{3,6}\b|rgb\(", st): errs.append("页面 <style> 里写死了颜色，用 var(--…)")
        if "</main>" in t and scripts and t.find(scripts[0]) < t.find("</main>"): errs.append("模拟器的 <script> 放在 </main> 之后")
    elif nsim or scripts or styles: errs.append(f"第 {N} 章没有模拟器，页面里不能有 .sim、<script> 或 <style>")

    # 词条：在自己那一节的小标题下
    words_sec = part("词与短语")
    rng = {s[0]: (s[2], s[3]) for s in secs}
    cur = None
    for m in re.finditer(r'<h3 class="sec-head" id="s([0-9.]+)">|<div class="loc" data-p="(\d+)">', words_sec):
        if m.group(1): cur = m.group(1); continue
        p = int(m.group(2))
        if cur is None: errs.append(f"第 {p} 段的词条前面没有节的小标题 <h3 class=\"sec-head\" id=\"sK\">"); continue
        a, b = rng.get(cur, (0, -1))
        if not (a or 0) <= p <= (b if b is not None else -1): errs.append(f"第 {p} 段的词条放在了 §{cur} 下面（§{cur} 是第 {a}–{b} 段）")
    for k, first in re.findall(r'<h3 class="sec-head" id="s([0-9.]+)">§([0-9.]+) ', words_sec):
        if k not in rng: errs.append(f"词与短语：没有 §{k} 这一节")
        if k != first: errs.append(f"词与短语：id=\"s{k}\" 和标题里的 §{first} 对不上")
    prose = {p: v for p, v in paras.items() if marks.get(p) not in ("{C}", "{F}", "{T}", "{E}")}
    errs += check_entries(t, prose if N else paras, per_k=2.5 if N else None, max_n=90, trap_ratio=1 / 3, scope="这一章")
    c0 = counts(t)
    if c0["词条"] and c0["trap"] > c0["词条"] * 0.8: errs.append(f"trap {c0['trap']}/{c0['词条']}，标得太宽（三分之一到八成为宜）")

    # 先停下的分界
    if N:
        g = t.count('<div class="gate">')
        if g != 1: errs.append(f"要有且只有一处 <div class=\"gate\">（先停下，去读原书），现在 {g} 处")
        elif not (t.find("<h2>词与短语</h2>") < t.find('<div class="gate">') < t.find("<h2>读完：回到你的预测</h2>")):
            errs.append("<div class=\"gate\"> 要放在「词与短语」之后、「读完：回到你的预测」之前")

    # 引用块：不超过 2 处，只引作者的正文
    errs += check_quotes(t, 2)
    for q in re.findall(r'<blockquote class="quote">(.*?)<cite>', t, flags=re.S):
        s = norm(re.sub(r"<[^>]+>", "", q)).strip("… ").strip()
        where = [p for p, v in paras.items() if s.replace("…", "") and all(x.strip() in v for x in s.split("…") if x.strip())]
        if not where: errs.append(f"引用块在原文里找不到（要一字不差，省略处用 …；引用别的章的话不行）：{s[:50]!r}")
        elif all(marks.get(p) in ("{C}", "{F}", "{T}", "{E}") for p in where): errs.append(f"引用块引的是题词、代码、图注或表格，只引作者的正文：{s[:50]!r}")
        if len(s.replace("…", " ").split()) > 25: errs.append(f"引用块超过 25 个词：{s[:50]!r}")

    # 判断题
    if N:
        jd = part("判断题：换成你来选")
        mcqs = re.findall(r'<div class="mcq" data-answer="(\d)">(.*?)<div class="explain">', jd, flags=re.S)
        if not 3 <= len(mcqs) <= 5: errs.append(f"「判断题」要有 3–5 道 <div class=\"mcq\" data-answer>，现在 {len(mcqs)} 道")
        if '<p class="quiz-score"></p>' not in jd: errs.append("「判断题」要有 <p class=\"quiz-score\"></p>")
        for a, body in mcqs:
            nb = body.count("<button>")
            if not 3 <= nb <= 4: errs.append(f"判断题的选项要 3–4 个，现在 {nb} 个")
            if int(a) >= nb: errs.append(f"判断题 data-answer={a} 超出了选项个数 {nb}")
            if '<p class="ctx">' not in body: errs.append("判断题要有 <p class=\"ctx\">场景：……</p>")
        if len(mcqs) >= 3 and len({a for a, _ in mcqs}) < 2: errs.append("判断题的正确答案位置要分散")

    # 精彩回顾
    if N:
        rc = part("精彩回顾")
        if '<p class="recall-line">' not in rc: errs.append("「精彩回顾」要有 <p class=\"recall-line\"><b>一句话：</b>…</p>")
        items_r = re.findall(r'<div class="item"><b>(.*?)</b><p>(.*?)</p><span class="sec">(§[^<]+)</span></div>', rc, flags=re.S)
        if not 5 <= len(items_r) <= 8 or len(items_r) != rc.count('<div class="item">'): errs.append(f"「精彩回顾」应有 5–8 张卡片，写法 <div class=\"item\"><b>标题</b><p>…</p><span class=\"sec\">§k</span></div>，现在认出 {len(items_r)} 张")
        for b_, p_, _ in items_r:
            if han(p_) > 100: errs.append(f"「精彩回顾」{b_}：{han(p_)} 个汉字，超过 100")
    else: items_r = []

    # 链接：术语页、本站其他书
    for gid in re.findall(r'href="\.\./glossary\.html#(g-[^"]+)"', t):
        if gid not in gloss_ids: errs.append(f"术语页里没有 #{gid}")
    for site, u in re.findall(r'href="/([a-z]+)/((?:chapters|topics|train)/[^"#]+)', t):
        d = SISTERS.get(site)
        if not d or not os.path.exists(os.path.join(os.path.expanduser(d), u)): errs.append(f"本站其他书的链接不对：/{site}/{u}")
    # 不写译本的译法（本站没有译本的文本）
    if re.search(r"译本(译作|译成|译为|作「)", re.sub(r"<[^>]+>", "", t)): errs.append("不写「译本译作……」：本站没有译本的文本，中文都是本站自己的译法")

    for src in sorted({x for x in re.findall(r'<img[^>]+src="([^"]+)"', t) if t.count(f'src="{x}"') > 1}): errs.append(f"同一张图出现了不止一次：{src}")
    if N: errs += check_images(t, path, min_photos=1, min_svgs=3)
    c = counts(t)
    if N and not 6 <= c["检查题"] <= 8: errs.append(f"理解检查应有 6–8 题，现在 {c['检查题']} 题")
    bare = t
    for x in scripts + styles: bare = bare.replace(x, "")
    errs += check_markup(bare, r"\.epub|\.pdf|ch\d\d\.html|OEBPS|source/")
    print(("✗" if errs else "✓"), path, " ".join(f"{k} {v}" for k, v in c.items()), f"地图 {len(items)} 坐下 {len(chunks)} 模拟器 {nsim} 回顾 {len(items_r)} 原文 {total} 词")
    for e in errs: print("    " + e)
    bad += bool(errs)
sys.exit(1 if bad else 0)
