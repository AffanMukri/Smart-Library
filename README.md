# Smart Library Automation

A FastAPI, SQLite, React, and Python simulator-bridge project for library circulation and the hardware that actually exists in the Tinkercad prototype.

## Connection model

The Arduino Uno does not make HTTP requests to FastAPI. `simulator/simulator.py` is the **simulator bridge**. The device registry identifies every source:

- `TINKERCAD_SIMULATOR`: HC-SR04 #1, SG90 servo, LDR, LCD, piezo, LED #1, LED #2, and a push button reused as the shelf-presence switch.
- `WEB_CAMERA`: student ID OCR and book barcode/OCR.
- `SOFTWARE`: loans, fines, and automation logic.
- `NOT_CONNECTED`: HC-SR04 #2, which is required for physical directional occupancy detection.

No RFID reader, Arduino camera, temperature sensor, smoke detector, or other unlisted hardware is claimed.

## Setup and run

Use three PowerShell terminals from the project directory.

Backend:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Simulator bridge:

```powershell
cd simulator
python -m pip install -r requirements.txt
python simulator.py
```

Open `http://127.0.0.1:5173`. Camera access works on localhost. Allow browser camera permission when prompted. Tesseract English language data may be fetched and cached by the browser the first time OCR is used; manual ID/code entry remains available if OCR cannot initialize. API documentation is at `http://127.0.0.1:8000/docs`.

## Database and safe migration

The existing `backend/smart_library.db` is preserved. Startup uses additive SQLite migrations for new `system_state`, `events`, and `sensor_readings` columns, and creates these tables when absent:

- `students`: code, name, department, email, status, blocked state, borrowing limit.
- `books`: individual code, ISBN, title, author, category, shelf, status, cover URL.
- `loans`: student/book links, issue/due/return dates, status, and fine.

Demo students and books are inserted only when their respective tables are empty. Legacy count-based inventory, transactions, sensor history, and endpoints remain available. A pre-upgrade copy is kept under `backend/backups/`.

Demo defaults are 14 loan days and ₹5 per overdue day. These are project settings, not universal library rules.

## Main API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/dashboard` | Unified operational state and metrics |
| GET | `/api/devices` | Device capability/source registry |
| POST | `/api/sensor` | Backward-compatible and extended bridge telemetry |
| GET | `/api/device-command` | LCD, buzzer, LED, light, and door desired state |
| GET/POST | `/api/events`, `/api/event` | Extended event log / legacy event input |
| GET | `/api/students` | Registered students |
| GET | `/api/students/{student_code}` | Student, active-loan, and fine summary |
| POST | `/api/students/identify` | Resolve OCR/manual text to a student |
| GET | `/api/books` | Legacy counts plus individual `items` |
| GET | `/api/books/{book_code}` | Book by code |
| GET | `/api/books/isbn/{isbn}` | Book by ISBN |
| POST | `/api/books/identify` | Resolve barcode/OCR/manual code |
| POST | `/api/books/issue`, `/api/books/return` | Legacy count-based operations |
| GET | `/api/loans` | Loans with calculated status/fine |
| GET | `/api/loans/active`, `/api/loans/overdue` | Filtered circulation lists |
| GET | `/api/students/{student_code}/loans` | Student history |
| POST | `/api/loans/issue`, `/api/loans/return` | Individual circulation transactions |
| POST | `/api/occupancy` | Explicit software-simulated entry/exit |
| POST | `/api/shelf` | Push-button shelf presence transition |
| POST | `/api/security/clear` | Clear alarm outputs and LCD state |
| GET | `/api/settings` | Fine and loan demo defaults |

## Exact demo sequence

1. Start backend, frontend, and simulator bridge. Open **Devices** and show that Sensor B is `NOT CONNECTED`, browser scanners are `WEB CAMERA`, and actual circuit components are `SIMULATED` through the bridge.
2. Open **Smart Checkout**, enable the camera, scan a card containing `23IT101`, or enter it manually. Show the OCR confidence and verified student.
3. Scan the ISBN barcode for BOOK001 (`9780133970777`), OCR `BOOK001`, or enter it manually. Show title, author, shelf, and availability.
4. Review all eligibility checks and press **Issue book**. Show the success screen, then **Loans**, **Activity**, and the LCD state (`Book Issued` / due date).
5. In the simulator select `7` within ten seconds of checkout. This is an authorized shelf removal and must not alarm.
6. Select `8`, wait for the authorization window to expire, then select `7`. Show the security alert, piezo ON, LED #2 ON, LCD alarm, and **Smart Shelf** page. Select `12` to clear it.
7. Select `5` for `PERSON_ENTERED`, then `9` for darkness. Occupancy becomes 1 and LED #1/lights become ON.
8. Select `6` for `PERSON_EXITED` while it remains dark. Occupancy becomes 0 and lights turn OFF for energy saving.
9. For an overdue-return demonstration, use the API docs to call `POST /api/loans/return` with a future `returned_at`, or adjust the loan due date in a demo database. The response and Loans page show overdue days and ₹5/day fine.
10. Use simulator option `13` to display the current bridge state and LCD output.

## Simulator menu

The menu supports student/book scans, issue/return, explicit entry/exit, shelf removal/restoration, dark/bright environments, alarm trigger/clear, and full state display. Telemetry continues posting at `POLL_INTERVAL_SECONDS` (default two seconds).

## Verification

```powershell
cd backend
python -m compileall -q app

cd ..\simulator
python -m compileall -q simulator.py

cd ..\frontend
npm run lint
npm run build
```

## Current limitations and required hardware

- Polling at 1.5 seconds is retained for reliability; there is no WebSocket/SSE dependency.
- Browser `BarcodeDetector` availability varies. Tesseract OCR and manual correction are the fallback.
- OCR quality depends on focus, lighting, card design, and font; IDs remain the primary database key.
- Energy savings are clearly labeled estimates based on automation state, not physical meter measurements.
- Add a second HC-SR04 to move occupancy from `SOFTWARE_SIMULATION` to physical A→B/B→A directional detection.
- Add a network-capable bridge or serial gateway if future hardware must communicate with FastAPI outside the current Python simulator bridge.
