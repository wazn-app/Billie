
Here is the **Product Brief**, **UX/UI Specs**, and **MVP Plan** for a friendly AP SaaS. Let's call it **"Billie"** (Simple, friendly).

---

### 1. Product Brief

* **Product Name:** Billie
* **Tagline:** The Assistant who reads your bills so you don't have to.
* **Target User:** Small business owners or freelancers who hate data entry but need to pay bills on time.
* **Core Value:** Eliminates manual typing of invoices. upload a PDF, check the numbers, and mark it as "Paid".
* **The "CRUD" Reality:**
* **Create:** Upload Invoice (PDF/Image).
* **Read:** View list of unpaid/paid bills.
* **Update:** Correct errors the AI made (Human-in-the-loop).
* **Delete:** Archive or reject invalid invoices.



---

### 2. MVP Feature Set (Minimum Viable Product)

Do not build the bank integration or complex 3-way matching yet. Focus strictly on **Digitization & Organization**.

#### Phase 1: The "Digital Filing Cabinet"

1. **Smart Upload:** Drag-and-drop zone for PDFs.
2. **Auto-Extraction (The Magic):** Python backend extracts `Vendor`, `Date`, `Total`, and `Invoice #`.
3. **Side-by-Side Review:** A screen showing the PDF on the left and the extracted data forms on the right (for easy checking).
4. **Vendor Manager:** A simple address book of vendors (can be auto-populated from invoices).
5. **Export:** A "Download CSV" button formatted for her accounting software (Xero/QuickBooks/Excel).

---

### 3. UX/UI Specifications

The design must feel **calm** and **uncluttered**. Finance creates anxiety; your UI should remove it.

#### **Design Language**

* **Font:** Inter or Open Sans (Clean, legible sans-serif).
* **Primary Color:** Soft Blue or Teal (Trust, Calm). Avoid "Error Red" unless necessary.
* **Whitespace:** Generous padding. Don't crowd the data.

#### **Screen 1: The Dashboard (Home)**

* **Hero Section:** Large "Drop Invoices Here" box in the center.
* **Stats Row:** 3 Cards at the top:
* *To Review* (Orange badge count).
* *Unpaid Total* (Bold currency).
* *Paid this Month* (Green text).


* **Recent Activity:** A simple table below showing the last 5 files processed.

#### **Screen 2: The "Review" Workspace (The Core CRUD)**

* **Layout:** Split screen (50/50).
* **Left Panel:** PDF Viewer (Zoomable).
* **Right Panel:** Editable Form Fields.


* **Form Fields:**
* Vendor Name (Dropdown with "Create New" option).
* Invoice Date (Date Picker).
* Total Amount (Currency input).
* Invoice Number (Text).


* **Action Buttons (Bottom Right):**
* `Save & Approve` (Primary Button - Green).
* `Reject` (Secondary Button - Ghost/Gray).



#### **Screen 3: The "All Invoices" List**

* **Filter Tabs:** [All] | [Drafts] | [Ready to Pay] | [Paid]
* **Table Columns:** Status (Colored Dot), Vendor, Date, Amount, Actions (Edit/Delete icons).

---

### 4. Technical Architecture (The "How-To")

Since you are a mobile/app developer, this stack will be comfortable but powerful.

* **Frontend (The Look):** **React** (with **Vite**) + **Tailwind CSS** (for rapid styling).
* *Why?* Fast, responsive, and you can easily wrap this into a mobile app later using Capacitor.


* **Backend (The Brains):** **FastAPI** (Python).
* *Why?* It's blazing fast and native to Python, making it easy to integrate the OCR scripts we discussed earlier.


* **Database (The Memory):** **PostgreSQL** (via **Supabase**).
* *Why?* Supabase gives you Auth (Login/Signup), Database, and File Storage (for the PDFs) out of the box. Zero setup.


* **AI/OCR:** **Azure Document Intelligence** (Free tier is generous) or stay open-source with **PaddleOCR**.
* *Recommendation:* Start with Azure or OpenAI Vision API for the MVP. It is more accurate than open-source tools and requires zero maintenance.



---

