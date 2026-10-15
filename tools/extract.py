#!/usr/bin/env python3
"""从本机的 epub 解压目录（source/epub/OEBPS/）提取文本到 source/text/NN.txt，并生成 assets/sections.js。
  00.txt  Preface（序言），各 sect1 小标题是一节
  01–14   十四章
节号：原书没有给小节编号，本站按出现顺序编：
  §0      （开篇）：章名之后、第一个一级小标题之前
  §a      一级小标题（原书 sect1，epub 里是 h1）
  §a.b    二级小标题（原书 sect2，h2）
  ### 标题   三级小标题（sect3，h3），不算一节
  #### 标题  方框和提示的标题（sidebar 的 h5、note 的 h6）
每行一段，行首 [段号]（每个文件内连续编号）。段落标记：
  {C} 代码或查询（一行一段，原书的换行写成 ⏎）  {F} 图（只留图注）  {T} 表格的一行（格子用 | 隔开）
  {S} 方框（sidebar）或提示（note）里的话       {E} 章首题词（别人的话）
  {D} 术语列表里的词（dt），后面一段是它的解释（dd）
*词* 是原书的斜体。文献号已去掉，文献表另存 source/text/refs/NN.txt（核对事实用）。
原书词汇表另存 source/text/glossary.txt（只给作者参考，本站的术语页是自己写的，不能翻译它）。"""
import html, json, os, re
from html.parser import HTMLParser

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
EP = os.path.join(ROOT, "source/epub/OEBPS")
OUT = os.path.join(ROOT, "source/text")
BLOCK = {"p", "li", "dt", "dd", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "figcaption", "tr", "blockquote", "div", "section", "aside", "figure", "table", "ul", "ol", "dl"}


class Walker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # (tag, attrs dict)
        self.buf = []
        self.out = []            # (kind, text, marks)
        self.skip = 0            # 在不要的元素里（文献号）
        self.refs = []           # 文献表
        self.in_refs = 0
        self.cells = None

    def ctx(self, key, val=None):
        for t, a in self.stack:
            if val is None and a.get(key) is not None: return True
            if val is not None and a.get(key) == val: return True
        return False

    def flush(self, kind="p"):
        s = re.sub(r"\s+", " ", "".join(self.buf)).strip() if kind != "pre" else "".join(self.buf)
        self.buf = []
        if not s.strip(): return
        if self.in_refs:
            self.refs.append(s); return
        if kind == "pre":
            s = " ⏎ ".join(x.rstrip() for x in s.strip("\n").split("\n"))
        s = s.replace("**", "").replace("* *", " ")
        s = re.sub(r"\s*\[[\s,–-]*\]", "", s)                 # 去掉文献号留下的空方括号
        if kind.startswith("h") and any(t == "figure" for t, _ in self.stack): kind = "fig"   # 图注是图里的 h6
        box = any(a.get("data-type") in ("sidebar", "note", "warning", "tip") for _, a in self.stack)
        epi = any(a.get("data-type") == "epigraph" for _, a in self.stack)
        self.out.append((kind, s, "S" if box else "E" if epi else ""))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("br",):
            self.buf.append(" "); return
        if tag == "img":
            return
        if self.skip:
            self.stack.append((tag, a)); self.skip += 1; return
        if tag == "a" and a.get("data-type") == "noteref":
            self.stack.append((tag, a)); self.skip = 1; return
        if tag == "div" and a.get("data-type") == "footnotes":
            self.flush(); self.in_refs += 1; self.stack.append((tag, a)); return
        if tag in ("td", "th"):
            if self.cells is not None: self.cells.append(""); self.buf = []
            self.stack.append((tag, a)); return
        if tag in BLOCK:
            self.flush(self.cur_kind())
        if tag == "tr": self.cells = []
        if tag in ("em", "i") and not self.ctx("data-type", "programlisting"): self.buf.append("*")
        if tag == "sup": self.buf.append("^")                                   # 上标：2^32
        self.stack.append((tag, a))

    def handle_endtag(self, tag):
        if tag in ("br", "img"): return
        if not self.stack: return
        t, a = self.stack.pop()
        if self.skip:
            self.skip -= 1; return
        if t == "div" and a.get("data-type") == "footnotes":
            self.flush(); self.in_refs -= 1; return
        if t in ("td", "th"):
            if self.cells is not None: self.cells[-1] = re.sub(r"\s+", " ", "".join(self.buf)).strip(); self.buf = []
            return
        if t == "tr":
            row = " | ".join(self.cells or []); self.cells = None; self.buf = []
            if row.strip(" |"): self.out.append(("tr", row, ""))
            return
        if t in ("em", "i") and not self.ctx("data-type", "programlisting"): self.buf.append("*")
        if t in BLOCK:
            self.flush(self.kind_of(t, a))

    def handle_data(self, d):
        if self.skip: return
        self.buf.append(d)

    def cur_kind(self):
        # 块开始前残留的文字（比如 li 里在 p 之前的字）归到最近的块
        for t, a in reversed(self.stack):
            if t in BLOCK: return self.kind_of(t, a)
        return "p"

    def kind_of(self, t, a):
        if t == "pre": return "pre"
        if t in ("h1", "h2", "h3", "h4", "h5", "h6"): return t
        if t == "figcaption": return "fig"
        if t == "dt": return "dt"
        return "p"


