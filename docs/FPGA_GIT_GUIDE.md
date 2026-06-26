# 使用GitLab管理逻辑代码及产品主线版本说明

- 使用GitLab管理逻辑代码及产品主线版本说明
  - 1 引言
    - 1.1 目的
    - 1.2 适用范围
  - 2 GitLab平台介绍
  - 3 逻辑版本原则
    - 3.1 逻辑工程推荐目录结构
    - 3.2 核心原则：严格过滤文件（.gitignore是关键）
    - 3.2 只跟踪必要文件
  - 4 自定义IP核管理策略
    - 4.1 核心原则：源码控制+脚本化重建
    - 4.2 推荐目录结构
    - 4.3 必须版本控制的文件
    - 4.4 关键脚本实现
    - 4.5 .gitignore配置（自定义IP部分）
    - 4.6 IP更新工作流程
    - 4.7 验证流程（关键！）
  - 5 Block Design(BD)管理
    - 5.1 关键脚本实现
    - 5.2 Block Design(BD)更新流程
  - 6 FPGA工程管理策略
    - 6.1 关键脚本实现
  - 7 FPGA工程归档策略
    - 7.1 关键脚本实现
    - 7.2 管理大型二进制文件（Bitstreams,Reports）
    - 7.3 仓库维护优化
    - 7.4 关键检查点
  - 8 总结：节省空间的本质
    - 8.1 存储空间对比
    - 8.2 常见问题解决

---

## 1 引言

### 1.1 目的

本文档旨在明确规范逻辑团队使用GitLab版本管理系统的流程、日常使用方法及归档规范。通过统一的标准，确保代码版本管理的高效性、安全性和可追溯性，提升团队协作效率和项目质量。

### 1.2 适用范围

本规范适用与逻辑团队所有员工及所有FPGA工程（包括但不限于Vivado、HDL源代码、IP核、约束文件、TCL脚本等）的版本管理。

## 2 GitLab平台介绍

和SVN对比，SVN是集中式版本控制系统，存在网络依赖性强、分支管理笨重、协同效率低等固有缺点，更适合项目版本受控管理。Git是分布式版本控制系统，配合GitLab平台，能为我们带来显著优势：

1. **分布式开发：****每位开发者都拥有完整的本地仓库历史**，支持离线提交、查看历史、创建分支。
2. **高效的分支管理：****分支创建和切换瞬间完成**，鼓励基于功能分支（Feature Branch）的开发模式，实现高效的并行开发。
3. **卓越的合并能力：****智能的合并算法极大地降低了分支合并的复杂度和冲突概率。**
4. **完整的变更集追踪：****每次提交（Commit）都是项目的一个完整快照**，易于追踪与某个功能或修复相关的所有文件修改。

### 5 强大的协作平台（GitLab）：

- **Merge Request(MR):****强制代码审查（Code Review），提升代码质量。**
- **Issue跟踪:****无缝集成任务、Bug管理与代码版本。**
- **CI/CD:****为未来自动化编译、仿真、测试提供基础。**
- **Wiki:****便捷的技术文档管理。**

---

## 3 逻辑版本原则

### 3.1 逻辑工程推荐目录结构

```
my_project
├── ip_repo/                          #IP库（只管自定义IP，xilinx官方IP给不受控）
│   ├── my_ipcore                     #my_ipcore替代自定义IP目录，详见4.1章节
│   │   ├──******                     #详见4.2章节自定义IP目录结构
│   └──version_reg                    #详见4.2章节自定义IP目录结构
├── project/                          #IP工程源代码及调用的IP存放此处（绝不放本控制！！！节省空间的关键）
│   ├── my_project.xpr
│   └──******
├── tcl/                              #重建脚本（必须版本控制）
│   ├── package_project.tcl           #工程归档脚本，将vivado工程打包成tcl重建脚本
│   ├── recreate_block_design.tcl     #Block Design重建脚本
│   └── recreate_project.tcl          #工程重建脚本
├── xdc/                              #逻辑工程约束文件（必须版本控制）
│   ├── my_project.xdc                #xdc文件的命名要和工程名保持一致，否则tcl脚本将无法识别哪个是工程约束文件
├── app/                              #应用文件（必须版本控制）
│   ├── fsbl_app.elf                  #zynq或NCB elf文件
│   └── my_project.hdf                #zynq平台PL hdf文件
└── release/                          #工程固件发布版本
    ├── my_project.bit
    ├── my_project.bin
    └── my_project.mcs
├── README.md                         #工程说明文件，如功能象、版本号、更新记录等
└── .gitignore                        #过滤文件
```

