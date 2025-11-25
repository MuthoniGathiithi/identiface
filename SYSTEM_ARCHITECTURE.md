# Identiface - Facial Recognition Attendance System
## Complete System Architecture & Integration Guide

---

## 📋 System Overview

Identiface is a facial recognition-based attendance system that allows teachers to:
1. Create multiple classes with unique enrollment links
2. Students enroll via unique links (no mixing between classes)
3. Mark attendance using facial recognition (3 photos) OR manual entry
4. View real-time attendance metrics across all classes

---

## 🏗️ Architecture

### **Django Backend** (Main Application)
- User authentication (teachers)
- Class management
- Dashboard with metrics
- Database for classes, students, attendance

### **FastAPI Service** (Face Recognition Backend)
- Face feature extraction during enrollment
- Face matching during attendance
- Stores/retrieves face encodings
- Located in your `face_service` folder

---

## 🔄 How It Works

### **1. Class Creation Flow**

```
Teacher creates class "Database Systems"
    ↓
System generates unique enrollment_code: "A3F9B2C1D4E5"
    ↓
Enrollment link created: https://yoursite.com/enroll/A3F9B2C1D4E5
    ↓
Teacher shares this link with Database students ONLY
```

**Key Point:** Each class has its OWN unique code. Database students use one link, Networking students use a different link. **No mixing possible.**

---

### **2. Student Enrollment Flow**

```
Student clicks enrollment link for "Database Systems"
    ↓
Student fills form:
  - Name
  - Student ID
  - Email
  - Upload 3 photos of their face
    ↓
Django sends to FastAPI: /api/enroll
  - student_id
  - student_name
  - class_code: "A3F9B2C1D4E5"
  - 3 images
    ↓
FastAPI extracts face features → returns face_encoding
    ↓
Django saves student to database:
  - Linked to "Database Systems" class ONLY
  - face_encoding stored
    ↓
Student enrolled successfully!
```

**Key Point:** Student is enrolled in ONE specific class. Their face encoding is tied to that class code.

---

### **3. Facial Recognition Attendance Flow**

```
Teacher opens "Database Systems" class
    ↓
Clicks "Mark Attendance" → chooses "Facial Recognition"
    ↓
Teacher uploads 3 photos of the classroom
    ↓
Django creates AttendanceSession:
  - class_code: "A3F9B2C1D4E5"
  - method: "facial"
  - Saves 3 photos
    ↓
Django calls FastAPI: /api/mark-attendance
  - class_code: "A3F9B2C1D4E5"
  - 3 classroom photos
    ↓
FastAPI:
  1. Loads all face encodings for class "A3F9B2C1D4E5"
  2. Detects faces in 3 photos
  3. Matches detected faces against enrolled students
  4. Returns list of present student_ids
    ↓
Django marks attendance:
  - Students in list → status: "present"
  - Students NOT in list → status: "absent"

Attendance saved to database
```

**Key Point:** FastAPI ONLY looks at students enrolled in "Database Systems". Networking students are never checked.

---

### **4. Manual Attendance Flow (Backup)**

```
Teacher opens "Database Systems" class
    ↓
Clicks "Mark Attendance" → chooses "Manual Entry"
    ↓
Teacher sees checkbox list of ALL students in Database class
    ↓
Teacher checks boxes for present students
    ↓
Submits form
    ↓
Django marks attendance:
  - Checked students → status: "present"
  - Unchecked students → status: "absent"
  - method: "manual"
    ↓
Attendance saved to database
```

**Key Point:** Manual entry as backup if facial recognition fails or camera issues.

---

## 🔗 FastAPI Integration Points

### **Required FastAPI Endpoints**

#### **1. POST /api/enroll**
**Purpose:** Extract face features during student enrollment

**Request:**
```python
{
    "student_id": "STU12345",
    "student_name": "John Doe",
    "class_code": "A3F9B2C1D4E5",
    "images": [file1, file2, file3]  # 3 image files
}
```

**Response:**
```python
{
    "success": True,
    "face_encoding": "base64_encoded_string_or_json",
    "confidence": 0.95
}
```

**What FastAPI Should Do:**
1. Receive 3 images
2. Detect face in each image
3. Extract face features/encoding
4. Average the 3 encodings for better accuracy
5. Store encoding with class_code + student_id
6. Return encoding to Django

---

#### **2. POST /api/mark-attendance**
**Purpose:** Match classroom photos against enrolled students

**Request:**
```python
{
    "class_code": "A3F9B2C1D4E5",
    "images": [photo1, photo2, photo3]  # 3 classroom photos
}
```

**Response:**
```python
{
    "success": True,
    "present_students": ["STU12345", "STU67890", "STU11111"],
    "total_detected": 3,
    "confidence_scores": {
        "STU12345": 0.92,
        "STU67890": 0.88,
        "STU11111": 0.95
    }
}
```

**What FastAPI Should Do:**
1. Load all face encodings for class_code "A3F9B2C1D4E5"
2. Detect all faces in the 3 classroom photos
3. For each detected face:
   - Compare against all enrolled student encodings
   - If match found (confidence > threshold), add student_id to present list
4. Return list of present student IDs

---

