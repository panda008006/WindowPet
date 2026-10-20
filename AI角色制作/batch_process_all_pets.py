"""WindowPet 4只爱宠一键批量视频处理与上架脚本 (Batch Video Pet Processor)

自动扫描 `小角色/` 下的 4 个待处理文件夹：
  1. 01_白化蜜袋鼯_输入视频 -> SugarGliderPet (兑换码: WPX-2026-SUGARGLIDER)
  2. 02_矮脚橘白猫_输入视频 -> MunchkinCatPet (兑换码: WPX-2026-MUNCHKIN)
  3. 03_金渐层胖猫_输入视频 -> ChubbyGoldenCatPet (兑换码: WPX-2026-GOLDENCAT)
  4. 04_微笑守宫_输入视频   -> LeopardGeckoPet (兑换码: WPX-2026-GECKO)

只要文件夹里有视频，脚本就会全自动调用 DirectML GPU 进行影院级去绿幕抠像、
零碎片打包至 assets、生成舞台预览、写入兑换码并注册到 package_registry.json！
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PET_CONFIGS = [
    {
        "input_folder": "01_白化蜜袋鼯_输入视频",
        "output_name": "白化蜜袋鼯",
        "char_id": "SugarGliderPet",
        "display_name": "白化蜜袋鼯",
        "redeem_code": "WPX-2026-SUGARGLIDER",
        "registry_code": "1008",
        "package_id": "sugarglider",
    },
    {
        "input_folder": "02_矮脚橘白猫_输入视频",
        "output_name": "矮脚橘白猫",
        "char_id": "MunchkinCatPet",
        "display_name": "矮脚橘白猫",
        "redeem_code": "WPX-2026-MUNCHKIN",
        "registry_code": "1009",
        "package_id": "munchkincat",
    },
    {
        "input_folder": "03_金渐层胖猫_输入视频",
        "output_name": "金渐层胖猫",
        "char_id": "ChubbyGoldenCatPet",
        "display_name": "金渐层胖猫",
        "redeem_code": "WPX-2026-GOLDENCAT",
        "registry_code": "1010",
        "package_id": "chubbygoldencat",
    },
    {
        "input_folder": "04_微笑守宫_输入视频",
        "output_name": "微笑守宫",
        "char_id": "LeopardGeckoPet",
        "display_name": "微笑守宫",
        "redeem_code": "WPX-2026-GECKO",
        "registry_code": "1011",
        "package_id": "leopardgecko",
    },
]


def register_in_package_registry(registry_json_path: Path, item: dict):
    if not registry_json_path.exists():
        return
    data = json.loads(registry_json_path.read_text(encoding="utf-8"))
    existing_codes = {p.get("code") for p in data.get("packages", [])}
    existing_folders = {p.get("folder_name") for p in data.get("packages", [])}

    if item["char_id"] in existing_folders:
        print(f"  [注册表] 角色包 {item['char_id']} 已存在于 package_registry.json")
        return

    new_pkg = {
        "code": item["registry_code"],
        "package_id": item["package_id"],
        "folder_name": item["char_id"],
        "display_name": item["display_name"],
        "owner_type": "custom",
        "status": "published",
    }
    data["packages"].append(new_pkg)
    registry_json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [注册表] 已成功追加登记 {item['display_name']} (代码 {item['registry_code']})")


def main():
    root = Path(__file__).resolve().parent.parent
    roles_base = root / "小角色"
    process_py = root / "AI角色制作" / "process_video_pet.py"
    control_py = root / "window_pet_app" / "control_panel.py"
    registry_json = root / "package_registry.json"

    print("==========================================================")
    print("      WindowPet 4只新爱宠一键批量处理流水线")
    print("==========================================================")
    print(f"工程根目录: {root}")

    found_any = False
    for cfg in PET_CONFIGS:
        in_dir = roles_base / cfg["input_folder"]
        out_dir = roles_base / cfg["output_name"]

        if not in_dir.exists():
            continue

        # 如果存在 zip 压缩包，自动解压出视频文件
        for zip_f in list(in_dir.glob("*.zip")):
            print(f"  [解压] 发现压缩包 {zip_f.name}，正在自动解压...")
            with zipfile.ZipFile(zip_f, "r") as zf:
                for member in zf.infolist():
                    target_name = Path(member.filename).name
                    if not target_name:
                        continue
                    if Path(target_name).suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}:
                        target_path = in_dir / target_name
                        with zf.open(member) as src, open(target_path, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        print(f"    -> 已解压: {target_name}")

        vfiles = [f for f in in_dir.iterdir() if f.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}]
        if not vfiles:
            print(f"[-] {cfg['display_name']} ({cfg['input_folder']}): 暂无视频文件，跳过")
            continue

        # 检查是否已制作完成（增量加速）
        char_f = cfg["char_id"] if cfg["char_id"].endswith("Pet") else f"{cfg['char_id']}Pet"
        assets_dir = root / "assets" / char_f
        if (assets_dir / "asset.json").exists() and (out_dir / "idle.mov").exists():
            print(f"[*] {cfg['display_name']} 已在 assets 中完整就绪，跳过重复渲染。")
            register_in_package_registry(registry_json, cfg)
            cp_text = control_py.read_text(encoding="utf-8", errors="ignore")
            if cfg["redeem_code"] not in cp_text:
                m = re.search(r"(public_map\s*=\s*\{)(.*?)(\})", cp_text, flags=re.DOTALL)
                if m:
                    entry = f'\n            "{cfg["redeem_code"]}": ("{char_f}", "{cfg["display_name"]}"),'
                    pos = m.start(1) + len(m.group(1))
                    control_py.write_text(cp_text[:pos] + entry + cp_text[pos:], encoding="utf-8")
                    print(f"  [兑换码] 成功补入: {cfg['redeem_code']}")
            print(f"[OK] {cfg['display_name']} 上线状态确认！兑换码: {cfg['redeem_code']}")
            continue

        found_any = True
        print(f"\n[+] 发现 {cfg['display_name']} 的待处理视频 ({len(vfiles)} 个)，启动 GPU 抠像处理...")

        cmd = [
            sys.executable,
            str(process_py),
            "--input_dir",
            str(in_dir),
            "--character_id",
            cfg["char_id"],
            "--display_name",
            cfg["display_name"],
            "--output_dir",
            str(out_dir),
            "--assets_root",
            str(root / "assets"),
            "--control_panel",
            str(control_py),
            "--redemption_code",
            cfg["redeem_code"],
        ]
        res = subprocess.run(cmd)
        if res.returncode == 0:
            register_in_package_registry(registry_json, cfg)
            print(f"[OK] {cfg['display_name']} 生产与上线成功！兑换码: {cfg['redeem_code']}")
        else:
            print(f"[ERROR] {cfg['display_name']} 处理发生错误，请检查日志。")

    if not found_any:
        print("\n提示：所有角色包均已处理完成或输入文件夹为空。")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
