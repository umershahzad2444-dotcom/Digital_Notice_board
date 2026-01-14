from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pyodbc
import shutil
import os
from database import get_db_connection
from nlp_logic import analyze_text_smartly

app = FastAPI()

# --- 1. SETUP & FOLDERS ---
# Ye folder lazmi hone chahiyen taake error na aaye
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- 2. DATABASE CONNECTION ---
# --- 2. DATABASE CONNECTION ---
# Connection logic moved to database.py

# --- 3. LANDING PAGE ---
@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/admin-login-page", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

# --- 4. ADMIN SECTION ---

@app.post("/admin-login")
async def admin_login(request: Request, email: str = Form(...), password: str = Form(...)): # Added request: Request
    try:
        # Professional login check (Ideally check DB in future, currently hardcoded in main.py but we verified table exists)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Email = ? AND Password = ? AND Role = 'Admin'", (email, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
             return RedirectResponse(url="/manage-notices", status_code=303)
        return templates.TemplateResponse("error.html", {"request": request, "error_message": "Invalid Admin Credentials.", "back_url": "/admin-login-page"})
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error_message": f"System Error: {e}", "back_url": "/admin-login-page"})

@app.get("/manage-notices", response_class=HTMLResponse)
async def manage_notices(request: Request):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # SQL query for all notices
        cursor.execute("SELECT id, Title, Content, Category, CreatedAt, Attachment FROM Notifications ORDER BY CreatedAt DESC")
        rows = cursor.fetchall()
        notices = [{"id": r[0], "title": r[1], "content": r[2], "category": r[3], "date": r[4], "attachment": r[5]} for r in rows]
        conn.close()
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "notices": notices})
    except Exception as e:
        return HTMLResponse(f"<h3>Error loading dashboard: {e}</h3><a href='/'>Go Back</a>")

@app.post("/post-notice")
async def post_notice(title: str = Form(...), content: str = Form(...), file: UploadFile = File(None)):
    file_path = ""
    if file and file.filename:
        file_path = f"static/uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # NLP Integration (Error-Free Wrapper)
    try:
        category, priority, ai_emoji = analyze_text_smartly(content)
        
        # Append AI Emoji to Title for Visual Feedback
        title = f"{ai_emoji} {title}"
        
        # Agar priority High hai to title mein bhi add kar do
        if priority == "High Priority" and "[URGENT]" not in title:
            title = f"[URGENT] {title}"
    except Exception as e:
        print(f"NLP Error (Ignored for Stability): {e}")
        category = "General"  # Fallback
        priority = "Normal"

    cursor.execute("INSERT INTO Notifications (Title, Content, Category, Attachment) VALUES (?, ?, ?, ?)", 
                   (title, content, category, file_path))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/manage-notices", status_code=303)

@app.get("/delete-notice/{notice_id}")
async def delete_notice(notice_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Notifications WHERE id = ?", (notice_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/manage-notices", status_code=303)
    conn.close()
# --- 5. STUDENT SECTION ---

@app.get("/student-login-page", response_class=HTMLResponse)
async def student_login_page(request: Request):
    return templates.TemplateResponse("student_login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(request: Request, name: str = Form(...), email: str = Form(...), pwd: str = Form(...)): # Added request: Request
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check validation
        cursor.execute("SELECT UserID FROM Users WHERE Email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return templates.TemplateResponse("error.html", {"request": request, "error_message": "This email is already registered.", "back_url": "/register"})
        
        # Insert new student
        cursor.execute("INSERT INTO Users (FullName, Email, Password, Role, IsApproved) VALUES (?, ?, ?, 'Student', 0)", 
                       (name, email, pwd))
        conn.commit()
        conn.close()
        return templates.TemplateResponse("registration_success.html", {"request": request})
    except Exception as e:
        return HTMLResponse(f"<h3>Error registering: {e}</h3><a href='/register'>Go Back</a>")

@app.post("/login-student")
async def login_student(request: Request, email: str = Form(...), password: str = Form(...)): # Added request
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Email = ? AND Password = ? AND Role = 'Student'", (email, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            if user.IsApproved == 1:
                return RedirectResponse(url="/notices", status_code=303)
            return templates.TemplateResponse("error.html", {"request": request, "error_message": "Your account is pending Admin Approval.", "back_url": "/student-login-page"})
        return templates.TemplateResponse("error.html", {"request": request, "error_message": "Invalid Login Credentials.", "back_url": "/student-login-page"})
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error_message": f"System Error: {e}", "back_url": "/student-login-page"})

@app.get("/notices", response_class=HTMLResponse)
async def student_view(request: Request, view_as: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, Title, Content, Category, CreatedAt, Attachment FROM Notifications ORDER BY CreatedAt DESC")
    rows = cursor.fetchall()
    notices = [{"id": r[0], "title": r[1], "content": r[2], "category": r[3], "date": r[4], "attachment": r[5]} for r in rows]
    conn.close()
    
    is_admin = (view_as == "admin")
    return templates.TemplateResponse("student_view.html", {"request": request, "notices": notices, "is_admin": is_admin})

@app.get("/view-attachment", response_class=HTMLResponse)
async def view_attachment(request: Request, file: str):
    # Determine file type for proper rendering (Image vs Iframe)
    file_type = 'document'
    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        file_type = 'image'
        
    return templates.TemplateResponse("attachment_viewer.html", {"request": request, "file_path": file, "file_type": file_type})

# --- 6. STUDENT MANAGEMENT (APPROVALS) ---

@app.get("/manage-students", response_class=HTMLResponse)
async def manage_students(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT UserID, FullName, Email, IsApproved FROM Users WHERE Role = 'Student'")
    rows = cursor.fetchall()
    students = [{"id": r[0], "name": r[1], "email": r[2], "status": r[3]} for r in rows]
    conn.close()
    return templates.TemplateResponse("students_portal.html", {"request": request, "students": students})

@app.get("/approve-student/{user_id}")
async def approve_student(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Users SET IsApproved = 1 WHERE UserID = ?", (user_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/manage-students", status_code=303)

@app.get("/delete-student/{user_id}")
async def delete_student(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Users WHERE UserID = ?", (user_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/manage-students", status_code=303)

# --- 7. LOGOUT ---
@app.get("/logout")
async def logout():
    return RedirectResponse(url="/", status_code=303)