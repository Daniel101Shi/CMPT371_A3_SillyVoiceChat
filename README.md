# SillyVoiceChat — UDP Walkie-Talkie

A real-time, peer-to-peer voice chat application built with Python and raw UDP sockets. Two users on the same local network can talk to each other like a walkie-talkie, with no central server required.

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

Each peer runs `app.py`, which opens a small **Tkinter GUI**. After entering the partner's IP and clicking Connect, the app uses three background threads managed by `NetworkLogic` (in `network.py`):

| Thread | Role |
|---|---|
| **Send thread** | Reads 1024-frame chunks from the microphone, prepends a 4-byte sequence number, and fires them over UDP to the partner. |
| **Receive thread** | Listens for incoming UDP packets, strips the sequence number, and inserts the audio chunk into a sorted **jitter buffer**. |
| **Playback thread** | Drains the jitter buffer to the speakers as soon as it holds ≥ 3 packets (~70 ms of audio). |

The **jitter buffer** compensates for UDP's lack of ordering guarantees. Packets are sorted before playback; late or duplicate packets (sequence number ≤ last played) are silently dropped.

---

## Prerequisites

- **Python 3.8 or newer** — [python.org/downloads](https://www.python.org/downloads/)
- **pip** — bundled with Python 3.4+
- **PortAudio** — system-level audio library required by PyAudio (see table below)
- **Tkinter** — comes bundled with the standard Python installer on all major platforms

### Install PortAudio

| Operating System | Command |
|---|---|
| **macOS** | `brew install portaudio` |
| **Ubuntu / Debian** | `sudo apt-get install portaudio19-dev python3-pyaudio` |
| **Windows** | No extra step needed — PyAudio's pip wheel bundles PortAudio |

> **macOS Apple Silicon (M1/M2/M3) Note:**  
> If Homebrew is installed at `/usr/local/` (Intel/Rosetta path), you may need to compile PyAudio for x86_64. See the [Installation](#installation) section for the fix.

---

## Installation

**1. Clone the repository:**
```bash
git clone https://github.com/Daniel101Shi/CMPT371_A3_SillyVoiceChat.git
cd CMPT371_A3_SillyVoiceChat
```

**2. (Optional but recommended) Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate.bat     # Windows
```

**3. Install Python dependencies:**
```bash
pip install -r requirements.txt
```

> **If `import pyaudio` fails on macOS** (symbol not found / architecture mismatch), force a local compile:
> ```bash
> pip uninstall -y pyaudio
> LDFLAGS="-L/usr/local/lib" CFLAGS="-I/usr/local/include" pip install --no-cache-dir pyaudio --no-binary :all:
> ```
> Then prefix every `python3` command below with `arch -x86_64`.

---

## Running the Application

> **Note:** All source files are located in the `src/` directory.

Both peers must be on the **same local network** (or the same machine for loopback testing).

There is **one way to run the application**: via `app.py`. Both peers run the same script.

### Step 1 — Launch the app

```bash
cd src
python3 app.py
```

> macOS Apple Silicon with Rosetta Homebrew:
> ```bash
> cd src
> arch -x86_64 python3 app.py
> ```

### Step 2 — Find and share your local IP

The app **automatically detects and displays your local IP** in the "Your IP" field at the top. Share this address with your partner (e.g., via text or chat).

You can also find it manually:
```bash
# macOS / Linux
ifconfig | grep "inet "

# Windows
ipconfig
```

### Step 3 — Connect

1. Enter your **partner's IP address** in the "Partner IP" field.
2. Click **Connect**.
3. The status bar turns **green** when the call is live.
4. Click **Disconnect** (same button) or close the window to end the call.

Both peers must connect to **each other's IP address** at the same time. Port `5000` is used automatically on both sides.

---

### Loopback Test (No Partner Needed)

Use this to verify that audio capture and playback work on a single machine.

```bash
cd src
python3 app.py
```

Tick the **"Loopback test (same machine)"** checkbox and click **Connect**. Both send and receive happen on `127.0.0.1:5000`. You will hear your own voice played back after the jitter-buffer delay (~70 ms).

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  app.py  — Tkinter GUI                                   │
│  Reads IP fields → creates NetworkLogic → calls start()  │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│  network.py  — NetworkLogic class                        │
│                                                          │
│  [send_loop thread]                                      │
│   mic.read(1024 frames)                                  │
│   header = struct.pack("!I", seq_num)  ← 4-byte header  │
│   sock.sendto(header + audio, partner_addr)              │
│                                                          │
│  [receive_loop thread]                                   │
│   data = sock.recvfrom(4096)                             │
│   seq = struct.unpack("!I", data[:4])                    │
│   if seq ≤ last_played_seq → drop (late / duplicate)    │
│   else → insert into jitter_buffer (kept sorted)         │
│   if len(buffer) ≥ 3 → pop oldest → audio_queue.put()   │
│                                                          │
│  [playback_loop thread]                                  │
│   audio_chunk = audio_queue.get()                        │
│   speaker_stream.write(audio_chunk)                      │
└──────────────────────────────────────────────────────────┘
```

### Packet Format

```
 0        3  4              N
 ┌────────┬──────────────────┐
 │seq_num │  raw PCM audio   │
 │ 4 bytes│  (1024 frames)   │
 └────────┴──────────────────┘
```

### Jitter & Ordering Strategy

| Problem | Solution |
|---|---|
| Out-of-order packets | 4-byte sequence number + sorted jitter buffer |
| Jitter (variable arrival delay) | Buffer holds 3 packets (~70 ms) before playing |
| Late or duplicate packets | Dropped if `seq_num ≤ last_played_seq` |
| Lost packets | Silent gap in audio; stream continues automatically |

---

## Limitations

- **LAN only** — both machines must be on the same local network. Internet calls would require manual port forwarding on each router, which is outside the scope of this project.
- **No encryption** — audio is transmitted as raw UDP plaintext. Not suitable for private conversations.
- **No retransmission** — UDP does not guarantee delivery. Dropped packets produce brief silence gaps; there is no recovery mechanism.
- **One-to-one only** — the application supports exactly two peers. Group calls are not supported.
- **Jitter buffer latency** — the 3-packet buffer introduces approximately 70 ms of intentional delay to smooth playback. Reducing `JITTER_BUFFER_SIZE` in `network.py` lowers latency but risks choppy audio on congested networks.
- **Default microphone only** — the app uses whatever PyAudio selects as the system's default input device. There is no in-app device selector.
- **Same port on both peers** — both sides listen and send on port `5000` (configurable via `DEFAULT_PORT` in `network.py`). If your OS or firewall blocks that port, the connection will silently fail.
- **Loopback limitation** — the GUI loopback mode (`127.0.0.1:5000 → 127.0.0.1:5000`) sends and receives on the same socket, so you hear your own voice echoed rather than a true two-peer exchange. Use the two-terminal method (two instances of `app.py`) to simulate two peers locally.
- **macOS Rosetta quirk** — Apple Silicon Macs using an Intel Homebrew installation may need the `arch -x86_64` prefix as documented above.
- **Microphone permission required** — on macOS and Windows, the OS may prompt for microphone access the first time the app runs. The app will hang silently if permission is denied.
