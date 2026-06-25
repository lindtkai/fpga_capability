================================================================
  FPGA Toolbox — 离线部署说明
================================================================

【项目简介】
  Verilog/VHDL 例化模板生成工具，支持 GUI 和命令行两种模式。
  完整便携环境: Python 3.13.12 + tkinter + paramiko + pillow + pyserial.
  目标机器无需装 Python，也无需联网。

【目录结构】
  tool/
  ├── run.bat              ← Windows 一键启动
  ├── setup_offline.bat    ← Windows 离线部署向导
  ├── run.sh               ← Linux 一键启动
  ├── setup_offline.sh     ← Linux 离线部署向导
  ├── src/                 ← 源代码
  │   ├── gen_inst.py      ← 主程序（解析/生成/CLI/GUI 入口）
  │   └── gen_gui.py       ← GUI 界面代码 (tkinter)
  ├── scripts/             ← 辅助/部署脚本
  │   ├── build_portable_runtime.py  ← 跨平台 build 入口 (核心)
  │   └── make_portable.sh           ← Linux 包装, 调上面的 Python 脚本
  ├── assets/              ← 静态资源 (qci_flow.png 等)
  ├── docs/                ← 文档
  ├── ip_docs/             ← IP PDF 文档（用户自己放入）
  ├── iperf3_bin/          ← iperf3 多版本 (Windows)
  ├── _pyserial_lib/       ← 离线 Python 依赖包 (paramiko, pyserial 等)
  └── runtime/             ← 便携 Python 环境 (构建后 ~130 MB)


================================================================
  Windows 部署（2 步）
================================================================

【前提】你需要在有 Python 3.10+ 的电脑上做第 1 步，然后通过 U盘/共享文件夹
        把 runtime\ 文件夹复制到目标内网电脑的 tool\ 目录下。

-- 第 1 步：在有 Python 3.10+ 的电脑上生成 runtime\ --

  把整个 tool\ 目录 (含 src\, scripts\, assets\ 等) 复制到有 Python 的电脑
  双击 setup_offline.bat
  脚本会自动:
    1. 复制 Python 解释器 + tkinter + 标准库到 runtime\
    2. 用 pip 安装 paramiko / pillow / pyserial 到 runtime\Lib\site-packages\
    3. 验证所有依赖可加载
  生成 runtime\ 目录 (~130 MB)

-- 第 2 步：传输到目标机器 --

  把整个 tool\ 目录 (含 runtime\) 复制到目标电脑
  双击 run.bat 启动 FPGA Toolbox!

================================================================
  Linux 部署（2 步）
================================================================

【前提】在有 Python 3.10+ + tkinter 的 Linux 机器上做第 1 步，
        然后把整个 tool/ 目录复制到目标 Linux。

-- 第 1 步：在有 Python 3.10+ + tkinter 的 Linux 上生成 runtime\ --

  cd tool/
  ./setup_offline.sh
  脚本会自动:
    1. 复制 Python 解释器 + tkinter + 标准库到 runtime/
    2. 用 pip 安装 paramiko / pillow / pyserial 到 runtime/Lib/site-packages/
    3. 验证所有依赖可加载

-- 第 2 步：传输到目标 Linux --

  把整个 tool/ 目录 (含 runtime/) 复制到目标机器:
    scp -r tool/ user@target:/path/to/
    或 U盘/共享文件夹

  cd /path/to/tool/
  chmod +x run.sh setup_offline.sh scripts/*.sh
  ./run.sh


================================================================
  备选: 完全离线 (内网/无网环境, 没有 pip)
================================================================

  在有网络的电脑上提前下载所有依赖 wheel:
    pip download paramiko pillow pyserial -d pkgs/

  然后把 pkgs/ 目录和 tool/ 目录一起传过去.
  在 build 脚本运行时, 用 --find-links 让 pip 用本地 wheel:
    pip install --target runtime/Lib/site-packages \
                --no-index --find-links=pkgs/ \
                paramiko pillow pyserial

  (如果通过本仓库 build 脚本自动构建, 已经用了 --target 参数,
   网络失败时会回退到国内镜像站 tsinghua)


================================================================
  启动方式
================================================================

  Windows:
    双击 run.bat
    或命令行: run.bat foo.v -n 3

  Linux:
    ./run.sh
    或: ./run.sh foo.v -n 3


================================================================
  故障排查
================================================================

  Q: 提示 "python not found"
  A: runtime\ 缺少 python.exe，请按上面的步骤生成。

  Q: 提示 "No module named tkinter"
  A: 系统的 Python 在装的时候没有勾选 "tcl/tk and IDLE"，
     重装 Python 3.13 时勾上即可。

  Q: 提示 "No module named paramiko" / "No module named PIL"
  A: runtime\Lib\site-packages\ 目录里的库没装上.
     删除整个 runtime\ 重新跑 build_portable_runtime.py.

  Q: 双击 run.bat 后窗口一闪而过
  A: 打开 cmd, cd 到 tool\, 然后手动运行 run.bat 看错误信息.

  Q: 我在内网，U盘都被禁了怎么办?
  A: 可以:
     1. 把 build 好的 runtime/ 通过内网文件服务器传输
     2. 或者在同网段一台有 Python 的机器上 build, 通过共享文件夹
     3. 或者把文件刻录到光盘 / 通过安全审批传入