### 3.2 核心原则：严格过滤文件（.gitignore是关键）

创建一个强大的.gitignore文件，排除所有可自动生成的文件。实例模板：

```gitignore
# Vivado 自动生成的文件和目录
project/
ip_project/
*.jou
*.log
*.str
*.xpe
.cache/
.hw
.sim/
*ip_user_files/
.gen
.runs/
.srcs/
.sdk/
.tmp
*hwdef
*.xpr.lock
*xpr.ip_user_files/

#编译结果和中间文件
*.bit
*.mcs
*.prn
*.bin
*.rpt
*.dcp
*.ltx
*.hdf
*.sysdef

# IP产生的文件（IP元文件需单独管理）
*.xcix
.*/ip/*
.*/bd/*/ip/*

#检查点文件（除非必要）
*.dcp

#排除Vivado工程设置（部分关键设置需通过TCL管理）
.xpr.user
```

### 3.2 只跟踪必要文件

必须纳入版本控制的文件：

- HDL源代码（*.v, *.vhd, *.sv）
- 约束文件（*.xdc）
- TCL脚本（重建工程/IP/Block Design的脚本）
- 关键配置文件（*.xpr可选，见下方说明）
- 文档（README.md, 设计文档）

---

## 4 自定义IP核管理策略

### 4.1 核心原则：源码控制+脚本化重建

- 绝不直接跟踪自动生成的IP文件
- 只存储原始源代码和重建脚本
- 确保一键重建整个IP核

### 4.2 推荐目录结构

```
my_ipcore
├── ip_project/                      #IP Vivado工程存放处（绝不版本控制！！！ip_project文件夹不可保留）
│   ├── my_ipcore.***               #my_ipcore替代自定义IP目录
├── src/                             #IP工程源代码及调用的IP存放此处（必须版本控制）
│   ├── top.v
│   ├── user_logic.v
│   └── ip/
│       ├── cdc_fifo.xci             #调用的IP存放处，只保留xci文件（必须版本控制）
│       └── clock_gen.xci
├── sim/                             #仿真源代码存放处（必须版本控制）
│   └── tb.sv
├── xdc/                             #IP专用约束（可选）
│   └── constraints.xdc
├── doc/                             #IP供设计文档（必须版本控制，考虑后续wiki集成）
│   ├── my_ipcore_spec.doc
│   └── my_ipcore_spec.pdf
├── tcl/                             #重建脚本（必须版本控制）
│   ├── create_project.tcl
│   ├── recreate_ip_project.tcl
├── packaged_ip/                     #IP封装文件（必须版本控制）
│   ├── component.xml
│   └── xgui/
│       └── my_ipcore.tcl
├── README.md                        #IP核说明文件，如版本号、更新记录等
└── .gitignore                       #严格过滤生成文件
```

**建议：****自定义IP命名规则：命名要体现IP功能，不能带版本号，IP的版本号统一在README文件中进行迭代描述，同时，在xci文件以及xml文件中，也常带有版本号，如：version_reg，不能用version_reg_v1_0**

### 4.3 必须版本控制的文件

1. **HDL源代码：**
   - Verilog/VHDL文件（*.v, *.vhd, *.sv）
   - 参数化配置package文件
2. **IP定义文件**
   - .xci文件（Vivado IP配置的核心描述文件）
   - 新版Vivado中的.xcix文件（本质是XML，可版本化管理）
