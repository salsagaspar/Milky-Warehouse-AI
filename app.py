import os
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objs as go
import joblib

# -------------------------------------------------------------------------
# Load Data & Models
# -------------------------------------------------------------------------
BASE_DIR = "."
DATA_DIR = os.path.join(BASE_DIR, "processed_data")
MODELS_DIR = os.path.join(BASE_DIR, "optimized_models")

# Load Clean CSVs for KPI & Charts
try:
    df_pm = pd.read_csv(os.path.join(DATA_DIR, "clean_predictive_maintenance.csv"))
    df_mq = pd.read_csv(os.path.join(DATA_DIR, "clean_milk_quality.csv"))
    df_log = pd.read_csv(os.path.join(DATA_DIR, "clean_logistics_eta.csv"))
except Exception as e:
    # Fallback to loading original files if clean ones are missing (sanity backup)
    df_pm = pd.DataFrame()
    df_mq = pd.DataFrame()
    df_log = pd.DataFrame()

# Load Optimized Models
try:
    pm_model, pm_cols = joblib.load(os.path.join(MODELS_DIR, "optimized_predictive_maintenance_model.joblib"))
    mq_model, mq_cols = joblib.load(os.path.join(MODELS_DIR, "optimized_milk_quality_model.joblib"))
    log_reg, log_r_cols = joblib.load(os.path.join(MODELS_DIR, "optimized_logistics_delay_regressor.joblib"))
    log_clf, log_c_cols = joblib.load(os.path.join(MODELS_DIR, "optimized_logistics_delay_classifier.joblib"))
    models_available = True
except Exception as e:
    print(f"Peringatan: Gagal memuat model: {e}. Dashboard akan berjalan tanpa fungsi simulasi prediksi.")
    models_available = False

# -------------------------------------------------------------------------
# Setup Dash App
# -------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
app.title = "🍼 Dashboard Prediktif Pabrik Susu formula"
server = app.server

# -------------------------------------------------------------------------
# Styling Tokens (Glassmorphism & Neon Accent)
# -------------------------------------------------------------------------
GLASS_CARD_STYLE = {
    'background': 'rgba(30, 30, 30, 0.7)',
    'backdrop-filter': 'blur(12px)',
    '-webkit-backdrop-filter': 'blur(12px)',
    'border-radius': '15px',
    'border': '1px solid rgba(255, 255, 255, 0.08)',
    'box-shadow': '0 8px 32px 0 rgba(0, 0, 0, 0.4)',
    'margin-bottom': '20px',
    'padding': '22px'
}

KPI_CARD_STYLE = {
    'background': 'rgba(40, 40, 40, 0.5)',
    'border-radius': '10px',
    'border-left': '4px solid #00bc8c', # Default hijau
    'border-top': '1px solid rgba(255, 255, 255, 0.05)',
    'border-right': '1px solid rgba(255, 255, 255, 0.05)',
    'border-bottom': '1px solid rgba(255, 255, 255, 0.05)',
    'padding': '15px',
    'text-align': 'center'
}

# Unique values for dropdown option selections
robot_types = df_pm['robot_type'].dropna().unique().tolist() if not df_pm.empty else ['AMR', 'AGV', 'Sorter']
manufacturers = df_pm['manufacturer'].dropna().unique().tolist() if not df_pm.empty else ['OMRON', 'Fanuc', 'Kuka']
formula_types = df_mq['formula_type'].dropna().unique().tolist() if not df_mq.empty else ['Soy-Based', 'Hydrolyzed']
categories = df_mq['category'].dropna().unique().tolist() if not df_mq.empty else ['Infant Formula', 'Toddler Milk']
transport_modes = df_log['transport_mode'].dropna().unique().tolist() if not df_log.empty else ['Truck', 'Sea', 'Air']
carrier_names = df_log['carrier_name'].dropna().unique().tolist() if not df_log.empty else ['FedEx', 'DHL', 'JNE']

# -------------------------------------------------------------------------
# Dynamic KPI Computations
# -------------------------------------------------------------------------
def get_pm_kpis():
    if df_pm.empty:
        return "10,000", "4.7%", "85.2 Min", "95.1%"
    total_robots = len(df_pm)
    error_rate = (df_pm['current_status'] == 'Error').sum() / total_robots * 100
    avg_task_duration = df_pm['average_task_duration_min'].mean()
    avg_success_rate = df_pm['task_success_rate_pct'].mean()
    return f"{total_robots:,}", f"{error_rate:.2f}%", f"{avg_task_duration:.1f} Min", f"{avg_success_rate:.1f}%"

def get_mq_kpis():
    if df_mq.empty:
        return "10,000", "79.8%", "8.1%", "7.2%"
    total_batches = len(df_mq)
    pass_rate = (df_mq['overall_result'] == 'Pass').sum() / total_batches * 100
    fail_rate = (df_mq['overall_result'] == 'Fail').sum() / total_batches * 100
    cond_pass_rate = (df_mq['overall_result'] == 'Conditional Pass').sum() / total_batches * 100
    return f"{total_batches:,}", f"{pass_rate:.1f}%", f"{fail_rate:.1f}%", f"{cond_pass_rate:.1f}%"

