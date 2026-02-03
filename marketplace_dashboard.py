import streamlit as st
import pandas as pd
import pymongo
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from bson import ObjectId

# -------------------------------------------------------
# 🔌 CONFIGURATION & CONNECTION
# -------------------------------------------------------
st.set_page_config(
    page_title="MongoDB Sharding Dashboard ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# MongoDB Connection
@st.cache_resource
def init_connection():
    try:
        MONGO_URI = "mongodb://localhost:27025"  # ajuste si besoin
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client
    except Exception as e:
        # Ne raise pas pour que l'app puisse démarrer même sans DB
        st.error(f"❌ Connection failed: {e}")
        return None

client = init_connection()
if client:
    db = client.get_database("marketplace")
    products = db.get_collection("products")
    config_db = client.get_database("config")
else:
    db = None
    products = None
    config_db = None

def safe_rerun():
    """
    Re-exécute la page Streamlit de façon robuste :
    - utilise st.experimental_rerun() si disponible,
    - sinon tente de lever RerunException (API interne),
    - sinon modifie les query params pour forcer un reload et stoppe l'exécution.
    """
    # 1) try the public API
    try:
        if hasattr(st, "experimental_rerun"):
            return st.experimental_rerun()
    except Exception:
        # continue to fallback attempts
        pass

    # 2) try the internal rerun exception (different Streamlit versions use different import paths)
    try:
        from streamlit.runtime.scriptrunner import RerunException
        raise RerunException()
    except Exception:
        try:
            from streamlit.script_runner import RerunException as _R
            raise _R()
        except Exception:
            # 3) final fallback: update query params (causes client reload) and stop execution
            try:
                st.experimental_set_query_params(_rerun=int(time.time()))
            except Exception:
                pass
            st.stop()

# -------------------------------------------------------
# 🔧 HELPERS (PLACÉ ICI POUR ÉVITER NameError)
# -------------------------------------------------------
@st.cache_data(ttl=60)
def load_products(query_dict, limit=5000):
    """Charge des documents depuis la collection products et renvoie un DataFrame."""
    if products is None:
        return pd.DataFrame()
    try:
        docs = list(products.find(query_dict).limit(limit))
        # Convert ObjectId en string pour l'affichage
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])
        return pd.DataFrame(docs) if docs else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading products: {e}")
        return pd.DataFrame()

def safe_to_list(cursor, limit=1000):
    """Récupère les résultats d'un cursor en convertissant les ObjectId en str."""
    try:
        docs = list(cursor) if not hasattr(cursor, '__iter__') else list(cursor)
    except Exception:
        docs = cursor or []
    out = []
    for d in docs[:limit]:
        if isinstance(d, dict) and "_id" in d:
            d["_id"] = str(d["_id"])
        out.append(d)
    return out

def format_ms(t0, t1):
    return (t1 - t0) * 1000.0