3. **重建脚本**
   - 每个IP独立的"recreate_ip.tcl"
   - 全局IP重建脚本"build_all_ips.tcl"（尚未实现，待上线......）
4. **专属约束文件（如果有）：**
   - IP专用的"xdc"约束，如IPCle、fifo等。

### 4.4 关键脚本实现

**1. 单个IP重建脚本（recreate_ip.tcl）**

本质上是重建IP core的vivado工程，打开IP工程，在vivado的Tcl Console界面输入：

```tcl
write_project_tcl -all_properties -use_bd_files {../../tcl/recreate_ip.tcl}
```

**2. 全局IP重建脚本（build_all_ips.tcl）**

暂未实现，后期上线......

### 4.5 .gitignore配置（自定义IP部分）

```gitignore
#在项目.gitignore中添加
my_ipcore/ip_project/                 #过滤所有工程文件及Vivado自动生成的文件
!my_ipcore/src/**/*.xci              #过滤调用的IP生成的非xci文件
!my_ipcore/src/**/*.xcix             #过滤调用的IP生成的非xcix文件
```

### 4.6 IP更新工作流程

当需要对IP做修改时：

1. 修改HDL源码和xci文件
2. 重新封装IP
3. 在Vivado中验证IP功能
4. 重新导出重建脚本：

```tcl
write_project_tcl -all_properties -use_bd_files {../../tcl/recreate_ip.tcl}
```

5. 测试重建脚本：
   - 进入到IP核归档目录下的ip_project子目录下；
   - 在terminal或CMD窗口中执行：

```tcl
vivado -source ../../tcl/recreate_ip.tcl
```

   - 验证是否能重建IP
6. 提交变更：HDL源码 + xci + component.xml + recreate_ip.tcl

### 4.7 验证流程（关键！）

**1. 新环境测试**

```bash
git clone <repo> --depth 1        #从gitlab拉取基线工程
cd <repo>/ip/my_ipcore/ip_project/
vivado -source ../../tcl/recreate_ip.tcl
```

**2. 检查重建工程**

打开重建后的IP工程，进行功能验证。

**3. 自动化测试（推荐，但还没实现/(ToT)/~~......）**

在gitlab CI中执行：
```bash
vivado -source ../../tcl/recreate_ip.tcl
```

---

## 5 Block Design(BD)管理

### 5.1 关键脚本实现

Vivado提供了Block Design TCL脚本生成工具，也可以通过tcl命令来生成重建脚本。步骤如下：

**- Vivado gui界面操作方法**

1. 打开Vivado工程；
2. 打开Block Design；
3. 找到顶部菜单栏，选择File->Export->Export Block Design；
4. 选择重建脚本存放路径：/tcl/recreate_block_design.tcl（注意命名）；

**- TCL命令生成重建脚本：**

1. 打开Vivado工程；
2. 打开Block Design；
3. 在vivado界面TCL Console窗口输入指令：

```tcl
write_bd_tcl -force <repo>/tcl/recreate_block_design.tcl
```

### 5.2 Block Design(BD)更新流程

当需要对BD做修改时：

1. 修改Block Design设计
2. 在Vivado中验证IP功能
3. 按照5.1的操作，重新导出重建脚本；

---

## 6 FPGA工程管理策略

### 6.1 关键脚本实现

前面铺垫了FPGA工程管理的原则，即工程重建脚本化（核心节省空间策略），实现不跟踪.xpr工程文件！用TCL脚本重建整个工程，脚本恢复逻辑工程的步骤和手动创建工程的步骤类似：

1. 打开Vivado；
2. 新建工程；
3. 新建BD；
4. 开展BD设计；
5. 生成顶层文件；
6. 添加XDC约束；
7. 综合、布局布线、生成bit文件；

基于以上我们归档的IP库和BD设计，那么重建工程的脚本就很简单，在vivado tcl console窗口输入以下指令，即可完成工程创建：