#### **3. GET /api/encodings/{class_code}** (Optional)
**Purpose:** Retrieve all face encodings for a class

**Response:**
```python
{
    "class_code": "A3F9B2C1D4E5",
    "students": [
        {
            "student_id": "STU12345",
            "student_name": "John Doe",
            "face_encoding": "...",
            "enrolled_date": "2024-11-04"
        }
    ]
}
```

---

## 📊 Dashboard Metrics Explained

### **Today's Attendance Rate**
- **What it shows:** Percentage of students marked present TODAY across ALL teacher's classes
- **Calculation:** (Total Present Today / Total Marked Today) × 100
- **Example:** Teacher has 3 classes. 50 students marked present out of 60 total = 83.3%

### **Absences Today**
- **What it shows:** Total number of students marked absent TODAY across ALL classes
- **Example:** 10 students absent across Database, Networking, and Math classes

### **Pending Classes**
- **What it shows:** Number of classes that haven't taken attendance yet TODAY
- **Example:** Teacher has 5 classes, only marked attendance for 2 = 3 pending

### **Today's Absences List**
- **What it shows:** Scrollable list of individual students who are absent
- **Shows:** Student name, class name, time marked
- **Purpose:** Quick reference for follow-up

---

## 🔐 Data Isolation (No Mixing)

### **How Classes Stay Separate:**

1. **Unique Enrollment Codes**
   - Each class gets a UUID-based code
   - Database: `A3F9B2C1D4E5`
   - Networking: `B7G2H8J3K9L1`
   - Math: `C4M9N2P5Q8R3`

2. **Student-Class Relationship**
   ```python
   Student.class_enrolled = ForeignKey(Class)
   ```
   - Each student is linked to ONE class
   - Cannot be enrolled in multiple classes via same link

3. **FastAPI Storage**
   - Face encodings stored with class_code
   - When marking attendance, FastAPI only loads encodings for that specific class_code
   - Database students' faces never compared against Networking students

4. **Attendance Records**
   ```python
   Attendance.class_session = ForeignKey(Class)
   ```
   - Each attendance record tied to specific class
   - Dashboard filters by teacher's classes only

---

## 🛠️ Setup Instructions

### **1. Configure FastAPI URL**

In `identiface/settings.py`:
```python
# FastAPI Face Service Configuration
FACE_API_URL = 'http://localhost:8000'  # Change to your FastAPI URL
```

### **2. Run Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

### **3. Configure Media Files**

In `identiface/settings.py`:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

In `identiface/urls.py`:
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your patterns
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### **4. Install Required Packages**
```bash
pip install requests Pillow
```

---

## 📝 Usage Workflow

### **For Teachers:**

1. **Create Class**
   - Go to Dashboard → Create New Class
   - Enter class title and time
   - System generates enrollment link

2. **Share Enrollment Link**
   - Copy enrollment link from class card
   - Share with students (email, WhatsApp, LMS, etc.)

3. **Mark Attendance**
   - Option A: Upload 3 classroom photos (facial recognition)
   - Option B: Manual checkbox list (backup)

4. **View Metrics**
   - Dashboard shows today's overview
   - See absences, pending classes, attendance rate

### **For Students:**

1. **Click Enrollment Link**
   - Unique link for each class

2. **Fill Enrollment Form**
   - Name, Student ID, Email
   - Upload 3 clear photos of face

3. **Done!**
   - Enrolled in that specific class
   - Face registered for attendance

---

## 🔄 FastAPI Expected Behavior

### **Your face_service folder should:**

1. **Store face encodings** with class_code as key
   - Use database, Redis, or file system
   - Structure: `{class_code: {student_id: encoding}}`

2. **Handle multiple faces** in classroom photos
   - Detect all faces in image
   - Match each against enrolled students
   - Return all matches

3. **Use confidence threshold**
   - Only return matches above threshold (e.g., 0.75)
   - Prevents false positives

4. **Handle errors gracefully**
   - Return `{"success": False, "error": "message"}`
   - Django will fall back to manual entry

---

## 📱 Example URLs

- **Landing Page:** `http://localhost:8000/`
- **Teacher Login:** `http://localhost:8000/login/`
- **Dashboard:** `http://localhost:8000/dashboard/`
- **Create Class:** `http://localhost:8000/create-class/`
- **Enrollment Link:** `http://localhost:8000/enroll/A3F9B2C1D4E5/`
- **Mark Attendance:** `http://localhost:8000/mark-attendance/1/`

---

## ✅ Key Features

✓ **Unique enrollment links per class** - No mixing
✓ **Facial recognition attendance** - Upload 3 photos
✓ **Manual attendance backup** - If facial fails
✓ **Real-time dashboard metrics** - Today's overview
✓ **Multi-class support** - Teachers can have many classes
✓ **FastAPI integration** - Separate face service
✓ **Clean UI** - Green, black, white theme
✓ **Mobile responsive** - Works on all devices

---

## 🚀 Next Steps

1. Run migrations to create new database tables
2. Configure FACE_API_URL in settings
3. Ensure your FastAPI service implements the required endpoints
4. Test enrollment flow with a student
5. Test facial attendance with classroom photos
6. Test manual attendance as backup

---

**Questions? Check the code comments or refer to this document!**