def execute_test_query(selected_query):
    """
    Exécute une requête de test simple sur la collection products.
    Retourne (result_list, query_code_str, exec_time_ms)
    """
    if products is None:
        return [], "// No DB connection", 0.0

    start = time.time()
    query_code = ""
    result = []

    try:
        if selected_query == "🔍 seller_id = 3":
            query = {"seller_id": 3}
            query_code = "db.products.find({ seller_id: 3 }).limit(100)"
            cursor = products.find(query).limit(100)
            result = safe_to_list(cursor)

        elif selected_query == "📌 status = 'active'":
            query = {"status": "active"}
            query_code = "db.products.find({ status: 'active' }).limit(200)"
            cursor = products.find(query).limit(200)
            result = safe_to_list(cursor)

        elif selected_query == "📂 category_id = 'beauty' + projection":
            query = {"category_id": "beauty"}
            projection = {"title": 1, "price": 1, "seller_id": 1}
            query_code = "db.products.find({ category_id: 'beauty' }, { title:1, price:1, seller_id:1 }).limit(200)"
            cursor = products.find(query, projection).limit(200)
            result = safe_to_list(cursor)

        elif selected_query == "💰 seller_id = 8 + price range":
            query = {"seller_id": 8, "price": {"$gte": 50, "$lte": 300}}
            query_code = "db.products.find({ seller_id:8, price:{ $gte:50, $lte:300 } }).limit(200)"
            cursor = products.find(query).limit(200)
            result = safe_to_list(cursor)

        elif selected_query == "📊 status = 'active' + sort by price":
            query = {"status": "active"}
            query_code = "db.products.find({ status:'active' }).sort({ price: -1 }).limit(200)"
            cursor = products.find(query).sort("price", -1).limit(200)
            result = safe_to_list(cursor)

        elif selected_query == "🔎 title regex 'jacket'":
            query = {"title": {"$regex": "jacket", "$options": "i"}}
            query_code = "db.products.find({ title: /jacket/i }).limit(200)"
            cursor = products.find(query).limit(200)
            result = safe_to_list(cursor)

        elif selected_query == "📈 avg price per category":
            pipeline = [
                {"$match": {"price": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$category_id", "avg_price": {"$avg": "$price"}, "count": {"$sum": 1}}},
                {"$sort": {"avg_price": -1}},
                {"$limit": 50}
            ]
            query_code = "db.products.aggregate([ { $group: { _id: '$category_id', avg_price: { $avg: '$price' } } } ])"
            cursor = products.aggregate(pipeline)
            result = safe_to_list(cursor)

        elif selected_query == "📝 text search 'floral fragrance'":
            # Nécessite un index texte sur les champs appropriés : db.products.createIndex({ title: "text", description: "text" })
            query_code = "db.products.find({ $text: { $search: 'floral fragrance' } }).limit(200)"
            try:
                cursor = products.find({"$text": {"$search": "floral fragrance"}}).limit(200)
                result = safe_to_list(cursor)
            except Exception as e:
                result = [{"error": "Text search failed — make sure text index exists", "detail": str(e)}]

        else:
            query_code = "// Unknown test query"
            result = []

    except Exception as e:
        result = [{"error": str(e)}]

    end = time.time()
    exec_time = format_ms(start, end)
    return result, query_code, exec_time

def display_query_results(query_type, result, chart_theme):
    """Affiche les résultats de la requête (ton code existant, légèrement durci)."""
    st.subheader("📊 Résultats")

    if not result:
        st.warning("Aucune donnée disponible")
        return

    df = pd.DataFrame(result)

    # Si _id présent et pas string, forcer string
    if "_id" in df.columns:
        df["_id"] = df["_id"].astype(str)

    if query_type == "🛍️ Produits les plus vendus (aujourd'hui)":
        st.metric("Total de produits", len(df))
        df['product_id'] = df['_id']
        chart_df = df[['product_id', 'sales']].head(10)
        fig = px.bar(chart_df, x='product_id', y='sales',
                    title="Top 10 Produits les plus vendus",
                    template=chart_theme)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['product_id', 'sales']], use_container_width=True)

    elif query_type == "💰 Top vendeurs du mois":
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total vendeurs", len(df))
        with col2:
            st.metric("Revenu total", f"${df['revenue'].sum():,.2f}")

        df['seller_id'] = df['_id']
        fig = px.bar(df.head(10), x='seller_id', y='revenue',
                    title="Top 10 Vendeurs par Revenu",
                    template=chart_theme)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['seller_id', 'revenue', 'total_orders']], use_container_width=True)

    elif query_type == "⭐ Produits les mieux notés":
        df['product_id'] = df['_id']
        if 'avg_rating' in df.columns:
            df['avg_rating'] = df['avg_rating'].round(2)
        fig = px.bar(df.head(10), x='product_id', y='avg_rating',
                    title="Top 10 Produits les mieux notés",
                    template=chart_theme)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['product_id', 'avg_rating', 'review_count']], use_container_width=True)

    elif query_type == "🚚 Temps de livraison par vendeur":
        df['seller_id'] = df['_id']
        if 'avg_delivery_days' in df.columns:
            df['avg_delivery_days'] = df['avg_delivery_days'].round(1)
            st.metric("Délai moyen global", f"{df['avg_delivery_days'].mean():.1f} jours")
        fig = px.bar(df.head(15), x='seller_id', y='avg_delivery_days',
                    title="Temps de livraison moyen par vendeur",
                    template=chart_theme)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['seller_id', 'avg_delivery_days']], use_container_width=True)

    elif query_type == "📈 Pics de trafic (2 dernières heures)":
        if '_id' in df.columns and df['_id'].apply(lambda x: isinstance(x, dict)).any():
            df['hour'] = df['_id'].apply(lambda x: x.get('hour', 0) if isinstance(x, dict) else 0)
        fig = px.line(df, x='hour', y='orders',
                     title="Trafic des commandes (2 dernières heures)",
                     template=chart_theme)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['hour', 'orders']], use_container_width=True)

    elif query_type == "🛒 Analyse des paniers abandonnés":
        st.metric("Utilisateurs avec paniers abandonnés", len(df))
        if 'abandoned_items' in df.columns:
            st.metric("Total items abandonnés", int(df['abandoned_items'].sum()))
        df['user_id'] = df['_id']
        fig = px.bar(df.head(20), x='user_id', y='abandoned_items',
                    title="Top 20 Utilisateurs - Paniers abandonnés",
                    template=chart_theme)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['user_id', 'abandoned_items']], use_container_width=True)

    elif query_type == "💸 Heatmap des prix par catégorie":
        if '_id' in df.columns and df['_id'].apply(lambda x: isinstance(x, dict)).any():
            df['category'] = df['_id'].apply(lambda x: x.get('category_id', 'Unknown') if isinstance(x, dict) else 'Unknown')
        df = df.round(2)
        if 'avg_price' in df.columns:
            fig = px.bar(df.head(15), x='category', y='avg_price',
                        title="Prix moyen par catégorie (Top 15)",
                        template=chart_theme)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[['category', 'avg_price', 'min_price', 'max_price']], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

    elif query_type == "⚖️ Test de balancing des shards":
        df['seller_id'] = df['_id']
        st.metric("Vendeurs analysés", len(df))

        fig = px.bar(df.head(25), x='seller_id', y='products',
                    title="Distribution des produits par vendeur (Top 25)",
                    template=chart_theme)
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Moyenne", f"{int(df['products'].mean())}" if 'products' in df.columns else "N/A")
        with col2:
            st.metric("Écart-type", f"{int(df['products'].std())}" if 'products' in df.columns else "N/A")
        with col3:
            if 'products' in df.columns and df['products'].min() > 0:
                st.metric("Ratio Max/Min", f"{df['products'].max() / df['products'].min():.2f}x")
            else:
                st.metric("Ratio Max/Min", "N/A")

        st.dataframe(df[['seller_id', 'products']] if 'products' in df.columns else df, use_container_width=True)

    else:
        st.dataframe(df, use_container_width=True)

