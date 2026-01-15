from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import os
from database import get_db_connection
from nlp_logic import analyze_text_smartly
from db_setup import create_database_if_not_exists, init_tables

app = FastAPI()

# --- 1. SETUP & FOLDERS ---
@app.on_event("startup")
async def startup_event():
    # Ensure Database Exists and Tables are Created
    if create_database_if_not_exists():
        init_tables()
    
    # Ensure Uploads Folder Exists
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
    conn = None
    try:
        # Professional login check (Ideally check DB in future, currently hardcoded in main.py but we verified table exists)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Email = ? AND Password = ? AND Role = 'Admin'", (email, password))
        user = cursor.fetchone()
        
        if user:
             return RedirectResponse(url="/manage-notices", status_code=303)
        return templates.TemplateResponse("error.html", {"request": request, "error_message": "Invalid Admin Credentials.", "back_url": "/admin-login-page"})
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error_message": f"System Error: {e}", "back_url": "/admin-login-page"})
    finally:
        if conn:
            conn.close()

@app.get("/manage-notices", response_class=HTMLResponse)
async def manage_notices(request: Request):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # SQL query for all notices
        cursor.execute("SELECT id, Title, Content, Category, CreatedAt, Attachment, ExpiryDate FROM Notifications ORDER BY CreatedAt DESC")
        rows = cursor.fetchall()
        notices = [{"id": r[0], "title": r[1], "content": r[2], "category": r[3], "date": r[4], "attachment": r[5], "expiry_date": r[6]} for r in rows]
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "notices": notices})
    except Exception as e:
        return HTMLResponse(f"<h3>Error loading dashboard: {e}</h3><a href='/'>Go Back</a>")
    finally:
        if conn:
            conn.close()

@app.post("/post-notice")
async def post_notice(title: str = Form(...), content: str = Form(...), category: str = Form("Auto"), expiry_date: str = Form(None), file: UploadFile = File(None)):
    file_path = ""
    if file and file.filename:
        # Sanitize filename
        safe_filename = os.path.basename(file.filename)
        file_path = f"static/uploads/{safe_filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # NLP Integration (Error-Free Wrapper)
        try:
            ai_category, priority, ai_emoji = analyze_text_smartly(content)
            
            # Use manual category if chosen, otherwise use AI category
            if category == "Auto":
                category = ai_category

            # Append AI Emoji to Title for Visual Feedback
            title = f"{ai_emoji} {title}"
            
            # Agar priority High hai to title mein bhi add kar do
            if priority == "High Priority" and "[URGENT]" not in title:
                title = f"[URGENT] {title}"
        except Exception as e:
            print(f"NLP Error (Ignored for Stability): {e}")
            if category == "Auto":
                category = "General"  # Fallback
            priority = "Normal"

        cursor.execute("INSERT INTO Notifications (Title, Content, Category, Attachment, ExpiryDate) VALUES (?, ?, ?, ?, ?)", 
                       (title, content, category, file_path, expiry_date if expiry_date else None))
        conn.commit()
    except Exception as e:
        print(f"Error posting notice: {e}")
        # Optionally return an error page here
    finally:
        if conn:
            conn.close()
            
    return RedirectResponse(url="/manage-notices", status_code=303)

