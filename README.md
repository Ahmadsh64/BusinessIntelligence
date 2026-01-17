# 📊 Retail Business Intelligence Web Application

מערכת Business Intelligence מבוססת Web לניתוח מכירות, רווחיות ומלאי. המערכת מספקת דשבורדים אינטראקטיביים, KPIs, תובנות עסקיות ומערכת ניהול משתמשים מתקדמת.

## 🎯 מטרת הפרויקט

פיתוח מערכת BI מקצועית המספקת:
- ניתוח מכירות, רווחיות ומלאי
- תמיכה בקבלת החלטות ניהוליות
- הצגת KPIs ותובנות עסקיות
- מערכת ניהול משתמשים עם הרשאות
- סימולציה של סביבת BI ארגונית אמיתית

## 👥 קהל יעד

| תפקיד | שימוש במערכת |
|------|-------------|
| **CEO** | ביצועים כלליים, רווחיות |
| **Store Manager** | ביצועי סניף, נתונים מקומיים |
| **Finance** | הכנסות, הוצאות, רווחיות |
| **Analyst** | מגמות, השוואות, תחזיות |

## 🛠️ טכנולוגיות (Tech Stack)

### Backend / Data
- **Python 3.8+** - שפת תכנות ראשית
- **Pandas & NumPy** - עיבוד נתונים
- **Faker** - יצירת נתונים סינתטיים
- **MySQL** - מסד נתונים
- **SQLAlchemy** - ORM למסד הנתונים

### ETL Pipeline
- **Python ETL Pipelines** - עיבוד וטרנספורמציה
- **Excel to SQL** - טעינת נתונים

### Web Application
- **Flask** - Framework ל-Web
- **Plotly.js** - ויזואליזציה אינטראקטיבית
- **Bootstrap 5** - עיצוב רספונסיבי
- **JWT** - Authentication מאובטח

### Machine Learning
- **scikit-learn** - מודלים לחיזוי מכירות

## 📁 מבנה הפרויקט

```
BusinessIntelligence/
│
├── data/
│   └── raw_excel/              # קבצי Excel גולמיים
│       ├── sales_raw.xlsx       # עסקאות מכירה
│       ├── products.xlsx        # קטלוג מוצרים
│       ├── stores.xlsx         # סניפים
│       └── customers.xlsx       # לקוחות
│
├── data_generation/
│   └── generate_data.py        # יצירת נתונים סינתטיים
│
├── etl/
│   └── etl_pipeline.py         # תהליך ETL מלא
│
├── warehouse/
│   └── star_schema.sql         # סכימת Data Warehouse
│
├── app/
│   ├── app.py                  # Flask Backend
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css       # עיצוב
│   │   └── js/
│   │       ├── dashboard.js    # לוגיקת דשבורד
│   │       └── admin_users.js # ניהול משתמשים
│   └── templates/
│       ├── base.html           # Template בסיס
│       ├── index.html          # דף דשבורד
│       ├── login.html          # דף התחברות
│       ├── insights.html       # תובנות עסקיות
│       ├── about.html          # אודות
│       └── admin_users.html    # ניהול משתמשים
│
├── scripts/
│   └── create_users.py         # יצירת משתמשים ראשוניים
│
├── insights/
│   └── business_insights.md    # תובנות עסקיות
│
└── README.md                   # קובץ זה
```

## 🚀 התקנה והפעלה

### דרישות מוקדמות

