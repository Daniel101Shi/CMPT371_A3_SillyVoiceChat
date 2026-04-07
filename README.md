# SillyVoiceChat — UDP Walkie-Talkie

A real-time, peer-to-peer voice chat application built with Python and raw UDP sockets. Two users on the same local network can talk to each other like a walkie-talkie, with no server required.

> **CMPT 371 — Assignment 3**
> Made by **Daniel Shi** (Networking & Threading) & **Vincent** (Audio & UI)

---

## 📋 Table of Contents
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Architecture](#architecture)
- [Limitations](#limitations)

---

## How It Works

Each peer runs one Python script that has **two threads running simultaneously**:

- **Send Thread (main):** Reads raw audio from your microphone in 1024-frame chunks, attaches a 4-byte sequence number header, and blasts it out over UDP.
- **Receive Thread (background daemon):** Listens for incoming UDP packets, strips the sequence number, and places the chunk into a **Jitter Buffer**. Once the buffer holds 3 packets, it pops the oldest one and writes it to your speakers.

The **Jitter Buffer** is how we handle UDP's lack of ordering guarantees. Because UDP packets can arrive out of order, we wait and sort them before playing. Late or duplicate packets (those with a sequence number ≤ the last played one) are silently dropped.

---

## Prerequisites

- **Python 3.8+**
- **PortAudio** (system-level audio library, required by PyAudio)

### Install PortAudio

| Operating System | Command |
|---|---|
| **macOS** | `brew install portaudio` |
| **Ubuntu / Debian** | `sudo apt-get install portaudio19-dev python3-pyaudio` |
| **Windows** | No extra step needed — PyAudio's wheel includes PortAudio |

> **macOS Apple Silicon (M1/M2/M3) Note:**
> If your Mac uses an Apple Silicon chip but your Homebrew is installed at `/usr/local/` (Intel/Rosetta), you may need to compile PyAudio for x86_64 and run with `arch -x86_64`. See the Installation section below.

---

## Installation

**1. Clone the repository:**
```bash
git clone https://github.com/Daniel101Shi/CMPT371_A3_SillyVoiceChat.git
cd CMPT371_A3_SillyVoiceChat
```

**2. Install Python dependencies:**
```bash
pip install -r requirements.txt
```

> **If `import pyaudio` fails on macOS** (symbol not found / architecture error), run this instead to force a local compile:
> ```bash
> pip uninstall -y pyaudio
> LDFLAGS="-L/usr/local/lib" CFLAGS="-I/usr/local/include" pip install --no-cache-dir pyaudio --no-binary :all:
> ```
> Then run all Python commands prefixed with `arch -x86_64` (see examples below).

---

## Running the Application

Both users must be on the same local network (or the same machine for testing).

### Step 1 — Find Your Local IP Address

```bash
# macOS / Linux
ifconfig | grep "inet "

# Windows
ipconfig
```

### Step 2 — Edit the config at the top of `backend/network.py`

Open `backend/network.py` and set:
```python
LOCAL_IP = "0.0.0.0"       # Listen on all interfaces
LOCAL_PORT = 5000           # The port YOU listen on
TARGET_IP = "192.168.X.X"  # Your PARTNER's IP address
TARGET_PORT = 5000          # The port your PARTNER listens on
```

Your partner does the same thing in their copy, pointing `TARGET_IP` back at you.

### Step 3 — Run

**Standard (most machines):**
```bash
cd backend
python3 network.py
```

**macOS Apple Silicon with Rosetta Homebrew:**
```bash
cd backend
arch -x86_64 python3 network.py
```

Press `Ctrl+C` to quit cleanly.

---

### Local Loopback Test (Single Machine, No Partner Needed)

To test that everything works by yourself, open **two terminals**.

**Terminal 1 — `network.py` (listens on 5000, sends to 5001):**
```bash
cd backend
# Edit LOCAL_PORT = 5000, TARGET_PORT = 5001 in network.py first
python3 network.py
```

**Terminal 2 — `CLIENT_B.py` (listens on 5001, sends to 5000):**
```bash
cd backend
# CLIENT_B.py already has LOCAL_PORT = 5001, TARGET_PORT = 5000
python3 CLIENT_B.py
```

Speak into your mic — you will hear your own voice played back after a brief jitter-buffer delay (~70 ms).

---

## Architecture

```
┌──────────────────────────────────────────────┐
│  network.py (each peer runs this)            │
│                                              │
│  [Main Thread — Sender]                      │
│   mic.read(1024 frames)                      │
│   struct.pack("!I", seq_num) → 4-byte header │
│   packet = header + audio_bytes              │
│   sock.sendto(packet, partner)               │
│                                              │
│  [Daemon Thread — Receiver]                  │
│   data = sock.recvfrom(4096)                 │
│   seq = struct.unpack("!I", data[:4])        │
│   if seq ≤ last_played → drop (late/dup)     │
│   else → insert into jitter_buffer (sorted)  │
│   if len(buffer) ≥ 3 → pop oldest           │
│                      → speaker.write(audio)  │
└──────────────────────────────────────────────┘
```

### Jitter & Ordering Strategy

| Problem | Our Solution |
|---|---|
| Out-of-order packets | 4-byte sequence number header + sorted jitter buffer |
| Jitter (variable arrival time) | Buffer holds 3 packets (~70 ms) before playing, smoothing variance |
| Late packets | Dropped if `seq_num ≤ last_played_seq` |
| Duplicate packets | Same check — silently discarded |
| Lost packets | Gap results in brief silence; audio stream continues |

---

## Limitations

- **LAN only** — requires both machines on the same network (or manual port forwarding for internet use).
- **No encryption** — audio bytes are transmitted as raw UDP plaintext. Not suitable for private conversations.
- **No retransmission** — UDP does not resend lost packets. Network congestion will cause brief silence gaps.
- **One-to-one only** — the application only supports two peers simultaneously.
- **Jitter buffer latency** — the 3-packet buffer adds approximately 70 ms of intentional delay to smooth playback.
- **Microphone required** — the application assumes a default system microphone is available and accessible.
- **macOS Rosetta quirk** — Apple Silicon Macs using Intel Homebrew may need `arch -x86_64` prefix (documented above).
