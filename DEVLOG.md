# DevLog — AI 繪本專案

---

## 2026-09-27 | v2 全書重生成 + 塔造型統一（v3）

### 背景
- 故事定案後（`storyboard/完整故事.md`、`storyboard/42頁提示詞.md`），42 頁全數以新 prompt 重生成：`generated/page{N}_v2.png`
- ODT v2（`繪本_42頁完整版_v2.odt`）改新格式：每頁＝頁碼（小灰）＋標題（粗體置中）＋圖片＋故事正文；不再含場景/Prompt 元資料
- 用戶驗收後回報「塔的造型沒有統一」：每張圖獨立生成、prompt 沒有鎖塔的固定描述，AI 每頁畫不同塔

### 決策
- 新增「塔視覺塊」（全書統一，寫進 42頁提示詞.md，P35 為基準頁）：
  `a very tall slender tower with a smooth rounded top, smooth plain walls, softly glowing from within like a giant lantern`
  光色依段落：P1-16 pale blue-purple / P22-27 red warning / P34 dim fading / P36-42 soft green-gold
- 有塔的 15 頁（P1/2/3/4/5/7/8/15/22/23/27/34/36/37/42）改用塔塊重生成；P35 保留（基準頁）
- 新圖命名 `page{N}_v3.png`，舊 v2 不動

### 執行
1. `Temp\opencode\batch_tower_v3.py`：15 頁批量，全部成功
2. `Temp\opencode\compress_v3.py`：15 張壓至 `compressed/page{N}.jpg`（覆蓋）
3. `Temp\opencode\build_odt_v3.py`（v2 腳本複製改名）：DOCX 中繼 → `繪本_42頁完整版_v3.odt`

### 驗證結果
- Round-trip：42 draw:frame、42 draw:image、42 jpg media
- PDF：42 頁、6.49 MB、有嵌入 JPEG
- ODT：約 5 MB

### 技術細節 / 坑
- ODT 檔正被開啟時（用戶翻閱中），`os.remove` 會 PermissionError [WinError 32] → 解法：改輸出新檔名（v3），不強刪舊檔
- LibreOffice 啟動偵測預設印表機時，若印表機離線會顯示「等待印表機連線」，不影響轉換結果

### 驗收
- 2026-09-27 用戶確認塔造型 OK
- `繪本_42頁完整版_v3.odt` 改名為 `繪本_42頁完整版.odt`（正式版）

### 目錄整理
- 舊版 ODT、舊腳本、NOTES.md、prompt_ids、test_round1 → `archive/`
- 正式腳本收進專案：`build_odt.py`（打包）、`compress_images.py`（壓圖，自動選最新版）、`api/batch_generate.py`（批次生成，直接讀 42頁提示詞.md）
- `generated/`（160MB 原圖）、`archive/` 不進 git
- git init、.gitignore 完成，準備 commit

### 靜態網頁版（GitHub Pages 用）
- 本專案目的：測試「Qwen-Image 2.1 模型＋GB10 機器」軟硬體組合（前言寫明）
- `build_web.py`：解析 `完整故事.md`（42 頁＋5 段落）→ 產出根目錄 `index.html`；同時複製 `compressed/page{N}.jpg` 到 `images/`
- 頁面結構：前言（測試源起＋故事大綱）→ 42 頁正文（頁碼＋標題＋圖片＋正文）→ 開發過程 → 生成環境
- 翻頁電子書視圖（預設）：共 47 頁（封面＋前言 2 頁＋42 頁＋開發過程＋生成環境），3D 翻頁動畫，方向鍵／點畫面／左右滑動／左右按鈕翻頁，附進度條與頁碼
- 頂部按鈕可切換「直式捲動」完整版面（同樣內容，方便一次看全部）
- 純靜態（單一 HTML＋42 張 JPG＋少量原生 JS、無外掛、無 CDN），改故事文字重跑腳本即可更新
- 發布方式：push 到 GitHub 後在 Settings → Pages 啟用（root）

---

## 2026-09-26 | ODT 完整版產出

### 決策
- 直接寫 ODF `draw:frame` 時，LibreOffice 會保留文字但丟掉所有圖片 frame。
- 改採「DOCX 中繼」路線：先用 Python 產生含 42 張 JPEG 的 DOCX，再交給 LibreOffice 轉成 ODT。
- 此路線可讓 LibreOffice 產生正確的 `draw:frame` / `draw:image` 與 `Pictures/` 媒體檔。

