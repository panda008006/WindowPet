<div align="center">

# 🐾 WindowPet (桌面宠物)

**新一代高互动·自主生命体桌面伴侣｜支持自家爱宠专属定制｜内置灵动岛便签与专注时钟**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.13-brightgreen.svg)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://microsoft.com)
[![Release: v1.0.32](https://img.shields.io/badge/Release-v1.0.32--candidate-orange.svg)]()

[English](README.md) · [简体中文](README.md#中文文档) · [自家宠物定制指南](#-自家宠物定制专区-custom-pet) · [角色制作教程](AI角色制作/START_HERE.md)

</div>

---

## 🌟 核心特色 (Key Features)

### 🐾 1. 栩栩如生的自主生命体
- **丰富动作状态机**：漫步、发呆、打瞌睡、屏幕边缘攀爬、下落打滚，每只宠物都有独特的个性与行为。
- **桌面物理引擎**：支持真实桌面重力、窗口边缘碰撞避障与下落反馈。
- **多实例共存**：桌面支持同时放置多只不同的小可爱，陪伴你的每一个工作与游戏时刻。

### 🪄 2. 趣味交互道具系统
- **羽毛逗猫棒**：鼠标挥动逗弄宠物，触发欢快跳跃追逐。
- **趣味小皮鞭**：轻触互动，触发趣味受击反馈与撒娇动画。
- **麦克风音乐响应**：捕捉系统或麦克风音乐节奏，跟着动感节拍摇摆起舞。

### 📌 3. 桌面效率神器
- **NotchNotes 顶部刘海便签**：贴附在屏幕顶部的便签板，随时记录灵感与待办事项。
- **专注时钟与休息提醒**：番茄工作法加持，让宠物陪伴你的每一次专注冲刺。

### 🎨 4. 自家爱宠专属定制 (Custom Pet) —— 你的猫狗，住进电脑
- **不仅仅是现成模型**：支持将你自己家里的猫咪、狗狗、龙猫、鹦鹉制作成专属桌宠！
- **AI 赋能 + 画师精修**：提供从照片一键风格化提取到多动作切片全套支持。

---

## 🚀 快速上手 (Quick Start)

### 选项 A：普通用户（无需安装任何环境，双击即用）
1. 在 [Releases](../../releases) 页面下载最新版安装包 `WindowPet_Setup_v1.0.32.exe`。
2. 双击运行安装向导，一路点击“下一步”，即可自动在桌面生成快捷方式。
3. 双击桌面的 **WindowPet** 图标即可召唤你的桌面伙伴！

> **关于 Windows 拦截提示说明**：
> 作为独立开源软件，若下载后系统提示“未知发布者”或“Windows 已保护你的电脑”，请点击 **【更多信息】 -> 【仍要运行】** 即可正常开启。

### 选项 B：开发者本地运行 (Developer Mode)
```bash
# 1. 克隆代码仓库
git clone https://github.com/your-username/WindowPet.git
cd WindowPet

# 2. 安装依赖
pip install -r requirements.txt
# 或直接安装核心依赖
pip install PySide6 pillow screeninfo pywin32 pynput

# 3. 运行主程序
python main.py
```

---

## 🎨 自家宠物定制专区 (Custom Pet)

想把自家毛孩子做成每天陪你写代码、看电影、上课的专属桌宠？

1. **准备素材**：准备 1~3 张爱宠清晰的全身照（站立、趴着、坐姿正面）。
2. **动作定制**：
   - 基础版：待机动作（发呆/打哈欠）+ 走路动作 + 睡觉动作。
   - 进阶版：加入专属玩具互动、打字敲键盘联动等。
3. **联系方式**：
   - 欢迎加入官方交流群或联系开发者/入驻画师进行专属定制咨询！
   - QQ 交流群：`待添加` / 微信：`待添加`

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
