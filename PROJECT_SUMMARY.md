# 📊 סיכום מקיף - פרויקט Retail Business Intelligence

## 🎯 סקירה כללית

פרויקט **Retail Business Intelligence** הוא מערכת BI מלאה ומקצועית לניתוח מכירות, רווחיות ומלאי עבור רשת קמעונאית. המערכת מספקת דשבורדים אינטראקטיביים, תחזיות מכירות, ניהול מלאי חכם, מערכת משתמשים עם הרשאות, ותובנות עסקיות מתקדמות.

---

## 📅 התפתחות הפרויקט - ציר זמן

### שלב 1: הקמה בסיסית
- ✅ יצירת מבנה Data Warehouse (Star Schema)
- ✅ פיתוח ETL Pipeline לטעינת נתונים
- ✅ יצירת נתונים סינתטיים (67,000+ עסקאות)
- ✅ הקמת אפליקציית Flask בסיסית

### שלב 2: דשבורדים ו-KPIs
- ✅ דשבורד ראשי עם KPIs מרכזיים
- ✅ גרפים אינטראקטיביים (Plotly.js)
- ✅ ניתוח מכירות, רווחיות, ביצועי סניפים
- ✅ ניתוח מוצרים וקטגוריות
- ✅ ניתוח לקוחות (דמוגרפיה, גיל, מגדר)

### שלב 3: מערכת משתמשים ואבטחה
- ✅ מערכת התחברות עם JWT
- ✅ ניהול משתמשים (Admin/Store Manager)
- ✅ Role-Based Access Control (RBAC)
- ✅ הגבלת גישה לפי סניף
- ✅ שינוי סיסמאות מאובטח

### שלב 4: תכונות מתקדמות
- ✅ תחזיות מכירות (Linear Regression, ARIMA, Prophet)
- ✅ ניתוח עונתי
- ✅ סגמנטציה של לקוחות (K-Means Clustering)
- ✅ זיהוי אנומליות
- ✅ מערכת התראות (Notifications)

### שלב 5: ניהול מלאי חכם
- ✅ חישוב EOQ (Economic Order Quantity)
- ✅ חישוב Reorder Point
- ✅ הצעות הזמנה אוטומטיות
- ✅ ניהול מלאי מרכזי וסניפים
- ✅ התראות על מלאי נמוך

### שלב 6: UI/UX ו-DevOps (עכשיו)
- ✅ עיצוב מודרני ורספונסיבי
- ✅ מצב כהה/בהיר
- ✅ קונפיגורציה אישית למשתמש
- ✅ Docker + docker-compose
- ✅ CI/CD בסיסי

---

## 🏗️ ארכיטקטורת המערכת

### 1. Data Warehouse (Star Schema)

#### Fact Table (טבלת עובדות)
**`fact_sales`** - כל עסקאות המכירה
- `sale_id` - מזהה ייחודי
- `date_id` - קישור לתאריך
- `store_id` - קישור לסניף
- `product_id` - קישור למוצר
- `customer_id` - קישור ללקוח
- `quantity` - כמות
- `revenue` - הכנסות
- `cost` - עלות
- `profit` - רווח

#### Dimension Tables (טבלאות מימדים)
1. **`dim_date`** - מימד תאריכים
   - תאריך, יום, חודש, רבעון, שנה
   - שם חודש, שם רבעון
   - יום בשבוע, סוף שבוע, חג

2. **`dim_store`** - מימד סניפים
   - שם סניף, עיר, אזור, סוג סניף
   - תאריך פתיחה

3. **`dim_product`** - מימד מוצרים
   - שם מוצר, קטגוריה, מותג
   - מחיר, עלות

4. **`dim_customer`** - מימד לקוחות
   - שם לקוח, מגדר, גיל
   - קבוצת גיל, עיר

#### System Tables (טבלאות מערכת)
1. **`users`** - משתמשים והרשאות
   - `user_id`, `username`, `password_hash`
   - `store_id`, `role` (admin/store_manager)
   - `created_at`, `last_login`, `is_active`

2. **`notifications`** - התראות
   - `notification_id`, `user_id`, `store_id`
   - `type`, `title`, `message`, `severity`
   - `is_read`, `created_at`