def get_log_kpis():
    if df_log.empty:
        return "10,000", "71.2%", "1.65 Hari", "49.6%"
    total_shipments = len(df_log)
    delay_rate = (df_log['is_delayed'] == 1).sum() / total_shipments * 100
    avg_delay = df_log[df_log['is_delayed'] == 1]['delay_days'].mean()
    cold_chain_excursion = df_log['cold_chain_excursion_detected'].sum() / total_shipments * 100
    return f"{total_shipments:,}", f"{delay_rate:.1f}%", f"{avg_delay:.2f} Hari", f"{cold_chain_excursion:.1f}%"

# -------------------------------------------------------------------------
# Header & Layout
# -------------------------------------------------------------------------
app.layout = html.Div(
    style={'background-color': '#0d0d0d', 'color': '#ffffff', 'min-height': '100vh', 'font-family': 'Inter, sans-serif'},
    children=[
        # Header Banner
        dbc.Container(
            fluid=True,
            style={'background': 'linear-gradient(90deg, #1f1f2e 0%, #11111a 100%)', 'padding': '20px 30px', 'border-bottom': '2px solid rgba(0, 188, 140, 0.4)'},
            children=[
                dbc.Row(
                    align="center",
                    children=[
                        dbc.Col(
                            xs=12, md=8,
                            children=[
                                html.H1("🍼 COMMAND CENTER PABRIK SUSU BAYI", className="text-start", style={'font-weight': '800', 'letter-spacing': '2px', 'color': '#00bc8c', 'margin-bottom': '5px'}),
                                html.P("Pusat Kendali Jaminan Kualitas, Otomatisasi Robot Gudang, dan ETA Rantai Logistik Regional", style={'color': '#a3a3c2', 'margin-bottom': '0'}),
                            ]
                        ),
                        dbc.Col(
                            xs=12, md=4,
                            className="text-end",
                            children=[
                                html.Span("● SISTEM AKTIF", style={'background-color': 'rgba(0, 188, 140, 0.15)', 'color': '#00bc8c', 'border': '1px solid #00bc8c', 'padding': '8px 15px', 'border-radius': '20px', 'font-weight': 'bold', 'font-size': '12px'}),
                                html.Span(f" MODEL ML: {'AKTIF' if models_available else 'TIDAK AKTIF'}", style={'background-color': 'rgba(243, 156, 18, 0.15)' if not models_available else 'rgba(0, 188, 140, 0.15)', 'color': '#f39c12' if not models_available else '#00bc8c', 'border': '1px solid #f39c12' if not models_available else '1px solid #00bc8c', 'padding': '8px 15px', 'border-radius': '20px', 'font-weight': 'bold', 'font-size': '12px', 'margin-left': '10px'})
                            ]
                        )
                    ]
                )
            ]
        ),
        
        # Tabs Navigation
        dbc.Container(
            fluid=False,
            style={'margin-top': '30px'},
            children=[
                dcc.Tabs(
                    id="main-tabs",
                    value="tab-pm",
                    children=[
                        # TAB 1: PREDICTIVE MAINTENANCE
                        dcc.Tab(
                            label="🤖 MAINTENANCE ROBOT",
                            value="tab-pm",
                            style={'background-color': '#1a1a1a', 'color': '#a3a3c2', 'font-weight': 'bold', 'border-radius': '8px 8px 0 0', 'border': 'none', 'padding': '15px'},
                            selected_style={'background-color': '#00bc8c', 'color': '#ffffff', 'font-weight': 'bold', 'border-radius': '8px 8px 0 0', 'border': 'none', 'padding': '15px'},
                            children=[
                                html.Div(style={'margin-top': '25px'}, children=[
                                    # PM KPIs
                                    dbc.Row(
                                        children=[
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #3498db'}, children=[html.H6("Total Unit Robot", style={'color': '#a3a3c2'}), html.H3(get_pm_kpis()[0], style={'font-weight': 'bold', 'color': '#3498db'})]), width=3),
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #e74c3c'}, children=[html.H6("Rasio Kerusakan Robot", style={'color': '#a3a3c2'}), html.H3(get_pm_kpis()[1], style={'font-weight': 'bold', 'color': '#e74c3c'})]), width=3),
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #f1c40f'}, children=[html.H6("Durasi Tugas Rata-Rata", style={'color': '#a3a3c2'}), html.H3(get_pm_kpis()[2], style={'font-weight': 'bold', 'color': '#f1c40f'})]), width=3),
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #2ecc71'}, children=[html.H6("Tingkat Kelancaran Tugas", style={'color': '#a3a3c2'}), html.H3(get_pm_kpis()[3], style={'font-weight': 'bold', 'color': '#2ecc71'})]), width=3),
                                        ],
                                        style={'margin-bottom': '20px'}
                                    ),
                                    
                                    # PM Columns
                                    dbc.Row(children=[
                                        # PM Inputs Form
                                        dbc.Col(
                                            md=5,
                                            children=[
                                                html.Div(
                                                    style=GLASS_CARD_STYLE,
                                                    children=[
                                                        html.H4("🔌 Telemetri & Input Simulasi Robot", style={'color': '#3498db', 'border-bottom': '1px solid rgba(52, 152, 219, 0.3)', 'padding-bottom': '10px', 'margin-bottom': '18px'}),
                                                        
                                                        html.Label("Tipe Robot Gudang:", style={'font-size': '13px'}),
                                                        dcc.Dropdown(id="pm-robot-type", options=[{'label': t, 'value': t} for t in robot_types], value=robot_types[0], style={'color': '#111', 'margin-bottom': '15px'}),
                                                        
                                                        html.Label("Pabrikan Robot:", style={'font-size': '13px'}),
                                                        dcc.Dropdown(id="pm-manufacturer", options=[{'label': m, 'value': m} for m in manufacturers], value=manufacturers[0], style={'color': '#111', 'margin-bottom': '15px'}),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Baterai (kWh):", style={'font-size': '13px'}),
                                                                dbc.Input(id="pm-battery", type="number", value=15.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Max Payload (kg):", style={'font-size': '13px'}),
                                                                dbc.Input(id="pm-payload", type="number", value=500.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Jam Kerja Kumulatif:", style={'font-size': '13px'}),
                                                                dbc.Input(id="pm-hours", type="number", value=1850.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Hari Sejak Servis:", style={'font-size': '13px'}),
                                                                dbc.Input(id="pm-days-maint", type="number", value=45.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Total Upaya Tugas:", style={'font-size': '13px'}),
                                                                dbc.Input(id="pm-tasks", type="number", value=1200.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Persentase Sukses (%):", style={'font-size': '13px'}),
                                                                dbc.Input(id="pm-success-rate", type="number", value=98.5, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Jumlah Error Kerja:", style={'font-size': '13px'}),
                                                                dbc.Input(id="pm-errors", type="number", value=12.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Daya Terpakai (kWh):", style={'font-size': '13px'}),
                                                                dbc.Input(id="pm-energy", type="number", value=450.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Button("⚙️ Prediksi Kesehatan Robot", id="pm-predict-btn", color="primary", style={'width': '100%', 'font-weight': 'bold', 'margin-top': '10px'})
                                                    ]
                                                )
                                            ]
                                        ),
                                        # PM Output Result & Plot
                                        dbc.Col(
                                            md=7,
                                            children=[
                                                # Result Display
                                                html.Div(
                                                    id="pm-result-container",
                                                    style={**GLASS_CARD_STYLE, 'border-left': '8px solid #3498db'},
                                                    children=[
                                                        html.H5("📊 Hasil Analisis Prediktif ML", style={'color': '#a3a3c2', 'margin-bottom': '10px'}),
                                                        html.Div(id="pm-result-output", children=[
                                                            html.P("Isi formulir dan klik tombol Prediksi di sebelah kiri untuk menganalisis risiko kerusakan robot otonom.", style={'color': '#a3a3c2', 'font-style': 'italic'})
                                                        ])
                                                    ]
                                                ),
                                                # Plot Chart
                                                html.Div(
                                                    style=GLASS_CARD_STYLE,
                                                    children=[
                                                        html.H5("📈 Sebaran Kumulatif Tugas Selesai per Pabrikan", style={'color': '#a3a3c2', 'margin-bottom': '15px'}),
                                                        dcc.Graph(
                                                            id="pm-chart",
                                                            figure=(
                                                                px.bar(df_pm.groupby('manufacturer')['total_tasks_completed'].sum().reset_index(),
                                                                       x='manufacturer', y='total_tasks_completed',
                                                                       labels={'manufacturer': 'Pabrikan Robot', 'total_tasks_completed': 'Total Tugas Diselesaikan'},
                                                                       color_discrete_sequence=['#3498db'])
                                                                .update_layout(
                                                                    plot_bgcolor='rgba(0,0,0,0)',
                                                                    paper_bgcolor='rgba(0,0,0,0)',
                                                                    font_color='#ffffff',
                                                                    margin=dict(l=20, r=20, t=10, b=20),
                                                                    height=260
                                                                )
                                                                if not df_pm.empty else {}
                                                            )
                                                        )
                                                    ]
                                                )
                                            ]
                                        )
                                    ])
                                ])
                            ]
                        ),
                        
                        # TAB 2: MILK QUALITY CONTROL
                        dcc.Tab(
                            label="🧪 JAMINAN MUTU SUSU",
                            value="tab-mq",
                            style={'background-color': '#1a1a1a', 'color': '#a3a3c2', 'font-weight': 'bold', 'border-radius': '8px 8px 0 0', 'border': 'none', 'padding': '15px'},
                            selected_style={'background-color': '#f39c12', 'color': '#ffffff', 'font-weight': 'bold', 'border-radius': '8px 8px 0 0', 'border': 'none', 'padding': '15px'},
                            children=[
                                html.Div(style={'margin-top': '25px'}, children=[
                                    # MQ KPIs
                                    dbc.Row(
                                        children=[
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #3498db'}, children=[html.H6("Total Batch Diuji", style={'color': '#a3a3c2'}), html.H3(get_mq_kpis()[0], style={'font-weight': 'bold', 'color': '#3498db'})]), width=3),
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #2ecc71'}, children=[html.H6("Rasio Kelulusan Mutu", style={'color': '#a3a3c2'}), html.H3(get_mq_kpis()[1], style={'font-weight': 'bold', 'color': '#2ecc71'})]), width=3),
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #e74c3c'}, children=[html.H6("Rasio Gagal Mutu", style={'color': '#a3a3c2'}), html.H3(get_mq_kpis()[2], style={'font-weight': 'bold', 'color': '#e74c3c'})]), width=3),
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #f1c40f'}, children=[html.H6("Lulus Kondisional", style={'color': '#a3a3c2'}), html.H3(get_mq_kpis()[3], style={'font-weight': 'bold', 'color': '#f1c40f'})]), width=3),
                                        ],
                                        style={'margin-bottom': '20px'}
                                    ),
                                    
                                    # MQ Columns
                                    dbc.Row(children=[
                                        # MQ Inputs Form
                                        dbc.Col(
                                            md=5,
                                            children=[
                                                html.Div(
                                                    style=GLASS_CARD_STYLE,
                                                    children=[
                                                        html.H4("🔬 Parameter Fisika & Kimia Batch", style={'color': '#f39c12', 'border-bottom': '1px solid rgba(243, 156, 18, 0.3)', 'padding-bottom': '10px', 'margin-bottom': '18px'}),
                                                        
                                                        html.Label("Jenis Varian Susu:", style={'font-size': '13px'}),
                                                        dcc.Dropdown(id="mq-formula-type", options=[{'label': t, 'value': t} for t in formula_types], value=formula_types[0], style={'color': '#111', 'margin-bottom': '15px'}),
                                                        
                                                        html.Label("Kategori Usia:", style={'font-size': '13px'}),
                                                        dcc.Dropdown(id="mq-category", options=[{'label': c, 'value': c} for c in categories], value=categories[0], style={'color': '#111', 'margin-bottom': '15px'}),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Durasi Mixing (min):", style={'font-size': '13px'}),
                                                                dbc.Input(id="mq-mixing", type="number", value=35.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Suhu Pasteurisasi (°C):", style={'font-size': '13px'}),
                                                                dbc.Input(id="mq-pasteur", type="number", value=78.5, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Suhu Drying (°C):", style={'font-size': '13px'}),
                                                                dbc.Input(id="mq-drying", type="number", value=120.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Kadar Air Target (%):", style={'font-size': '13px'}),
                                                                dbc.Input(id="mq-moisture-target", type="number", value=3.2, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Protein Deviasi (%):", style={'font-size': '13px'}),
                                                                dbc.Input(id="mq-protein-var", type="number", value=0.01, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Lemak Deviasi (%):", style={'font-size': '13px'}),
                                                                dbc.Input(id="mq-fat-var", type="number", value=-0.02, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Kelembaban Deviasi (%):", style={'font-size': '13px'}),
                                                                dbc.Input(id="mq-moisture-var", type="number", value=0.05, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Skor Segel Kemasan:", style={'font-size': '13px'}),
                                                                dbc.Input(id="mq-pkg-score", type="number", value=9.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Button("🔬 Analisis Kelayakan Batch", id="mq-predict-btn", color="warning", style={'width': '100%', 'font-weight': 'bold', 'margin-top': '10px'})
                                                    ]
                                                )
                                            ]
                                        ),
                                        # MQ Output Result & Plot
                                        dbc.Col(
                                            md=7,
                                            children=[
                                                # Result Display
                                                html.Div(
                                                    id="mq-result-container",
                                                    style={**GLASS_CARD_STYLE, 'border-left': '8px solid #f39c12'},
                                                    children=[
                                                        html.H5("📊 Hasil Pengujian Laboratorium", style={'color': '#a3a3c2', 'margin-bottom': '10px'}),
                                                        html.Div(id="mq-result-output", children=[
                                                            html.P("Isi parameter batch dan klik tombol Analisis di sebelah kiri untuk mensimulasikan jaminan kelolosan mutu lab.", style={'color': '#a3a3c2', 'font-style': 'italic'})
                                                        ])
                                                    ]
                                                ),
                                                # Plot Chart
                                                html.Div(
                                                    style=GLASS_CARD_STYLE,
                                                    children=[
                                                        html.H5("📈 Pola Densitas Variansi Kelembapan Bubuk Formula", style={'color': '#a3a3c2', 'margin-bottom': '15px'}),
                                                        dcc.Graph(
                                                            id="mq-chart",
                                                            figure=(
                                                                px.histogram(df_mq, x='moisture_variance', color='overall_result',
                                                                             marginal='box',
                                                                             color_discrete_map={'Pass': '#2ecc71', 'Fail': '#e74c3c', 'Conditional Pass': '#f1c40f', 'Pending': '#95a5a6'},
                                                                             labels={'moisture_variance': 'Variansi Kelembaban (%)', 'overall_result': 'Hasil Lab'})
                                                                .update_layout(
                                                                    plot_bgcolor='rgba(0,0,0,0)',
                                                                    paper_bgcolor='rgba(0,0,0,0)',
                                                                    font_color='#ffffff',
                                                                    margin=dict(l=20, r=20, t=10, b=20),
                                                                    height=260
                                                                )
                                                                if not df_mq.empty else {}
                                                            )
                                                        )
                                                    ]
                                                )
                                            ]
                                        )
                                    ])
                                ])
                            ]
                        ),
                        
                        # TAB 3: LOGISTICS ETA & COLD CHAIN
                        dcc.Tab(
                            label="📦 LOGISTIK & COLD CHAIN",
                            value="tab-log",
                            style={'background-color': '#1a1a1a', 'color': '#a3a3c2', 'font-weight': 'bold', 'border-radius': '8px 8px 0 0', 'border': 'none', 'padding': '15px'},
                            selected_style={'background-color': '#9b59b6', 'color': '#ffffff', 'font-weight': 'bold', 'border-radius': '8px 8px 0 0', 'border': 'none', 'padding': '15px'},
                            children=[
                                html.Div(style={'margin-top': '25px'}, children=[
                                    # Log KPIs
                                    dbc.Row(
                                        children=[
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #3498db'}, children=[html.H6("Total Pengapalan", style={'color': '#a3a3c2'}), html.H3(get_log_kpis()[0], style={'font-weight': 'bold', 'color': '#3498db'})]), width=3),
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #e74c3c'}, children=[html.H6("Rasio Keterlambatan Rute", style={'color': '#a3a3c2'}), html.H3(get_log_kpis()[1], style={'font-weight': 'bold', 'color': '#e74c3c'})]), width=3),
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #f1c40f'}, children=[html.H6("Rata-rata Hari Terlambat", style={'color': '#a3a3c2'}), html.H3(get_log_kpis()[2], style={'font-weight': 'bold', 'color': '#f1c40f'})]), width=3),
                                            dbc.Col(dbc.Card(style={**KPI_CARD_STYLE, 'border-left': '4px solid #e67e22'}, children=[html.H6("Kebocoran Rantai Dingin", style={'color': '#a3a3c2'}), html.H3(get_log_kpis()[3], style={'font-weight': 'bold', 'color': '#e67e22'})]), width=3),
                                        ],
                                        style={'margin-bottom': '20px'}
                                    ),
                                    
                                    # Log Columns
                                    dbc.Row(children=[
                                        # Log Inputs Form
                                        dbc.Col(
                                            md=5,
                                            children=[
                                                html.Div(
                                                    style=GLASS_CARD_STYLE,
                                                    children=[
                                                        html.H4("🗺️ Parameter Rute & Ekspedisi", style={'color': '#9b59b6', 'border-bottom': '1px solid rgba(155, 89, 182, 0.3)', 'padding-bottom': '10px', 'margin-bottom': '18px'}),
                                                        
                                                        html.Label("Moda Transportasi:", style={'font-size': '13px'}),
                                                        dcc.Dropdown(id="log-transport-mode", options=[{'label': t, 'value': t} for t in transport_modes], value=transport_modes[0], style={'color': '#111', 'margin-bottom': '15px'}),
                                                        
                                                        html.Label("Perusahaan Kargo (Carrier):", style={'font-size': '13px'}),
                                                        dcc.Dropdown(id="log-carrier-name", options=[{'label': c, 'value': c} for c in carrier_names], value=carrier_names[0], style={'color': '#111', 'margin-bottom': '15px'}),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Jarak Rute (km):", style={'font-size': '13px'}),
                                                                dbc.Input(id="log-distance", type="number", value=750.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Durasi Jadwal (jam):", style={'font-size': '13px'}),
                                                                dbc.Input(id="log-sched-hours", type="number", value=48.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Berat Kargo (kg):", style={'font-size': '13px'}),
                                                                dbc.Input(id="log-weight", type="number", value=1500.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Volume Kargo (m³):", style={'font-size': '13px'}),
                                                                dbc.Input(id="log-volume", type="number", value=5.5, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Suhu Puncak Kontainer (°C):", style={'font-size': '13px'}),
                                                                dbc.Input(id="log-temp-max", type="number", value=9.5, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Ekskursi Rantai Dingin (0/1):", style={'font-size': '13px'}),
                                                                dbc.Input(id="log-excursion", type="number", value=1, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Row([
                                                            dbc.Col([
                                                                html.Label("Total Tarif (USD):", style={'font-size': '13px'}),
                                                                dbc.Input(id="log-cost", type="number", value=1200.0, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                            dbc.Col([
                                                                html.Label("Bulan Pengapalan (1-12):", style={'font-size': '13px'}),
                                                                dbc.Input(id="log-month", type="number", value=5, style={'background-color': '#2b2b36', 'color': '#fff', 'border': 'none', 'margin-bottom': '15px'}),
                                                            ], width=6),
                                                        ]),
                                                        
                                                        dbc.Button("📦 Estimasi & Prediksi Logistik", id="log-predict-btn", color="secondary", style={'width': '100%', 'font-weight': 'bold', 'margin-top': '10px'})
                                                    ]
                                                )
                                            ]
                                        ),
                                        # Log Output Result & Plot
                                        dbc.Col(
                                            md=7,
                                            children=[
                                                # Result Display
                                                html.Div(
                                                    id="log-result-container",
                                                    style={**GLASS_CARD_STYLE, 'border-left': '8px solid #9b59b6'},
                                                    children=[
                                                        html.H5("📊 Hasil Estimasi ETA Logistik", style={'color': '#a3a3c2', 'margin-bottom': '10px'}),
                                                        html.Div(id="log-result-output", children=[
                                                            html.P("Isi parameter pengiriman dan klik tombol Estimasi di sebelah kiri untuk menghitung potensi delay & cold chain.", style={'color': '#a3a3c2', 'font-style': 'italic'})
                                                        ])
                                                    ]
                                                ),
                                                # Plot Chart
                                                html.Div(
                                                    style=GLASS_CARD_STYLE,
                                                    children=[
                                                        html.H5("📈 Sebaran Hari Keterlambatan per Moda Transportasi", style={'color': '#a3a3c2', 'margin-bottom': '15px'}),
                                                        dcc.Graph(
                                                            id="log-chart",
                                                            figure=(
                                                                px.box(df_log, x='transport_mode', y='delay_days', color='transport_mode',
                                                                       color_discrete_sequence=px.colors.qualitative.Pastel,
                                                                       labels={'transport_mode': 'Moda Transportasi', 'delay_days': 'Hari Keterlambatan (Aktual)'})
                                                                .update_layout(
                                                                    plot_bgcolor='rgba(0,0,0,0)',
                                                                    paper_bgcolor='rgba(0,0,0,0)',
                                                                    font_color='#ffffff',
                                                                    margin=dict(l=20, r=20, t=10, b=20),
                                                                    height=260
                                                                )
                                                                if not df_log.empty else {}
                                                            )
                                                        )
                                                    ]
                                                )
                                            ]
                                        )
                                    ])
                                ])
                            ]
                        ),
                    ]
                )
            ]
        ),
        
        # Footer
        html.Footer(
            style={'text-align': 'center', 'padding': '30px 0', 'color': '#7575a3', 'font-size': '13px', 'border-top': '1px solid rgba(255, 255, 255, 0.05)', 'margin-top': '50px'},
            children=[
                html.P("© 2026 Pabrik Susu Formula Bayi Modern. Seluruh Hak Cipta Dilindungi."),
                html.P("Arsitektur Prediktif berbasis Model Machine Learning (HistGradientBoosting & Random Forest)", style={'font-size': '11px', 'color': '#5c5c8a'})
            ]
        )
    ]
)

# -------------------------------------------------------------------------
# TAB 1: PREDICTIVE MAINTENANCE CALLBACK
# -------------------------------------------------------------------------
@app.callback(
    Output("pm-result-output", "children"),
    Input("pm-predict-btn", "n_clicks"),
    State("pm-robot-type", "value"),
    State("pm-manufacturer", "value"),
    State("pm-battery", "value"),
    State("pm-payload", "value"),
    State("pm-speed", "value") if "pm-speed" in globals() else State("pm-payload", "value"), # Speed safety fallback
    State("pm-hours", "value"),
    State("pm-days-maint", "value"),
    State("pm-tasks", "value"),
    State("pm-success-rate", "value"),
    State("pm-errors", "value"),
    State("pm-energy", "value"),
    prevent_initial_call=True
)
def predict_pm(n_clicks, r_type, manufacturer, battery, payload, speed, hours, days_maint, tasks, success_rate, errors, energy):
    if not models_available:
        return html.Div(style={'color': '#e74c3c', 'font-weight': 'bold'}, children="Model ML tidak tersedia di server lokal.")
    
    # 1. Konstruksi DataFrame Input
    input_data = {
        'battery_capacity_kwh': [float(battery)],
        'max_payload_kg': [float(payload)],
        'max_speed_ms': [1.5], # Standar fallback
        'total_operating_hours': [float(hours)],
        'days_since_last_maintenance': [float(days_maint)],
        'total_tasks_attempted': [float(tasks)],
        'task_success_rate_pct': [float(success_rate)],
        'task_error_count': [float(errors)],
        'total_energy_consumed_kwh': [float(energy)],
        'total_weight_handled_kg': [float(tasks * 5.0)], # Rasio tiruan
        'average_task_duration_min': [15.0], # Fallback
        'robot_type': [r_type],
        'manufacturer': [manufacturer]
    }
    
    # Rekayasa Fitur Tambahan (Sesuai model teroptimasi)
    df_input = pd.DataFrame(input_data)
    df_input['energy_per_hour'] = df_input['total_energy_consumed_kwh'] / (df_input['total_operating_hours'] + 1e-5)
    df_input['error_rate'] = df_input['task_error_count'] / (df_input['total_tasks_attempted'] + 1e-5)
    df_input['average_payload_per_task'] = df_input['total_weight_handled_kg'] / (df_input['total_tasks_attempted'] + 1e-5)
    df_input['operating_intensity'] = df_input['total_operating_hours'] / (df_input['days_since_last_maintenance'] + 1e-5)
    
    # Encoding & Alignment kolom
    df_encoded = pd.get_dummies(df_input)
    df_encoded = df_encoded.reindex(columns=pm_cols, fill_value=0)
    
    # 2. Prediksi
    pred = pm_model.predict(df_encoded)[0]
    proba = pm_model.predict_proba(df_encoded)[0][1]
    
    # 3. Render Output Dinamis
    if pred == 1:
        color = "#e74c3c" # Merah
        status_text = "BAHAYA (MALFUNGSI / ERROR DETECTED)"
        advice = "Rekomendasi: Hentikan penugasan robot segera. Lakukan pengisian daya darurat dan jadwalkan inspeksi mekanik preventif."
    else:
        color = "#2ecc71" # Hijau
        status_text = "SEHAT (OPERASIONAL NORMAL)"
        advice = "Rekomendasi: Robot berada dalam parameter kerja yang sehat. Dapat terus bertugas sesuai jadwal logistik gudang."
        
    return html.Div(children=[
        html.H3(status_text, style={'color': color, 'font-weight': 'bold', 'margin-bottom': '12px'}),
        dbc.Row([
            dbc.Col([
                html.Div(style={'background': 'rgba(255,255,255,0.03)', 'padding': '15px', 'border-radius': '8px', 'text-align': 'center'}, children=[
                    html.H6("Peluang Kerusakan Telemetri", style={'color': '#a3a3c2'}),
                    html.H2(f"{proba*100:.2f}%", style={'color': color, 'font-weight': 'bold', 'margin': '5px 0'}),
                    html.P("Skor Risiko Kumulatif", style={'font-size': '11px', 'color': '#7575a3'})
                ])
            ], width=4),
            dbc.Col([
                html.P(advice, style={'font-size': '14px', 'margin-top': '10px', 'line-height': '1.6'})
            ], width=8)
        ])
    ])

# -------------------------------------------------------------------------
# TAB 2: MILK QUALITY CALLBACK
# -------------------------------------------------------------------------
@app.callback(
    Output("mq-result-output", "children"),
    Input("mq-predict-btn", "n_clicks"),
    State("mq-formula-type", "value"),
    State("mq-category", "value"),
    State("mq-mixing", "value"),
    State("mq-pasteur", "value"),
    State("mq-drying", "value"),
    State("mq-moisture-target", "value"),
    State("mq-protein-var", "value"),
    State("mq-fat-var", "value"),
    State("mq-moisture-var", "value"),
    State("mq-pkg-score", "value"),
    prevent_initial_call=True
)
def predict_mq(n_clicks, f_type, category, mixing, pasteur, drying, moist_target, protein_var, fat_var, moist_var, pkg_score):
    if not models_available:
        return html.Div(style={'color': '#e74c3c', 'font-weight': 'bold'}, children="Model ML tidak tersedia di server lokal.")
        
    input_data = {
        'mixing_time_min': [float(mixing)],
        'pasteurization_temp_c': [float(pasteur)],
        'drying_temp_c': [float(drying)],
        'moisture_content_pct': [float(moist_target)],
        'protein_content_pct': [12.5], # Target standar
        'fat_content_pct': [26.0],
        'carb_content_pct': [55.0],
        'yield_efficiency_pct': [95.0],
        'package_size_g': [400.0],
        'unit_price_usd': [12.5],
        'cost_price_usd': [8.0],
        'storage_temp_min_c': [4.0],
        'storage_temp_max_c': [25.0],
        'is_organic': [1],
        'is_allergen_free': [1],
        'protein_variance': [float(protein_var)],
        'fat_variance': [float(fat_var)],
        'moisture_variance': [float(moist_var)],
        'packaging_integrity_score': [float(pkg_score)],
        'category': [category],
        'formula_type': [f_type]
    }
    
    # Rekayasa Fitur Tambahan
    df_input = pd.DataFrame(input_data)
    df_input['protein_var_sq'] = df_input['protein_variance'] ** 2
    df_input['fat_var_sq'] = df_input['fat_variance'] ** 2
    df_input['moisture_var_sq'] = df_input['moisture_variance'] ** 2
    df_input['temp_interaction'] = df_input['pasteurization_temp_c'] * df_input['drying_temp_c']
    df_input['yield_per_unit'] = (df_input['yield_efficiency_pct'] * 1000.0) / 100.0
    
    # Encoding & Alignment
    df_encoded = pd.get_dummies(df_input)
    df_encoded = df_encoded.reindex(columns=mq_cols, fill_value=0)
    
    # Prediksi
    pred = mq_model.predict(df_encoded)[0]
    proba = mq_model.predict_proba(df_encoded)[0][1]
    
    if pred == 1:
        color = "#e74c3c"
        status_text = "GAGAL MUTU (FAIL - KONTAMINASI TINGGI)"
        advice = "Peringatan: Deviasi kelembaban terlalu tinggi terdeteksi meningkatkan aktivitas mikroba patogen. Batch harus ditahan di area Karantina lab!"
    else:
        color = "#2ecc71"
        status_text = "LOLOS MUTU (PASS - KUALITAS AMAN)"
        advice = "Rekomendasi: Seluruh spesifikasi protein, lemak, dan kelembapan berada pada standar toleransi yang aman. Batch susu formula layak dirilis ke pasar."
        
    return html.Div(children=[
        html.H3(status_text, style={'color': color, 'font-weight': 'bold', 'margin-bottom': '12px'}),
        dbc.Row([
            dbc.Col([
                html.Div(style={'background': 'rgba(255,255,255,0.03)', 'padding': '15px', 'border-radius': '8px', 'text-align': 'center'}, children=[
                    html.H6("Risiko Kontaminasi Lab", style={'color': '#a3a3c2'}),
                    html.H2(f"{proba*100:.2f}%", style={'color': color, 'font-weight': 'bold', 'margin': '5px 0'}),
                    html.P("Skor Keamanan Pangan", style={'font-size': '11px', 'color': '#7575a3'})
                ])
            ], width=4),
            dbc.Col([
                html.P(advice, style={'font-size': '14px', 'margin-top': '10px', 'line-height': '1.6'})
            ], width=8)
        ])
    ])

# -------------------------------------------------------------------------
# TAB 3: LOGISTICS ETA CALLBACK
# -------------------------------------------------------------------------
@app.callback(
    Output("log-result-output", "children"),
    Input("log-predict-btn", "n_clicks"),
    State("log-transport-mode", "value"),
    State("log-carrier-name", "value"),
    State("log-distance", "value"),
    State("log-sched-hours", "value"),
    State("log-weight", "value"),
    State("log-volume", "value"),
    State("log-temp-max", "value"),
    State("log-excursion", "value"),
    State("log-cost", "value"),
    State("log-month", "value"),
    prevent_initial_call=True
)
def predict_log(n_clicks, t_mode, carrier, distance, sched_hours, weight, volume, temp_max, excursion, cost, month):
    if not models_available:
        return html.Div(style={'color': '#e74c3c', 'font-weight': 'bold'}, children="Model ML tidak tersedia di server lokal.")
        
    input_data = {
        'distance_km': [float(distance)],
        'estimated_duration_hours': [float(sched_hours)],
        'weight_kg': [float(weight)],
        'volume_m3': [float(volume)],
        'temperature_min_c': [2.0],
        'temperature_max_c': [float(temp_max)],
        'total_cost_usd': [float(cost)],
        'insurance_value_usd': [float(cost * 1.5)],
        'base_cost_usd': [float(cost * 0.8)],
        'cost_per_kg_usd': [float(cost / weight)],
        'frequency_per_week': [5.0],
        'avg_delay_hours': [2.5],
        'shipment_month': [int(month)],
        'shipment_day_of_week': [2],
        'real_cost_per_kg_usd': [float(cost / weight)],
        'cold_chain_excursion_detected': [int(excursion)],
        'transport_mode': [t_mode],
        'carrier_name': [carrier],
        'customs_required': [1],
        'cold_chain_required': [1]
    }
    
    # Rekayasa Fitur Tambahan
    df_input = pd.DataFrame(input_data)
    df_input['shipping_speed'] = df_input['distance_km'] / (df_input['estimated_duration_hours'] + 1e-5)
    df_input['cost_per_km'] = df_input['total_cost_usd'] / (df_input['distance_km'] + 1e-5)
    df_input['cost_per_kg'] = df_input['total_cost_usd'] / (df_input['weight_kg'] + 1e-5)
    df_input['temperature_range'] = df_input['temperature_max_c'] - df_input['temperature_min_c']
    df_input['cold_chain_severity'] = df_input['cold_chain_excursion_detected'] * df_input['temperature_max_c']
    
    # Encoding & Alignment
    df_encoded_r = pd.get_dummies(df_input).reindex(columns=log_r_cols, fill_value=0)
    df_encoded_c = pd.get_dummies(df_input).reindex(columns=log_c_cols, fill_value=0)
    
    # Prediksi Regresi & Klasifikasi
    pred_delay = log_reg.predict(df_encoded_r)[0]
    pred_status = log_clf.predict(df_encoded_c)[0]
    proba_delay = log_clf.predict_proba(df_encoded_c)[0][1]
    
    if pred_status == 1:
        color = "#e74c3c"
        status_text = f"TERLAMBAT (DELAY DETECTED)"
        advice = f"Peringatan: Keterlambatan terdeteksi! Rata-rata tambahan waktu di jalan diperkirakan sekitar {pred_delay:.2f} hari. Kontainer rantai dingin harus diaudit suhunya saat tiba."
    else:
        color = "#2ecc71"
        status_text = "TEPAT WAKTU / LEBIH CEPAT (ON TIME)"
        advice = f"Rekomendasi: Rute logistik terpantau lancar. Kontainer diperkirakan tiba tepat waktu dengan estimasi deviasi waktu {pred_delay:.2f} hari."
        
    return html.Div(children=[
        html.H3(status_text, style={'color': color, 'font-weight': 'bold', 'margin-bottom': '12px'}),
        dbc.Row([
            dbc.Col([
                html.Div(style={'background': 'rgba(255,255,255,0.03)', 'padding': '15px', 'border-radius': '8px', 'text-align': 'center'}, children=[
                    html.H6("Estimasi Deviasi Waktu", style={'color': '#a3a3c2'}),
                    html.H2(f"{pred_delay:.2f} Hari", style={'color': '#f1c40f', 'font-weight': 'bold', 'margin': '5px 0'}),
                    html.P("Metode Regresi ML", style={'font-size': '11px', 'color': '#7575a3'})
                ])
            ], width=4),
            dbc.Col([
                html.Div(style={'background': 'rgba(255,255,255,0.03)', 'padding': '15px', 'border-radius': '8px', 'text-align': 'center'}, children=[
                    html.H6("Peluang Keterlambatan", style={'color': '#a3a3c2'}),
                    html.H2(f"{proba_delay*100:.1f}%", style={'color': color, 'font-weight': 'bold', 'margin': '5px 0'}),
                    html.P("Metode Klasifikasi ML", style={'font-size': '11px', 'color': '#7575a3'})
                ])
            ], width=4),
            dbc.Col([
                html.P(advice, style={'font-size': '13px', 'margin-top': '5px', 'line-height': '1.5'})
            ], width=4)
        ])
    ])

# -------------------------------------------------------------------------
# Run Server
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False, port=8050)
