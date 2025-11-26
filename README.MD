
# SLE Suite PRO

SLE Suite PRO is an advanced tool for reading, analyzing, editing, and authenticating synchronous memory cards from the **SLE** family (SLE4442, SLE5542, SLE4428, SLE5528), using compatible **PC/SC** readers such as the *ACS ACR39U*.

---

## **Version 0.0.3**

### New Features & Improvements

- **Full support for reading and writing protection bits**  
  - Correct decoding of the Protection Memory.  
  - Safe, irreversible bit-write operations with confirmation.  
  - Automatic refresh of the protection table after each change.

- **Complete fix of the translation system (i18n)**  
  - All UI elements and internal logs now follow the selected language.  
  - Unified translation pipeline (UI + backend).  
  - Removed leftover Spanish text.

- **Reader moved to a dedicated background thread**  
  - The UI no longer freezes during read/write operations.  
  - Long tasks (memory reading, PSC operations) are now fully asynchronous.  
  - Improved stability when connecting/disconnecting PC/SC readers.

- **General UX and stability improvements**  
  - Faster log panel rendering with refined color scheme.  
  - Better PC/SC reader detection.  
  - Internal code optimizations for page refresh and data tables.

## **TODO**

- **Improve auth detection, sometimes say "auth ok" but still not authenticated**

- **Acquire SLE5542 and SLE5528 cards**  
  Required for real-world testing of protection bits and write operations on these models.

- **Implement driver support for additional PC/SC readers**  
  Extend compatibility beyond ACS ACR39U and improve cross-platform detection.

- **Interactive HEX editor highlighting**  
  Allow users to colorize specific bytes, ranges, or patterns directly inside the memory viewer.

- **Customizable UI color themes**  
  Add a configuration panel to pick accents, background colors, or full theme presets.

- **Amazing future features**  
  Research and prototype advanced tools to take SLE Suite PRO further.



## Main Features



### ✔ Full SLE Card Reading
- Full support for:

- **SLE4442 / SLE5542** (256 bytes + security + protection)

- **SLE4428 / SLE5528** (1024 bytes + protection bits)
- Range reading or full memory reading.

- Automatic decoding of ATR, Protection Memory, and Security Memory.

### ✔ Secure Write
- Page or byte writing.

- System that prevents destructive operations (e.g., *protect byte*) without confirmation.

- Authentication status validation before modifying EEPROM.

### ✔ Secure PSC Authentication
- Full compatibility with ACS commands:

-  → Read Security Memory

-  → Authenticate PSC

- → Change PSC and write memory
- Prevents accidental decrease of the **error counter** on SLE4442 cards.

- “Read-only safe” mode to detect visible PSCs without risk.

### ✔ Modern GUI with PySide6
- Clean, dark/light design.

- Log panel with timestamps.

- Tabs for:

- Main card view

- Chip information (ChipData)
- Real-time status indicators.

### ✔ Dynamic language system (i18n)
- The application automatically detects the available `.json` files in `/i18n/`.

- Persistent language change (requires restart).

- Initial support for:

- Spanish

- English

- Portuguese

- French

- German

(Expandable by adding a JSON file)

---


---

## Basic Operation

### 1. Launch the application
```
python app.py
```

### 2. Select reader
The program automatically detects compatible PC/SC readers.

### 3. Read card
When you press **Read Card**:
- The type (4442/4428) is automatically detected.

- The entire memory is read.

- The view is updated with HEX/ASCII content.

### 4. Authenticate PSC
On the control panel:
- Enter PSC (e.g., `FF FF FF`)
- Press **Authenticate PIN**

If successful:
- Write functions are enabled.

### 5. Write to memory
- Individual pages can be edited.

- BIN files can be imported/exported.

---

## Internationalization (i18n)

To add a new language:
1. Create the `i18n/XX.json` file.
2. Add existing keys with translations.
3. Upon startup, the app will automatically add it to the menu.

---

## Compatibility

Tested on:
- Linux (Ubuntu / Debian)


Main dependencies:
- `PySide6`
- `pyscard`
- `python3`

---

## Security and warnings

The application **does not attempt to bypass** card restrictions.

However, **misuse of the AUTH command ** can **permanently block** SLE4442 cards, reducing the *error counter* to zero.

Therefore:
- All authentication operations on 4442 are **secure**.


WRITE and CHANGE PSC commands are not executed without explicit prior authentication.

---

## License

Project developed by **Wikilift**
Authorized use exclusively for research and technical maintenance.

**Disclaimer:** THE SOFTWARE IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. IN NO EVENT SHALL THE COPYRIGHT HOLDER (WIKILIFT) BE LIABLE FOR ANY DAMAGES, LOSSES, OR LIABILITY OF ANY KIND (INCLUDING, BUT NOT LIMITED TO, MISUSE, LOSS OF DATA, OR LOSS OF PROFITS) ARISING OUT OF THE USE OF, OR INABILITY TO USE, THE SOFTWARE. THE USER ASSUMES ALL RESPONSIBILITY FOR THE RESULTS OBTAINED FROM THE USE OF THIS SOFTWARE.

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://buymeacoffee.com/wikilift)