@app.get("/edit-notice/{notice_id}", response_class=HTMLResponse)
async def edit_notice_page(request: Request, notice_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, Title, Content, ExpiryDate FROM Notifications WHERE id = ?", (notice_id,))
        row = cursor.fetchone()
        if row:
            # Format expiry date for datetime-local input (YYYY-MM-DDTHH:MM)
            expiry_val = ""
            if row[3]:
                expiry_val = row[3].strftime('%Y-%m-%dT%H:%M')
            cursor.execute("SELECT Category FROM Notifications WHERE id = ?", (notice_id,))
            cat_row = cursor.fetchone()
            category = cat_row[0] if cat_row else "General"
            notice = {"id": row[0], "title": row[1], "content": row[2], "expiry_date": expiry_val, "category": category}
            return templates.TemplateResponse("edit_notice.html", {"request": request, "notice": notice})
        return RedirectResponse(url="/manage-notices", status_code=303)
    except Exception as e:
        print(f"Error loading edit page: {e}")
        return RedirectResponse(url="/manage-notices", status_code=303)
    finally:
        if conn:
            conn.close()

@app.post("/update-notice/{notice_id}")
async def update_notice(notice_id: int, title: str = Form(...), content: str = Form(...), category: str = Form(...), expiry_date: str = Form(None)):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Notifications SET Title = ?, Content = ?, Category = ?, ExpiryDate = ? WHERE id = ?", 
                       (title, content, category, expiry_date if expiry_date else None, notice_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating notice: {e}")
    finally:
        if conn:
            conn.close()
    return RedirectResponse(url="/manage-notices", status_code=303)

@app.get("/delete-notice/{notice_id}")
async def delete_notice(notice_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Notifications WHERE id = ?", (notice_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting notice: {e}")
    finally:
        if conn:
            conn.close()
    return RedirectResponse(url="/manage-notices", status_code=303)
# --- 5. STUDENT SECTION ---

@app.get("/student-login-page", response_class=HTMLResponse)
async def student_login_page(request: Request):
    return templates.TemplateResponse("student_login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(request: Request, name: str = Form(...), email: str = Form(...), pwd: str = Form(...)): # Added request: Request
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check validation
        cursor.execute("SELECT UserID FROM Users WHERE Email = ?", (email,))
        if cursor.fetchone():
            return templates.TemplateResponse("error.html", {"request": request, "error_message": "This email is already registered.", "back_url": "/register"})
        
        # Insert new student
        cursor.execute("INSERT INTO Users (FullName, Email, Password, Role, IsApproved) VALUES (?, ?, ?, 'Student', 0)", 
                       (name, email, pwd))
        conn.commit()
        return templates.TemplateResponse("registration_success.html", {"request": request})
    except Exception as e:
        return HTMLResponse(f"<h3>Error registering: {e}</h3><a href='/register'>Go Back</a>")
    finally:
        if conn:
            conn.close()

@app.post("/login-student")
async def login_student(request: Request, email: str = Form(...), password: str = Form(...)): # Added request
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Email = ? AND Password = ? AND Role = 'Student'", (email, password))
        user = cursor.fetchone()
        
        if user:
            # Check IsApproved (assumed to be index 5 or attribute based on driver)
            is_approved = getattr(user, 'IsApproved', None)
            if is_approved is None:
                # Fallback to index 5 if attribute access fails (safety)
                try:
                    is_approved = user[5]
                except IndexError:
                    is_approved = 0 # Default to not approved if cannot determine
            
            if is_approved == 1 or is_approved is True:
                return RedirectResponse(url="/notices", status_code=303)
            return templates.TemplateResponse("error.html", {"request": request, "error_message": "Your account is pending Admin Approval.", "back_url": "/student-login-page"})
        return templates.TemplateResponse("error.html", {"request": request, "error_message": "Invalid Login Credentials.", "back_url": "/student-login-page"})
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error_message": f"System Error: {e}", "back_url": "/student-login-page"})
    finally:
        if conn:
            conn.close()

@app.get("/notices", response_class=HTMLResponse)
async def student_view(request: Request, category: str = None, view_as: str = None):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT id, Title, Content, Category, CreatedAt, Attachment 
            FROM Notifications 
            WHERE (ExpiryDate IS NULL OR ExpiryDate > GETDATE())
        """
        params = []
        if category and category != "All":
            query += " AND Category = ?"
            params.append(category)
        
        query += " ORDER BY CreatedAt DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        notices = [{"id": r[0], "title": r[1], "content": r[2], "category": r[3], "date": r[4], "attachment": r[5]} for r in rows]
        
        is_admin = (view_as == "admin")
        return templates.TemplateResponse("student_view.html", {
            "request": request, 
            "notices": notices, 
            "is_admin": is_admin,
            "current_category": category or "All"
        })
    except Exception as e:
        return HTMLResponse(f"<h3>Error loading notices: {e}</h3>")
    finally:
        if conn:
            conn.close()

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
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT UserID, FullName, Email, IsApproved FROM Users WHERE Role = 'Student'")
        rows = cursor.fetchall()
        students = [{"id": r[0], "name": r[1], "email": r[2], "status": r[3]} for r in rows]
        return templates.TemplateResponse("students_portal.html", {"request": request, "students": students})
    except Exception as e:
        return HTMLResponse(f"<h3>Error loading students: {e}</h3><a href='/manage-notices'>Go Back</a>")
    finally:
        if conn:
            conn.close()

@app.get("/approve-student/{user_id}")
async def approve_student(user_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Users SET IsApproved = 1 WHERE UserID = ?", (user_id,))
        conn.commit()
    except Exception as e:
        print(f"Error approving student: {e}")
    finally:
        if conn:
            conn.close()
    return RedirectResponse(url="/manage-students", status_code=303)

@app.get("/delete-student/{user_id}")
async def delete_student(user_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Users WHERE UserID = ?", (user_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting student: {e}")
    finally:
        if conn:
            conn.close()
    return RedirectResponse(url="/manage-students", status_code=303)

# --- 7. LOGOUT ---
@app.get("/logout")
async def logout():
    return RedirectResponse(url="/", status_code=303)