3. **`inventory_levels`** - רמות מלאי בסניפים
   - `inventory_id`, `store_id`, `product_id`
   - `current_quantity`, `min_quantity`, `max_quantity`
   - `reorder_point`, `last_updated`

4. **`central_inventory`** - מלאי מרכזי
   - `central_inventory_id`, `product_id`
   - `current_quantity`, `last_updated`

5. **`activity_log`** - לוג פעילות
   - `activity_id`, `user_id`, `action`
   - `details`, `timestamp`

6. **`user_preferences`** - העדפות משתמש (חדש!)
   - `preference_id`, `user_id`
   - `theme` (light/dark)
   - `preferred_charts`, `preferred_tables`
   - `created_at`, `updated_at`

---

## 🛠️ טכנולוגיות ומערכות

### Backend
- **Python 3.8+** - שפת תכנות ראשית
- **Flask** - Web Framework
- **MySQL** - מסד נתונים
- **SQLAlchemy** - ORM
- **Pandas & NumPy** - עיבוד נתונים
- **scikit-learn** - Machine Learning
- **Prophet** - תחזיות זמן (Time Series)
- **ARIMA** (statsmodels) - תחזיות מתקדמות
- **JWT** - Authentication
- **Werkzeug** - Security (Password Hashing)

### Frontend
- **HTML5/CSS3** - מבנה ועיצוב
- **Bootstrap 5** - Framework רספונסיבי
- **Bootstrap Icons** - אייקונים
- **JavaScript (ES6+)** - לוגיקה אינטראקטיבית
- **Plotly.js** - ויזואליזציה מתקדמת

### DevOps
- **Docker** - Containerization
- **docker-compose** - אורכיסטרציה
- **GitHub Actions** - CI/CD

### Data Processing
- **ETL Pipeline** - Extract, Transform, Load
- **Faker** - יצירת נתונים סינתטיים
- **openpyxl** - קריאת/כתיבת Excel
- **fpdf2** - יצירת דוחות PDF

---

## 📁 מבנה הפרויקט

```
BusinessIntelligence/
│
├── 📂 app/                          # אפליקציית Flask
│   ├── app.py                      # Backend ראשי (1,939 שורות!)
│   ├── 📂 static/
│   │   ├── 📂 css/
│   │   │   └── style.css           # עיצוב + מצב כהה
│   │   └── 📂 js/
│   │       ├── dashboard.js        # לוגיקת דשבורד
│   │       └── admin_users.js      # ניהול משתמשים
│   └── 📂 templates/
│       ├── base.html               # Template בסיס
│       ├── index.html              # דשבורד ראשי
│       ├── login.html              # דף התחברות
│       ├── insights.html           # תובנות עסקיות
│       ├── about.html              # אודות
│       └── admin_users.html        # ניהול משתמשים
│
├── 📂 data/
│   └── 📂 raw_excel/               # נתונים גולמיים
│       ├── sales_raw.xlsx          # ~67,000 עסקאות
│       ├── products.xlsx           # 200 מוצרים
│       ├── stores.xlsx              # 20 סניפים
│       └── customers.xlsx           # 1,000 לקוחות
│
├── 📂 data_generation/
│   └── generate_data.py            # יצירת נתונים סינתטיים
│
├── 📂 etl/
│   └── etl_pipeline.py             # תהליך ETL מלא
│
├── 📂 warehouse/
│   └── star_schema.sql             # סכימת Data Warehouse
│
├── 📂 scripts/
│   ├── create_users.py             # יצירת משתמשים
│   └── create_sample_notifications.py
│
├── 📂 insights/
│   └── business_insights.md         # תובנות עסקיות
│
├── 📂 .github/
│   └── 📂 workflows/
│       └── ci.yml                   # CI/CD Pipeline
│
├── Dockerfile                       # Docker Image
├── docker-compose.yml               # Docker Compose
├── .dockerignore                    # קבצים להתעלם
├── requirements.txt                 # Python Dependencies
└── README.md                        # תיעוד ראשי
```

---

## 🚀 תהליך העבודה (Workflow)

### 1. יצירת נתונים
```bash
python data_generation/generate_data.py
```
- יוצר קבצי Excel עם נתונים סינתטיים
- ~67,000 עסקאות מכירה
- 200 מוצרים, 20 סניפים, 1,000 לקוחות

