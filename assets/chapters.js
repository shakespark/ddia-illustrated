// 全书目录。n: 章号（0 是「开读之前」：Preface 和全书地图）；en: 原书章名；t: 本站给的中文章名（自己译的，不是译本的）；
// part: 本站给全书分的块（原书第二版不分部分）；topic: 一个词的主题；d: 一句话（本站写的，主编从作者报告里收）；
// sim: 这一章的模拟器（没有就不写）。词数和各节在 sections.js（tools/extract.py 生成）。
window.DD_PARTS = [
  { k: 1, t: "地基：取舍与需求", ch: [1, 2], d: "这本书看问题的方法：没有最好的方案，只有取舍；先说清楚要什么（性能、可靠、可扩展、好维护）。" },
  { k: 2, t: "一台机器上的数据", ch: [3, 4, 5], d: "数据长什么样（模型和查询语言）、怎么存到盘上再找回来（存储引擎）、怎么在程序之间传（编码和演化）。" },
  { k: 3, t: "分布到多台机器", ch: [6, 7, 8, 9, 10], d: "复制、分片、事务，然后直面网络、时钟和进程停顿这些麻烦，最后用一致性和共识把它们收住。" },
  { k: 4, t: "派生数据", ch: [11, 12, 13], d: "批处理和流处理把一份数据变成很多份：索引、缓存、分析表；作者主张整个系统都可以围绕数据流来设计。" },
  { k: 5, t: "做正确的事", ch: [14], d: "数据系统对人的影响：偏见、监控、隐私和同意。" },
];
window.DD_CHAPTERS = [
  { n: 0, en: "Preface", t: "开读之前", part: 0, topic: "全书地图", d: "这本书讲什么、第二版新在哪、怎么配合译本读" },
  { n: 1, en: "Trade-Offs in Data Systems Architecture", t: "数据系统架构里的取舍", part: 1, topic: "取舍", d: "分不分开、上不上云、要不要分布式，都是取舍" },
  { n: 2, en: "Defining Nonfunctional Requirements", t: "定义非功能需求", part: 1, topic: "需求", d: "快、稳、能扩、好改，先说成能测的数字", sim: "扇出与尾延迟" },
  { n: 3, en: "Data Models and Query Languages", t: "数据模型与查询语言", part: 2, topic: "数据模型", d: "表、文档、图、事件日志：按数据关系的形状选模型" },
  { n: 4, en: "Storage and Retrieval", t: "存储与检索", part: 2, topic: "存储引擎", d: "存储引擎在写得快和找得快之间怎么选位置", sim: "LSM 树：写入、刷盘与合并" },
  { n: 5, en: "Encoding and Evolution", t: "编码与演化", part: 2, topic: "编码", d: "新旧代码并存时，数据怎样两个方向都读得通", sim: "模式演化：新旧代码能不能互读" },
  { n: 6, en: "Replication", t: "复制", part: 3, topic: "复制", d: "三种复制方式：谁能收写，延迟和冲突落在哪里", sim: "复制延迟：读到旧数据" },
  { n: 7, en: "Sharding", t: "分片", part: 3, topic: "分片", d: "数据怎么分到多台机器，加机器时怎么少搬", sim: "加一台机器要搬多少数据" },
  { n: 8, en: "Transactions", t: "事务", part: 3, topic: "事务", d: "隔离级别挡住哪些竞争，两阶段提交卡在哪", sim: "两个事务交错执行" },
  { n: 9, en: "The Trouble with Distributed Systems", t: "分布式系统的麻烦", part: 3, topic: "故障", d: "网络、时钟、进程都靠不住时，节点还能确知什么", sim: "租约、进程停顿与防护令牌" },
  { n: 10, en: "Consistency and Consensus", t: "一致性与共识", part: 3, topic: "共识", d: "让多份副本像一份：线性一致、逻辑时钟与共识", sim: "逻辑时钟" },
  { n: 11, en: "Batch Processing", t: "批处理", part: 4, topic: "批处理", d: "只读输入、从头算出输出，靠洗牌把同一个键凑到一起", sim: "洗牌：按键分组与数据倾斜" },
  { n: 12, en: "Stream Processing", t: "流处理", part: 4, topic: "流处理", d: "消息、日志、数据库变更和窗口：处理永不结束的数据", sim: "事件时间、窗口与迟到的事件" },
  { n: 13, en: "A Philosophy of Streaming Systems", t: "流式系统的哲学", part: 4, topic: "数据流架构", d: "只写一处其余派生，端到端守住完整性" },
  { n: 14, en: "Doing the Right Thing", t: "做正确的事", part: 5, topic: "伦理", d: "数据对人的影响：偏见、监控、同意与隐私" },
];
// 已经写好的章节（主编统一维护）
window.DD_READY = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14];
