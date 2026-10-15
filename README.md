# DDIA 第二版 · 导读

陪读 *Designing Data-Intensive Applications*, 2nd Edition（Martin Kleppmann、Chris Riccomini，O'Reilly，2026）的静态站，一章一页。
读者以英文原书（电子书和纸书）为主，读不顺时按章号翻中国电力出版社的第二版译本（纸书）。本站没有译本的文本，中文都是自己译的。
线上地址 https://t.miaowuao.cn/ddia/ ，仓库 shakespark/ddia-illustrated。推送到 main 就由 GitHub Actions 部署。

## 目录

| 路径 | 作用 |
|---|---|
| `index.html` | 首页：这本书、英文和译本怎么配合、全书地图、目录、我的词本 |
| `chapters/NN.html` | `00` 开读之前（序言和全书地图），`01`–`14` 是原书各章。样板是 `04.html` |
| `glossary.html` | 全书术语（英文、本站的中文、本站写的解释），章节页链过来，主编维护 |
| `recap.html` | 全书回顾：`dd.js` 读各个已完成章节页的「精彩回顾」汇总 |
| `assets/chapters.js` | 目录数据（原书章名、本站中文章名、分块、主题、一句话、模拟器）和已完成的章 |
| `assets/sections.js` | 各节的原书小标题、层级、词数。由 `tools/extract.py` 生成，不要手改 |
| `assets/dd.js`、`assets/style.css` | 共享脚本和样式。骨架来自 Free to Choose 导读，模拟器和选择题来自 APOSD 精读站 |
| `AUTHORING.md` | 章节页编写规范（公共部分见 `~/tutorials-deploy/AUTHORING-COMMON.md`） |
| `tools/` | `extract.py` 提取文本；`lint.py` 本站的结构检查；`overlap.py`、`check.mjs`、`fetch_img.py` 转调 `~/tutorials-deploy/scripts/` 里的共用版 |
| `source/` | 原书 epub、提取的文本、截图、作者任务说明。**不入库、不部署** |

十章有模拟器（第 2、4、5、6、7、8、9、10、11、12 章），脚本写在各自页面末尾，只用浏览器、不联网。

localStorage 键都带 `dd-` 前缀：`dd-done-N`（N 是 0–14）、`dd-sec-N-节号`、`dd-star-NN-词条`、`dd-note-…`、`dd-bet-…`、`dd-theme`。

## 重新提取文本

```sh
mkdir -p source/epub && cd source/epub && unzip -o ../ebook/*.epub && cd ../..
python3 -I tools/extract.py      # 读 source/epub/OEBPS/，写 source/text/00.txt … 14.txt、refs/、glossary.txt 和 assets/sections.js
```

节号是本站编的：§0 开篇，§a 一级小标题，§a.b 二级小标题。改了提取规则，所有章节页的分节地图都要跟着对一遍（`tools/lint.py` 会查）。
