# Manual Frontend Functional Testing Plan

This document outlines the manual testing plan for the frontend of the Repair Quotation System.

## 1. Environment Setup & Prerequisites

### 1.1. Running the Backend
1.  Navigate to the `backend` directory in your terminal.
2.  Ensure all Python dependencies are installed (e.g., Flask, Flask-SQLAlchemy, Flask-CORS, openpyxl, Pillow). If not, run `pip install -r requirements.txt` (assuming a `requirements.txt` file exists or install them manually: `pip install Flask Flask-SQLAlchemy Flask-CORS openpyxl Pillow`).
3.  Run the Flask application: `python app.py`.
4.  The backend should now be running, typically on `http://127.0.0.1:5001`. Verify this by opening the URL in a browser; you should see the welcome JSON message.

### 1.2. Running the Frontend
1.  Open the `frontend/index.html` file directly in a modern web browser (e.g., Chrome, Firefox, Edge, Safari).
2.  No separate build step is required for the frontend as it's composed of HTML, CSS, and vanilla JavaScript.

### 1.3. Initial Data
*   **Option 1 (Recommended for consistent testing):**
    1.  Ensure the backend is running.
    2.  Navigate to the `backend` directory.
    3.  Run the data import script: `python import_school_data.py`. This will populate the database with predefined schools and repair items. This provides a consistent dataset for testing.
    4.  *Note:* If `repair_system.db` already exists, you might want to delete it before running the import script to start with a fresh, predictable dataset. The `import_school_data.py` script also includes a `clear_data()` function that can be called.
*   **Option 2 (Manual/Empty start):**
    1.  If you start with an empty database, the application should still function, but you will need to manually add schools and items through the (yet-to-be-built or separately tested) admin interface or directly via API calls if you want to test item listing. For this test plan, using `import_school_data.py` is preferred.
    2.  The "其他" (Other) item should be automatically created for any school added via the API, even if the database starts empty.

**Prerequisite Check:**
*   Before starting tests, ensure at least 2-3 schools are loaded, each with 3-5 repair items (including the default "其他" item). One school should ideally have only the "其他" item if possible to test TC9. The `import_school_data.py` script should facilitate this.

## 2. Test Cases (Desktop Browser)

**Browser:** (Tester to specify, e.g., Chrome Version X, Firefox Version Y)
**Operating System:** (Tester to specify, e.g., Windows 10, macOS Big Sur)

---

### TC1: School and Item Loading
*   **Objective:** Verify that schools and their respective repair items load correctly in the dropdowns.
*   **Steps:**
    1.  Open `frontend/index.html`.
    2.  **Expected:** The "选择学校" (`#school-select`) dropdown should be populated with school names from the database.
    3.  Select the first school in the dropdown.
    4.  **Expected:** The "选择维修项目" (`#repair-item-select`) dropdown should populate with items specific to the selected school, including an "其他" option.
    5.  Select a different school from the `#school-select` dropdown.
    6.  **Expected:** The `#repair-item-select` dropdown should update to show items for this newly selected school.
    7.  If a school exists that is known to have only the "其他" item (after data import), select this school.
    8.  **Expected:** The `#repair-item-select` should show only "其他" or a message like "该学校暂无特定维修项目" along with "其他".
*   **Pass/Fail:**
*   **Notes:**

---

### TC2: Adding Items to Quotation
*   **Objective:** Verify items can be added to the quotation list correctly and totals update.
*   **Steps:**
    1.  Select a school (e.g., "第一中学" if using imported data).
    2.  Select a repair item from `#repair-item-select` (e.g., "更换灯管").
    3.  Enter `2` in the quantity input field for that item.
    4.  Click the "添加到计价单" button for that item.
    5.  **Expected:** The item "更换灯管" should appear in the "当前计价单" section. The displayed name, quantity (2), unit price (e.g., 20.00), and subtotal (e.g., 40.00) should be correct. The "总金额" at the bottom should update to 40.00.
    6.  Select another repair item (e.g., "维修水龙头", quantity 1). Click "添加到计价单".
    7.  **Expected:** "维修水龙头" should also appear in the "当前计价单" section. The total price should update to reflect both items (e.g., 40.00 + 50.00 = 90.00).
    8.  Select the first item again ("更换灯管"). Change its quantity to `3`. Click "添加到计价单".
    9.  **Expected:** The existing entry for "更换灯管" in the "当前计价单" section should update its quantity to `3` and its subtotal accordingly (e.g., 60.00). The "总金额" should update (e.g., 60.00 + 50.00 = 110.00).
