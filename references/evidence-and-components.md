# 证据与组件：事实从仓库来，画面从真组件来

## 1. 功能证据 `evidence/feature-evidence.md`

先读仓库规则与目录索引，再定向查 release notes、CHANGELOG、版本标签、实现路径。不要全量导出 git log 或读取 `.env`。

用户说"最近几周"：以**今天日期**划范围，再对应到版本记录；范围未定时可建议最近 2–4 周，标明"拟定"。

每条功能一行：

| 字段 | 含义 |
|---|---|
| feature / benefit | 实现了什么 / 用户得到什么 |
| status / release | 已发布 / 已合并 / 开发中；版本号 |
| source | `repo:src/x.tsx#L40` + 提交或标签，或用户文档 |
| component | 可复用的真实业务组件与样式入口 |
| demoState | 演示需要的输入、状态、fixture |
| limits | 无法证明的部分、演示范围 |

`plan.json` 里 `claim: true` 的镜头必须有 `source`。开发中的功能不作为"已上线"宣传。

## 2. 风格审计 `evidence/style-audit.md`

沿功能页面找到实际业务组件，再追它用的 tokens / CSS 变量 / Tailwind 配置、字体、图标、主题上下文。写出：

1. 色板语义（背景、表面、正文、弱文本、描边、强调色）+ 代码来源
2. 字体：英文标题、中文标题/正文的字体、字重、行距，以及**实际加载结果**
3. 间距、圆角、阴影、线宽、密度
4. 品牌：完整 app icon（带底板）、横向 logo、单色版本；只用仓库已有资产
5. 镜头适配：哪些细节可直接放大，哪些要裁切或拆分；有没有暗色主题
6. 母题候选（交给 [影片方向](direction.md)）
7. 决策：repo / default / hybrid + 理由 + 保留的品牌识别点

"审美不好"要转成可操作判断：层级乱、字号间距不一致、对比不足、密度过高、描边阴影杂乱。不要背着用户换掉品牌。

## 3. 把真组件接进视频

**顺序**（前一步走不通才走下一步）：

1. 直接导入实际业务组件或组合组件，加载完整样式链。已有 Storybook / demo route / preview harness 可作挂载入口。
2. 补最小 provider/context（i18n、tooltip、主题、面板状态）；报错 `must be used within ...` 就是缺哪个。数据请求按路径返回 fixture，fixture 从产品自身常量派生（名字和图标就是真的）。固定时钟与随机种子。
3. 仍跑不起来：复用纯展示子组件，保留原组合结构和样式；必要的源码提取最小化并注明来源。
4. 平台边界导致无法运行（原生 SwiftUI/GPUI、Electron IPC）：写明阻碍、已试方法、受影响镜头，征得同意后用受控录屏或**忠实重建**（尺寸取自源码、颜色取自主题文件、字体图标用仓库原文件、会变的东西写成时间的纯函数），并在证据中标注"重建"。

"依赖多、不好做动画、省时间"不是静默手绘复刻的理由。

### 在渲染工程里挂载真实产品（`assets/starter` + `src/film/product-frame.js`）

- **每个镜头一个同源 iframe**（`productFrame()`）：产品在 iframe 里以真实窗口尺寸运行。弹层（portal、`position: fixed`、菜单、选区浮层）、`getBoundingClientRect`、文本选区都和视口自洽；摄像机只变换 iframe。这比把 portal 改挂载点更通用。
- **`director({ setup, steps, track })`**：`setup` 在每次启动后把产品带到镜头起始状态；`steps` 是按镜头内时间执行的真实操作（点击、选择、切换）；`track(local)` 处理随时间连续变化的状态（选区一个字一个字扩大、滑块移动）。倒退 seek 时自动重启重放，前进时只执行新步骤——渲染永远是时间的函数。
- **`rehearse()`**：先把全部步骤跑一遍记录真实坐标（`mark()`），再复位；摄像机推拉、光标路径、飞行层都以这些实测坐标为目标，不手算。
- 组件打包：esbuild 把产品源码打进视频工程（`film.config.json` 的 `alias`、`nodePaths`、`loader`、`entries`）。展示依赖装在视频工程，不动产品仓库。
- 冻结组件内部 CSS transition/animation（与主时钟争夺状态）；要保留的动态按时间重建。
- 墙钟定时器（防抖弹层、自动消失的通知）不等于影片时间：用显式步骤控制它们出现和消失。
- 等图片解码再截帧；`idle()` 只等视口内的图片（懒加载图片永远不会加载）。
- 真实数据：`FILM_RECORD=1 node tools/lab.mjs --record` 经 `/__proxy` 录下真实请求，之后只读 fixture。

Vue / Svelte / 原生 DOM（如 Obsidian 插件）同理：先写宿主 shim，再用 iframe + director。见 [产品适配](adapters.md)。

## 4. 组件复用证据 `evidence/component-usage.json`

每个功能镜头一条：`shotId, featureEntry, components[], styleEntries[], stateDriver, adapters[], reuseMode (original|subcomponent|rebuild|recording), exceptions`。路径指向真正使用的源码。

核对：用的是业务组件还是只有通用按钮？样式来自组件实际样式链还是几项颜色常量？状态是原组件呈现的吗？构建图有导入 ≠ 真上镜；静帧相似 ≠ 复用了源码，两份证据结合看。未用原组件的部分明确标注，不笼统说"全部原生组件"。

## 5. 隐私与链接

- 不把用户仓库里的真实对话、账号、密钥、浏览历史、商业数据放进 fixture；fixture 表达真实功能，但不冒充真实业绩或客户成果。
- 按用户的发布要求处理链接。不要求出现时：清空 fixture 里的 URL、地址栏中性化、去掉片尾链接；必须遮罩时遮罩随组件一起移动缩放。所有镜头、封面、导出帧一并检查。