### 執行
1. 新增 `build_odt_via_docx.py`
   - 解析 `storyboard/storyboard.md` 的 42 頁文字
   - 使用 `compressed/page1.jpg` 至 `compressed/page42.jpg`
   - 產生 DOCX（每頁：頁碼、標題、圖片、場景、Prompt）
   - 以 LibreOffice headless 轉成 ODT
   - 再轉 PDF 做驗證
2. 輸出：
   - `picturebook_final.odt`
   - `繪本_42頁完整版.odt`（最終檔，已取代舊版）

### 驗證結果
- ODT 可正常開啟
- Round-trip 後仍有 42 個 `draw:frame`、42 個 `draw:image`
- PDF 驗證：42 頁、約 7.37 MB、有嵌入 JPEG 圖片
- 最終 ODT 大小約 6.36 MB
- 原始 PNG 保留在 `generated/`，未更動

### 技術細節
- 直接 ODT 路徑：`build_odt_v5.py`（文字有效，但圖片被 LibreOffice 丟棄）
- 成功路徑：`build_odt_via_docx.py`
- DOCX 使用 WordprocessingML inline drawing，圖片放在 `word/media/image{N}.jpg`
- LibreOffice 轉換 filter：`odt:writer8`

---

## 2026-09-26 | 批量重生成完成

### 決策
- **覆寫 Page 2-34**：使用更新後的 storyboard 提示詞，以 page1 風格為基準重新生成
- **目的**：確保所有頁面風格一致，避免品質參差

### 執行
1. **清理**：刪除 `generated/page2*.png` 至 `page34*.png`
2. **批次送出**：分 4 批，每批 10-12 張
   - 第 1 批：Page 2-10
   - 第 2 批：Page 11-20
   - 第 3 批：Page 21-30
   - 第 4 批：Page 31-42
3. **Polling**：使用 `GET /history/{prompt_id}` 輪詢完成狀態
4. **下載**：成功後即時下載至 `generated/`

### 結果
- ✅ **42 頁全部完成**，無遺漏
- 所有檔案使用 page1 風格基準
- 提示詞包含：`Japanese picture book style, soft colors, illustrated, 4k` + `cinematic lighting, moody` + 構圖標籤

### 技術細節
- API 端點：`http://100.89.149.50:8188`
- `/prompt` POST → 送出生成
- `/history/{pid}` GET → 查詢狀態
- `/view` GET → 下載成品
- 每張圖間隔 3 秒，避免 API 阻塞
- 下載後檔名格式：`page{N}_*.png`

---

## 待確認

- [x] 圖片品質評估（2026-09-27 用戶驗收通過）
- [x] 段落色調加入 prompt（v2 已完成，2026-09-26）
- [ ] CFG 參數調整（true_cfg_scale？）
- [ ] 生成速度優化（每張 30-60 秒，批次總耗時過長）

---

## API JSON 結構（template.json）

```json
{
  "UNETLoader": {
    "inputs": {
      "unet_name": "qwen_image_2.1_int8_convrot.safetensors"
    }
  },
  "CLIPLoader": {
    "inputs": {
      "clip_name": "qwen3_vl_8b_int8_convrot.safetensors"
    }
  },
  "VAELoader": {
    "inputs": {
      "vae_name": "qwen_image_2.1_vae_bf16.safetensors"
    }
  },
  "prompt": {
    "4": {
      "inputs": {
        "prompt": "[PAGE_PROMPT]",
        "negative_prompt": "[NEGATIVE_PROMPT]"
      }
    }
  },
  "EmptyLatentImage": {
    "inputs": {
      "width": 1024,
      "height": 1024,
      "batch_size": 1
    }
  },
  "KSampler": {
    "inputs": {
      "seed": 0,
      "steps": 30,
      "cfg": 1.0,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1
    }
  },
  "VAEDecode": {
    "inputs": {
      "samples": ["6", 0]
    }
  },
  "SaveImage": {
    "inputs": {
      "filename_prefix": "page{N}",
      "images": ["7", 0]
    }
  }
}
```

### 節點對應
| 節點編號 | 功能 |
|----------|------|
| 1 | UNETLoader — 模型載入 |
| 2 | CLIPLoader — Text Encoder |
| 3 | VAELoader — VAE |
| 4 | TextEncodeQwenImage21API — Prompt |
| 5 | EmptyLatentImage — 畫布 |
| 6 | KSampler — 生成 |
| 7 | VAEDecode — 解碼 |
| 8 | SaveImage — 儲存 |

---

## Notes

- ComfyUI 版本：需確認
- 模型：Qwen Image 2.1 + Qwen3-VL 8B
- 畫布：1024x1024（32 的倍數）
- 風格提示詞：所有頁面統一使用
- 色調規劃：段落 1-2 藍/紫、段落 3-4 紅/橙、段落 5 綠/金
