# 📊 Retail Business Intelligence Web Application

מערכת Business Intelligence מלאה לניתוח נתוני מכירות, רווחיות ומלאי של רשת קמעונאות.

## 🎯 מטרת הפרויקט

פיתוח מערכת BI מבוססת Web המספקת:
- ✅ ניתוח מכירות, רווחיות ומלאי
- ✅ תמיכה בקבלת החלטות ניהוליות
- ✅ הצגת KPIs ו-Insights עסקיים
- ✅ סימולציה של סביבת BI ארגונית אמיתית

## 🏗️ מבנה הפרויקט

```
retail-bi-project/
│
├── data/
│   └── raw_excel/          # קבצי Excel גולמיים
│       ├── sales_raw.xlsx
│       ├── products.xlsx
│       ├── stores.xlsx
│       └── customers.xlsx
│
├── data_generation/
│   └── generate_data.py    # יצירת נתונים סינתטיים
│
├── etl/
│   └── etl_pipeline.py     # ETL Pipeline
│
├── warehouse/
│   └── star_schema.sql     # Data Warehouse Schema
│
├── app/
│   ├── app.py              # Flask Web Application
│   ├── templates/
│   │   └── index.html      # HTML Template
│   └── static/
│       ├── css/
│       │   └── style.css   # Stylesheet
│       └── js/
│           └── dashboard.js # JavaScript Dashboard Logic
│
├── insights/
│   └── business_insights.md # Business Insights
│
├── requirements.txt        # Python Dependencies
└── README.md              # Documentation
```

## 🛠️ טכנולוגיות

### Backend / Data
- **Python 3.8+**
- **Pandas, NumPy** - עיבוד נתונים
- **Faker** - יצירת נתונים סינתטיים
- **SQL (MySQL)** - Data Warehouse

### Web Application
- **Flask** - Web Framework
- **Plotly.js** - ויזואליזציה אינטראקטיבית בדפדפן
- **HTML/CSS/JavaScript** - Frontend רגיל

## 📋 דרישות מערכת

1. **Python 3.8+**
2. **MySQL Server** (5.7+ או 8.0+)
3. **pip** - מנהל חבילות Python

## 🚀 התקנה והפעלה

### שלב 1: התקנת תלויות

```bash
pip install -r requirements.txt
```

### שלב 2: הגדרת MySQL

1. התקן MySQL Server אם עדיין לא מותקן
2. צור משתמש MySQL (או השתמש ב-root)
3. עדכן את פרטי החיבור ב-`etl/etl_pipeline.py` ו-`app/app.py`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'retail_bi',
    'user': 'root',        # שנה לפי הצורך
    'password': 'root',    # שנה לסיסמה שלך
    'charset': 'utf8mb4'
}
```

### שלב 3: יצירת נתונים

הרץ את הסקריפט ליצירת נתונים סינתטיים:

```bash
python data_generation/generate_data.py
```

זה ייצור 4 קבצי Excel בתיקייה `data/raw_excel/`:
- `sales_raw.xlsx` - ~150,000 עסקאות מכירה
- `products.xlsx` - 200 מוצרים
- `stores.xlsx` - 20 סניפים
- `customers.xlsx` - 1,000 לקוחות

### שלב 4: הרצת ETL Pipeline

הרץ את ה-ETL Pipeline לטעינת הנתונים ל-Data Warehouse:

```bash
python etl/etl_pipeline.py
```

הסקריפט יבצע:
1. יצירת מסד הנתונים `retail_bi` (אם לא קיים)
2. יצירת טבלאות (Star Schema)
3. טעינת נתונים מ-Excel ל-SQL
4. יצירת Views לשאילתות נפוצות

### שלב 4.5: יצירת משתמשים למערכת

יצירת משתמשים לכניסה למערכת:

```bash
python scripts/create_users.py
```

הסקריפט יוצר:
- משתמש **admin** - גישה מלאה לכל הנתונים
- משתמש לכל סניף - גישה רק לנתוני הסניף שלו

**פרטי כניסה ברירת מחדל:**
- Admin: `username=admin`, `password=admin123`
- Store Managers: `username=store_X`, `password=storeX123` (X = store_id)

⚠️ **חשוב**: שנה את הסיסמאות לאחר הכניסה הראשונה!

### שלב 5: הפעלת Web Application

הרץ את אפליקציית Flask:

```bash
cd app
python app.py
```

האפליקציה תיפתח בדפדפן בכתובת: `http://localhost:5000`

