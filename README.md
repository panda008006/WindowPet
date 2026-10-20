<div align="center">

# 🐾 WindowPet (桌面宠物)

**新一代高互动·自主生命体桌面伴侣｜1440P 超清透明与多宠同屏｜支持自家爱宠专属定制｜内置灵动岛便签与专注时钟**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.13-brightgreen.svg)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://microsoft.com)
[![Release: v2.0.0](https://img.shields.io/badge/Release-v2.0.0--latest-brightgreen.svg)](https://github.com/panda008006/WindowPet/releases/latest)
[![Website: windowpet.cn](https://img.shields.io/badge/Website-windowpet.cn-ff6b81.svg)](https://windowpet.cn)

[官方网站与展馆](https://windowpet.cn) · [📥 直接下载安装包 (v2.0.0)](https://windowpet.cn/pet/downloads/window-pet-2.0.0.zip) · [Releases 发行页](../../releases) · [角色制作教程](AI角色制作/START_HERE.md)

</div>

---

## 🌟 核心特色 (Key Features)

### 🐾 1. 栩栩如生的自主生命体 & 默认双宠同屏
- **丰富动作状态机**：漫步、发呆、打瞌睡、屏幕边缘攀爬、下落打滚，每只宠物都有独特的个性与行为。
- **开箱即用默认同屏双宠**：首次启动默认同屏召唤「大DeepSeek」与「大肥鱼」，智能阶梯错位排布，各自独立动画定时与互动。
- **多实例多宠共存**：桌面支持同时放置多只不同的小可爱，陪伴你的每一个工作与游戏时刻。

### 🎨 2. 全量 1440P 超清点对点原生无损透明渲染
- **原生透明通道**：基于无损透明视频与 WebP 高帧率渲染技术，发丝级画质，彻底告别灰底与白毛边。
- **流畅低占用**：智能后台帧缓存与硬件加速，保持桌面极高流畅度与极低资源开销。

### 🪄 3. 趣味交互道具系统
- **羽毛逗猫棒**：鼠标挥动逗弄宠物，触发欢快跳跃追逐。
- **趣味小皮鞭**：轻触互动，触发趣味受击反馈与撒娇动画。
- **麦克风音乐响应**：捕捉系统或麦克风音乐节奏，跟着动感节拍摇摆起舞。

### 📌 4. 桌面效率神器
- **NotchNotes 顶部刘海便签**：贴附在屏幕顶部的便签板，随时记录灵感与待办事项。
- **专注时钟与休息提醒**：番茄工作法加持，让宠物陪伴你的每一次专注冲刺。

### 🤖 5. DeepSeek AI 角色工坊
- **AI 赋能角色生成**：全新集成 DeepSeek AI 提示词生成器与 Q 版鲸鱼看板，一键生成符合规范的角色设计提示词。
- **极简「动作」工坊**：界面纯粹直观，支持拖拽快速绑定动作素材。

---

## 🚀 快速上手 (Quick Start)

### 选项 A：普通用户（绿色免安装，双击即用）
1. 在 [官方网站](https://windowpet.cn) 或 [Releases](../../releases) 页面下载最新版压缩包 `window-pet-2.0.0.zip`。
2. 解压到任意文件夹。
3. 双击运行 **【双击启动 Window Pet】.exe**（已嵌入官方爪印多分辨率原生 Logo，免配 Python 环境，无黑框命令行，跨机便携秒启）。

> **关于 Windows 拦截提示说明**：
> 作为独立开源软件，若下载后系统提示“未知发布者”或“Windows 已保护你的电脑”，请点击 **【更多信息】 -> 【仍要运行】** 即可正常开启。

### 选项 B：开发者本地运行 (Developer Mode)
```bash
# 1. 克隆代码仓库
git clone https://github.com/panda008006/WindowPet.git
cd WindowPet

# 2. 安装依赖
pip install -r requirements.txt
# 或直接安装核心依赖
pip install PySide6 pillow screeninfo pywin32 pynput

# 3. 运行主程序
python main.py
```

---

## 🛠️ 自制角色与 AI 创作管线

本项目内置了完整的角色扩展规范与 AI 自动化生产流水线：
- 查看完整制作指南：[AI角色制作/START_HERE.md](AI角色制作/START_HERE.md)
- 新建角色只需在 `assets/<角色英文名Pet>/` 目录下添加图片与 `动作说明.md`。
- 本地自动化测试校验脚本：
  ```bash
  python AI角色制作/validate_character.py assets/<YourPetName>Pet
  ```

---

## 🤝 鸣谢与贡献 (Contributing)

欢迎提交 Issue 与 Pull Request！无论你是修复 Bug、改进动作、还是贡献了全新的免费宠物角色包，都将被列入鸣谢名单！

---

## 📄 开源许可证 (License)

本项目采用 [MIT 许可证](LICENSE) 开源。欢迎所有人自由使用、学习与二创！