```tcl
create_project <project_name> ../project -part <FPGA project device>      #新建一个vivado工程
set_property ip_repo_paths ../../ip_repo [current_project]                 #添加ip库
update_ip_catalog                                                        #刷新IP catalog
update_compile_order -fileset sources_1                                   #刷新source文件
source ../../tcl/recreate_block_design.tcl                                #重建Block Design设计
set bdname [get_bd_designs]                                               #获取Block Design设计名称
make_wrapper -files [get_files ../../bd/$bdname/$bdname.bd] -top         #新建顶层文件
add_files -norecurse ../../tcl/bd/$bdname/hdl/${bdname}_wrapper.v         #添加顶层文件
```

将以上指令保存为`recreate_project.tcl`脚本，我们就可以实现工程的脚本化重建：

**方法一：****在/project/文件夹下打开Vivado，在TCL console窗口执行：**

```tcl
source ../../tcl/recreate_project.tcl
```

**方法二：****在linux系统的terminal或windows系统的CMD窗口中执行：**

1. `cd /project/`
2. 执行脚本

```tcl
vivado -source ../../tcl/recreate_project.tcl
```

---

## 7 FPGA工程归档策略

### 7.1 关键脚本实现

基于以上的内容，我们可以发现，Vivado工程的操作步骤几乎都可以用tcl来完成，那么能否用脚本来实现工程归档，BD脚本生成，工程脚本生成呢？答案是肯定的：

```tcl
#FPGA工程归档脚本
set tcl_obj [current_project]
set proj_name [file tail [get_property name $tcl_obj]]
set proj_dir [get_property directory $tcl_obj]
set part_name [get_property part $tcl_obj]

#设置路径
set origin_dir ".."
set tcl_obj [current_project]
#自动获取工程名称
set proj_name [file tail [get_property name $tcl_obj]]
#设置工程路径
set proj_dir [get_property directory $tcl_obj]
#自动获取FPGA型号
set part_name [get_property part $tcl_obj]

#生成block Design重建脚本
write_bd_tcl -force $origin_dir/../tcl/recreate_block_design.tcl

#生成vivado工程重建脚本
set fileId [open "recreate_project.tcl" "w"]
puts $fileId "create_project $proj_name ../project -part $part_name"
puts $fileId "set_property  ip_repo_paths  $origin_dir/../ip_repo \[current_project\]"
puts $fileId "update_ip_catalog"
puts $fileId "update_compile_order -fileset sources_1"
puts $fileId "source $origin_dir/../../tcl/recreate_block_design.tcl"
puts $fileId "set bdname \[get_bd_designs\]"
puts $fileId "make_wrapper -files \[get_files $origin_dir/../project/bd/\$bdname/\$bdname.bd\] -top"
puts $fileId "add_files -norecurse $origin_dir/../project/bd/\$bdname/hdl/\${bdname}_wrapper.v"
close $fileId
```

我们将这个脚本保存为`package_project.tcl`，在基线工程归档的时候，只需要在vivado中输入：

```tcl
source ../../tcl/pakcage_project.tcl
```

即可在tcl文件夹中自动生成`recreate_project.tcl`和`recreate_block_design.tcl`，将这些脚本提交到git中，在另一台电脑上拉取基线版本，即可通过BD重建脚本来和工程重建脚本恢复基线工程。

### 7.2 管理大型二进制文件（Bitstreams,Reports）

- **命名规则：**
  
  ".bit、.mcs、*.bin"文件命名要和工程名保持一致，如：`my_project.bit`、`my_project.bin`、`my_project.mcs`。

- **使用Git LFS(Large File Storage)：**

```bash
git lfs track "*.bit, *.mcs, *.bin"
```

  - 将大型二进制文件存储在LFS服务器，仓库只保留指针。
  - 为节省LFS空间，仅跟踪正式版本的编译结果（release版本）。