*   **Pass/Fail:**
*   **Notes:**

---

### TC3: Removing Items from Quotation
*   **Objective:** Verify items can be removed from the quotation list and totals update.
*   **Steps:**
    1.  Add 2-3 different items to the quotation as per TC2.
    2.  For one of the items in the "当前计价单" section, click its "移除" button.
    3.  **Expected:** The item should be removed from the list. The "总金额" should update to reflect the removal.
    4.  Remove all remaining items one by one.
    5.  **Expected:** The "当前计价单" section should display the "计价单为空" message. The "总金额" should be 0.00.
*   **Pass/Fail:**
*   **Notes:**

---

### TC4: Submitting a Quotation
*   **Objective:** Verify a complete quotation can be submitted successfully.
*   **Steps:**
    1.  Select a school.
    2.  Add at least two items to the quotation list.
    3.  In the "客户信息及提交" section, fill in:
        *   客户名称/班级: `Test Customer/Class A`
        *   维修人员: `John Doe`
        *   维修地点: `Library Room 3`
        *   维修时间: Select today's date and a valid time (e.g., using the date picker).
    4.  Click the "提交计价单" button.
    5.  **Expected:** A success message/alert should appear (e.g., "计价单提交成功！"). A confirmation prompt may ask if you want to download/view the generated Image and Excel files.
    6.  **Expected (after success):** The "当前计价单" list should clear and show the "计价单为空" message. The "总金额" should reset to 0.00. The input fields (客户名称, 维修人员, 维修地点, 维修时间) should be reset to their default/empty state.
*   **Pass/Fail:**
*   **Notes:**

---

### TC5: Input Validations (Quotation Submission)
*   **Objective:** Verify that appropriate error messages or behaviors occur for invalid submissions.
*   **Steps & Expected Outcomes:**
    1.  **No items:** Do not add any items to the quotation. Fill in all customer info. Click "提交计价单".
        *   **Expected:** An alert/message like "计价单中没有项目，请先添加维修项目。" should appear.
    2.  **No school selected:** (This might be prevented by UI logic disabling item selection). If possible to proceed to submission stage without a school selected (e.g. by clearing selection or if UI allows): Click "提交计价单".
        *   **Expected:** An alert/message like "请选择学校。" should appear.
    3.  **No "维修人员":** Add items, select school, fill other fields but leave "维修人员" blank. Click "提交计价单".
        *   **Expected:** An alert/message like "请填写维修人员。" should appear. The "维修人员" input field might be focused or highlighted.
    4.  **No "维修地点":** Add items, select school, fill other fields but leave "维修地点" blank. Click "提交计价单".
        *   **Expected:** An alert/message like "请填写维修地点。" should appear. The "维修地点" input field might be focused or highlighted.
    5.  **No "维修时间":** Add items, select school, fill other fields but leave "维修时间" blank/unselected. Click "提交计价单".
        *   **Expected:** An alert/message like "请选择维修时间。" should appear. The "维修时间" input field might be focused or highlighted.
*   **Pass/Fail:**
*   **Notes:** (Document actual error messages observed)

---

### TC6: Image and Excel Generation (Post-Submission)
*   **Objective:** Verify that the prompts for downloading/viewing generated files appear and options function.
*   **Steps:**
    1.  Successfully submit a quotation as in TC4.
    2.  **Expected:** A confirmation dialog should appear asking "是否立即生成并下载计价单图片和Excel文件?".
    3.  Click "确定" (or "Yes").
    4.  **Expected:** Two new browser tabs/windows should attempt to open, or two file downloads should initiate. One for a PNG image and one for an XLSX Excel file. The exact behavior (new tab vs. download) depends on browser settings and backend `Content-Disposition` headers. The key is that the browser is instructed to fetch these files. (Actual file content deep verification is a secondary, more involved test).
    5.  Repeat TC4 to submit another quotation.
    6.  When the confirmation dialog appears, click "取消" (or "No").
    7.  **Expected:** No new tabs/windows should open, and no downloads should initiate related to the image/Excel files.
*   **Pass/Fail:**
*   **Notes:**

---

## 3. Test Cases (Mobile View - using Browser DevTools Emulation)

**General Instructions:** Use the browser's developer tools (e.g., Chrome DevTools -> Toggle Device Toolbar) to emulate various mobile devices. Refresh the page after changing emulation if necessary.

