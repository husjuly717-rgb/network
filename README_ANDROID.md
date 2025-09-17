# Android APK build guide (Kivy + Buildozer)

This repo contains `main.py` (Kivy app) that replicates your original Tkinter app's encoding visualizations and is suitable for packaging as an Android APK using Buildozer.

## Option A) Build in GitHub Actions (no local Linux needed)
This repository includes a workflow at `.github/workflows/android-build.yml` that builds the APK in the cloud.

Steps:
1. Push your project to a GitHub repository.
2. Go to GitHub → Actions → run the workflow "Android APK (Buildozer)" (or push to `main`).
3. After it finishes, download the APK from the workflow run under "Artifacts" (file name like `apk-artifacts`).

## 1) Set up on Windows via WSL (recommended)
Buildozer officially targets Linux. On Windows, use WSL2 Ubuntu.

1. Install WSL2 and Ubuntu from Microsoft Store.
2. Open Ubuntu and install dependencies:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git openjdk-17-jdk zip unzip libffi-dev libssl-dev libbz2-dev libsqlite3-dev libncurses5-dev libncursesw5-dev libreadline-dev liblzma-dev
pip3 install --upgrade pip
pip3 install buildozer cython
```
3. In Ubuntu, clone or copy your project directory containing `main.py` and `buildozer.spec`.

## 2) Build the APK
From the project root (same folder as `buildozer.spec`):
```bash
buildozer android debug
```
The first build can take a long time. When it finishes, the APK will be in:
```
bin/encodingvisualizer-1.0.0-armeabi-v7a-debug.apk
```
(There may be one per architecture.)

## 3) Install on a device
Enable developer mode + USB debugging on your Android phone and connect via USB:
```bash
buildozer android deploy run
```
Or copy the APK to the device and install manually.

## 4) Notes
- Requirements in `buildozer.spec` are minimal: `python3,kivy`. If you add more packages, list them in `requirements`.
- If you need landscape orientation for more width, set `orientation = landscape` in `buildozer.spec`.
- For release builds:
```bash
buildozer android release
```
Then sign and align the APK per Buildozer docs.

## 5) Running locally (desktop)
You can test on desktop before building:
```bash
pip install kivy
python main.py
```

## 6) Original Tkinter app
The original `app.py` uses Tkinter + Matplotlib, which are not suitable for Android. The Kivy rewrite (`main.py`) reproduces the encoding logic and draws the digital waveforms using Kivy's Canvas API, making it portable to Android.
