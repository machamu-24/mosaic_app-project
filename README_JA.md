# モザイク処理アプリ (Mosaic App) 利用手順書

本書では、このアプリケーション（ローカルデスクトップ版 および Webブラウザ版）の起動方法と使い方について説明します。

---

## 💻 1. ローカルでの実行

### 前提条件 (必須環境)
*   **Python 3.9 以上** がインストールされていること。（※AIモデルである YOLOv8 の実行に必須となります）

### ターミナルの準備
Macをお使いの場合は「ターミナル」アプリを開き、アプリケーションのフォルダ（`mosaic_app-project`）に移動し、仮想環境を有効化してください。

```bash
cd /Users/machamu/mosaic_app-project
source .venv/bin/activate
```
※コマンド入力箇所が `(.venv)` で始まっていれば準備完了です。

### 1-A: デスクトップ用アプリ (GUI) を使う場合
直感的な画面（ウィンドウ）で操作できる軽量版です。

**起動コマンド:**
```bash
python gui_app.py
```

**使い方:**
1.  **Input File:** 「Browse...」ボタンを押し、モザイクをかけたい動画（.mp4/.mov）や画像（.jpg/.png）を選択します。
2.  **Output File:** 自動的に保存場所（ファイル名に `_masked` が付きます）が入力されますが、必要に応じて「Browse...」から変更できます。
3.  **Mosaic Block Size:** モザイクの粗さを調整します。数字が大きいほどモザイクが強くなります（初期値：20）。
4.  **Run Processing:** 実行ボタンを押します。一番下に進捗メッセージが表示され、完了するとポップアップでお知らせします。

---

### 1-B: Webブラウザ版アプリ (Streamlit) を使う場合
ブラウザ上でモダンなインターフェースを使って操作・確認ができるため、人に説明したりデモを見せたりするのに最適です。

**起動コマンド:**
```bash
streamlit run app.py
```

**使い方:**
1.  コマンドを実行すると、自動的にブラウザが開きアプリ（ `http://localhost:8501` ）が表示されます。
2.  **ファイルアップロード:** 点線で囲まれたエリアにファイルをドラッグ＆ドロップ、または「Browse files」から選択します。
3.  **左側メニュー (Settings):** スライダーでモザイクの強さを調整できます。（※Advanced Settingsは通常は触らなくて大丈夫です）
4.  **適用:** 「Apply Mosaic」ボタンをクリックします。
5.  **ダウンロード:** 処理完了後、画面上に結果が表示されるとともに「Download Masked...」というボタンが出現します。こちらから保存可能です。

**終了方法:**
ブラウザ画面を閉じた後、ターミナルで `Ctrl + C` キーを押すと実行状態を終了できます。

---

## 🌐 2. 外部へのWeb公開 (Streamlit Community Cloud共有)

上司や他のスタッフのパソコンからでもアクセスできるよう、URLを発行する方法です。

**前提:** このプロジェクトがご自身のGitHubリポジトリ（`main` ブランチ）に最新の状態でプッシュされている必要があります。

1.  **ログイン:** [Streamlit Community Cloud](https://streamlit.io/)（ https://streamlit.io/ ） にアクセスし、右上の「Login」からご自身のGitHubアカウントでログインします。
2.  **新規アプリ作成:** 画面右上の青い **「New app」** ボタンをクリックします。
3.  連携画面で以下のように設定します。
    *   **Repository:** 今回のGitHubリポジトリ（例: `machamu-24/mosaic_app-project`）を選択
    *   **Branch:** `main` を選択
    *   **Main file path:** `app.py` と入力
4.  **デプロイ:** 右下の **「Deploy!」** ボタンをクリックします。

数分待つと自動でサーバーが立ち上がり、ブラウザ上でアプリが開きます。
ブラウザ上部に表示されているURL（例: `https://xxxxxx.streamlit.app`）をコピーし、他のスタッフに共有してください。

*(※無料クラウドサーバーはスペックが制限されているため、Web公開時に長時間の動画を処理しようとするとエラーが発生する可能性があります。デモ目的の場合は、数秒間の短いテスト動画を使用することをお勧めします。実業務での長時間処理は、上記「1. ローカルでの実行」をご利用ください)*

---

## 📦 3. GitHub ActionsでZIP配布 (Mac / Windows)

このリポジトリには、タグ push をきっかけにデスクトップアプリを自動ビルドし、ZIP形式で配布できる GitHub Actions ワークフロー（`.github/workflows/build_desktop.yml`）が含まれています。

### 3-1. リリース用タグを作成して push する

```bash
git tag v1.0.0
git push origin v1.0.0
```

### 3-2. 自動ビルドされる内容

- Windows (`windows-latest`) と macOS (`macos-latest`) を並列ビルド
- 生成物を ZIP 化
- GitHub Actions の Artifacts にアップロード
- タグ実行時は GitHub Releases に ZIP を自動添付

ZIPファイル名の例:

- `MosaicApp-v1.0.0-windows-x64.zip`
- `MosaicApp-v1.0.0-macos.zip`

### 3-3. 配布方法

GitHub の **Releases** 画面を開き、対象バージョンの ZIP をそのまま配布してください。

### 3-4. macOS で初回起動時に警告が出る場合

未Notarizeのアプリを配布する場合、macOSで初回起動時にセキュリティ警告が表示されることがあります。  
`ゴミ箱に入れる` は押さず、`完了` で閉じてから以下を実行してください。

```bash
APP="/展開先/MosaicApp"
xattr -dr com.apple.quarantine "$APP"
"$APP/MosaicApp"
```

`Python.framework` を削除・ゴミ箱移動した場合は復旧できないため、ZIPを再展開してください。

### 3-5. 非エンジニア向けに「警告なし配布」するには (推奨)

GitHub Secrets に以下を設定すると、Actions が macOS 版を **Developer ID署名 + Notarization** し、利用者はターミナル操作なしで起動しやすくなります。

- `MACOS_CERTIFICATE_P12_BASE64`
- `MACOS_CERTIFICATE_PASSWORD`
- `MACOS_CODESIGN_IDENTITY` (例: `Developer ID Application: ...`)
- `MACOS_NOTARY_APPLE_ID`
- `MACOS_NOTARY_TEAM_ID`
- `MACOS_NOTARY_PASSWORD` (app-specific password)

これらが未設定の場合は、ワークフローは自動で ad-hoc 署名にフォールバックします（警告が出る可能性あり）。
