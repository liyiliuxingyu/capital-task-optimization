# 资金任务论文：完整工程归档

[阅读论文 PDF](九笔整百付款_多角度严谨分析.pdf) · [查看 LaTeX 源码](九笔整百付款_多角度严谨分析.tex) · [新对话接续提示词](新对话接续提示词.txt) · [归档清单](UPLOAD_MANIFEST.json) · [Releases：完整 ZIP 下载入口](https://github.com/liyiliuxingyu/capital-task-optimization/releases)

本仓库以 **7 个归档分片**保存完整续作工程。七片合起来是同一个 ZIP，解包后得到 `project/`，其中包含 **4,427 个正式文件（含 SHA-256 清单）**：完整论文、源码、数学核验程序、接续状态、内容索引、TeX 宏包、字体及其许可材料。仓库根目录另提供 PDF 与 TeX，方便直接阅读。

## 下载与恢复

先克隆仓库，或使用 GitHub 的“Code → Download ZIP”下载并解压。私有仓库需要相应访问权限。确保下列文件都在同一目录：`restore_project.py`、`UPLOAD_MANIFEST.json`、`capital-project-20261124.part01` 至 `.part07`。

```sh
git clone https://github.com/liyiliuxingyu/capital-task-optimization.git
cd capital-task-optimization
python3 restore_project.py --check
python3 restore_project.py
cd project
python3 run.py verify
python3 run.py build
```

`restore_project.py` 只使用 Python 3.9 或更新版本的标准库。它核对每片的大小和 SHA-256、拼接后的完整 ZIP，再安全解包并逐文件核对工程内的 `MANIFEST.sha256.json`。默认目标是脚本所在目录下的 `project/`；已有非空目录会被拒绝覆盖。`--check` 只核对七片和完整 ZIP，不解包；`--output-dir /path/to/project` 可以指定不存在或为空的目标目录。

恢复脚本不联网、不访问认证文件、不修改 GitHub，也不自动运行工程中的程序。恢复后由你执行 `python3 run.py verify`，核对清单、源码结构、两段原附录程序与独立数学枚举。

`python3 run.py build` 使用包内宏包和字体重建论文，仍需要系统已安装 XeTeX/XeLaTeX、xdvipdfmx 和 kpsewhich。结果写入 `project/build/`。解包后请阅读 `project/docs/编译环境.md` 和 `project/docs/验证记录.md`。Windows 可将 `python3` 替换为 `py -3`。

如 Releases 已提供完整 `capital-project-20261124.zip` 附件，也可以下载该 ZIP 并解压，再进入其中的 `project/` 执行相同核验与编译命令。完整 ZIP 的大小为 **50,433,573 字节**，SHA-256 为：

```text
1887078a1260d7e8e5e82016fef8122eb03817065e894f95f2618cda312b6d66
```

## 兼容原工程的根目录入口

也可以直接在仓库根目录运行：

```sh
python3 run.py status
python3 run.py verify
python3 run.py build
```

根目录 `run.py` 是普通的本地包装入口。你首次显式运行它时，如果 `project/` 尚不存在或为空，它先调用同目录 `restore_project.py` 校验并恢复工程，再将你提供的参数按列表传给 `project/run.py`；已有非空工程不会被重新解包覆盖。参数转交不使用 shell 字符串拼接。后续执行直接进入已恢复的工程，原归档 README 中的根目录命令因此仍然可用。

两种使用方式都在你的机器上由你显式启动：可以先手动恢复再进入 `project/`，也可以使用此根目录入口。恢复脚本本身只解包与校验；包装入口仅在你运行它时继续执行所请求的 `status`、`verify`、`build` 等工程命令。它不联网、不访问认证文件、不修改 GitHub。

## 接续工程的位置

| 解包后路径 | 内容 |
| --- | --- |
| `project/README.md` | 原工程说明与运行入口 |
| `project/AGENTS.md` | 固定模型、版式和真实性要求 |
| `project/state/接续状态.json` | 已完成事项、核验范围与待办 |
| `project/docs/内容索引.md` | 章节、标签、物理页和印刷页定位 |
| `project/pdf/九笔整百付款_多角度严谨分析.pdf` | 61 页完整论文 |
| `project/src/九笔整百付款_多角度严谨分析.tex` | 完整 ctexbook 源码，含 51 个证明环境和 9 幅 TikZ 图 |
| `project/scripts/` | 核验、编译及打包程序 |
| `project/vendor/` | TeX 宏包、字体、锁定记录与许可 |

新对话先读取根目录的接续提示词，再读取恢复工程中的规则、状态和内容索引。完整工程使用标准文件保存接续资料；聊天额度、账号权限和模型选择由使用平台决定。

## 数学结论与待办

当前目标依次为“先笔数最少，再本金最少”。主结论是 **9 笔、初始本金 41,100 元、两次柜台全额回收**。第一轮付款 `9900、9800、9700、9600`，合计 39,000 元；回收后第二轮付款 `9500、9400、9300、9200、3700`，合计 41,100 元。有效累计 80,100 元，最后一次回收已计入两次柜台。

论文 PDF 与 TeX 保留恢复版原始字节。历史“文献 1”要求仍为 **OPEN**：第五章开头仍有 `\cite{boyd}`，书末仍有 `\bibitem{boyd}`，后续需按接续状态处理。当前工程没有 Lean 文件，也没有全部定理的证明助手形式化验证。

本次归档恢复流程的本地解包、逐文件清单、原附录程序和独立数学核验均已执行。仓库采用普通文件存储与用户本地运行的恢复方式。
