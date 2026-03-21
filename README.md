# Mosaic App

[![build-desktop](https://github.com/machamu-24/mosaic_app-project/actions/workflows/build_desktop.yml/badge.svg)](https://github.com/machamu-24/mosaic_app-project/actions/workflows/build_desktop.yml)
[![GitHub Release](https://img.shields.io/github/v/release/machamu-24/mosaic_app-project)](https://github.com/machamu-24/mosaic_app-project/releases)

## Project Info

- **プロジェクト名:** Mosaic App
- **バージョン:** `v1.0.12`
- **作成者:** まさむ（理学療法士/エンジニア）

動画や画像に写った顔を自動検出し、モザイク処理を適用するアプリケーションです。  
医療・研究・記録用途など、プライバシー保護を目的とした匿名化処理を想定しています。

顔検出には `YOLOv8-Face` を使用し、マスク着用時や小さな顔、横顔なども含めて検出できるよう構成しています。  
ローカル PC 上で扱えるため、外部サービスにアップロードせずに匿名化データを作成したいケースに向いています。

## プロジェクト概要

このリポジトリでは、同じ顔モザイク処理エンジンを 3 つの利用形態で提供しています。

| 方式 | エントリーポイント | 想定用途 |
| --- | --- | --- |
| Desktop GUI | `python gui_app.py` | 非エンジニア向けのシンプルなローカル実行 |
| Web UI | `streamlit run app.py` | デモ、確認、ブラウザ上での操作 |
| CLI | `python run_mosaic.py ...` | バッチ処理、詳細パラメータ調整、スクリプト連携 |

## 主な機能

- `YOLOv8-Face` による自動顔検出
- 動画と静止画の両方に対応
- 顔領域への自動モザイク適用
- 初回実行時のモデル自動ダウンロード
- モザイク強度、推論サイズ、信頼度閾値、IoU 閾値の調整
- Apple Silicon では `MPS` を優先利用し、必要に応じて CPU へフォールバック
- Windows / macOS 向けデスクトップ配布 ZIP の自動生成

## ユースケース

- 医療・介護現場での歩行動画や記録映像の匿名化
- 研究用途の動画・写真データのプライバシー保護
- デモ映像や説明用資料に含まれる人物の顔隠し
- ローカル環境で完結する匿名化ワークフローの構築

## 技術スタック

- Python 3.9+
- `ultralytics==8.3.17`
- `opencv-python==4.10.0.84`
- `numpy==1.26.4`
- `moviepy==1.0.3`
- `streamlit==1.41.1`

ビルド用途では以下も利用します。

- `pyinstaller`
- `streamlit-desktop-app`
- `imageio-ffmpeg`

## クイックスタート

### 前提条件

- Python 3.9 以上
- macOS または Windows を想定
- 初回実行時にモデルを自動取得する場合はインターネット接続

### インストール

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### デスクトップGUI

もっとも簡単な起動方法です。

```bash
python gui_app.py
```

操作の流れ:

1. 入力ファイルを選択
2. 出力先を確認または変更
3. モザイクの強さを設定
4. 実行ボタンで処理開始

### Web UI

ブラウザ上で確認しながら使いたい場合はこちらです。

```bash
streamlit run app.py
```

起動後は通常 `http://localhost:8501` で利用できます。  
アップロード、設定変更、処理結果の保存までブラウザから操作できます。

### CLI

スクリプトから実行したい場合や、パラメータを細かく調整したい場合はこちらです。

```bash
python run_mosaic.py --input input.mp4 --output output.mp4
```

主なオプション:

```bash
python run_mosaic.py \
  --input input.mp4 \
  --output output.mp4 \
  --mosaic 20 \
  --yolo-imgsz 960 \
  --yolo-conf 0.25 \
  --yolo-iou 0.45
```

主要引数:

| 引数 | 説明 | デフォルト |
| --- | --- | --- |
| `--input` | 入力ファイルパス | 必須 |
| `--output` | 出力ファイルパス | 必須 |
| `--mosaic` | モザイク強度 | `20` |
| `--yolo-weights` | モデルファイルパス | `models/yolov8m-face.pt` |
| `--yolo-imgsz` | 推論解像度 | `960` |
| `--yolo-conf` | 信頼度閾値 | `0.25` |
| `--yolo-iou` | IoU 閾値 | `0.45` |
| `--device` | `cpu` / `mps` / GPU 指定 | 自動選択 |

## 対応ファイル

入力ファイルは拡張子から画像・動画を判定します。

- 動画: `mp4`, `mov`, `avi`
- 画像: `jpg`, `jpeg`, `png`, `webp`, `bmp`, `tif`, `tiff`

動画はフレーム単位で処理し、可能な場合は元動画の音声を保持します。

## ビルド済みアプリのダウンロード

**ソースコードを実行せずに使いたい場合は、ビルド済み ZIP を利用できます。**

- 正式な配布物: [GitHub Releases](https://github.com/machamu-24/mosaic_app-project/releases)
- 手動実行のビルド成果物: [GitHub Actions / build-desktop](https://github.com/machamu-24/mosaic_app-project/actions/workflows/build_desktop.yml)

`Releases` には、タグ付きリリース時に生成された ZIP が添付されます。  
開発中の確認用に一時的な ZIP が必要な場合は、Actions の実行結果から `Artifacts` をダウンロードしてください。

想定される ZIP 名の例:

- `MosaicApp-v1.0.0-windows-x64.zip`
- `MosaicApp-v1.0.0-macos.zip`

## Build And Release With GitHub Actions

このリポジトリには、Windows / macOS 向けデスクトップアプリを自動ビルドして ZIP 化する workflow が含まれています。

対象 workflow:

- [`.github/workflows/build_desktop.yml`](.github/workflows/build_desktop.yml)

### Manual Build

GitHub の Actions タブから `build-desktop` を手動実行できます。

手順:

1. [Actions / build-desktop](https://github.com/machamu-24/mosaic_app-project/actions/workflows/build_desktop.yml) を開く
2. `Run workflow` を実行する
3. 完了後、実行ページの `Artifacts` から ZIP を取得する

### Release Build

タグを push すると、Windows / macOS の ZIP が自動生成され、GitHub Releases に添付されます。

```bash
git tag v1.0.0
git push origin v1.0.0
```

workflow の主な動作:

- `windows-latest` と `macos-latest` を並列ビルド
- 生成物を ZIP 化
- Artifacts にアップロード
- タグ push 時は GitHub Release を自動作成し、ZIP を添付

### macOS Distribution Notes

macOS では、署名や Notarization の有無によって初回起動時の挙動が変わります。

- GitHub Secrets が設定されている場合: `Developer ID` 署名と `Notarization` を実施
- 未設定の場合: `ad-hoc codesign` にフォールバック
- **macOS 版では、アプリを×(×)ボタンで閉じた際に終了まで `1〜2分` ほどかかることがあります**

後者では、利用者の環境でセキュリティ警告が表示される場合があります。  
非エンジニア向けに配布する場合は、workflow に必要な Secrets を設定した運用を推奨します。

**上記の終了待ち時間は、特に Streamlit ベースの macOS アプリで発生することがあります。**  
終了に時間がかかる場合でも、直ちに不具合とは限りません。利用者向けには「終了に時間がかかることがありますが、バグではありません」と案内しておくことを推奨します。

## Streamlit Community Cloud

簡易的な Web 共有やデモ用として `Streamlit Community Cloud` に公開することもできます。

基本的な公開条件:

- GitHub リポジトリに最新コードが push されていること
- `main file path` に `app.py` を指定すること

ただし、無料クラウド環境では処理時間やリソースに制約があります。  
長時間動画や高負荷な本番用途では、ローカル実行またはデスクトップ配布版の利用を推奨します。

## 処理の流れ

処理の流れは以下の通りです。

1. 入力ファイルを読み込む
2. `YOLOv8-Face` で顔のバウンディングボックスを検出する
3. 検出領域を低解像度に縮小し、再拡大してモザイク化する
4. 画像または動画として保存する

小さな顔の検出率を上げるため、デフォルトの推論サイズは `imgsz=960` に設定しています。  
用途に応じて、速度優先なら小さめ、検出重視なら大きめに調整できます。

## プロジェクト構成

| ファイル | 役割 |
| --- | --- |
| `run_mosaic.py` | 顔検出とモザイク適用のコア処理 |
| `gui_app.py` | Tkinter ベースのローカル GUI |
| `app.py` | Streamlit ベースの Web UI |
| `requirements.txt` | 実行時依存関係 |
| `requirements_build.txt` | デスクトップビルド用依存関係 |
| `.github/workflows/build_desktop.yml` | ZIP ビルドとリリース自動化 |
| `README_JA.md` | 詳細な利用手順書 |
| `application_specification.md` | 背景・目的・仕様の整理 |

## 関連ドキュメント

- 詳細な利用手順: [README_JA.md](README_JA.md)
- 仕様・背景説明: [application_specification.md](application_specification.md)

README では入口となる情報をまとめ、詳細な操作説明や背景説明は上記ドキュメントに分離しています。

## 注意事項

- AI による顔検出は高精度ですが、100% の検出を保証するものではありません
- 公開・共有前には、必ず出力結果を目視確認してください
- 長時間動画や高解像度動画では処理時間が長くなります
- 初回実行時はモデルダウンロードのため時間がかかる場合があります
- Web 版は説明やデモに向いていますが、業務用途の長尺動画にはローカル実行が適しています
- macOS 版では、Streamlit アプリをバツボタンで終了した際に終了処理が `1〜2分` ほどかかる場合があります。これは既知の挙動であり、必ずしもバグではありません

## ライセンス

現時点では、このリポジトリにライセンスファイルは含まれていません。  
公開範囲や再利用条件を明確にする場合は、別途 `LICENSE` の追加を推奨します。