### 2. ETL Pipeline
```bash
python etl/etl_pipeline.py
```
**מה קורה:**
1. יצירת מסד הנתונים `BusinessIntelligence`
2. יצירת טבלאות (Star Schema)
3. טעינת נתונים מ-Excel
4. ניקוי וטרנספורמציה
5. בדיקות איכות נתונים
6. יצירת Indexes לביצועים

### 3. יצירת משתמשים
```bash
python scripts/create_users.py
```
- משתמש Admin: `admin` / `admin123`
- משתמשי Store Manager: `store_1` עד `store_20`

### 4. הפעלת האפליקציה
```bash
# דרך רגילה
python app/app.py

# דרך Docker
docker compose up --build
```

---

## 📊 תכונות המערכת

### 1. דשבורד ראשי (`/`)

#### KPIs מרכזיים
- **Total Revenue** - סך הכנסות
- **Total Profit** - סך רווח
- **Profit Margin (%)** - שולי רווח
- **Average Order Value** - ערך הזמנה ממוצע
- **Total Transactions** - סך עסקאות

#### גרפים וניתוחים
1. **Revenue & Profit Trend** - מגמת הכנסות ורווח לאורך זמן
2. **Sales by Store** - ביצועי סניפים (גרף עמודות)
3. **Top Products** - 10 המוצרים המובילים
4. **Category Revenue** - הכנסות לפי קטגוריה (Pie Chart)
5. **Customer Insights** - ניתוח לקוחות (גיל, מגדר)
6. **Seasonal Analysis** - ניתוח עונתי (רבעונים, חודשים)
7. **Sales Forecast** - תחזית מכירות (6 חודשים קדימה)
8. **Inventory Management** - ניהול מלאי חכם

### 2. פילטרים דינמיים

הדשבורד תומך בפילטרים מתקדמים:
- **תאריכים** - טווח תאריכים (מתאריך עד תאריך)
- **סניפים** - בחירת סניפים ספציפיים
- **קטגוריות** - סינון לפי קטגוריות מוצרים
- **אזורים** - סינון לפי אזורים גיאוגרפיים

**הערה חשובה:** Store Managers רואים רק את נתוני הסניף שלהם (אוטומטי)

### 3. תחזיות מכירות (`/api/sales-forecast`)

תמיכה ב-3 מודלים:
1. **Linear Regression** - פשוט ומהיר
2. **ARIMA** - מתקדם, תומך ב-seasonality
3. **Prophet** - של Facebook, מתאים למגמות עונתיות

**פרמטרים:**
- `months` - מספר חודשים לחיזוי (ברירת מחדל: 6)
- `model` - בחירת מודל (linear/arima/prophet)
- `arima_order` - פרמטרי ARIMA (לדוגמה: "1,1,1")

### 4. ניהול מלאי חכם (`/api/inventory-*`)

#### תכונות:
- **EOQ Calculation** - חישוב כמות הזמנה אופטימלית
- **Reorder Point** - נקודת הזמנה אוטומטית
- **Auto Order Suggestions** - הצעות הזמנה אוטומטיות
- **Central Inventory** - ניהול מלאי מרכזי
- **Store Inventory** - מלאי לפי סניף
- **Low Stock Alerts** - התראות על מלאי נמוך

#### נוסחאות:
- **EOQ** = √(2 × D × S / H)
  - D = ביקוש שנתי
  - S = עלות הזמנה
  - H = עלות אחסון ליחידה
- **Reorder Point** = (ביקוש יומי ממוצע × זמן אספקה) + Safety Stock

### 5. סגמנטציה של לקוחות (`/api/customer-segments`)

שימוש ב-**K-Means Clustering** לחלוקת לקוחות ל-3 קבוצות:
- **High Value** - לקוחות בעלי ערך גבוה
- **Medium Value** - לקוחות בעלי ערך בינוני
- **Low Value** - לקוחות בעלי ערך נמוך

**פרמטרים:**
- `n_clusters` - מספר קבוצות (ברירת מחדל: 3)
- `features` - תכונות לניתוח (revenue, frequency, recency)

### 6. זיהוי אנומליות (`/api/anomaly-detection`)

