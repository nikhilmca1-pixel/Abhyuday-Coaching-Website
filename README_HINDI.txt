ABHYUDAY COACHING INSTITUTE WEBSITE
===================================

इस ZIP में पूरी Flask website है:
- Home, About, Courses, Faculty, Library & Gallery, Contact
- Student registration form (Registration fee ₹0)
- Admin login और dashboard
- Students list / delete
- Faculty profiles add करने और photo upload करने का option
- Courses add / show / hide
- Library और coaching centre की photos upload / delete करने का option
- SQLite database अपने आप बनता है

जरूरी:
1. Python 3.10 या नया version install होना चाहिए।
2. ZIP extract करें।
3. इस folder में terminal / PowerShell खोलें।
4. Virtual environment बनाएँ:
   py -m venv .venv
5. Activate करें (Windows PowerShell):
   .venv\Scripts\Activate.ps1
   अगर execution policy error आए:
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   फिर activate command दोबारा चलाएँ।
6. Dependencies install करें:
   pip install -r requirements.txt
7. Website start करें:
   python app.py
8. Browser में खोलें:
   http://127.0.0.1:5000

ADMIN LOGIN (पहली बार):
Username: admin
Password: ChangeMe123!

SECURITY:
- Login करने के बाद इस default password को बदलना जरूरी है।
- Internet पर live करने से पहले SECRET_KEY और ADMIN_PASSWORD बदलें।
- अभी यह starter project local development के लिए है; public hosting से पहले HTTPS,
  secure secret, production server, backups और proper admin password-change feature
  configure करें।
- SQLite database file abhyuday.db पहली बार run होने पर बनेगी।
- Uploaded photos static/uploads folder में save होंगी।
- Phone number बाद में Contact page और footer में update कर सकते हैं।

LOGO:
आपका दिया हुआ Abhyuday logo static/img/abhuday.jpeg में रखा गया है।

UPDATED ADMISSION FORM:
- Personal details: student name, parents' names, DOB, gender, category, mobile, email, address
- Annual family income
- Domicile state and district
- Last qualification, board/university, passing year, marks/percentage
- Student photo and signature upload
- Income, domicile, character certificate and last qualification document upload
- Declaration checkbox
- Admin can click a student name to view application details and submitted document links

PRIVACY & SECURITY:
These documents contain sensitive personal information. Collect only what is necessary,
limit access to authorized staff, protect backups, and define a retention/deletion policy.
This starter stores uploads in static/uploads for local testing. Before public hosting,
move private documents to protected storage and serve them only through authenticated
admin routes; do not expose uploaded certificates through public static URLs.