1. **Python 3.8+** - [הורדה](https://www.python.org/downloads/)
2. **MySQL 5.7+** - [הורדה](https://dev.mysql.com/downloads/)
3. **Git** (אופציונלי) - [הורדה](https://git-scm.com/downloads)

### שלב 1: התקנת Python Packages

```bash
# התקן את כל החבילות הנדרשות
pip install -r requirements.txt
```

**חבילות עיקריות:**
- `flask` - Web Framework
- `flask-cors` - CORS support
- `pandas` - עיבוד נתונים
- `numpy` - חישובים מספריים
- `mysql-connector-python` - חיבור ל-MySQL
- `sqlalchemy` - ORM
- `faker` - יצירת נתונים סינתטיים
- `scikit-learn` - Machine Learning
- `PyJWT` - Authentication
- `Werkzeug` - Security utilities

### שלב 2: הגדרת MySQL

1. **התקן MySQL** (אם עדיין לא מותקן)

2. **צור משתמש MySQL** (אופציונלי):
```sql
CREATE USER 'root'@'localhost' IDENTIFIED BY '12345';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

3. **עדכן את פרטי ההתחברות** בקבצים הבאים:
   - `etl/etl_pipeline.py` - שורה 20-25
   - `app/app.py` - שורה 21-26
   - `scripts/create_users.py` - שורה 12-17

```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'BusinessIntelligence',
    'user': 'root',
    'password': '12345',  # שנה לסיסמה שלך
    'charset': 'utf8mb4'
}
```

### שלב 3: יצירת נתונים סינתטיים

הרץ את הסקריפט ליצירת קבצי Excel עם נתונים סינתטיים:

```bash
python data_generation/generate_data.py
```

**מה הסקריפט יוצר:**
- `data/raw_excel/sales_raw.xlsx` - ~67,000 עסקאות מכירה
- `data/raw_excel/products.xlsx` - 200 מוצרים
- `data/raw_excel/stores.xlsx` - 20 סניפים
- `data/raw_excel/customers.xlsx` - 1,000 לקוחות

### שלב 4: יצירת Data Warehouse

הרץ את סכימת ה-SQL ליצירת הטבלאות:

```bash
# דרך 1: דרך MySQL Command Line
mysql -u root -p < warehouse/star_schema.sql

# דרך 2: דרך Python (אוטומטי ב-ETL)
# הסקריפט יוצר את הטבלאות אוטומטית
```

**מה נוצר:**
- **Fact Table**: `fact_sales` - טבלת עובדות מכירות
- **Dimension Tables**:
  - `dim_date` - מימד תאריכים
  - `dim_store` - מימד סניפים
  - `dim_product` - מימד מוצרים
  - `dim_customer` - מימד לקוחות
- **Users Table**: `users` - משתמשים והרשאות

### שלב 5: הרצת ETL Pipeline

הרץ את תהליך ה-ETL לטעינת הנתונים:

```bash
python etl/etl_pipeline.py
```

**מה הסקריפט עושה:**
1. ✅ יצירת מסד הנתונים `BusinessIntelligence` (אם לא קיים)
2. ✅ יצירת טבלאות (Star Schema)
3. ✅ טעינת נתונים מ-Excel ל-SQL
4. ✅ ניקוי וטרנספורמציה של נתונים
5. ✅ בדיקות איכות נתונים
6. ✅ יצירת Views לשאילתות נפוצות

**זמן ביצוע:** ~2-5 דקות (תלוי במחשב)

### שלב 6: יצירת משתמשים ראשוניים

יצירת משתמשים למערכת:

```bash
python scripts/create_users.py
```

**מה נוצר:**
- **משתמש Admin**: 
  - Username: `admin`
  - Password: `admin123`
  - גישה מלאה לכל הנתונים

- **משתמשים לסניפים**:
  - Username: `store_1`, `store_2`, ... `store_20`
  - Password: `store1123`, `store2123`, ... `store20123`
  - גישה רק לנתוני הסניף שלהם

⚠️ **חשוב**: שנה את הסיסמאות לאחר הכניסה הראשונה!

### שלב 7: הפעלת Web Application

הרץ את אפליקציית Flask:

```bash
cd app
python app.py
```

או מהתיקייה הראשית:

```bash
python app/app.py
```

**האפליקציה תיפתח בכתובת:**
- **Local**: `http://localhost:5000`
- **Network**: `http://192.168.x.x:5000` (לשימוש ברשת מקומית)

## 🔐 התחברות למערכת

### 1. פתח את הדפדפן

נווט לכתובת: `http://localhost:5000`

### 2. התחברות

**משתמש Admin (גישה מלאה):**
- Username: `admin`
- Password: `admin123`

**משתמש Store Manager (גישה מוגבלת):**
- Username: `store_1` (או store_2, store_3, וכו')
- Password: `store1123` (או store2123, store3123, וכו')

### 3. דפים זמינים

לאחר התחברות, תוכל לגשת ל:

- **דשבורד** (`/`) - KPIs, גרפים, ניתוחים
- **תובנות עסקיות** (`/insights`) - תובנות ומסקנות
- **אודות** (`/about`) - מידע על הפרויקט
- **ניהול משתמשים** (`/admin/users`) - רק ל-Admin

## 📊 Data Warehouse Design (Star Schema)

### ⭐ Fact Table

**fact_sales**
- `sale_id` (PK) - מזהה עסקה
- `date_id` (FK) - קישור לתאריך
- `store_id` (FK) - קישור לסניף
- `product_id` (FK) - קישור למוצר
- `customer_id` (FK) - קישור ללקוח
- `quantity` - כמות
- `revenue` - הכנסות
- `cost` - עלות
- `profit` - רווח

### 🔹 Dimension Tables

**dim_date**
- `date_id`, `date`, `day`, `month`, `quarter`, `year`, `month_name`, `quarter_name`

**dim_store**
- `store_id`, `store_name`, `city`, `region`, `store_type`

**dim_product**
- `product_id`, `product_name`, `category`, `brand`, `price`

**dim_customer**
- `customer_id`, `customer_name`, `gender`, `age_group`

**users** (ניהול משתמשים)
- `user_id`, `username`, `password_hash`, `store_id`, `role`, `created_at`, `last_login`, `is_active`

## 📈 KPIs מרכזיים

### 💰 פיננסי
- **Total Revenue** - סך הכנסות
- **Total Profit** - סך רווח
- **Profit Margin (%)** - שולי רווח
- **Average Order Value** - ערך הזמנה ממוצע

### 📊 מכירות
- **Monthly Sales Trend** - מגמת מכירות חודשית
- **Top 10 Products** - 10 המוצרים המובילים
- **Sales by Category** - מכירות לפי קטגוריה

### 🏪 סניפים
- **Revenue by Store** - הכנסות לפי סניף
- **Store Performance Comparison** - השוואת ביצועי סניפים

## 🎨 Dashboards

### 1. Executive Dashboard
- KPI Cards (Revenue, Profit, Margin, AOV)
- Revenue & Profit Trends
- Top Products
- Store Performance

### 2. Product & Inventory Dashboard
- Category Performance
- Top/Bottom Products
- Sales vs Profit Analysis

### 3. Customer Insights
- Customer Demographics
- Age Group Analysis
- Gender Distribution

### 4. Seasonal Analysis
- Quarterly Trends
- Monthly Patterns
- Peak/Low Months Identification

### 5. Sales Forecasting
- Future Sales Predictions
- Model Accuracy (R² Score)
- 6-Month Forecast

## 🔧 Filters

הדשבורד תומך בפילטרים דינמיים:

- **תאריכים** - טווח תאריכים (מתאריך עד תאריך)
- **סניפים** - בחירת סניפים ספציפיים
- **קטגוריות** - סינון לפי קטגוריות מוצרים
- **אזורים** - סינון לפי אזורים גיאוגרפיים

**הערה**: Store Managers רואים רק את נתוני הסניף שלהם (אוטומטי)

## 👥 ניהול משתמשים (Admin Only)

### גישה לדף ניהול משתמשים

1. התחבר כ-Admin
2. לחץ על "ניהול משתמשים" ב-Navbar
3. או גש ישירות ל-`/admin/users`

### פעולות זמינות

#### הוספת משתמש חדש
1. לחץ על "הוסף משתמש חדש"
2. מלא את הפרטים:
   - שם משתמש (חובה)
   - סיסמה (מינימום 6 תווים)
   - תפקיד (Admin / Store Manager)
   - סניף (נדרש למנהל סניף)
3. לחץ "הוסף"

#### עריכת משתמש
1. לחץ על "ערוך" בשורה של המשתמש
2. עדכן את הפרטים:
   - שם משתמש
   - סיסמה (אופציונלי - השאר ריק אם לא רוצה לשנות)
   - תפקיד
   - סניף
   - סטטוס פעיל/לא פעיל
3. לחץ "עדכן"

#### מחיקת משתמש
1. לחץ על "מחק" בשורה של המשתמש
2. אשר את המחיקה
3. ⚠️ לא ניתן למחוק את המשתמש שלך

#### שינוי סיסמה
1. לחץ על שם המשתמש ב-Navbar
2. בחר "שנה סיסמה"
3. הזן סיסמה נוכחית וסיסמה חדשה
4. לחץ "שנה סיסמה"

## 🔒 אבטחה והרשאות

### תפקידים (Roles)

**Admin**
- ✅ גישה מלאה לכל הנתונים
- ✅ ניהול משתמשים
- ✅ גישה לכל הסניפים
- ✅ יצירה, עריכה ומחיקה של משתמשים

**Store Manager**
- ✅ גישה רק לנתוני הסניף שלו
- ✅ צפייה בדשבורדים
- ✅ שינוי סיסמה אישית
- ❌ לא יכול לראות נתונים של סניפים אחרים
- ❌ לא יכול לנהל משתמשים

### אבטחה

- **Password Hashing** - סיסמאות מאוחסנות כ-Hash (bcrypt)
- **Session Management** - ניהול סשן מאובטח
- **JWT Tokens** - תמיכה ב-API authentication
- **Role-Based Access Control** - הגבלת גישה לפי תפקיד
- **SQL Injection Protection** - שימוש ב-Parameterized Queries

## 📤 Export & Share

### ייצוא ל-CSV
1. בדשבורד, לחץ על "ייצא ל-CSV"
2. הנתונים ייוצאו עם כל הפילטרים הפעילים
3. מקסימום 10,000 שורות

### שיתוף דשבורד
1. לחץ על "שתף דשבורד"
2. הקישור כולל את כל הפילטרים
3. ניתן לשתף עם משתמשים אחרים

## 🐛 פתרון בעיות

### בעיה: שגיאת התחברות ל-MySQL

**פתרון:**
1. ודא ש-MySQL רץ: `mysql -u root -p`
2. בדוק את פרטי ההתחברות ב-`DB_CONFIG`
3. ודא שהמשתמש קיים ויש לו הרשאות

### בעיה: טבלאות לא נוצרות

**פתרון:**
1. הרץ את `warehouse/star_schema.sql` ידנית
2. או הרץ את `etl/etl_pipeline.py` מחדש

### בעיה: נתונים לא נטענים

**פתרון:**
1. ודא ש-Excel files קיימים ב-`data/raw_excel/`
2. הרץ `data_generation/generate_data.py` מחדש
3. הרץ `etl/etl_pipeline.py` מחדש

### בעיה: משתמשים לא נוצרים

**פתרון:**
1. ודא שהטבלה `users` קיימת
2. ודא שיש סניפים ב-`dim_store`
3. הרץ `scripts/create_users.py` מחדש

### בעיה: דף Admin לא נפתח

**פתרון:**
1. ודא שהתחברת כ-Admin (לא Store Manager)
2. בדוק ב-Console אם יש שגיאות JavaScript
3. רענן את הדף (Ctrl+F5)

## 📝 API Endpoints

### Authentication
- `POST /api/login` - התחברות (JSON)
- `GET /logout` - התנתקות

### Dashboard Data
- `GET /api/kpis` - KPIs מרכזיים
- `GET /api/sales-trend` - מגמת מכירות
- `GET /api/store-performance` - ביצועי סניפים
- `GET /api/product-performance` - ביצועי מוצרים
- `GET /api/category-revenue` - הכנסות לפי קטגוריה
- `GET /api/customer-insights` - תובנות לקוחות
- `GET /api/seasonal-analysis` - ניתוח עונתי
- `GET /api/sales-forecast` - תחזית מכירות
- `GET /api/business-insights` - תובנות עסקיות
- `GET /api/filters` - אפשרויות פילטרים

### User Management (Admin Only)
- `GET /api/users` - רשימת משתמשים
- `POST /api/users` - יצירת משתמש
- `PUT /api/users/<id>` - עדכון משתמש
- `DELETE /api/users/<id>` - מחיקת משתמש
- `POST /api/change-password` - שינוי סיסמה

### Export
- `GET /api/export-csv` - ייצוא נתונים ל-CSV

## 🎓 שימוש במערכת

### למנהל מערכת (Admin)

1. **התחברות**: `admin` / `admin123`
2. **צפייה בדשבורד**: גישה מלאה לכל הנתונים
3. **ניהול משתמשים**: הוספה, עריכה, מחיקה
4. **ניתוחים**: כל הסניפים והקטגוריות

### למנהל סניף (Store Manager)

1. **התחברות**: `store_X` / `storeX123` (X = מספר סניף)
2. **צפייה בדשבורד**: רק נתוני הסניף שלו
3. **פילטרים**: מוגבלים אוטומטית לסניף
4. **שינוי סיסמה**: דרך תפריט המשתמש

## 📚 משאבים נוספים

- **Documentation**: כל הקוד כולל הערות מפורטות
- **Code Comments**: הסברים בעברית ואנגלית
- **Error Messages**: הודעות שגיאה ברורות

## 🤝 תרומה לפרויקט

זהו פרויקט לימודי/תיק עבודות. אם תרצה לשפר או להוסיף תכונות:

1. Fork את הפרויקט
2. צור Branch חדש
3. בצע שינויים
4. שלח Pull Request

## 📄 רישיון

פרויקט זה נוצר למטרות לימודיות ותיק עבודות.

## 👨‍💻 יצירת קשר

לשאלות או בעיות, פתח Issue ב-GitHub או צור קשר.

---

**נבנה עם ❤️ באמצעות Python, Flask, MySQL & Plotly**

© 2024 Retail Business Intelligence System