זיהוי חריגות בנתונים:
- מכירות חריגות (גבוהות/נמוכות מהנורמה)
- רווחיות חריגה
- פעילות חריגה בסניפים

**שיטה:** Z-Score Analysis + IQR (Interquartile Range)

### 7. מערכת התראות (`/api/notifications`)

**סוגי התראות:**
- `low_stock` - מלאי נמוך
- `high_sales` - מכירות גבוהות
- `anomaly` - חריגות
- `forecast` - תחזיות
- `system` - התראות מערכת

**חומרה (Severity):**
- `info` - מידע
- `warning` - אזהרה
- `critical` - קריטי

**תכונות:**
- ספירת התראות לא נקראות
- סימון כנקרא/לא נקרא
- סימון הכל כנקרא
- התראות לפי משתמש/סניף

### 8. ניהול משתמשים (`/admin/users`)

**זמין רק ל-Admin:**
- ✅ הוספת משתמש חדש
- ✅ עריכת משתמש קיים
- ✅ מחיקת משתמש
- ✅ שינוי סיסמה
- ✅ הפעלה/השבתה של משתמש

**תפקידים:**
- **Admin** - גישה מלאה
- **Store Manager** - גישה רק לסניף שלו

### 9. ייצוא נתונים

**פורמטים:**
- **CSV** (`/api/export-csv`) - עד 10,000 שורות
- **Excel** (`/api/export-excel`) - עם פורמט
- **PDF** (`/api/export-pdf`) - דוחות מפורמטים

**תכונות:**
- ייצוא עם כל הפילטרים הפעילים
- כותרות בעברית
- פורמט מקצועי

### 10. שיתוף דשבורד

יצירת קישור דינמי עם כל הפילטרים:
```
http://localhost:5000/?date_start=2024-01-01&date_end=2024-12-31&stores=1,2,3
```

---

## 🔐 אבטחה והרשאות

### Authentication
- **JWT Tokens** - ניהול סשן מאובטח
- **Password Hashing** - bcrypt (Werkzeug)
- **Session Management** - Flask Sessions

### Authorization (RBAC)
- **Admin** - גישה מלאה לכל הנתונים
- **Store Manager** - גישה רק לנתוני הסניף שלו

### Security Best Practices
- ✅ Parameterized Queries (מניעת SQL Injection)
- ✅ Password Hashing
- ✅ CORS Configuration
- ✅ Secret Keys (יש לשנות ב-Production!)

---

## 📡 API Endpoints

### Authentication
- `POST /api/login` - התחברות
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
- `GET /api/customer-segments` - סגמנטציה של לקוחות
- `GET /api/anomaly-detection` - זיהוי אנומליות
- `GET /api/business-insights` - תובנות עסקיות
- `GET /api/filters` - אפשרויות פילטרים

### Inventory Management
- `GET /api/inventory-optimization` - חישוב EOQ/RP
- `GET /api/inventory-reorder-suggestions` - הצעות הזמנה
- `GET /api/inventory-availability` - זמינות מלאי
- `GET /api/inventory-auto-orders` - הזמנות אוטומטיות

### User Management (Admin Only)
- `GET /api/users` - רשימת משתמשים
- `POST /api/users` - יצירת משתמש
- `PUT /api/users/<id>` - עדכון משתמש
- `DELETE /api/users/<id>` - מחיקת משתמש
- `POST /api/change-password` - שינוי סיסמה

### Notifications
- `GET /api/notifications` - רשימת התראות
- `POST /api/notifications/<id>/read` - סימון כנקרא
- `POST /api/notifications/read-all` - סימון הכל כנקרא

### Export
- `GET /api/export-csv` - ייצוא ל-CSV
- `GET /api/export-excel` - ייצוא ל-Excel
- `GET /api/export-pdf` - ייצוא ל-PDF

### User Preferences (חדש!)
- `GET /api/user-preferences` - קבלת העדפות
- `POST /api/user-preferences` - עדכון העדפות
- `GET /api/theme` - קבלת נושא (light/dark)

---

## 🎨 UI/UX Features

