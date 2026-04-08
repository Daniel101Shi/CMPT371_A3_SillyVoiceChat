# **CMPT 371 A3 Socket Programming `SillyVoiceChat`**

**Course:** CMPT 371 — Data Communications & Networking  
**Instructor:** Mirza Zaeem Baig  
**Semester:** Spring 2026  

---

## **Group Members**

| Name | Student ID | Email |
| :---- | :---- | :---- |
| Daniel Shi | 301594914 | dsa179@sfu.ca |
| Vincent | 301600805 | viw@sfu.ca |

---

## **1. Project Overview & Description**

SillyVoiceChat is a real-time, peer-to-peer voice chat application built using Python's raw UDP socket API. Two users on the same local network can talk to each other like a walkie-talkie with no central server required.

Each peer runs `app.py`, which opens a **Tkinter GUI**. After entering the partner's IP and clicking Connect, the app spins up three background threads managed by `NetworkLogic` (in `network.py`):

| Thread | Role |
| :---- | :---- |
| **Send thread** | Reads 1024-frame chunks from the microphone, prepends a 4-byte sequence number, and fires them over UDP to the partner. |
| **Receive thread** | Listens for incoming UDP packets, strips the sequence number, and inserts the audio chunk into a sorted **jitter buffer**. |
| **Playback thread** | Drains the jitter buffer to the speakers once it holds ≥ 3 packets (~70 ms of audio). |

The **jitter buffer** compensates for UDP's lack of ordering guarantees. Packets are sorted before playback; late or duplicate packets (sequence number ≤ last played) are silently dropped.

### Packet Format

```
 0        3  4              N
 ┌────────┬──────────────────┐
 │seq_num │  raw PCM audio   │
 │ 4 bytes│  (1024 frames)   │
 └────────┴──────────────────┘
```

---

## **2. System Limitations & Edge Cases**

As required by the project specifications, we have identified and handled (or defined) the following limitations and potential issues:

* **Out-of-Order UDP Packets:**
  * <span style="color: green;">*Solution:*</span> Each packet is prefixed with a 4-byte sequence number. The receive thread inserts incoming packets into a sorted jitter buffer before popping them for playback, ensuring audio is always played in order.
  * <span style="color: red;">*Limitation:*</span> Packets that arrive after the buffer has already played their sequence position are permanently dropped; there is no retransmission mechanism.

* **Jitter (Variable Network Delay):**
  * <span style="color: green;">*Solution:*</span> The jitter buffer holds at least 3 packets (~70 ms) before starting playback. This smooths out bursts and variable arrival times.
  * <span style="color: red;">*Limitation:*</span> The 3-packet buffer is a fixed constant (`JITTER_BUFFER_SIZE` in `network.py`). On high-jitter networks it may still be insufficient; on very stable LAN connections it adds unnecessary latency.

* **Lost Packets:**
  * <span style="color: red;">*Limitation:*</span> UDP provides no delivery guarantee. A lost packet produces a brief silence gap in the audio; the stream automatically resumes on the next received packet. There is no error recovery.

* **Race Conditions on the Jitter Buffer:**
  * <span style="color: green;">*Solution:*</span> The receive thread acquires a `threading.Lock` (`jitter_lock`) before reading or writing the jitter buffer, preventing data corruption from concurrent access.

* **LAN-Only Connectivity:**
  * <span style="color: red;">*Limitation:*</span> Both machines must be on the same local network. Internet calls require manual port forwarding on each router, which is outside the scope of this project.

* **No Encryption:**
  * <span style="color: red;">*Limitation:*</span> Audio is transmitted as raw UDP plaintext. This is not suitable for private conversations.

* **One-to-One Only:**
  * <span style="color: red;">*Limitation:*</span> The application supports exactly two peers. Group calls are not supported.

* **Default Microphone & Port:**
  * <span style="color: red;">*Limitation:*</span> The app uses the system's default PyAudio input device — there is no in-app device selector. Both peers must have port `5000` open (configurable via `DEFAULT_PORT` in `network.py`). If a firewall blocks this port, the connection will silently fail.

* **Loopback Limitation:**
  * <span style="color: red;">*Limitation:*</span> The GUI loopback mode (`127.0.0.1:5000 → 127.0.0.1:5000`) sends and receives on the same socket, so you hear your own voice echoed rather than a true two-peer exchange. It is only useful for verifying that audio hardware is working.