## 📊 Data Warehouse Design (Star Schema)

### ⭐ Fact Table

**fact_sales**
- `sale_id` (PK)
- `date_id` (FK)
- `store_id` (FK)
- `product_id` (FK)
- `customer_id` (FK)
- `quantity`
- `revenue`
- `cost`
- `profit`

### 🔹 Dimension Tables

**dim_date**
- `date_id`, `date`, `day`, `month`, `quarter`, `year`, `month_name`, `quarter_name`, `day_of_week`, `is_weekend`

**dim_store**
- `store_id`, `store_name`, `city`, `region`, `store_type`, `opening_date`

**dim_product**
- `product_id`, `product_name`, `category`, `brand`, `price`, `cost`

**dim_customer**
- `customer_id`, `customer_name`, `gender`, `age`, `age_group`, `city`

## 📈 KPIs מרכזיים

### 💰 פיננסי
- **Total Revenue** - סך הכנסות
- **Total Profit** - סך רווח
- **Profit Margin (%)** - שולי רווח
- **Average Order Value** - ערך הזמנה ממוצע

### 📈 מכירות
- **Monthly Sales Trend** - מגמת מכירות חודשית
- **Top 10 Products** - 10 המוצרים המובילים
- **Sales by Category** - מכירות לפי קטגוריה

### 🏪 סניפים
- **Revenue by Store** - הכנסות לפי סניף
- **Store Performance Comparison** - השוואת ביצועי סניפים
- **Profit Margin by Store** - שולי רווח לפי סניף

## 🎨 Dashboards

### Executive Dashboard
- KPI Cards - מדדי ביצוע מרכזיים
- Revenue Trend - מגמת הכנסות
- Profit by Store - רווח לפי סניף
- Top Products - מוצרים מובילים

### Product & Inventory Dashboard
- Category Performance - ביצועי קטגוריות
- Product Analysis - ניתוח מוצרים
- Sales vs Profit - מכירות מול רווח

### Filters
- **Date Range** - טווח תאריכים
- **Store** - בחירת סניפים
- **Category** - בחירת קטגוריות
- **Region** - בחירת אזורים

## 💡 Business Insights

המערכת כוללת מסמך Business Insights (`insights/business_insights.md`) המכיל:
- ניתוח ביצועים
- המלצות אסטרטגיות
- זיהוי הזדמנויות
- ניתוח סיכונים

## 🔧 פתרון בעיות

### בעיית חיבור ל-MySQL
- ודא ש-MySQL Server פועל
- בדוק את פרטי החיבור ב-`DB_CONFIG`
- ודא שהמסד `retail_bi` קיים

### שגיאות בטעינת נתונים
- ודא שקבצי Excel קיימים ב-`data/raw_excel/`
- הרץ שוב את `generate_data.py` אם צריך

### בעיות עם Flask
- ודא שכל התלויות מותקנות: `pip install -r requirements.txt`
- נסה להריץ: `python -c "import flask; print(flask.__version__)"`

## 📝 הערות חשובות

1. **נתונים סינתטיים**: כל הנתונים נוצרים אוטומטית באמצעות Faker
2. **ביצועים**: לנתונים גדולים, שקול להוסיף אינדקסים נוספים
3. **אבטחה**: בסביבת ייצור, השתמש בסיסמאות חזקות ו-SSL

## 🎓 שימוש בקורות חיים

פרויקט זה מדגים:
- ✅ כישורי Python (Pandas, NumPy)
- ✅ עבודה עם SQL ו-Data Warehouses
- ✅ פיתוח ETL Pipelines
- ✅ בניית Web Applications
- ✅ Data Visualization
- ✅ Business Intelligence

## 📞 תמיכה

לשאלות או בעיות, בדוק:
1. את קובץ ה-README הזה
2. את הודעות השגיאה בקונסול
3. את הלוגים של MySQL

## 📄 רישיון

פרויקט זה נוצר למטרות לימודיות והדגמה.

---

**נבנה עם ❤️ באמצעות Python, Flask, ו-MySQL**