### עיצוב מודרני
- ✅ Bootstrap 5 - רספונסיבי מלא
- ✅ Bootstrap Icons - אייקונים מקצועיים
- ✅ Plotly.js - גרפים אינטראקטיביים
- ✅ Animations - אנימציות חלקות
- ✅ Hover Effects - אפקטים על hover

### מצב כהה/בהיר
- ✅ כפתור החלפה בסרגל העליון
- ✅ שמירה אוטומטית בהעדפות משתמש
- ✅ מעבר חלק בין מצבים

### רספונסיביות
- ✅ Mobile First Design
- ✅ Tablet Optimization
- ✅ Desktop Full Features
- ✅ גרפים מותאמים למסך

### נגישות
- ✅ תמיכה ב-RTL (עברית)
- ✅ תמיכה בקוראי מסך (בתהליך)
- ✅ ניגודיות גבוהה

---

## 🐳 Docker & DevOps

### Docker
- **Dockerfile** - Image מותאם
- **docker-compose.yml** - אורכיסטרציה (App + MySQL)
- **.dockerignore** - אופטימיזציה

### CI/CD
- **GitHub Actions** - בדיקות אוטומטיות
- **Syntax Checks** - בדיקת קוד Python
- **Linting** - בדיקת איכות קוד

---

## 📈 Machine Learning & AI

### מודלים מיושמים

1. **Linear Regression**
   - תחזיות מכירות פשוטות
   - מהיר וקל לפרשנות

2. **ARIMA** (AutoRegressive Integrated Moving Average)
   - תחזיות מתקדמות
   - תמיכה ב-seasonality
   - פרמטרים: (p, d, q)

3. **Prophet** (Facebook)
   - תחזיות עונתיות
   - תמיכה ב-trends ו-holidays

4. **K-Means Clustering**
   - סגמנטציה של לקוחות
   - 3 קבוצות: High/Medium/Low Value

5. **Anomaly Detection**
   - Z-Score Analysis
   - IQR Method

---

## 🔄 תהליך ETL

### Extract (חילוץ)
- קריאת נתונים מ-Excel
- `pandas.read_excel()`

### Transform (טרנספורמציה)
- ניקוי נתונים
- חישוב שדות חדשים (profit, revenue)
- יצירת מימד תאריכים
- נרמול נתונים

### Load (טעינה)
- טעינה ל-MySQL
- יצירת Indexes
- בדיקות איכות נתונים

---

## 📊 דוגמאות לשאילתות SQL

### KPI - סך הכנסות
```sql
SELECT SUM(revenue) AS total_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
WHERE d.date BETWEEN '2024-01-01' AND '2024-12-31'
```

### Top Products
```sql
SELECT 
    p.product_name,
    SUM(f.revenue) AS total_revenue,
    SUM(f.profit) AS total_profit
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name
ORDER BY total_revenue DESC
LIMIT 10
```

### Store Performance
```sql
SELECT 
    s.store_name,
    s.city,
    s.region,
    SUM(f.revenue) AS revenue,
    SUM(f.profit) AS profit,
    COUNT(*) AS transactions
FROM fact_sales f
JOIN dim_store s ON f.store_id = s.store_id
GROUP BY s.store_id, s.store_name, s.city, s.region
ORDER BY revenue DESC
```

---

## 🎯 שימושים עסקיים

### למנהל כללי (CEO)
- ✅ סקירה כללית של ביצועים
- ✅ השוואת סניפים
- ✅ מגמות רווחיות
- ✅ תחזיות עתידיות

### למנהל סניף
- ✅ ביצועי הסניף שלו בלבד
- ✅ ניהול מלאי מקומי
- ✅ התראות על בעיות
- ✅ דוחות יומיים/שבועיים

### לאנליסט
- ✅ ניתוחים מתקדמים
- ✅ סגמנטציה של לקוחות
- ✅ זיהוי אנומליות
- ✅ תחזיות מכירות

### למחלקת כספים
- ✅ ניתוח רווחיות
- ✅ עלויות ותקציבים
- ✅ דוחות פיננסיים
- ✅ ייצוא ל-Excel/PDF

---

## 🚧 תכונות עתידיות (Roadmap)

### שלב 1 - ערך מידי
- ✅ UI/UX מודרני + רספונסיבי
- ✅ קונפיגורציה אישית
- ⏳ Activity Log מתקדם
- ⏳ חיפוש משופר