- **分离存储策略：**
  - 正式版本（release版本）Bitstreams → 用LFS + 打Tag；
  - 中间版本（debug版本）Bitstreams → 本地备份，不入库；
  - 报告文件（*.rpt）→ 仅保留关键报告（如时序报告、资源和功耗报告）。

### 7.3 仓库维护优化

- **定期清理历史（减少LFS占用）：**

```bash
git lfs prune  #删除旧版本LFS文件
git gc         #垃圾回收
```

- **浅克隆（节省下载时间）：**

```bash
git clone --depth 1 <repo_url>
```

### 7.4 关键检查点

1. 验证重建流程：在新目录中运行`vivado -source recreate_project.tcl`必须能完整重建工程。
2. 测试关键操作：综合、实现、生成Bitstream应无错误。
3. gitignore严格性：确保git status不显示任何生成文件。
4. LFS配置正确：检查`.gitattributes`中的LFS跟踪规则。

---

## 8 总结：节省空间的本质

| 传统方式 | 优化方式 |
|---------|---------|
| 跟踪整个工程目录（GB级） | 只跟踪源码+TCL脚本（MB级别） |
| 直接跟踪IP/BD生成文件 | 用TCL脚本重建IP/BD |
| 所有版本Bitstream入仓库 | 仅关键Bitstream用LFS存储 |
| 手动管理工程 | 脚本化一键重建 |

通过以上方法，可将Vivado工程版本库压缩到原始大小的1%~5%，同时确保完整的设计可追溯性和可重复性。

### 8.1 存储空间对比

**1. 自定义IP存储空间对比：**

| 管理方式 | 存储占用 | 可重建性 | 易用性 |
|---------|---------|---------|--------|
| 跟踪所有生成文件（SVN） | 100MB+ | √ | √（完整复制，无需重建） |
| 仅跟踪源码 | 1~5M | √ | ！（需手动重建工程） |
| 本方案（仅跟踪源码+脚本） | 2~10M | √ | √（脚本化重建） |

> 实测案例：TSN端节点工程中，fpga_core IP工程，传统方式占用150MB，本方案仅占用5.1MB（节省96.6%）

**2. 逻辑工程存储空间对比：**

| 管理方式 | 存储占用 | 可重建性 | 易用性 |
|---------|---------|---------|--------|
| 跟踪所有生成文件（SVN） | 1GB+ | √ | √完整复制，无需重建 |
| 仅跟踪源码 | 1~5M | √ | ！（需手动重建工程） |
| 本方案（仅跟踪源码+脚本） | 10~50M | √ | √（脚本化重建） |

> 实测案例：TSN端节点工程，传统方式占用2.1GB，本方案仅占用51.5MB（节省97.6%）

### 8.2 常见问题解决

**Q：IP的GUI配置如何保存？**
**A：** 所有配置都储存在.xci文件中，重建脚本会读取这些配置

**Q：是否必须要按照推荐目录结构存储？**
**A：** 是的，如果不按照推荐目录结构存储，重建工程会失败，建议统一目录结构

**Q：.gitignore文件如何使用？**
**A：** .gitignore文件只需要放在对应文件夹中，在git commit提交时git会检查.gitignore文件中的过滤策略，当过滤策略设置好之后，无需人为干预。

**Q：7.4节的关键检查点是谁来执行检查？**
**A：** 1、2和3检查点在本地检验，当从远程仓库拉取新版本时，由开发人员自行检查是否能够重建工程和编译，如果不能，请及时反馈给本仓库的维护者（maintainer），maintainer将被公布在项目的README界面中。第4项由项目的拥有者（owner）即负责人进行检查，当每次项目有合并请求时，请拥有着主动检查。

**Q：如何做merge管理？**
**A：** 当项目有更新，且需要提交至主线时，请owner检查修改点是否描述完整，如不完整，不允许合并至主线，因此，各位在提交commit时，请如实填写完整的修改记录，保持主线的版本的可追溯性，同样的，分支的commit信息也要提交完整，否则在合并主线时，内容是缺失的，也将不被允许合并至主线。
