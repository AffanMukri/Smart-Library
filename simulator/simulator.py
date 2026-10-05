"""Interactive simulator bridge for the Smart Library FastAPI backend.

This is a communication/simulation layer for the listed Tinkercad components;
it is not direct HTTP communication from an Arduino Uno.
"""
from dataclasses import dataclass
import os, random
from threading import Event, Lock, Thread
import httpx
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
SENSOR_INTERVAL_SECONDS = float(os.getenv("POLL_INTERVAL_SECONDS", "2"))
REQUEST_TIMEOUT, MAX_BOOKS = 5.0, 5

@dataclass
class LibraryState:
    distance: float = 50.0
    light: int = 700
    books: int = MAX_BOOKS
    occupancy: int = 0
    shelf_present: bool = True
    shelf_book_code: str | None = "BOOK001"
    security_alert: bool = False
    buzzer: str = "OFF"
    security_led: str = "OFF"
    lcd_line_1: str = "Smart Library"
    lcd_line_2: str = "System Ready"
    last_student_id: str | None = None
    last_book_id: str | None = None
    @property
    def door(self): return "OPEN" if self.distance <= 20 else "CLOSED"
    @property
    def lights(self): return "ON" if self.light < 500 and self.occupancy > 0 else "OFF"
    def payload(self):
        return {"distance": self.distance, "light": self.light, "books": self.books, "door": self.door,
                "lights": self.lights, "occupancy": self.occupancy, "shelf_present": self.shelf_present,
                "shelf_book_code": self.shelf_book_code, "security_alert": self.security_alert,
                "buzzer": self.buzzer, "security_led": self.security_led, "lcd_line_1": self.lcd_line_1,
                "lcd_line_2": self.lcd_line_2, "last_student_id": self.last_student_id, "last_book_id": self.last_book_id}