### שלב 2 - AI/ML
- ⏳ XGBoost / LSTM לתחזיות
- ⏳ Isolation Forest לאנומליות
- ⏳ Product Recommendations
- ⏳ Hyperparameter Tuning

### שלב 3 - אוטומציה
- ⏳ הזמנות מלאי אוטומטיות
- ⏳ דוחות תקופתיים (Email)
- ⏳ התראות WhatsApp/SMS
- ⏳ ניתוח עונתי מתקדם

### שלב 4 - DevOps
- ✅ Docker
- ✅ CI/CD בסיסי
- ⏳ פריסה ל-AWS/Heroku
- ⏳ Monitoring & Logging

### שלב 5 - אינטגרציות
- ⏳ ERP Systems (SAP, Odoo)
- ⏳ פלטפורמות מכירה (eBay, Amazon)
- ⏳ Payment Gateways

---

## 📝 הוראות שימוש

### התקנה ראשונית

1. **התקן Python 3.8+**
2. **התקן MySQL 5.7+**
3. **התקן חבילות:**
   ```bash
   pip install -r requirements.txt
   ```
4. **צור נתונים:**
   ```bash
   python data_generation/generate_data.py
   ```
5. **הרץ ETL:**
   ```bash
   python etl/etl_pipeline.py
   ```
6. **צור משתמשים:**
   ```bash
   python scripts/create_users.py
   ```
7. **הפעל אפליקציה:**
   ```bash
   python app/app.py
   ```

### התחברות
- **Admin**: `admin` / `admin123`
- **Store Manager**: `store_1` / `store1123`

### Docker
```bash
docker compose up --build
```

---

## 🐛 פתרון בעיות נפוצות

### שגיאת התחברות ל-MySQL
- ודא ש-MySQL רץ
- בדוק `DB_CONFIG` ב-`app.py`
- ודא שהמשתמש קיים

### טבלאות לא נוצרות
- הרץ `warehouse/star_schema.sql` ידנית
- או הרץ `etl/etl_pipeline.py` מחדש

### נתונים לא נטענים
- ודא ש-Excel files קיימים
- הרץ `generate_data.py` מחדש
- הרץ `etl_pipeline.py` מחדש

### שגיאות Python
- ודא שכל החבילות מותקנות
- בדוק גרסת Python (3.8+)
- ראה `requirements.txt`

---

## 📚 משאבים נוספים

- **README.md** - תיעוד מפורט
- **Code Comments** - הערות בקוד
- **API Documentation** - תיעוד API
- **Database Schema** - `warehouse/star_schema.sql`

---

## 🎓 למידה מהפרויקט

### מה למדנו
1. ✅ בניית Data Warehouse (Star Schema)
2. ✅ פיתוח ETL Pipeline
3. ✅ בניית REST API עם Flask
4. ✅ Machine Learning בפרויקט אמיתי
5. ✅ ניהול משתמשים ואבטחה
6. ✅ Docker & DevOps
7. ✅ UI/UX מודרני

### מיומנויות שנרכשו
- Python (Advanced)
- SQL (Complex Queries)
- Flask (Web Development)
- Data Science (Pandas, NumPy)
- Machine Learning (scikit-learn)
- Docker & DevOps
- Frontend (JavaScript, Bootstrap)

---

## 📊 סטטיסטיקות הפרויקט

- **שורות קוד**: ~5,000+ שורות
- **קבצים**: 20+ קבצים
- **API Endpoints**: 30+ endpoints
- **טבלאות DB**: 10+ טבלאות
- **נתונים**: 67,000+ עסקאות
- **זמן פיתוח**: מספר חודשים

---

## 🏆 הישגים

✅ מערכת BI מלאה ומקצועית  
✅ Data Warehouse עם Star Schema  
✅ מערכת משתמשים מאובטחת  
✅ תחזיות מכירות מתקדמות  
✅ ניהול מלאי חכם  
✅ UI/UX מודרני ורספונסיבי  
✅ Docker & CI/CD  
✅ תיעוד מפורט  

---

**נבנה עם ❤️ באמצעות Python, Flask, MySQL & Plotly**

© 2024 Retail Business Intelligence System