* **Microphone Permission:**
  * <span style="color: red;">*Limitation:*</span> On macOS and Windows, the OS may prompt for microphone access the first time the app runs. The app will hang silently if permission is denied.

---

## **3. Video Demo**

[ Watch Project Demo ](voice_chat_demonstration.mp4)

---

## **4. Prerequisites (Fresh Environment)**

To run this project, you need:

* **Python 3.8 or newer** — [python.org/downloads](https://www.python.org/downloads/)
* **pip** — bundled with Python 3.4+
* **PortAudio** — a system-level audio library required by PyAudio
* **Tkinter** — bundled with the standard Python installer on all major platforms
* **PyAudio** — listed in `requirements.txt`, installed via pip

### Install PortAudio (system dependency — required before pip install)

| Operating System | Command |
| :---- | :---- |
| **macOS** | `brew install portaudio` |
| **Ubuntu / Debian** | `sudo apt-get install portaudio19-dev python3-pyaudio` |
| **Windows** | No extra step needed — PyAudio's pip wheel bundles PortAudio |

> **macOS Apple Silicon (M1/M2/M3) Note:**  
> If you see an architecture mismatch error when importing PyAudio, see the fix in Step 3 of the run guide below.

---

## **5. Step-by-Step Run Guide**


### **Step 1: Clone the Repository**

```bash
git clone https://github.com/Daniel101Shi/CMPT371_A3_SillyVoiceChat.git
cd CMPT371_A3_SillyVoiceChat
```

### **Step 2: (Optional) Create a Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate.bat     # Windows
```

### **Step 3: Install Python Dependencies**

```bash
pip install -r requirements.txt
```

> **If `import pyaudio` fails on macOS** (symbol not found / architecture mismatch), force a source compile:
> ```bash
> pip uninstall -y pyaudio
> LDFLAGS="-L/usr/local/lib" CFLAGS="-I/usr/local/include" pip install --no-cache-dir pyaudio --no-binary :all:
> ```
> Then prefix every `python3` command below with `arch -x86_64`.

### **Step 4: Launch the App — Peer A**

Navigate to the `src/` directory and run the app. **Both peers run the exact same script.**

```bash
cd src
python3 app.py
# A small GUI window opens.
# The "Your IP" field displays your local IP address automatically.
```

> macOS Apple Silicon with Rosetta Homebrew:
> ```bash
> cd src
> arch -x86_64 python3 app.py
> ```

### **Step 5: Launch the App — Peer B**

On the **second machine** (or a second terminal for loopback testing), run the same command:

```bash
cd src
python3 app.py
```

### **Step 6: Share IPs and Connect**

1. Each peer reads their local IP from the **"Your IP"** label in the GUI.  
   You can also find it manually:
   ```bash
   # macOS / Linux
   ifconfig | grep "inet "
   # Windows
   ipconfig
   ```
2. Each peer types the **other person's IP** into the **"Partner IP"** field.
3. Both peers click **Connect**.
4. The status bar turns **green** and displays `Connected → <partner_ip>:5000`.
5. Speak into your microphone — you will hear each other in real time.
6. Click **Disconnect** (same button) or close the window to end the call.

---

### **Loopback Test (No Partner / Single Machine)**

Use this to verify audio hardware and the application without a second computer.

```bash
cd src
python3 app.py
```

Tick the **"Loopback test (same machine)"** checkbox and click **Connect**. Both send and receive happen on `127.0.0.1:5000`. You will hear your own voice played back after the jitter-buffer delay (~70 ms).

---

## **6. Technical Details**

### Architecture

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

### Jitter & Ordering Strategy

| Problem | Solution |
| :---- | :---- |
| Out-of-order packets | 4-byte sequence number + sorted jitter buffer |
| Jitter (variable arrival delay) | Buffer holds 3 packets (~70 ms) before playing |
| Late or duplicate packets | Dropped if `seq_num ≤ last_played_seq` |
| Lost packets | Silent gap in audio; stream continues automatically |

---

## **7. Academic Integrity & References**

* **Code Origin:**
  * The UDP socket setup and PyAudio streaming pipeline were written by the group from scratch. The jitter buffer ordering and threading architecture were designed specifically for this assignment.
* **GenAI Usage:**
  * Gemini was used to assist with `README.md` writing and polishing.
* **References:**
  * [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)
  * [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/docs/)
  * [Real Python: Intro to Python Threading](https://realpython.com/intro-to-python-threading/)