class SmartLibrarySimulator:
    def __init__(self):
        self.state, self.client, self.lock = LibraryState(), httpx.Client(timeout=REQUEST_TIMEOUT), Lock()
        self._stop, self._sensor_thread = Event(), None
    def start_periodic_sensors(self):
        self._sensor_thread = Thread(target=self._loop, daemon=True); self._sensor_thread.start()
    def _loop(self):
        while not self._stop.wait(SENSOR_INTERVAL_SECONDS): self.post_sensor(); self.sync_commands()
    def close(self):
        self._stop.set()
        if self._sensor_thread: self._sensor_thread.join(timeout=REQUEST_TIMEOUT + 1)
        self.client.close()
    def request(self, method, path, payload=None, quiet=False):
        try:
            response = self.client.request(method, f"{BACKEND_URL}{path}", json=payload); response.raise_for_status()
            data = response.json()
            if not quiet: print(f"[BRIDGE] {method} {path} OK")
            return data
        except httpx.HTTPStatusError as exc:
            try: detail = exc.response.json().get("detail", exc.response.text)
            except ValueError: detail = exc.response.text
            print(f"[ERROR] Backend returned {exc.response.status_code}: {detail}")
        except httpx.RequestError as exc: print(f"[ERROR] Cannot reach {BACKEND_URL}: {exc}")
        return None
    def post_sensor(self):
        with self.lock: payload = self.state.payload()
        data = self.request("POST", "/api/sensor", payload, quiet=True)
        return data is not None
    def sync_backend(self):
        data = self.request("GET", "/api/dashboard", quiet=True)
        if not data: return
        with self.lock:
            for key in ("books", "occupancy", "shelf_present", "shelf_book_code", "security_alert", "buzzer", "security_led", "lcd_line_1", "lcd_line_2", "last_student_id", "last_book_id"):
                if key in data: setattr(self.state, key, data[key])
        print(f"[SYNC] Inventory {self.state.books}/{MAX_BOOKS}; occupancy {self.state.occupancy}")
    def sync_commands(self):
        data = self.request("GET", "/api/device-command", quiet=True)
        if data:
            with self.lock:
                for key in ("lcd_line_1", "lcd_line_2", "buzzer", "security_led"):
                    setattr(self.state, key, data[key])
    def scan_student(self):
        code = input("Student ID (demo: 23IT101): ").strip() or "23IT101"
        data = self.request("POST", "/api/students/identify", {"text": code, "confidence": 1.0})
        if data:
            self.state.last_student_id = data["student_code"]; print(f"[STUDENT] {data['name']} verified ({data['student_code']})")
    def scan_book(self):
        code = input("Book code or ISBN (demo: BOOK001): ").strip() or "BOOK001"
        data = self.request("POST", "/api/books/identify", {"code": code})
        if data:
            self.state.last_book_id = data["book_code"]; self.state.shelf_book_code = data["book_code"]
            self.state.lcd_line_1, self.state.lcd_line_2 = "Book Scanned", data["book_code"][:16]
            print(f"[BOOK] {data['title']} - {data['status']}")
    def issue_book(self):
        student = self.state.last_student_id or input("Student ID: ").strip()
        book = self.state.last_book_id or input("Book code: ").strip()
        if not student or not book: print("[INPUT] Scan or enter student and book first."); return
        data = self.request("POST", "/api/loans/issue", {"student_code": student, "book_code": book})
        if data: self.sync_backend(); print(f"[LOAN] Issued {data['book']} to {data['student']}; due {data['due_at']}")
    def return_book(self):
        book = self.state.last_book_id or input("Book code: ").strip()
        if not book: print("[INPUT] Scan or enter a book first."); return
        data = self.request("POST", "/api/loans/return", {"book_code": book})
        if data: self.sync_backend(); print(f"[RETURN] Fine Rs {data['fine_amount']:.0f}")
    def person(self, entered):
        event = "PERSON_ENTERED" if entered else "PERSON_EXITED"; data = self.request("POST", "/api/occupancy", {"event": event})
        if data: self.state.occupancy = data["occupancy"]; print(f"[OCCUPANCY] {self.state.occupancy} (SOFTWARE SIMULATION)")
    def shelf(self, present):
        data = self.request("POST", "/api/shelf", {"present": present, "book_code": self.state.shelf_book_code})
        if data:
            self.state.shelf_present, self.state.security_alert = data["shelf_present"], data["security_alert"]
            self.state.buzzer, self.state.security_led = data["buzzer"], data["security_led"]
            print(f"[SHELF] {'PRESENT' if present else 'REMOVED'}; security {'ALERT' if data['security_alert'] else 'SAFE'}")
    def set_light(self, dark):
        self.state.light = random.randint(100, 450) if dark else random.randint(550, 1000); self.post_sensor()
        print(f"[LDR] {self.state.light}; lights {self.state.lights} (occupancy-aware)")
    def trigger_alarm(self):
        self.shelf(True); self.shelf(False)
    def clear_alarm(self):
        if self.request("POST", "/api/security/clear", {}): self.sync_backend(); print("[SECURITY] Alarm cleared")
    def show_status(self):
        self.sync_backend(); print("\n--- CURRENT SYSTEM STATE ---")
        for label, value in (("Distance", f"{self.state.distance:.1f} cm"), ("Door", self.state.door), ("LDR", self.state.light), ("Occupancy", self.state.occupancy), ("Lights", self.state.lights), ("Books", f"{self.state.books}/{MAX_BOOKS}"), ("Shelf", "PRESENT" if self.state.shelf_present else "REMOVED"), ("Security", "ALERT" if self.state.security_alert else "SAFE"), ("Buzzer", self.state.buzzer), ("Security LED", self.state.security_led), ("LCD", f"{self.state.lcd_line_1} | {self.state.lcd_line_2}")): print(f"{label:12}: {value}")

MENU = """
Smart Library Simulator Bridge
1  Scan student                 8  Book restored to shelf
2  Scan book                    9  Environment dark
3  Issue book                  10  Environment bright
4  Return book                 11  Trigger security alarm
5  Person enters               12  Clear security alarm
6  Person exits                13  Show current system state
7  Book removed from shelf      0  Exit
"""
def run():
    simulator = SmartLibrarySimulator()
    actions = {"1": simulator.scan_student, "2": simulator.scan_book, "3": simulator.issue_book, "4": simulator.return_book, "5": lambda: simulator.person(True), "6": lambda: simulator.person(False), "7": lambda: simulator.shelf(False), "8": lambda: simulator.shelf(True), "9": lambda: simulator.set_light(True), "10": lambda: simulator.set_light(False), "11": simulator.trigger_alarm, "12": simulator.clear_alarm, "13": simulator.show_status}
    print(f"Simulator bridge connected to {BACKEND_URL}"); simulator.sync_backend(); simulator.post_sensor(); simulator.start_periodic_sensors()
    try:
        while True:
            print(MENU); choice = input("Select an option: ").strip()
            if choice == "0": break
            action = actions.get(choice)
            if action: action()
            else: print("[INPUT] Invalid option. Enter 0-13.")
    except (KeyboardInterrupt, EOFError): print("\nSimulator stopped.")
    finally: simulator.close()
if __name__ == "__main__": run()