def walk(name):
    """返回 ([(kind, text, 容器)], 文献表)。容器：S 方框或提示，E 题词，空串是正文。"""
    t = open(os.path.join(EP, name), encoding="utf-8").read()
    t = t[t.find("<body"):]
    t = re.sub(r'<a data-type="indexterm"[^>]*>\s*</a>', "", t)
    w = Walker(); w.feed(t); w.flush()
    return w.out, w.refs


def build(files, out, title, is_preface=False):
    lines, k = [], 0
    secs = []                       # [k, 标题, 词数, 层级]
    a = b = 0
    for f in files:
        items, refs = walk(f)
        for kind, s, box in items:
            if kind == "h1" and not secs and s.startswith("Chapter "):  # 章名
                continue
            if kind == "h1" and not box:
                a += 1; b = 0
                secs.append([str(a), s, 0, 1]); lines.append(f"## §{a} {s}")
            elif kind == "h2" and not box:
                b += 1
                secs.append([f"{a}.{b}", s, 0, 2]); lines.append(f"## §{a}.{b} {s}")
            elif kind == "h3" and not box:
                lines.append(f"### {s}")
            elif kind in ("h1", "h2", "h3", "h4", "h5", "h6"):
                if s not in ("Note", "Tip", "Warning", "Footnotes", "References"): lines.append(f"#### {s}")
            else:
                if not secs: secs.append(["0", "（开篇）", 0, 1]); lines.append("## §0 （开篇）")
                mark = {"pre": "{C} ", "fig": "{F} ", "tr": "{T} ", "dt": "{D} "}.get(kind, "")
                if not mark and box: mark = "{%s} " % box
                k += 1; lines.append(f"[{k}] {mark}{s}")
                if mark not in ("{C} ", "{F} ", "{T} ", "{E} "): secs[-1][2] += len(s.split())
        if refs:
            os.makedirs(os.path.join(OUT, "refs"), exist_ok=True)
            open(os.path.join(OUT, "refs", out), "w", encoding="utf-8").write("\n".join(refs) + "\n")
    open(os.path.join(OUT, out), "w", encoding="utf-8").write(f"# {title}\n\n" + "\n".join(lines) + "\n")
    total = sum(x[2] for x in secs)
    print(f"{out}  {len(secs):2d} 节 {k:4d} 段 {total:6d} 词")
    return secs


os.makedirs(OUT, exist_ok=True)
TITLES = {}
for n in range(1, 15):
    t = open(os.path.join(EP, f"ch{n:02d}.html"), encoding="utf-8").read()
    m = re.search(r'<h1><span class="label">Chapter \d+\. </span>(.*?)</h1>', t, flags=re.S)
    TITLES[n] = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
meta = {}
meta[0] = build(["preface01.html"], "00.txt", "0 Preface", is_preface=True)
for n in range(1, 15):
    meta[n] = build([f"ch{n:02d}.html"], f"{n:02d}.txt", f"{n} {TITLES[n]}")

# 原书词汇表（参考用）
items, _ = walk("glossary01.html")
with open(os.path.join(OUT, "glossary.txt"), "w", encoding="utf-8") as f:
    for kind, s, _ in items:
        if s: f.write(("## " if kind == "dt" else "") + s + "\n")

with open(os.path.join(ROOT, "assets/sections.js"), "w", encoding="utf-8") as f:
    f.write("// 由 tools/extract.py 生成，不要手改。en: 原书章名。每章各节：k 节号（0 是开篇，a 是一级小标题，a.b 是二级小标题），\n"
            "// t 原书小标题（照抄），w 这一节自己的正文词数（不含代码、图注、表格；一级小标题的 w 只算它下面第一个二级小标题之前的部分），lv 层级。\n")
    data = {n: {"en": TITLES.get(n, "Preface"), "words": sum(s[2] for s in secs), "secs": [{"k": s[0], "t": s[1], "w": s[2], "lv": s[3]} for s in secs]} for n, secs in meta.items()}
    f.write("window.DD_SECS = " + json.dumps(data, ensure_ascii=False).replace('}, {', '},\n  {').replace('], "', '],\n "') + ";\n")
