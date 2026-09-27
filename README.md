# Qwen Image Book — AI 繪本

42 頁 AI 繪本。故事與提示詞定案後，用 Qwen Image 2.1 + ComfyUI 逐頁生成圖片，再與故事文字打包成可列印的 ODT。

## 最終成品

- `繪本_42頁完整版.odt` — 42 頁（每頁：頁碼、標題、圖片、故事文字），約 5.8 MB

## 目錄結構

```
storyboard/    故事與提示詞（正典，改這裡才有效）
compressed/    42 張 ODT 用圖（JPG，每頁最新版本）
generated/     原始 PNG（各版本，未壓縮；不進 git）
api/           ComfyUI 生成腳本與模板
archive/       舊版本（舊 ODT、舊腳本、舊筆記；不進 git）
build_odt.py   ODT 打包腳本
compress_images.py  壓圖腳本
```

## 故事與提示詞（唯一來源）

- `storyboard/完整故事.md` — 42 頁故事文字、地基設定、角色表
- `storyboard/42頁提示詞.md` — 42 頁生成 prompt（唯一來源）
  - **角色視覺塊**、**塔視覺塊**：固定字眼，全書統一，不得改字
- `storyboard/storyboard.md` — 分鏡檔，由上面兩檔同步而來

## 重新生成圖片

ComfyUI：`http://100.89.149.50:8188`（Linux / NVIDIA GB10 / 128GB 統一記憶體 / --highvram；模板 `api/template.json`，seed 1234，1024x1024，每張間隔 3 秒）

```
python api/api_script.py 18 "prompt 內容"        # 單頁
python api/batch_generate.py 1 18 42            # 指定頁
python api/batch_generate.py --suffix v4        # 全部頁，輸出綴字尾 v4
```

新圖輸出到 `generated/page{N}_{版本}.png`，已存在的頁會跳過。

## 生成環境

**故事**
- 生成模型：qwen3.8-27b（LLM，用於撰寫故事正文與整理 42 頁提示詞）

**圖片（ComfyUI 主機）**

**硬體**
- 主機：`100.89.149.50:8188`（Tailscale 內網位址）
- 系統：Linux
- GPU：NVIDIA GB10（128GB 統一記憶體）
- ComfyUI 0.37.0、PyTorch 2.10、Python 3.12.3
- 啟動參數：`--highvram --disable-mmap --disable-pinned-memory`

**模型**
- 主模型（UNet）：`qwen_image_2.1_int8_convrot.safetensors`
- 文字編碼器（CLIP）：`qwen3vl_8b_int8_convrot.safetensors`
- VAE：`qwen_image_2.1_vae_bf16.safetensors`

**生成參數**
- 畫布 1024x1024、steps 30、cfg 1.0、euler / simple、denoise 1.0、seed 1234
- negative prompt：`ugly, blurry`

## 重新打包 ODT

```
python compress_images.py          # 各頁取最新版本壓成 compressed/page{N}.jpg
python build_odt.py                # DOCX 中繼 → LibreOffice → 繪本_42頁完整版.odt
```

需要 LibreOffice（`C:\Program Files\LibreOffice\program\soffice.exe`）。`build_odt.py` 會自動轉 PDF 驗證 42 頁。
注意：打包前不要開著 ODT 檔（檔案被佔用會寫不進去）。

## 圖片版本記錄

| 版本 | 檔名 | 說明 |
|------|------|------|
| v1 | `page{N}_*.png` | 初版 42 頁 |
| v2 | `page{N}_v2.png` | 2026-09-26 故事定案後全書重生成（色調、小滿外貌統一） |
| v3 | `page{N}_v3.png` | 2026-09-27 有塔的 15 頁重生成（塔造型統一，P35 為基準） |

`compressed/page{N}.jpg` 是每頁「最新版」的混合體，ODT 用它。

## 常見問題

- **印表機訊息**：LibreOffice 啟動時偵測預設印表機，若離線會顯示「等待印表機連線」，不影響轉換。
- **ODT 寫不進去（WinError 32）**：ODT 正被開啟，關掉再打包。
- **某頁不滿意**：改 `42頁提示詞.md` 該頁 prompt 或換 seed，用 `batch_generate.py 頁碼 --suffix 新版本` 單跑，再壓圖、打包。