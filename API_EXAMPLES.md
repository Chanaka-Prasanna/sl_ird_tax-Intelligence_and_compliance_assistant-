# API Documentation & Examples

## Tax Intelligence & Compliance Assistant

---

## Table of Contents

- [API Endpoints](#api-endpoints)
- [Sample Questions](#sample-questions)

---

## API Endpoints

### 1. Health Check

```
GET /
```

**Response:**

```json
{
  "message": "Hello World"
}
```

**Example:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/"
```

---

### 2. Upload Documents

```
POST /upload
```

Upload PDF documents to the knowledge base.

**Request:** `multipart/form-data`

- `files`: PDF files (multiple)
- `urls`: Source URLs for each file

**Response:**

```json
{
  "message": "Successfully ingested 45 document splits from 1 files.",
  "files_processed": 1
}
```

**PowerShell Example:**

```powershell
$form = @{
    files = Get-Item -Path "tax_guide.pdf"
    urls = "https://ird.gov.lk/documents/tax_guide.pdf"
}
Invoke-RestMethod -Uri "http://localhost:8000/upload" -Method Post -Form $form
```

**cURL Example:**

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "files=@tax_guide.pdf" \
  -F "urls=https://ird.gov.lk/documents/tax_guide.pdf"
```

---

### 3. Chat (Main Q&A Endpoint)

```
POST /chat
```

Ask questions about tax documents.

**Request Body:**

```json
{
  "message": "What is the Corporate Income Tax rate for AY 2022/2023?",
  "thread_id": "user123"
}
```

**Response:**

```json
{
  "response": "The Corporate Income Tax rate for Assessment Year 2022/2023 is 30%...\n\n**Sources:**\n[1]- [Corporate Tax Guide 2022-2023](https://ird.gov.lk/...) - Page 12 - 12.2 Tax Rates"
}
```

**PowerShell Example:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/chat" `
    -Method Post `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"message": "What is the Corporate Income Tax rate for AY 2022/2023?", "thread_id": "session1"}'
```

**cURL Example:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the Corporate Income Tax rate for AY 2022/2023?", "thread_id": "session1"}'
```

**JavaScript/Fetch Example:**

```javascript
const response = await fetch("http://localhost:8000/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: "What is the Corporate Income Tax rate for AY 2022/2023?",
    thread_id: "session1",
  }),
});

const data = await response.json();
console.log(data.response);
```

---

## Sample Questions

### Tax Rates & Calculations

```
"What is the Corporate Income Tax rate for AY 2022/2023?"
```

```
"How is Self Employment Tax calculated for 2025/2026?"
```

---

### Policy Changes & Notices

```
"What changes were announced in PN_IT_2025-01?"
```

---

### Exemptions & Deductions

```
"Which IRD document explains SET exemptions?"
```

```
"What deductions are allowed for corporate donations?"
```

---

### Penalties & Compliance

```
"What penalties apply if SET is not paid on time?"
```

---

### Comparative Queries

```
"What is the difference between APIT and WHT?"
```

```
"Compare corporate tax rates between 2022/2023 and 2023/2024"
```

---

### Complex Procedural Queries

```
"How do I register for VAT as a new business?"
```

```
"What records must be maintained for tax audit purposes?"
```
