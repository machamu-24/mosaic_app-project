# Mosaic App

[![build-desktop](https://github.com/machamu-24/mosaic_app-project/actions/workflows/build_desktop.yml/badge.svg)](https://github.com/machamu-24/mosaic_app-project/actions/workflows/build_desktop.yml)
[![GitHub Release](https://img.shields.io/github/v/release/machamu-24/mosaic_app-project)](https://github.com/machamu-24/mosaic_app-project/releases)

## Project Info

- **プロジェクト名:** Mosaic App
- **バージョン:** `v1.0.13`
- **作成者:** まさむ（理学療法士エンジニア）

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

## 対応ファイル

入力ファイルは拡張子から画像・動画を判定します。

- 動画: `mp4`, `mov`, `avi`
- 画像: `jpg`, `jpeg`, `png`, `webp`, `bmp`, `tif`, `tiff`

動画はフレーム単位で処理し、可能な場合は元動画の音声を保持します。

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


## アプリケーションのダウンロードと起動方法

GitHubの操作に慣れていない方向けに、ダウンロードから初回起動までの流れを簡単にまとめます。

1. [GitHub Releases](https://github.com/machamu-24/mosaic_app-project/releases) を開きます
2. 一番上に表示されている最新版のリリースをクリックします
3. 現時点では、最新版は `v1.0.13` です
4. `Assets` の中に、macOS 版と Windows 版の ZIP ファイルがあります
5. macOS を使っている場合は `MosaicApp-v1.0.13-macos.zip`、Windows を使っている場合は `MosaicApp-v1.0.13-windows-x64.zip` をクリックしてください
6. `Source code (zip)` や `Source code (tar.gz)` は通常の利用では不要なので、触らなくて大丈夫です
7. ダウンロードが終わったら、`Downloads` フォルダ内にある ZIP ファイルを展開してください
8. 展開して `MosaicApp` フォルダまで開けたら、そのフォルダを `Downloads` の外へ移動してください
9. `Downloads` フォルダ内のままだと、うまく起動しないケースがあります
10. 移動後に `MosaicApp` を開いて起動してください

初回起動時は、macOS / Windows ともにセキュリティ確認が表示される場合があります。  
その場合は内容を確認し、起動を許可してください。通常、この確認は初回のみです。

macOS では「ゴミ箱に入れますか」といった警告が表示される場合がありますが、**絶対にゴミ箱には入れないでください。**  

macOSの場合、一度閉じた後、「システム設定」の「プライバシーとセキュリティ」の下の方に、このアプリケーションを許可しますか？みたいなポップアップ画面があるので、「このまま開く」を押していただくとアプリケーションが起動すると思います。

Windowsの場合は、セキュリティ画面が立ち上がると、小さい文字で詳細というところをクリックすると、開くというボタンが表示されると思いますので、そのまま開くをクリックするとアプリケーションが起動すると思います。

- **macOS 版では、アプリを × ボタンで閉じた際に終了まで `1〜2分` ほどかかることがあります**
**上記の終了待ち時間は、特に Streamlit ベースの macOS アプリで発生することがあります。**  
終了に時間がかかる場合でも、直ちに不具合とは限りません。利用者向けには「終了に時間がかかることがありますが、バグではありません」と案内しておくことを推奨します。


## 処理の流れ

処理の流れは以下の通りです。

1. 入力ファイルを読み込む
2. `YOLOv8-Face` で顔のバウンディングボックスを検出する
3. 検出領域を低解像度に縮小し、再拡大してモザイク化する
4. 画像または動画として保存する

小さな顔の検出率を上げるため、デフォルトの推論サイズは `imgsz=960` に設定しています。  
用途に応じて、速度優先なら小さめ、検出重視なら大きめに調整できます。


## クイックスタート(エンジニア向け)

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


### macOS Distribution Notes

macOS では、署名や Notarization の有無によって初回起動時の挙動が変わります。

- GitHub Secrets が設定されている場合: `Developer ID` 署名と `Notarization` を実施
- 未設定の場合: `ad-hoc codesign` にフォールバック

後者では、利用者の環境でセキュリティ警告が表示される場合があります。  
非エンジニア向けに配布する場合は、workflow に必要な Secrets を設定した運用を推奨します。


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