# -------------------------------------------------------
# 🎨 ENHANCED CSS STYLING
# (identique à ton bloc — inchangé sauf sécurité)
# -------------------------------------------------------
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
    }
    
    .subtitle {
        text-align: center;
        color: #6c757d;
        font-size: 16px;
        margin-bottom: 30px;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .section-divider {
        margin: 40px 0;
        border-top: 2px solid #e9ecef;
    }
    
    .info-box {
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    
    .info-box-success {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
    
    .info-box-warning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .info-box-info {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        border-radius: 8px;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
    }
    </style>
''', unsafe_allow_html=True)

# -------------------------------------------------------
# 🔧 SIDEBAR CONFIGURATION
# -------------------------------------------------------
with st.sidebar:
    st.image("https://www.mongodb.com/assets/images/global/leaf.svg", width=80)
    st.title("⚙️ Dashboard Control")
    
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "📍 Navigation",
        ["🏠 Overview", "📊 Analytics", "⚡ Performance", "🗂️ Sharding", "🧪 Test Requêtes"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Refresh Settings
    st.subheader("🔄 Refresh Settings")
    # st.toggle peut ne pas exister selon la version — on utilise checkbox
    enable_auto_refresh = st.checkbox("Enable Auto-Refresh", value=False)
    refresh_rate = st.slider("Refresh Interval (sec)", 5, 120, 30)
    
    st.markdown("---")
    
    # Display Options
    st.subheader("📊 Display Options")
    chart_theme = st.selectbox("Chart Theme", ["plotly", "plotly_dark", "plotly_white"]) 
    
    st.markdown("---")
    
    # Filters
    st.subheader("🔍 Data Filters")
    search_title = st.text_input("🔎 Search Title", placeholder="Enter product title...")
    
    price_range = st.slider("💰 Price Range", 0, 10000, (0, 5000))
    min_price, max_price = price_range
    
    vendor_filter = st.number_input("🏪 Vendor ID (0 = All)", 0, 5000, 0)
    
    category_filter = st.number_input("📂 Category ID (0 = All)", 0, 1000, 0)
    
    min_rating = st.slider("⭐ Minimum Rating", 0.0, 5.0, 0.0, 0.5)
    
    if st.button("🗑️ Clear Filters", use_container_width=True):
        safe_rerun()

    
    st.markdown("---")
    st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")

# -------------------------------------------------------
# 🔍 BUILD QUERY
# -------------------------------------------------------
query = {}
if search_title:
    query["title"] = {"$regex": search_title, "$options": "i"}
# only add price filter if user changed it from defaults
if min_price > 0 or max_price < 5000:
    query["price"] = {"$gte": min_price, "$lte": max_price}
if vendor_filter > 0:
    query["seller_id"] = vendor_filter
if category_filter > 0:
    query["category_id"] = category_filter
if min_rating > 0:
    query["rating"] = {"$gte": min_rating}

# -------------------------------------------------------
# 📊 LOAD DATA
# -------------------------------------------------------
df = load_products(dict(query))

# -------------------------------------------------------
# 🏷️ HEADER
# -------------------------------------------------------
st.markdown("<h1 class='main-header'>📊 MongoDB Sharding Dashboard </h1>", unsafe_allow_html=True)
st.markdown(f"<p class='subtitle'>Real-time monitoring & analytics • Connected to: <code>marketplace.products</code></p>", unsafe_allow_html=True)

# -------------------------------------------------------
# 🏠 OVERVIEW PAGE
# -------------------------------------------------------
if page == "🏠 Overview":
    st.subheader("📊 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    try:
        total_products = products.count_documents({}) if products is not None else 0
        filtered_products = len(df)
        unique_vendors = len(products.distinct("seller_id")) if products is not None else 0
        unique_categories = len(products.distinct("category_id")) if products is not None else 0
        
        avg_price_pipeline = []
        if products is not None:
            avg_price_pipeline = list(products.aggregate([
                {"$match": {"price": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": None, "avg": {"$avg": "$price"}}}
            ]))
        avg_price = avg_price_pipeline[0]["avg"] if avg_price_pipeline else 0
        
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        total_products = filtered_products = unique_vendors = unique_categories = avg_price = 0
    
    with col1:
        st.metric("📦 Total Products", f"{total_products:,}", delta=None)
    
    with col2:
        delta = filtered_products - total_products if query else None
        st.metric("🔍 Filtered", f"{filtered_products:,}", delta=f"{delta:,}" if delta else None)
    
    with col3:
        st.metric("🏪 Vendors", f"{unique_vendors:,}")
    
    with col4:
        st.metric("📂 Categories", f"{unique_categories:,}")
    
    with col5:
        st.metric("💰 Avg Price", f"${avg_price:.2f}")
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Quick Stats
    st.subheader("📈 Quick Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            shards = list(config_db["shards"].find({})) if config_db is not None else []
            chunks = list(config_db["chunks"].find({"ns": "marketplace.products"})) if config_db is not None else []
            
            st.markdown("### 🗂️ Sharding Status")
            st.metric("Active Shards", len(shards))
            st.metric("Total Chunks", len(chunks))
            
            if shards:
                st.success("✅ Sharding is configured and active")
            else:
                st.warning("⚠️ Sharding not configured")
        except Exception as e:
            st.error(f"Error: {e}")
    
    with col2:
        try:
            db_stats = db.command("dbStats") if db is not None else {}
            data_size = db_stats.get("dataSize", 0) / (1024**2)
            storage_size = db_stats.get("storageSize", 0) / (1024**2)
            
            st.markdown("### 💾 Storage Info")
            st.metric("Data Size", f"{data_size:.2f} MB")
            st.metric("Storage Size", f"{storage_size:.2f} MB")
            
            compression_ratio = (1 - data_size/storage_size) * 100 if storage_size > 0 else 0
            st.metric("Compression", f"{compression_ratio:.1f}%")
        except Exception as e:
            st.error(f"Error: {e}")

# -------------------------------------------------------
# 📊 ANALYTICS PAGE
# -------------------------------------------------------
elif page == "📊 Analytics":
    if not df.empty:
        st.subheader("📊 Data Analytics & Insights")
        
        anal_tab1, anal_tab2, anal_tab3, anal_tab4 = st.tabs([
            "📂 Categories", "🏪 Vendors", "💰 Pricing", "⭐ Ratings"
        ])
        
        with anal_tab1:
            try:
                cat_data = list(products.aggregate([
                    {"$group": {"_id": "$category_id", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 15}
                ])) if products is not None else []
                
                if cat_data:
                    df_cat = pd.DataFrame(cat_data)
                    df_cat.columns = ["Category", "Products"]
                    
                    fig = px.bar(df_cat, x="Category", y="Products",
                               title="Top 15 Categories by Product Count",
                               template=chart_theme, color="Products")
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")
        
        with anal_tab2:
            try:
                vendor_data = list(products.aggregate([
                    {"$group": {"_id": "$seller_id", "products": {"$sum": 1}}},
                    {"$sort": {"products": -1}},
                    {"$limit": 20}
                ])) if products is not None else []
                
                if vendor_data:
                    df_vendor = pd.DataFrame(vendor_data)
                    df_vendor.columns = ["Vendor ID", "Products"]
                    
                    fig = px.treemap(df_vendor, path=['Vendor ID'], values='Products',
                                   title="Top 20 Vendors - Product Distribution",
                                   template=chart_theme)
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")
        
        with anal_tab3:
            if "price" in df.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.histogram(df, x="price", nbins=50,
                                     title="Price Distribution",
                                     template=chart_theme,
                                     labels={"price": "Price ($)"})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.box(df, y="price", title="Price Box Plot",
                               template=chart_theme)
                    st.plotly_chart(fig, use_container_width=True)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Min Price", f"${df['price'].min():.2f}")
                col2.metric("Max Price", f"${df['price'].max():.2f}")
                col3.metric("Median", f"${df['price'].median():.2f}")
                col4.metric("Std Dev", f"${df['price'].std():.2f}")
        
        with anal_tab4:
            if "rating" in df.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    rating_counts = df['rating'].value_counts().sort_index()
                    fig = px.bar(x=rating_counts.index, y=rating_counts.values,
                               title="Rating Distribution",
                               labels={"x": "Rating", "y": "Count"},
                               template=chart_theme)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    avg_rating = df['rating'].mean()
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=avg_rating,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Average Rating"},
                        delta={'reference': 4.0},
                        gauge={'axis': {'range': [None, 5]},
                              'steps': [
                                  {'range': [0, 2.5], 'color': "lightgray"},
                                  {'range': [2.5, 4], 'color': "gray"}],
                              'threshold': {'line': {'color': "red", 'width': 4},
                                          'thickness': 0.75, 'value': 4.5}}
                    ))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        
        # Data Table
        st.subheader("📄 Product Data Browser")
        
        display_cols = [c for c in ["title", "price", "seller_id", "category_id", "rating", "stock", "created_at"] 
                       if c in df.columns]
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"Showing {min(len(df), 100)} of {len(df)} filtered products")
        with col2:
            if st.button("📥 Export to CSV", use_container_width=True):
                csv = df[display_cols].to_csv(index=False)
                st.download_button("Download", csv, "products.csv", "text/csv")
        
        st.dataframe(
            df[display_cols].head(100),
            use_container_width=True,
            hide_index=True,
            height=400
        )
    else:
        st.warning("⚠️ No products match your current filters")

# -------------------------------------------------------
# ⚡ PERFORMANCE PAGE
# -------------------------------------------------------
elif page == "⚡ Performance":
    st.subheader("⚡ Performance Monitoring")
    
    perf_tab1, perf_tab2, perf_tab3 = st.tabs(["🔍 Query Performance", "💾 Storage Stats", "📊 Collection Info"])
    
    with perf_tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            try:
                start = time.time()
                if products is not None:
                    products.find_one({"_id": {"$exists": True}})
                    simple_time = (time.time() - start) * 1000
                    st.metric("Simple Query", f"{simple_time:.2f} ms", 
                             delta="Excellent" if simple_time < 50 else "Slow")
                else:
                    st.metric("Simple Query", "N/A")
            except Exception as e:
                st.error(f"Error: {e}")
        
        with col2:
            try:
                start = time.time()
                if products is not None:
                    list(products.find({"price": {"$gt": 100}}).limit(100))
                    complex_time = (time.time() - start) * 1000
                    st.metric("Complex Query", f"{complex_time:.2f} ms",
                             delta="Good" if complex_time < 200 else "Slow")
                else:
                    st.metric("Complex Query", "N/A")
            except Exception as e:
                st.error(f"Error: {e}")
        
        with col3:
            try:
                start = time.time()
                if products is not None:
                    list(products.aggregate([
                        {"$match": {"price": {"$gt": 100}}},
                        {"$group": {"_id": "$category_id", "count": {"$sum": 1}}}
                    ]))
                    agg_time = (time.time() - start) * 1000
                    st.metric("Aggregation", f"{agg_time:.2f} ms",
                             delta="Fast" if agg_time < 500 else "Slow")
                else:
                    st.metric("Aggregation", "N/A")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with perf_tab2:
        try:
            db_stats = db.command("dbStats") if db is not None else {}
            
            col1, col2 = st.columns(2)
            
            with col1:
                data_size = db_stats.get("dataSize", 0) / (1024**2)
                storage_size = db_stats.get("storageSize", 0) / (1024**2)
                index_size = db_stats.get("indexSize", 0) / (1024**2)
                
                st.metric("Data Size", f"{data_size:.2f} MB")
                st.metric("Storage Size", f"{storage_size:.2f} MB")
                st.metric("Index Size", f"{index_size:.2f} MB")
            
            with col2:
                fig = go.Figure(data=[go.Pie(
                    labels=['Data', 'Indexes', 'Free Space'],
                    values=[data_size, index_size, max(0, storage_size - data_size - index_size)],
                    hole=.4
                )])
                fig.update_layout(title="Storage Distribution", height=300)
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error: {e}")
    
    with perf_tab3:
        try:
            coll_stats = db.command("collStats", "products") if db is not None else {}
            
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Documents", f"{coll_stats.get('count', 0):,}")
            col2.metric("Avg Doc Size", f"{coll_stats.get('avgObjSize', 0):.0f} B")
            col3.metric("Indexes", coll_stats.get('nindexes', 0))
            col4.metric("Sharded", "✅ Yes" if coll_stats.get('sharded', False) else "❌ No")
            
        except Exception as e:
            st.error(f"Error: {e}")

# -------------------------------------------------------
# 🧪 TEST REQUÊTES PAGE
# -------------------------------------------------------
elif page == "🧪 Test Requêtes":
    st.subheader("🧪 Requêtes de Test sur la collection shardée")

    test_queries = [
        "🔍 seller_id = 3",
        "📌 status = 'active'",
        "📂 category_id = 'beauty' + projection",
        "💰 seller_id = 8 + price range",
        "📊 status = 'active' + sort by price",
        "🔎 title regex 'jacket'",
        "📈 avg price per category",
        "📝 text search 'floral fragrance'"
    ]

    selected_query = st.selectbox("🧪 Choisissez une requête de test", test_queries)

    result, query_code, exec_time = execute_test_query(selected_query)

    st.code(query_code, language="javascript")
    st.metric("⏱️ Temps d'exécution", f"{exec_time:.2f} ms")

    if result:
        df_test = pd.DataFrame(result)
        # convert _id if present
        if "_id" in df_test.columns:
            df_test["_id"] = df_test["_id"].astype(str)
        st.dataframe(df_test.head(100), use_container_width=True)
    else:
        st.warning("Aucun résultat pour cette requête.")

# -------------------------------------------------------
# 🗂️ SHARDING PAGE
# -------------------------------------------------------
elif page == "🗂️ Sharding":
    st.subheader("🗂️ Sharding Architecture & Distribution")
    
    shard_tab1, shard_tab2, shard_tab3 = st.tabs(["📍 Shard Overview", "📦 Chunk Distribution", "🔑 Configuration"])
    
    with shard_tab1:
        try:
            shards = list(config_db["shards"].find({})) if config_db is not None else []
            
            if shards:
                shard_data = []
                for shard in shards:
                    shard_data.append({
                        "Shard ID": shard.get("_id", "N/A"),
                        "Host": shard.get("host", "N/A"),
                        "State": "🟢 Active" if shard.get("state") == 1 else "🔴 Inactive"
                    })
                
                df_shards = pd.DataFrame(shard_data)
                st.dataframe(df_shards, use_container_width=True, hide_index=True)
                st.success(f"✅ {len(shards)} shard(s) operational")
            else:
                st.warning("⚠️ No shards configured")
                
        except Exception as e:
            st.error(f"Error: {e}")
    
    with shard_tab2:
        try:
            chunks = list(config_db["chunks"].find({"ns": "marketplace.products"})) if config_db is not None else []
            
            if chunks:
                chunk_data = []
                for c in chunks:
                    chunk_data.append({
                        "shard": c.get("shard", "UNKNOWN"),
                        "min": str(c.get("min", {})),
                        "max": str(c.get("max", {}))
                    })
                
                df_chunks = pd.DataFrame(chunk_data)
                shard_counts = df_chunks["shard"].value_counts()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig = px.bar(
                        x=shard_counts.index,
                        y=shard_counts.values,
                        labels={"x": "Shard", "y": "Chunks"},
                        title="Chunks per Shard",
                        template=chart_theme
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("**Distribution Summary:**")
                    for shard, count in shard_counts.items():
                        st.write(f"• {shard}: **{count}** chunks")
                    
                    if len(shard_counts) > 1:
                        balance = shard_counts.max() / shard_counts.min()
                        if balance < 1.5:
                            st.success(f"✅ Well balanced ({balance:.2f}x)")
                        elif balance < 3:
                            st.warning(f"⚠️ Moderate imbalance ({balance:.2f}x)")
                        else:
                            st.error(f"🔴 High imbalance ({balance:.2f}x)")
                
                with st.expander("📋 Detailed Chunk List"):
                    st.dataframe(df_chunks, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ No chunks found")
                
        except Exception as e:
            st.error(f"Error: {e}")
    
    with shard_tab3:
        try:
            coll_info = list(config_db["collections"].find({"_id": "marketplace.products"})) if config_db is not None else []
            
            if coll_info:
                info = coll_info[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Shard Key Configuration:**")
                    st.code(str(info.get("key", {})), language="json")
                
                with col2:
                    st.markdown("**Properties:**")
                    st.write(f"• Unique: {'Yes' if info.get('unique') else 'No'}")
                    st.write(f"• Dropped: {'Yes' if info.get('dropped') else 'No'}")
                    st.write(f"• UUID: `{info.get('uuid', 'N/A')}`")
            else:
                st.info("Collection not sharded")
                
        except Exception as e:
            st.error(f"Error: {e}")

# ⏳ AUTO REFRESH (à la fin)
if enable_auto_refresh:
    time.sleep(refresh_rate)
    safe_rerun()
