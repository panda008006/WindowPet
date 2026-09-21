# WindowPet 宠物包规范

本文档对应当前 `01_桌面端源码_WindowPet/assets` 中已经验证可用的帧动画宠物包，用于官网商店、第三方投稿审核和后端数据建模。

## 当前可展示宠物包

| ID | 目录 | 名称 | 来源 | 规格 | 帧数 | 动作数 | 官网定位 |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| `jiyi` | `JiyiPet` | 吉伊 | 官方 | 192x208 | 69 | 13 | 轻快互动与合奏哼唱 |
| `usagi` | `UsagiPet` | 乌萨奇 | 官方 | 192x208 | 101 | 17 | 治愈陪伴、烟花合奏与活泼短动作 |
| `nuonuo` | `NuonuoPet` | 糯糯 | 自有IP | 192x208 | 64 | 15 | 粉发小团子、待机陪伴与基础互动动作 |
| `window-pet-buddy` | `WindowPetBuddy` | 电光小宠 | 官方 | 512x512 | 82 | 8 | 高清会员包与配饰 |
| `xiaoba` | `XiaobaPet` | 小八 | 创作者 | 192x208 | 69 | 13 | 第三方投稿审核示例 |

## 最小文件结构

`.wpet` 建议定义为 zip 包改后缀，解压后必须只有一个宠物根目录。

```txt
PetFolder/
  asset.json
  idle_01.png
  idle_02.png
  hover/
    hover_01.png
  click/
    click_01.png
  drag/
    drag_01.png
```

## 最小 `asset.json`

```json
{
  "type": "frame_animation",
  "name": "Pet Name",
  "fps": 10,
  "preview": "idle_01.png",
  "animations": {
    "idle": { "folder": ".", "fps": 10, "loop": true },
    "hover": { "folder": "hover", "fps": 10, "loop": false },
    "click": { "folder": "click", "fps": 12, "loop": false },
    "drag": { "folder": "drag", "fps": 10, "loop": true }
  }
}
```

## 可选能力字段

```json
{
  "idle_variants": ["waiting", "waving", "review", "running"],
  "animations": {
    "concert-hum": {
      "folder": "concert-hum",
      "fps": 8,
      "loop": false,
      "duration_seconds": 20
    }
  },
  "accessories": {
    "spark_cap": {
      "name": "星星小帽子",
      "image": "accessories/spark_cap.png",
      "x": 256,
      "y": 128,
      "pivot_x": 85,
      "pivot_y": 86,
      "scale": 1
    }
  }
}
```

## 审核规则

- `asset.json` 必须是 UTF-8 JSON object。
- 根目录必须至少有 2 张可读帧图，否则当前客户端不会识别为 `frame_animation`。
- 图片格式限制为 PNG、JPG、JPEG、WEBP；正式宠物推荐透明 PNG。
- 同一动作文件夹内的帧尺寸必须一致。
- 所有路径必须是包内相对路径，不能包含绝对路径、外链、脚本或可执行文件。
- 第三方包必须提交版权来源、授权声明和创作者信息。
- 第三方包默认进入 `pending_review`，审核通过后才能购买或生成下载授权。

## 后端字段

```ts
type PetPackage = {
  id: string
  slug: string
  folderName: string
  displayName: string
  sourceType: 'official' | 'creator'
  ownerId: string
  type: 'frame_animation'
  version: string
  minClientVersion: string
  tagline: string
  description: string
  tags: string[]
  previewImage: string
  previewFrame: string
  galleryImages: string[]
  actionKeys: string[]
  idleVariants: string[]
  accessoryKeys: string[]
  frameCount: number
  canvas: string
  defaultFps: number
  priceType: 'free' | 'paid' | 'member'
  priceCents: number
  currency: 'CNY'
  fileName: string
  fileSizeBytes: number
  storageKey: string
  sha256: string
  licenseType: string
  licenseText: string
  sourceUrl?: string
  reviewStatus: 'pending_review' | 'approved' | 'rejected'
  validationStatus: 'pending' | 'passed' | 'failed'
  publishedAt?: string
  createdAt: string
  updatedAt: string
}
```

```ts
type UserPetInstall = {
  id: string
  userId: string
  packageId: string
  packageVersion: string
  entitlementId: string
  installed: boolean
  favorite: boolean
  nickname: string
  createdAt: string
  updatedAt: string
}
```

```ts
type DevicePetState = {
  id: string
  userId: string
  deviceId: string
  installId: string
  packageId: string
  assetType: 'frame_animation'
  petDisplayName: string
  x: number
  y: number
  scale: number
  opacity: number
  speed: number
  locked: boolean
  alwaysOnTop: boolean
  clickThrough: boolean
  dockMode: string
  currentAnimation: string
  enabledAccessories: string[]
  memoVisible: boolean
  memoText: string
  memoChecked: boolean
  revision: number
  updatedAt: string
}
```