---

### TC7: Dropdown Display and Usability (Mobile)
*   **Objective:** Verify `#school-select` and `#repair-item-select` are displayed correctly and are usable on mobile screens.
*   **Emulated Devices:** (Tester to list, e.g., iPhone SE, iPhone X/12, Samsung Galaxy S8, Pixel 5)
*   **Steps:**
    1.  For each emulated device:
        a. Open `frontend/index.html`.
        b. **Expected:** The "选择学校" (`#school-select`) dropdown should appear full-width (or very close to it, respecting container padding). Text inside should be legible. The dropdown should be easily tappable (standard mobile select UI should appear).
        c. Select a school.
        d. **Expected:** The "选择维修项目" (`#repair-item-select`) dropdown should appear, also full-width, with legible text, and be easily tappable.
        e. Tap to open the `#school-select` dropdown.
        f. **Expected:** The native mobile OS options list/picker should appear and be usable.
        g. Tap to open the `#repair-item-select` dropdown.
        h. **Expected:** The native mobile OS options list/picker should appear and be usable.
*   **Pass/Fail:** (Log per device if issues are device-specific)
*   **Notes:** (Note any visual glitches, text cutoff, arrow misplacement, or issues with the options list)

---

### TC8: Full Mobile User Flow
*   **Objective:** Verify the core user flow (adding items, submitting quotation) is functional and usable on mobile.
*   **Emulated Devices:** (Tester to list, e.g., a small screen like iPhone SE and a medium/large like Galaxy S20/Pixel 5)
*   **Steps:**
    1.  For each selected emulated device:
        a. Repeat the core steps of TC1 (School and Item Loading).
        b. Repeat the core steps of TC2 (Adding Items to Quotation). Pay attention to ease of quantity input and button tappability.
        c. Repeat the core steps of TC3 (Removing Items from Quotation).
        d. Repeat the core steps of TC4 (Submitting a Quotation). Pay attention to ease of form input and date/time selection.
    2.  **Expected:** All actions should be completable. Layout should be adapted to mobile (e.g., single column for main sections). Buttons should be large enough to tap easily. Input fields should be usable. No major visual bugs.
*   **Pass/Fail:** (Log per device)
*   **Notes:** (Detail any layout issues, usability problems, or visual glitches specific to mobile emulation)

---

## 4. Edge Case Testing

---

### TC9: No Specific Repair Items for a School
*   **Objective:** Verify behavior when a school has only the default "其他" item.
*   **Prerequisite:** Ensure a school exists in the database that has no specific repair items assigned to it (only the auto-created "其他" item). This might require manual DB adjustment or a specific state from `import_school_data.py`.
*   **Steps:**
    1.  Select the school that only has the "其他" item.
    2.  **Expected:** The `#repair-item-select` dropdown should contain "其他". It might also show a disabled option like "该学校暂无特定维修项目" or similar, or only "其他" should be selectable. The key is that the user understands there are no other specific items.
*   **Pass/Fail:**
*   **Notes:**

---

### TC10: Zero Quantity Input
*   **Objective:** Verify how the system handles attempts to add an item with zero or negative quantity.
*   **Steps:**
    1.  Select a school and a repair item.
    2.  Attempt to enter `0` into the quantity field for that item.
    3.  **Expected:** The "添加到计价单" button might be disabled, or clicking it might show an alert (e.g., "数量必须大于0"). The item should not be added to the quotation list with quantity 0. (Based on `app.js` logic: `if (quantity <= 0) { alert("数量必须大于0"); return; }`, an alert is expected).
    4.  Attempt to enter `-1` into the quantity field.
    5.  **Expected:** Same as for quantity 0. An alert "数量必须大于0" should appear.
*   **Pass/Fail:**
*   **Notes:**

---

## 5. Reporting

For each test case, testers should record:
*   **Test Case ID:** (e.g., TC1)
*   **Browser/Device:** (e.g., Chrome Desktop v100, iPhone SE Emulated via Chrome DevTools)
*   **Pass/Fail Status:**
*   **Actual Results:** A brief description of what happened.
*   **Details for Failures:** If failed, provide:
    *   Clear steps to reproduce the issue.
    *   Expected result vs. Actual result.
    *   Screenshots or screen recordings if helpful.
    *   Any error messages observed in the console or UI.

A summary report should be compiled after test execution, highlighting overall application stability, any critical bugs, and areas of concern.
