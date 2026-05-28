# C-Overcharged: Compiler (UI)

import logging
import warnings
import os
import time


logging.getLogger("streamlit").setLevel(logging.ERROR)


class _StreamlitHtmlFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "st.components.v1.html" not in record.getMessage()

logging.getLogger().addFilter(_StreamlitHtmlFilter())


warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=r".*st\.components\.v1\.html.*")



import json
import sys
import importlib

import streamlit as st
import streamlit.components.v1 as components


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import src.linker
import src.compiler
import src.assembly_gen
importlib.reload(src.linker)
importlib.reload(src.assembly_gen)
importlib.reload(src.compiler)
from src.linker import ExecutableGenerator

from src.Parser_SDT.parser_sdt import parse_source


def _get_sample_files() -> dict:
    inputs_dir = os.path.join(ROOT_DIR, "inputs")
    files_dict = {}
    if os.path.exists(inputs_dir):
        for f in sorted(os.listdir(inputs_dir)):
            if f.endswith(".c"):
                
                name = f[:-2].replace("_", " ")
                if f.startswith("ok_"):
                    label = f"OK - {name[3:].capitalize()}"
                elif f.startswith("sem_"):
                    label = f"SEM - {name[4:].capitalize()}"
                elif f.startswith("syn_"):
                    label = f"SYN - {name[4:].capitalize()}"
                else:
                    label = name.capitalize()
                files_dict[label] = f
    return files_dict

SAMPLE_FILES = _get_sample_files()

def _read_sample_file(file_name: str) -> str:
    file_path = os.path.join(ROOT_DIR, "inputs", file_name)
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as sample_file:
            return sample_file.read()
    except OSError:
        return f"/* Failed to load sample: {file_name} */\n"


def _build_sample_code() -> dict:
    return {label: _read_sample_file(file_name) for label, file_name in SAMPLE_FILES.items()}


SAMPLE_CODE = _build_sample_code()
DEFAULT_SAMPLE_KEY = next(iter(SAMPLE_CODE), "")


def _load_css() -> None:
    css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as css_file:
            st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)


def _inject_theme_detector() -> None:
    """Inject fonts via st.markdown (safe — no script tags needed here)."""
    st.markdown(
        '''
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@500;600&family=Montserrat:wght@800;900&family=Playfair+Display:ital,wght@1,700&display=swap" rel="stylesheet">
        ''',
        unsafe_allow_html=True,
    )


def _inject_scripts_component() -> None:
    """Motor de CSS Dinámico Persistente e Inyección de Theming"""
    html_code = f"""<!DOCTYPE html>
<html>
<head><style>html,body{{margin:0;padding:0;background:transparent;}}</style></head>
<body>
<script>
(function() {{
    var pdoc;
    var pwin;
    try {{ 
        pwin = window.parent;
        pdoc = pwin.document; 
    }} catch(e) {{ return; }}

    var BG_DARK  = 'https://raw.githubusercontent.com/AngelHusielLaraHernandez/Compiladores_Documentacion/main/python/ui/video/darkmode.mp4';
    var BG_LIGHT = 'https://raw.githubusercontent.com/AngelHusielLaraHernandez/Compiladores_Documentacion/main/python/ui/video/lightmode.mp4';

    // ── MEMORIA PERSISTENTE (Supera recargas de Streamlit + localStorage) ──
    if (!pwin.__cr_customState) {{
        pwin.__cr_customState = {{
            dark: {{ videoSrc: null, imgSrc: null, cssVariables: '' }},
            light: {{ videoSrc: null, imgSrc: null, cssVariables: '' }},
            gallery: []  // {{ id, type:'video'|'image', thumbnail (dataURL), fullDataURL (for images), cssVariables, theme, label }}
        }};
        // Restaurar galería desde localStorage
        try {{
            var saved = localStorage.getItem('cr_gallery');
            if (saved) {{
                var parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) {{
                    pwin.__cr_customState.gallery = parsed;
                }}
            }}
        }} catch(e) {{}}
    }}
    var customState = pwin.__cr_customState;

    function saveGalleryToStorage() {{
        try {{
            // Guardar solo lo necesario (sin blobUrl que no sobrevive recarga)
            var toSave = customState.gallery.map(function(item) {{
                return {{
                    id: item.id || ('' + Date.now() + Math.random()),
                    type: item.type || 'video',
                    thumbnail: item.thumbnail,
                    fullDataURL: item.fullDataURL || null,
                    cssVariables: item.cssVariables,
                    theme: item.theme,
                    label: item.label
                }};
            }});
            localStorage.setItem('cr_gallery', JSON.stringify(toSave));
        }} catch(e) {{ console.log('Gallery save error:', e); }}
    }}

    function buildColorCSS(themeSelector, rgbStr, currentTheme) {{
        var newCSS = `
            ${{themeSelector}} {{
                --cr-accent: rgb(${{rgbStr}}) !important;
                --cr-accent-glow: rgba(${{rgbStr}}, 0.4) !important;
                --cr-title-mid: rgb(${{rgbStr}}) !important;
            }}
            ${{themeSelector}} [data-testid="stAlert"] {{
                border-color: rgb(${{rgbStr}}) !important;
            }}
            ${{themeSelector}} [data-testid="stAlert"] svg {{
                fill: rgb(${{rgbStr}}) !important;
            }}
        `;
        if (currentTheme === 'light') {{
            newCSS += `
                ${{themeSelector}} h1, ${{themeSelector}} h2, ${{themeSelector}} h3, ${{themeSelector}} h4, ${{themeSelector}} .status-title {{
                    text-shadow: 2px 2px 0px rgb(${{rgbStr}}), 0px 0px 8px rgba(255, 255, 255, 0.9) !important;
                }}
                ${{themeSelector}} [data-testid="stMain"] h3 {{
                    box-shadow: 4px 4px 0px rgb(${{rgbStr}}) !important;
                    border-color: #000000 !important;
                }}
                ${{themeSelector}} .status-card,
                ${{themeSelector}} .status-grid .status-card {{
                    box-shadow: 4px 4px 0px rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} .status-grid .status-card:nth-child(odd) {{ box-shadow: 5px 5px 0px rgb(${{rgbStr}}) !important; }}
                ${{themeSelector}} .status-grid .status-card:nth-child(even) {{ box-shadow: -5px 5px 0px rgb(${{rgbStr}}) !important; }}
                ${{themeSelector}} .status-grid .status-card:hover {{ background-color: rgb(${{rgbStr}}) !important; box-shadow: none !important; }}
                ${{themeSelector}} .stTabs [data-baseweb="tab-list"] {{
                    box-shadow: 5px 5px 0px rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} .stTabs [data-baseweb="tab"][aria-selected="true"],
                ${{themeSelector}} .stTabs button[role="tab"][aria-selected="true"] {{
                    background: rgb(${{rgbStr}}) !important;
                    border: 2px solid #000000 !important;
                    color: #FFFFFF !important;
                    box-shadow: 3px 3px 0px rgba(0,0,0,0.3) !important;
                }}
                ${{themeSelector}} .stTabs [data-baseweb="tab"]:hover {{
                    background-color: rgba(${{rgbStr}}, 0.15) !important;
                    border-color: rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} [data-testid="stTabsScrollLeft"],
                ${{themeSelector}} [data-testid="stTabsScrollRight"] {{
                    box-shadow: 3px 3px 0px rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} [data-testid="stTabsScrollLeft"]:hover,
                ${{themeSelector}} [data-testid="stTabsScrollRight"]:hover {{
                    background-color: rgb(${{rgbStr}}) !important;
                    color: #000000 !important;
                }}
                ${{themeSelector}} [data-testid="stDataFrame"],
                ${{themeSelector}} .cr-table-wrapper {{
                    box-shadow: 5px 5px 0px rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} .cr-table thead th {{
                    background: rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} .stButton > button,
                ${{themeSelector}} button[data-testid="baseButton-primary"] {{
                    box-shadow: 5px 5px 0px rgb(${{rgbStr}}) !important;
                    background-color: #000000 !important;
                }}
                ${{themeSelector}} .stButton > button:hover,
                ${{themeSelector}} button[data-testid="baseButton-primary"]:hover {{
                    background-color: rgb(${{rgbStr}}) !important;
                    border-color: rgb(${{rgbStr}}) !important;
                    color: #000000 !important;
                    box-shadow: 0px 0px 0px transparent !important;
                }}
                ${{themeSelector}} .stDownloadButton > button,
                ${{themeSelector}} [data-testid="stFileUploadDropzone"] button {{
                    box-shadow: 4px 4px 0px rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} .stDownloadButton > button:hover,
                ${{themeSelector}} [data-testid="stFileUploadDropzone"] button:hover {{
                    background-color: rgb(${{rgbStr}}) !important;
                    border-color: rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} [data-testid="stSelectbox"] div[data-baseweb="select"] {{
                    border: 2px solid rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} textarea {{
                    border: 2px solid rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} [data-testid="stAlert"] {{
                    box-shadow: 4px 4px 0px rgba(${{rgbStr}}, 0.5) !important;
                }}
            `;
        }} else {{
            newCSS += `
                ${{themeSelector}} [data-testid="stMain"] h3 {{
                    background-color: rgba(${{rgbStr}}, 0.25) !important;
                    border-color: rgba(${{rgbStr}}, 0.4) !important;
                    text-shadow: 0px 0px 10px rgba(${{rgbStr}}, 0.5) !important;
                }}
                ${{themeSelector}} .stTabs [data-baseweb="tab"][aria-selected="true"] {{
                    background: linear-gradient(135deg, rgba(${{rgbStr}}, 0.9), rgba(${{rgbStr}}, 0.6)) !important;
                    border-color: rgba(${{rgbStr}}, 0.5) !important;
                    box-shadow: 0 4px 20px rgba(${{rgbStr}}, 0.3) !important;
                }}
                ${{themeSelector}} .stTabs [data-baseweb="tab"]:hover {{
                    background-color: rgba(${{rgbStr}}, 0.15) !important;
                    border-color: rgba(${{rgbStr}}, 0.5) !important;
                }}
                ${{themeSelector}} [data-testid="stTabsScrollLeft"],
                ${{themeSelector}} [data-testid="stTabsScrollRight"] {{
                    box-shadow: 0 0 10px rgba(${{rgbStr}}, 0.2) !important;
                    border-color: rgba(${{rgbStr}}, 0.5) !important;
                }}
                ${{themeSelector}} [data-testid="stTabsScrollLeft"]:hover,
                ${{themeSelector}} [data-testid="stTabsScrollRight"]:hover {{
                    background: linear-gradient(135deg, rgba(${{rgbStr}}, 0.9), rgba(${{rgbStr}}, 0.6)) !important;
                    box-shadow: 0 0 20px rgba(${{rgbStr}}, 0.5) !important;
                }}
                ${{themeSelector}} .stButton > button,
                ${{themeSelector}} button[data-testid="baseButton-primary"] {{
                    box-shadow: 0 4px 16px rgba(${{rgbStr}}, 0.3) !important;
                }}
                ${{themeSelector}} .stButton > button:hover,
                ${{themeSelector}} button[data-testid="baseButton-primary"]:hover {{
                    background: rgb(${{rgbStr}}) !important;
                    box-shadow: 0 8px 28px rgba(${{rgbStr}}, 0.5) !important;
                    border-color: rgb(${{rgbStr}}) !important;
                }}
                ${{themeSelector}} .cr-table thead th {{
                    background: linear-gradient(135deg, rgba(${{rgbStr}}, 0.4), rgba(${{rgbStr}}, 0.2)) !important;
                    border-bottom: 2px solid rgba(${{rgbStr}}, 0.5) !important;
                }}
                ${{themeSelector}} .cr-table-wrapper,
                ${{themeSelector}} [data-testid="stDataFrame"] {{
                    border-color: rgba(${{rgbStr}}, 0.3) !important;
                    box-shadow: 0 4px 24px rgba(0,0,0,0.4), 0 0 40px rgba(${{rgbStr}}, 0.1) !important;
                }}
                ${{themeSelector}} [data-testid="stAlert"] {{
                    border-color: rgba(${{rgbStr}}, 0.5) !important;
                    box-shadow: 0 4px 15px rgba(${{rgbStr}}, 0.2) !important;
                }}
            `;
        }}
        return newCSS;
    }}

    function detectTheme() {{
        var body = pdoc.body;
        if (!body) return;
        var col = pwin.getComputedStyle(body).color;
        var m = col.match(/\\d+/g);
        if (!m) return;
        var lum = 0.299*+m[0] + 0.587*+m[1] + 0.114*+m[2];
        var theme = lum > 128 ? 'dark' : 'light';
        pdoc.documentElement.setAttribute('data-cr-theme', theme);
        applyCustomState();
    }}

    function forceTransparent() {{
        var sels = [
            'html','body','#root','.stApp','.withScreencast',
            '[data-testid="stAppViewContainer"]',
            '[data-testid="stHeader"]',
            '[data-testid="stMain"]',
            '[data-testid="stMainBlockContainer"]',
            'section.main',
            '[data-testid="stFullScreenFrame"]'
        ];
        sels.forEach(function(sel) {{
            pdoc.querySelectorAll(sel).forEach(function(el) {{
                el.style.setProperty('background',       'transparent', 'important');
                el.style.setProperty('background-color', 'transparent', 'important');
            }});
        }});
    }}

    function injectThemingEngine() {{
        if (pdoc.getElementById('cr-smart-themer')) return;

        var btnStyle = pdoc.createElement('style');
        btnStyle.textContent = `
            /* ── Botón Paleta (Abre Galería) ── */
            #cr-smart-themer {{
                position: fixed; bottom: 30px; right: 30px; z-index: 99999;
                width: 50px; height: 50px; border-radius: 50%;
                background: rgba(30, 33, 44, 0.85); backdrop-filter: blur(10px);
                border: 2px solid rgba(77, 141, 255, 0.5);
                display: flex; justify-content: center; align-items: center;
                cursor: pointer; transition: all 0.3s cubic-bezier(0.22,1,0.36,1);
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }}
            #cr-smart-themer:hover {{
                transform: scale(1.1) translateY(-5px); border-color: #4d8dff; box-shadow: 0 8px 25px rgba(77,141,255,0.4);
            }}
            #cr-smart-themer svg {{ width: 24px; height: 24px; fill: #e4e6eb; transition: fill 0.3s; }}
            #cr-smart-themer:hover svg {{ fill: #4d8dff; }}
            html[data-cr-theme="light"] #cr-smart-themer {{
                background: rgba(255, 255, 255, 0.9); border-color: #000; box-shadow: 4px 4px 0px #00BFFF;
            }}
            html[data-cr-theme="light"] #cr-smart-themer svg {{ fill: #000; }}
            html[data-cr-theme="light"] #cr-smart-themer:hover {{
                background: #00BFFF; border-color: #000; transform: translate(2px, 2px); box-shadow: none;
            }}

            /* ── Botón de Reinicio ── */
            #cr-theme-reset {{
                position: fixed; bottom: 95px; right: 35px; z-index: 99998;
                width: 40px; height: 40px; border-radius: 50%;
                background: rgba(220, 53, 69, 0.9); backdrop-filter: blur(10px);
                border: 2px solid rgba(255, 255, 255, 0.8);
                display: none; justify-content: center; align-items: center;
                cursor: pointer; transition: all 0.3s cubic-bezier(0.22,1,0.36,1);
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }}
            #cr-theme-reset:hover {{
                transform: scale(1.1) translateY(-3px);
                background: #ff4444;
                box-shadow: 0 6px 20px rgba(255, 68, 68, 0.4);
            }}
            #cr-theme-reset svg {{ width: 18px; height: 18px; fill: #fff; transition: transform 0.3s; }}
            #cr-theme-reset:hover svg {{ transform: rotate(-45deg); }}
            html[data-cr-theme="light"] #cr-theme-reset {{
                border: 2px solid #000; box-shadow: 3px 3px 0px #000;
            }}
            html[data-cr-theme="light"] #cr-theme-reset:hover {{
                box-shadow: none; transform: translate(2px, 2px);
            }}

            /* ── Panel Galería Brutalista ── */
            #cr-gallery-panel {{
                position: fixed; bottom: 90px; right: 80px; z-index: 100000;
                width: 260px; max-height: 420px;
                background: rgba(20, 24, 38, 0.95); backdrop-filter: blur(18px);
                border: 3px solid #4d8dff;
                border-radius: 0px;
                box-shadow: 6px 6px 0px rgba(77, 141, 255, 0.5);
                display: none; flex-direction: column;
                overflow: hidden;
                animation: crGallerySlideIn 0.3s cubic-bezier(0.22,1,0.36,1) both;
            }}
            @keyframes crGallerySlideIn {{
                0%   {{ opacity: 0; transform: translateY(20px) scale(0.95); }}
                100% {{ opacity: 1; transform: translateY(0) scale(1); }}
            }}
            #cr-gallery-panel .gallery-header {{
                padding: 12px 14px; display: flex; align-items: center; justify-content: space-between;
                border-bottom: 3px solid #4d8dff;
                background: rgba(77, 141, 255, 0.15);
            }}
            #cr-gallery-panel .gallery-header span {{
                font-family: 'Montserrat', sans-serif; font-weight: 800; font-size: 13px;
                text-transform: uppercase; letter-spacing: 1.5px; color: #e4e6eb;
            }}
            #cr-gallery-panel .gallery-upload-btn {{
                width: 34px; height: 34px; border-radius: 0;
                background: #4d8dff; border: 2px solid #fff;
                display: flex; justify-content: center; align-items: center;
                cursor: pointer; transition: all 0.2s;
                box-shadow: 3px 3px 0px rgba(0,0,0,0.4);
            }}
            #cr-gallery-panel .gallery-upload-btn:hover {{
                background: #fff; box-shadow: none; transform: translate(2px,2px);
            }}
            #cr-gallery-panel .gallery-upload-btn svg {{ width: 18px; height: 18px; fill: #fff; }}
            #cr-gallery-panel .gallery-upload-btn:hover svg {{ fill: #4d8dff; }}
            #cr-gallery-panel .gallery-list {{
                flex: 1; overflow-y: auto; padding: 10px;
                scrollbar-width: thin; scrollbar-color: rgba(77,141,255,0.4) transparent;
            }}
            #cr-gallery-panel .gallery-list::-webkit-scrollbar {{ width: 5px; }}
            #cr-gallery-panel .gallery-list::-webkit-scrollbar-thumb {{ background: rgba(77,141,255,0.4); border-radius: 3px; }}
            #cr-gallery-panel .gallery-empty {{
                text-align: center; padding: 30px 10px; color: rgba(228,230,235,0.5);
                font-family: 'JetBrains Mono', monospace; font-size: 11px;
            }}
            #cr-gallery-panel .gallery-item {{
                margin-bottom: 10px; cursor: pointer; position: relative;
                border: 2px solid rgba(77, 141, 255, 0.3);
                border-radius: 0px;
                overflow: hidden; transition: all 0.25s;
                box-shadow: 3px 3px 0px rgba(0,0,0,0.3);
            }}
            #cr-gallery-panel .gallery-item:hover {{
                border-color: #4d8dff;
                box-shadow: 0px 0px 0px transparent;
                transform: translate(2px, 2px);
            }}
            #cr-gallery-panel .gallery-item.active {{
                border-color: #4d8dff;
                box-shadow: 0 0 12px rgba(77, 141, 255, 0.6);
            }}
            #cr-gallery-panel .gallery-item img {{
                width: 100%; height: 80px; object-fit: cover; display: block;
                filter: sepia(0.8) contrast(1.5);
                transition: filter 0.3s;
            }}
            #cr-gallery-panel .gallery-item:hover img {{
                filter: sepia(0) contrast(1);
            }}
            #cr-gallery-panel .gallery-item .gallery-label {{
                position: absolute; bottom: 0; left: 0; right: 0;
                padding: 4px 8px;
                background: rgba(0,0,0,0.75);
                font-family: 'JetBrains Mono', monospace; font-size: 10px;
                color: #e4e6eb; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            }}
            #cr-gallery-panel .gallery-item .gallery-theme-badge {{
                position: absolute; top: 4px; right: 4px;
                padding: 2px 6px; font-size: 9px; font-weight: 700;
                font-family: 'Montserrat', sans-serif; text-transform: uppercase;
                letter-spacing: 0.8px;
                background: rgba(77, 141, 255, 0.85); color: #fff;
                border: 1px solid rgba(255,255,255,0.3);
            }}

            /* ── Botón Eliminar en galería ── */
            #cr-gallery-panel .gallery-delete-btn {{
                position: absolute; top: 4px; left: 50%; transform: translateX(-50%);
                width: 22px; height: 22px; border-radius: 50%;
                background: rgba(220, 53, 69, 0.9);
                color: #fff; font-size: 16px; font-weight: bold;
                display: none; justify-content: center; align-items: center;
                cursor: pointer; border: 1px solid rgba(255,255,255,0.5);
                line-height: 1; z-index: 10;
                transition: all 0.2s;
            }}
            #cr-gallery-panel .gallery-item:hover .gallery-delete-btn {{
                display: flex;
            }}
            #cr-gallery-panel .gallery-delete-btn:hover {{
                background: #ff2222; transform: translateX(-50%) scale(1.2);
            }}

            /* ── Panel Galería — Light mode ── */
            html[data-cr-theme="light"] #cr-gallery-panel {{
                background: rgba(255, 255, 255, 0.95);
                border: 3px solid #000;
                box-shadow: 6px 6px 0px #00BFFF;
            }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-header {{
                border-bottom: 3px solid #000;
                background: #00BFFF;
            }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-header span {{ color: #000; }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-upload-btn {{
                background: #000; border-color: #000;
                box-shadow: 3px 3px 0px #00BFFF;
            }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-upload-btn:hover {{
                background: #00BFFF;
            }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-upload-btn svg {{ fill: #fff; }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-upload-btn:hover svg {{ fill: #000; }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-empty {{ color: rgba(0,0,0,0.4); }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-item {{
                border: 2px solid #000;
                box-shadow: 3px 3px 0px #00BFFF;
            }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-item:hover {{
                box-shadow: none; transform: translate(2px,2px);
            }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-item.active {{
                border-color: #00BFFF; box-shadow: 0 0 0 3px #00BFFF;
            }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-item .gallery-theme-badge {{
                background: #00BFFF; color: #000; border-color: #000;
            }}
            html[data-cr-theme="light"] #cr-gallery-panel .gallery-item .gallery-label {{
                background: rgba(0,0,0,0.85); color: #fff;
            }}
        `;
        pdoc.head.appendChild(btnStyle);

        // ── ESTILOS Y LÓGICA DE ANIMACIÓN "COMPILANDO" ──
        var compileStyle = pdoc.createElement('style');
        compileStyle.textContent = `
            .stButton > button[data-testid="baseButton-primary"].is-compiling {{
                pointer-events: none !important;
                color: transparent !important;
                position: relative;
            }}
            .stButton > button[data-testid="baseButton-primary"].is-compiling::after {{
                content: 'COMPILANDO...';
                position: absolute; inset: 0;
                display: flex; align-items: center; justify-content: center;
                color: #fff !important; font-weight: 900; font-style: italic; letter-spacing: 2px;
                text-shadow: 0 0 10px rgba(255,255,255,0.5);
                z-index: 2;
            }}
            .stButton > button[data-testid="baseButton-primary"].is-compiling::before {{
                content: ''; position: absolute; bottom: 0; left: 0; height: 5px;
                background: #fff; z-index: 3;
                animation: crGlitchBar 1.5s infinite linear;
            }}
            @keyframes crGlitchBar {{
                0% {{ width: 0%; transform: translateX(0); opacity: 1; }}
                49% {{ width: 100%; transform: translateX(0); opacity: 1; }}
                50% {{ width: 100%; transform: translateX(10px); opacity: 0.5; }}
                51% {{ width: 100%; transform: translateX(-10px); opacity: 0.5; }}
                52% {{ width: 100%; transform: translateX(0); opacity: 1; }}
                100% {{ width: 0%; transform: translateX(0); opacity: 1; }}
            }}
            html[data-cr-theme="light"] .stButton > button[data-testid="baseButton-primary"].is-compiling::after {{
                color: #000 !important; text-shadow: none;
            }}
            html[data-cr-theme="light"] .stButton > button[data-testid="baseButton-primary"].is-compiling::before {{
                background: #000;
            }}
        `;
        pdoc.head.appendChild(compileStyle);

        // Detectar el clic en botones principales para activar la animación
        pdoc.addEventListener('click', function(e) {{
            var btn = e.target.closest('button[data-testid="baseButton-primary"]');
            if(btn && (btn.innerText.toUpperCase().includes('ANALYZE') || btn.innerText.toUpperCase().includes('COMPILAR') || btn.innerText.toUpperCase().includes('LINK'))) {{
                btn.classList.add('is-compiling');
            }}
        }});

        var fileInput = pdoc.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'video/*';
        fileInput.style.display = 'none';

        var imgFileInput = pdoc.createElement('input');
        imgFileInput.type = 'file';
        imgFileInput.accept = 'image/*';
        imgFileInput.style.display = 'none';

        // ── Panel Galería ──
        var galleryPanel = pdoc.createElement('div');
        galleryPanel.id = 'cr-gallery-panel';
        galleryPanel.innerHTML = `
            <div class="gallery-header">
                <span>Wallpaper</span>
                <div style="display:flex;gap:6px;">
                    <div class="gallery-upload-btn" id="cr-upload-video-btn" title="Cargar video de fondo">
                        <svg viewBox="0 0 24 24"><path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/></svg>
                    </div>
                    <div class="gallery-upload-btn" id="cr-upload-img-btn" title="Cargar imagen de fondo">
                        <svg viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                    </div>
                </div>
            </div>
            <div class="gallery-list"></div>
        `;

        // Botón Upload video dentro de la galería
        galleryPanel.querySelector('#cr-upload-video-btn').onclick = function(ev) {{
            ev.stopPropagation();
            fileInput.click();
        }};
        // Botón Upload imagen dentro de la galería
        galleryPanel.querySelector('#cr-upload-img-btn').onclick = function(ev) {{
            ev.stopPropagation();
            imgFileInput.click();
        }};

        // Función para renderizar miniaturas
        function renderGallery() {{
            var list = galleryPanel.querySelector('.gallery-list');
            var currentTheme = pdoc.documentElement.getAttribute('data-cr-theme') || 'light';
            if (!customState.gallery || customState.gallery.length === 0) {{
                list.innerHTML = '<div class="gallery-empty">No funds loaded.<br>Use the buttons to add.</div>';
                return;
            }}
            list.innerHTML = '';
            customState.gallery.forEach(function(item, idx) {{
                var div = pdoc.createElement('div');
                div.className = 'gallery-item';
                // Determinar si este item está activo
                var isActive = false;
                if (item.type === 'image') {{
                    isActive = customState[currentTheme].imgSrc === item.fullDataURL;
                }} else {{
                    isActive = customState[currentTheme].videoSrc === (item.blobUrl || item.fullDataURL);
                }}
                if (isActive) div.className += ' active';
                var img = pdoc.createElement('img');
                img.src = item.thumbnail;
                img.alt = item.label;
                div.appendChild(img);
                // Badge de tipo (VID / IMG)
                var typeBadge = pdoc.createElement('div');
                typeBadge.className = 'gallery-theme-badge';
                typeBadge.style.left = '4px'; typeBadge.style.right = 'auto';
                typeBadge.textContent = item.type === 'image' ? 'IMG' : 'VID';
                div.appendChild(typeBadge);
                var badge = pdoc.createElement('div');
                badge.className = 'gallery-theme-badge';
                badge.textContent = item.theme === 'dark' ? 'DRK' : 'LGT';
                div.appendChild(badge);
                // Botón eliminar
                var delBtn = pdoc.createElement('div');
                delBtn.className = 'gallery-delete-btn';
                delBtn.innerHTML = '&times;';
                delBtn.title = 'Eliminar fondo';
                delBtn.onclick = function(ev) {{
                    ev.stopPropagation();
                    // Si este fondo está activo, resetear
                    if (isActive) {{
                        if (item.type === 'image') {{
                            customState[currentTheme].imgSrc = null;
                        }} else {{
                            customState[currentTheme].videoSrc = null;
                        }}
                        customState[currentTheme].cssVariables = '';
                        applyCustomState();
                    }}
                    // Revocar blobUrl si existe
                    if (item.blobUrl) {{
                        try {{ pwin.URL.revokeObjectURL(item.blobUrl); }} catch(e2) {{}}
                    }}
                    customState.gallery.splice(idx, 1);
                    saveGalleryToStorage();
                    renderGallery();
                }};
                div.appendChild(delBtn);
                var lbl = pdoc.createElement('div');
                lbl.className = 'gallery-label';
                lbl.textContent = item.label;
                div.appendChild(lbl);
                div.onclick = function() {{
                    // Aplicar este fondo al tema actual
                    customState[currentTheme].cssVariables = item.cssVariables;
                    if (item.type === 'image') {{
                        customState[currentTheme].videoSrc = null;
                        customState[currentTheme].imgSrc = item.fullDataURL;
                    }} else {{
                        customState[currentTheme].imgSrc = null;
                        if (item.blobUrl) {{
                            customState[currentTheme].videoSrc = item.blobUrl;
                        }} else if (item.fullDataURL) {{
                            customState[currentTheme].videoSrc = null;
                            customState[currentTheme].imgSrc = item.fullDataURL;
                        }}
                    }}
                    applyCustomState();
                    galleryPanel.style.display = 'none';
                }};
                list.appendChild(div);
            }});
        }}

        // Botón principal (Paleta) — ahora abre/cierra galería
        var btn = pdoc.createElement('div');
        btn.id = 'cr-smart-themer';
        btn.title = "Galería de fondos";
        btn.innerHTML = `<svg viewBox="0 0 24 24"><path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4C8.67 8 8 7.33 8 6.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5S16.67 9 17.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>`;
        btn.onclick = function() {{
            var isOpen = galleryPanel.style.display === 'flex';
            if (isOpen) {{
                galleryPanel.style.display = 'none';
            }} else {{
                renderGallery();
                galleryPanel.style.display = 'flex';
            }}
        }};

        // Botón Reset — vuelve al fondo original, galería intacta
        var resetBtn = pdoc.createElement('div');
        resetBtn.id = 'cr-theme-reset';
        resetBtn.title = "Restaurar diseño original";
        resetBtn.innerHTML = `<svg viewBox="0 0 24 24"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/></svg>`;
        resetBtn.onclick = function() {{
            var currentTheme = pdoc.documentElement.getAttribute('data-cr-theme') || 'light';
            customState[currentTheme].videoSrc = null;
            customState[currentTheme].imgSrc = null;
            customState[currentTheme].cssVariables = '';
            applyCustomState();
        }};

        pdoc.body.appendChild(btn);
        pdoc.body.appendChild(resetBtn);
        pdoc.body.appendChild(galleryPanel);
        pdoc.body.appendChild(fileInput);
        pdoc.body.appendChild(imgFileInput);

        // ── Handler para IMÁGENES ──
        imgFileInput.onchange = function(e) {{
            var file = e.target.files[0];
            if (!file) return;
            var currentTheme = pdoc.documentElement.getAttribute('data-cr-theme') || 'light';
            var reader = new FileReader();
            reader.onload = function(re) {{
                var dataURL = re.target.result;
                var img = new Image();
                img.onload = function() {{
                    // Extraer color dominante
                    var canvas = pdoc.createElement('canvas');
                    canvas.width = img.width || 640;
                    canvas.height = img.height || 360;
                    var ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    try {{
                        var imgData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                        var targetR = 0, targetG = 0, targetB = 0;
                        var maxVibrance = -1;
                        for (var i = 0; i < imgData.length; i += 16 * 4) {{
                            var r = imgData[i], g = imgData[i+1], b = imgData[i+2];
                            var maxChannel = Math.max(r, g, b);
                            var minChannel = Math.min(r, g, b);
                            var saturation = (maxChannel === 0) ? 0 : (maxChannel - minChannel) / maxChannel;
                            var luminance = (maxChannel + minChannel) / 2;
                            if (luminance > 20 && luminance < 230) {{
                                var vibranceScore = saturation * luminance;
                                if (vibranceScore > maxVibrance) {{
                                    maxVibrance = vibranceScore;
                                    targetR = r; targetG = g; targetB = b;
                                }}
                            }}
                        }}
                        if (maxVibrance === 0 && targetR === targetG && targetG === targetB) {{
                            if (currentTheme === 'dark') {{ targetR=77; targetG=141; targetB=255; }}
                            else {{ targetR=0; targetG=191; targetB=255; }}
                        }}
                        var rgbStr = targetR + ', ' + targetG + ', ' + targetB;
                        var themeSelector = 'html[data-cr-theme="' + currentTheme + '"] body';
                        var newCSS = buildColorCSS(themeSelector, rgbStr, currentTheme);

                        customState[currentTheme].imgSrc = dataURL;
                        customState[currentTheme].videoSrc = null;
                        customState[currentTheme].cssVariables = newCSS;

                        // Generar miniatura
                        var thumbCanvas = pdoc.createElement('canvas');
                        thumbCanvas.width = 240; thumbCanvas.height = 135;
                        var thumbCtx = thumbCanvas.getContext('2d');
                        thumbCtx.drawImage(img, 0, 0, 240, 135);
                        var thumbnailDataURL = thumbCanvas.toDataURL('image/jpeg', 0.7);

                        var entryId = '' + Date.now() + Math.random();
                        var galleryEntry = {{
                            id: entryId,
                            type: 'image',
                            blobUrl: null,
                            thumbnail: thumbnailDataURL,
                            fullDataURL: dataURL,
                            cssVariables: newCSS,
                            theme: currentTheme,
                            label: file.name
                        }};
                        customState.gallery.push(galleryEntry);
                        saveGalleryToStorage();
                        applyCustomState();
                        var gp = pdoc.getElementById('cr-gallery-panel');
                        if (gp) gp.style.display = 'none';
                    }} catch(err) {{
                        console.log("Error al procesar imagen: ", err);
                    }}
                }};
                img.src = dataURL;
            }};
            reader.readAsDataURL(file);
            imgFileInput.value = "";
        }};

        fileInput.onchange = function(e) {{
            var file = e.target.files[0];
            if (!file) return;

            var currentTheme = pdoc.documentElement.getAttribute('data-cr-theme') || 'light';
            // Crear Blob URL en el window padre para que sobreviva recargas de iframe
            var url = pwin.URL.createObjectURL(file);

            var hiddenVideo = pdoc.createElement('video');
            hiddenVideo.src = url;
            hiddenVideo.muted = true;
            hiddenVideo.playsInline = true;

            hiddenVideo.onloadeddata = function() {{
                hiddenVideo.currentTime = Math.max(1, hiddenVideo.duration / 2);
            }};

            hiddenVideo.onseeked = function() {{
                var canvas = pdoc.createElement('canvas');
                canvas.width = hiddenVideo.videoWidth || 640;
                canvas.height = hiddenVideo.videoHeight || 360;
                var ctx = canvas.getContext('2d');
                ctx.drawImage(hiddenVideo, 0, 0, canvas.width, canvas.height);
                
                try {{
                    var imgData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                    var targetR = 0, targetG = 0, targetB = 0;
                    var maxVibrance = -1;

                    for (var i = 0; i < imgData.length; i += 16 * 4) {{
                        var r = imgData[i], g = imgData[i+1], b = imgData[i+2];
                        var maxChannel = Math.max(r, g, b);
                        var minChannel = Math.min(r, g, b);
                        var saturation = (maxChannel === 0) ? 0 : (maxChannel - minChannel) / maxChannel;
                        var luminance = (maxChannel + minChannel) / 2;

                        if (luminance > 20 && luminance < 230) {{
                            var vibranceScore = saturation * luminance;
                            if (vibranceScore > maxVibrance) {{
                                maxVibrance = vibranceScore;
                                targetR = r; targetG = g; targetB = b;
                            }}
                        }}
                    }}

                    // Si la imagen es blanco y negro puro, forzamos un color de la paleta
                    if (maxVibrance === 0 && targetR === targetG && targetG === targetB) {{
                        if (currentTheme === 'dark') {{ targetR=77; targetG=141; targetB=255; }}
                        else {{ targetR=0; targetG=191; targetB=255; }}
                    }}

                    var rgbStr = targetR + ', ' + targetG + ', ' + targetB;
                    var themeSelector = 'html[data-cr-theme="' + currentTheme + '"] body';
                    var newCSS = buildColorCSS(themeSelector, rgbStr, currentTheme);

                    customState[currentTheme].videoSrc = url;
                    customState[currentTheme].imgSrc = null;
                    customState[currentTheme].cssVariables = newCSS;

                    // ── Generar miniatura para la galería ──
                    var thumbCanvas = pdoc.createElement('canvas');
                    thumbCanvas.width = 240;
                    thumbCanvas.height = 135;
                    var thumbCtx = thumbCanvas.getContext('2d');
                    thumbCtx.drawImage(hiddenVideo, 0, 0, 240, 135);
                    var thumbnailDataURL = thumbCanvas.toDataURL('image/jpeg', 0.7);

                    // Para videos, generar un frame completo como dataURL para persistencia
                    var fullCanvas = pdoc.createElement('canvas');
                    fullCanvas.width = hiddenVideo.videoWidth || 640;
                    fullCanvas.height = hiddenVideo.videoHeight || 360;
                    var fullCtx = fullCanvas.getContext('2d');
                    fullCtx.drawImage(hiddenVideo, 0, 0, fullCanvas.width, fullCanvas.height);
                    var fullDataURL = fullCanvas.toDataURL('image/jpeg', 0.85);

                    var entryId = '' + Date.now() + Math.random();
                    var galleryEntry = {{
                        id: entryId,
                        type: 'video',
                        blobUrl: url,
                        thumbnail: thumbnailDataURL,
                        fullDataURL: fullDataURL,
                        cssVariables: newCSS,
                        theme: currentTheme,
                        label: file.name
                    }};
                    customState.gallery.push(galleryEntry);
                    saveGalleryToStorage();

                    applyCustomState();
                    // Cerrar galería después de aplicar
                    var gp = pdoc.getElementById('cr-gallery-panel');
                    if (gp) gp.style.display = 'none';
                }} catch(err) {{
                    console.log("Error al procesar frame: ", err);
                }}
                fileInput.value = "";
            }};
        }};
    }}

    function applyCustomState() {{
        var currentTheme = pdoc.documentElement.getAttribute('data-cr-theme') || 'light';
        var styleEl = pdoc.getElementById('cr-dynamic-theme-css');
        if (!styleEl) {{
            styleEl = pdoc.createElement('style');
            styleEl.id = 'cr-dynamic-theme-css';
            pdoc.head.appendChild(styleEl);
        }}
        styleEl.textContent = customState.dark.cssVariables + customState.light.cssVariables;

        var vidDark = pdoc.getElementById('vid-dark');
        var vidLight = pdoc.getElementById('vid-light');

        // ── Manejar fondos de imagen estática ──
        var imgBgEl = pdoc.getElementById('cr-img-bg');
        if (!imgBgEl) {{
            imgBgEl = pdoc.createElement('div');
            imgBgEl.id = 'cr-img-bg';
            imgBgEl.style.cssText = 'position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none;background-size:cover;background-position:center;opacity:0;transition:opacity 1.4s ease;';
            var vbg = pdoc.getElementById('cr-video-bg');
            if (vbg) vbg.parentNode.insertBefore(imgBgEl, vbg.nextSibling);
            else pdoc.body.insertBefore(imgBgEl, pdoc.body.firstChild);
        }}

        var hasImgDark = customState.dark.imgSrc !== null;
        var hasImgLight = customState.light.imgSrc !== null;

        // Para el tema actual, decidir si mostrar imagen o video
        if (currentTheme === 'dark') {{
            if (hasImgDark) {{
                imgBgEl.style.backgroundImage = 'url(' + customState.dark.imgSrc + ')';
                imgBgEl.style.opacity = '1';
                if (vidDark) vidDark.style.opacity = '0';
            }} else {{
                imgBgEl.style.opacity = '0';
                imgBgEl.style.backgroundImage = 'none';
                if (vidDark) {{
                    vidDark.style.opacity = '1';
                    var targetDark = customState.dark.videoSrc || BG_DARK;
                    if (vidDark.getAttribute('src') !== targetDark) {{
                        vidDark.setAttribute('src', targetDark);
                        vidDark.load(); vidDark.play();
                    }}
                }}
            }}
            if (vidLight) vidLight.style.opacity = '0';
        }} else {{
            if (hasImgLight) {{
                imgBgEl.style.backgroundImage = 'url(' + customState.light.imgSrc + ')';
                imgBgEl.style.opacity = '1';
                if (vidLight) vidLight.style.opacity = '0';
            }} else {{
                imgBgEl.style.opacity = '0';
                imgBgEl.style.backgroundImage = 'none';
                if (vidLight) {{
                    vidLight.style.opacity = '1';
                    var targetLight = customState.light.videoSrc || BG_LIGHT;
                    if (vidLight.getAttribute('src') !== targetLight) {{
                        vidLight.setAttribute('src', targetLight);
                        vidLight.load(); vidLight.play();
                    }}
                }}
            }}
            if (vidDark) vidDark.style.opacity = '0';
        }}

        // Sin imagen: restaurar comportamiento normal de videos
        if (!hasImgDark && vidDark) {{
            var targetDark2 = customState.dark.videoSrc || BG_DARK;
            if (vidDark.getAttribute('src') !== targetDark2) {{
                vidDark.setAttribute('src', targetDark2);
                vidDark.load(); vidDark.play();
            }}
        }}
        if (!hasImgLight && vidLight) {{
            var targetLight2 = customState.light.videoSrc || BG_LIGHT;
            if (vidLight.getAttribute('src') !== targetLight2) {{
                vidLight.setAttribute('src', targetLight2);
                vidLight.load(); vidLight.play();
            }}
        }}

        // Mostrar u Ocultar el botón de Reinicio
        var resetBtn = pdoc.getElementById('cr-theme-reset');
        if (resetBtn) {{
            if (customState[currentTheme].videoSrc !== null || customState[currentTheme].imgSrc !== null) {{
                resetBtn.style.display = 'flex';
            }} else {{
                resetBtn.style.display = 'none';
            }}
        }}
    }}

    function ensureVideoBg() {{
        if (pdoc.getElementById('cr-video-bg')) return;
        if (!pdoc.getElementById('cr-video-style')) {{
            var style = pdoc.createElement('style');
            style.id = 'cr-video-style';
            style.textContent = [
                '#cr-video-bg{{position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none;}}',
                '.cr-bg-video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;',
                '  opacity:0;transition:opacity 1.4s ease;will-change:opacity;}}',
                'html[data-cr-theme="dark"]  #vid-dark  {{opacity:1;}}',
                'html[data-cr-theme="light"] #vid-light {{opacity:1;}}',
                'html:not([data-cr-theme])   #vid-light {{opacity:1;}}'
            ].join('');
            pdoc.head.appendChild(style);
        }}

        var bg = pdoc.createElement('div');
        bg.id = 'cr-video-bg';

        function makeVid(id, src) {{
            var v = pdoc.createElement('video');
            v.id = id;
            v.className = 'cr-bg-video';
            v.autoplay = true; v.loop = true; v.muted = true;
            v.setAttribute('playsinline', ''); v.setAttribute('preload', 'auto');
            var s = pdoc.createElement('source');
            s.src  = src; s.type = 'video/mp4';
            v.appendChild(s); v.load(); v.play().catch(function(){{}});
            return v;
        }}
        bg.appendChild(makeVid('vid-dark',  BG_DARK));
        bg.appendChild(makeVid('vid-light', BG_LIGHT));
        pdoc.body.insertBefore(bg, pdoc.body.firstChild);
    }}
    
    function checkFullscreen() {{
        var isFs = false;
        if (pdoc.querySelector('.stFullScreen') || pdoc.querySelector('[data-testid="stFullScreenOverlay"]')) isFs = true;
        var vw = pwin.innerWidth; var vh = pwin.innerHeight;
        pdoc.querySelectorAll('[data-testid="stFullScreenFrame"]').forEach(function(frame) {{
            var rect = frame.getBoundingClientRect();
            if (rect.width > vw * 0.8 && rect.height > vh * 0.8) isFs = true;
        }});
        if (isFs) pdoc.body.setAttribute('data-cr-fullscreen', 'true');
        else pdoc.body.removeAttribute('data-cr-fullscreen');
    }}

    var lastActiveTab = ''; var twAnimating = false; var twTimer = null;
    function typewriterReveal(pre) {{
        if (!pre) return;
        var codeEl = pre.querySelector('code');
        if (!codeEl) return;
        var textNodes = [];
        function walk(node) {{
            if (node.nodeType === 3) {{ 
                if (node.textContent.length > 0) textNodes.push(node);
            }} else {{
                for (var i = 0; i < node.childNodes.length; i++) walk(node.childNodes[i]);
            }}
        }}
        walk(codeEl);
        if (textNodes.length === 0) {{ twAnimating = false; return; }}
        var originals = textNodes.map(function(n) {{ return n.textContent; }});
        var totalChars = originals.reduce(function(s, t) {{ return s + t.length; }}, 0);
        textNodes.forEach(function(n) {{ n.textContent = ''; }});
        pre.classList.add('cr-typing'); pre.style.overflow = 'hidden';
        var speed = Math.max(1, Math.min(15, Math.round(2500 / totalChars)));
        var nodeIdx = 0, charIdx = 0;
        function typeChar() {{
            if (nodeIdx >= textNodes.length) {{
                pre.classList.remove('cr-typing'); pre.style.overflow = 'auto'; twAnimating = false; return;
            }}
            var orig = originals[nodeIdx];
            charIdx++; textNodes[nodeIdx].textContent = orig.substring(0, charIdx);
            pre.scrollTop = pre.scrollHeight;
            if (charIdx >= orig.length) {{ nodeIdx++; charIdx = 0; }}
            twTimer = setTimeout(typeChar, speed);
        }}
        twTimer = setTimeout(typeChar, 60);
    }}

    function checkTabSwitch() {{
        var activeTab = pdoc.querySelector('[data-baseweb="tab"][aria-selected="true"]');
        if (!activeTab) return;
        var tabText = activeTab.textContent || '';
        if (tabText === lastActiveTab) return;
        lastActiveTab = tabText;
        var codeTabKeywords = ['optimized', 'tac', 'intermediate', 'assembly'];
        var isCodeTab = codeTabKeywords.some(function(kw) {{ return tabText.toLowerCase().indexOf(kw) !== -1; }});
        if (isCodeTab && !twAnimating) {{
            twAnimating = true;
            if (twTimer) {{ clearTimeout(twTimer); twTimer = null; }}
            setTimeout(function() {{
                var panels = pdoc.querySelectorAll('[data-baseweb="tab-panel"]');
                panels.forEach(function(panel) {{
                    if (panel.offsetHeight > 0) {{
                        var pre = panel.querySelector('pre');
                        if (pre) typewriterReveal(pre);
                    }}
                }});
            }}, 80);
        }}
    }}

    function bootstrap() {{
        detectTheme(); forceTransparent(); ensureVideoBg(); injectThemingEngine(); applyCustomState();
    }}

    bootstrap();
    setInterval(detectTheme, 800); setInterval(forceTransparent, 800);
    setInterval(ensureVideoBg, 1500); setInterval(checkFullscreen, 300); setInterval(checkTabSwitch, 400);

    try {{
        var obs = new MutationObserver(function() {{
            forceTransparent(); detectTheme(); ensureVideoBg(); injectThemingEngine(); applyCustomState();
        }});
        obs.observe(pdoc.body, {{ childList: true, subtree: true }});
    }} catch(e) {{}}
    
}})();
</script>
</body>
</html>"""
    components.html(html_code, height=0, scrolling=False)


def _intro_overlay() -> None:
    """Show a one-time cinematic intro overlay on first page load."""
    if st.session_state.get("intro_shown"):
        return
    st.session_state["intro_shown"] = True

    
    particles_html = ""
    import random
    random.seed(42)  
    for i in range(20):
        left = random.randint(5, 95)
        top = random.randint(20, 90)
        delay = round(random.uniform(0, 2.5), 2)
        size = random.randint(2, 6)
        opacity = round(random.uniform(0.2, 0.6), 2)
        particles_html += (
            f'<div class="intro-particle" style="'
            f'left:{left}%;top:{top}%;'
            f'width:{size}px;height:{size}px;'
            f'opacity:{opacity};'
            f'animation-delay:{delay}s;'
            f'"></div>'
        )

    st.markdown(
        f'''
        <div class="intro-overlay" id="introOverlay">
            <div class="intro-particles">{particles_html}</div>
            <span class="intro-line-1">Team 1</span>
            <span class="intro-line-2">Compilers</span>
            <span class="intro-line-3">Faculty of Engineering</span>
            <div class="intro-separator"></div>
            <span class="intro-title">C-Overcharged</span>
            <span class="intro-subtitle">Compiler/ &amp; visual</span>
        </div>
        <script>
            setTimeout(function() {{
                var el = document.getElementById('introOverlay');
                if (el) {{ el.classList.add('done'); }}
            }}, 7200);
            setTimeout(function() {{
                var el = document.getElementById('introOverlay');
                if (el) {{ el.remove(); }}
            }}, 7800);
        </script>
        ''',
        unsafe_allow_html=True,
    )

def _background_bubbles() -> None:
    """Inject persistent floating bubbles as animated background."""
    import random
    random.seed(99)
    bubbles = ""
    for _ in range(15):
        left = random.randint(2, 98)
        size = random.randint(18, 70)
        dur = round(random.uniform(12, 28), 1)
        sway = round(random.uniform(4, 8), 1)
        delay = round(random.uniform(0, 14), 1)
        bubbles += (
            f'<div class="bg-bubble" style="'
            f'left:{left}%;'
            f'width:{size}px;height:{size}px;'
            f'--dur:{dur}s;--sway:{sway}s;'
            f'animation-delay:{delay}s,{round(delay/2,1)}s;'
            f'"></div>'
        )
    st.markdown(
        f'<div class="bg-bubbles-container">{bubbles}</div>',
        unsafe_allow_html=True,
    )



def _status_block(syntax_ok: bool, semantic_ok: bool) -> None:
    syntax_class = "ok" if syntax_ok else "fail"
    syntax_text = "YES" if syntax_ok else "NO"

    sdt_ok = syntax_ok and semantic_ok
    sdt_class = "ok" if sdt_ok else "fail"
    if syntax_ok:
        sdt_text = "YES" if semantic_ok else "NO"
    else:
        sdt_text = "NO"

    st.markdown(
        f'''
        <div class="status-grid">
            <div class="status-card {syntax_class}">
                <div class="status-title">Valid Syntax</div>
                <div class="status-value">{syntax_text}</div>
            </div>
            <div class="status-card {sdt_class}">
                <div class="status-title">Valid SDT</div>
                <div class="status-value">{sdt_text}</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def _tokens_as_table(tokens):
    return [
        {"category": category, "lexeme": value}
        for category, value in tokens
    ]

def _normalize_cell(value):
    if isinstance(value, (dict, list, tuple, set)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _normalize_table(data):
    if data is None:
        return []
    if isinstance(data, dict):
        return [{k: _normalize_cell(v) for k, v in data.items()}]
    if isinstance(data, (list, tuple)):
        if not data:
            return []
        if all(isinstance(row, dict) for row in data):
            return [{k: _normalize_cell(v) for k, v in row.items()} for row in data]
        if all(isinstance(row, (list, tuple)) for row in data):
            return [[_normalize_cell(v) for v in row] for row in data]
    if hasattr(data, "applymap"):
        try:
            return data.applymap(_normalize_cell)
        except Exception:
            return data
    return data


def _render_custom_table(data, max_rows: int = 300) -> str:
    """Return an HTML string for a styled custom table from a list-of-dicts."""
    if not data:
        return ""
    rows = _normalize_table(data)
    if not rows or not isinstance(rows[0], dict):
        return ""
    headers = list(rows[0].keys())

    
    _tiny   = {"step", "line"}
    _narrow = {"status", "scope"}
    _medium = {"action", "node", "category", "lexeme", "identifier", "type"}
    num_cols = len(headers)
    col_parts = []
    for h in headers:
        hl = h.strip().lower()
        if hl in _tiny:
            col_parts.append('<col style="width:46px">')
        elif hl in _narrow:
            col_parts.append('<col style="width:58px">')
        elif hl in _medium:
            
            w = 70 if num_cols >= 6 else 80
            col_parts.append(f'<col style="width:{w}px">')
        else:
            col_parts.append('<col>')  
    colgroup_html = "<colgroup>" + "".join(col_parts) + "</colgroup>"

    
    header_html = "".join(f'<th>{h}</th>' for h in headers)

    
    body_rows = []
    for i, row in enumerate(rows[:max_rows]):
        cells = "".join(
            f'<td>{row.get(h, "")}</td>' for h in headers
        )
        body_rows.append(f'<tr style="animation-delay:{i * 0.03:.2f}s">{cells}</tr>')
    body_html = "\n".join(body_rows)

    return f'''<div class="cr-table-wrapper">
<table class="cr-table">
{colgroup_html}
<thead><tr>{header_html}</tr></thead>
<tbody>{body_html}</tbody>
</table>
</div>'''


def st_custom_table(data, max_rows: int = 300):
    """Render a beautifully styled table using st.markdown."""
    html = _render_custom_table(data, max_rows)
    if html:
        st.markdown(html, unsafe_allow_html=True)



def _ast_to_dot(ast_dict, rankdir="TB"):
    if not ast_dict:
        return "digraph AST { label=\"AST\"; bgcolor=\"transparent\"; }"

    nodes = []
    edges = []
    count = 0

    def esc(value):
        return str(value).replace('"', '\\"').replace("<", "&lt;").replace(">", "&gt;")

    def node_style(kind):
        if kind in {"if", "if_else", "while", "for", "block"}:
            return "#FFF4CE", "#B08900", "#4A4000"
        if kind in {"declaration", "declaration_list", "assignment", "return"}:
            return "#DFF6DD", "#2E7D32", "#1A4D1E"
        if kind in {"binary_op", "unary_op", "identifier", "constant", "literal"}:
            return "#DDEBFF", "#1E5AA8", "#0E2D54"
        return "#F3F2F1", "#605E5C", "#3B3A39"

    def walk(node, parent_id=None):
        nonlocal count
        count += 1
        node_id = f"n{count}"
        kind = node.get("kind", "node")
        value = node.get("value")
        lineno = node.get("lineno", 0)
        fill, border, font_color = node_style(kind)

        value_text = "-" if value is None else esc(value)
        if len(value_text) > 42:
            value_text = value_text[:39] + "..."
        line_text = f"L{lineno}" if lineno else "-"

        label = (
            "<"
            "<TABLE BORDER=\"0\" CELLBORDER=\"0\" CELLPADDING=\"2\">"
            f"<TR><TD><FONT COLOR=\"{font_color}\"><B>{esc(kind)}</B></FONT></TD></TR>"
            f"<TR><TD ALIGN=\"LEFT\"><FONT POINT-SIZE=\"10\" COLOR=\"{font_color}\">value: {value_text}</FONT></TD></TR>"
            f"<TR><TD ALIGN=\"LEFT\"><FONT POINT-SIZE=\"10\" COLOR=\"{font_color}\">line: {line_text}</FONT></TD></TR>"
            "</TABLE>>"
        )

        nodes.append(
            f"{node_id} [label={label}, shape=box, style=\"rounded,filled\", fillcolor=\"{fill}\", color=\"{border}\", penwidth=1.4]"
        )
        if parent_id is not None:
            edges.append(f"{parent_id} -> {node_id} [color=\"#8A8886\", arrowsize=0.7]")

        for child in node.get("children", []):
            walk(child, node_id)

    walk(ast_dict)
    body = "\n".join(nodes + edges)
    return (
        "digraph AST {\n"
        "bgcolor=\"transparent\";\n"
        f"rankdir={rankdir};\n"
        "nodesep=0.25;\n"
        "ranksep=0.35;\n"
        "fontname=\"Segoe UI\";\n"
        "node [fontname=\"Segoe UI\"];\n"
        f"{body}\n"
        "}\n"
    )


def main() -> None:
    st.set_page_config(page_title="C-Overcharged Compiler", page_icon="C", layout="wide")
    _inject_theme_detector()        
    _inject_scripts_component()     
    _load_css()
    _intro_overlay()
    _background_bubbles()

    
    if "source_code" not in st.session_state:
        st.session_state["source_code"] = SAMPLE_CODE[DEFAULT_SAMPLE_KEY]
    if "sample_choice" not in st.session_state:
        st.session_state["sample_choice"] = DEFAULT_SAMPLE_KEY
    if st.session_state["sample_choice"] not in SAMPLE_CODE:
        st.session_state["sample_choice"] = DEFAULT_SAMPLE_KEY
    if "analysis_result" not in st.session_state:
        st.session_state["analysis_result"] = None

    def _on_sample_change() -> None:
        selected = st.session_state["sample_choice"]
        st.session_state["source_code"] = SAMPLE_CODE[selected]
        st.session_state["analysis_result"] = None

    
    col_title, col_toggle = st.columns([3, 1], vertical_alignment="bottom")
    with col_title:
        st.markdown('<div class="project-title">C-Overcharged</div>', unsafe_allow_html=True)
        st.markdown("#### Compiler")
    with col_toggle:
        beta_mode = st.toggle("Modo Beta (Estatico)")

    
    if beta_mode:
        st.markdown("""
        <style>
            /* 1. Ocultar los videos dinámicos */
            #cr-video-bg { display: none !important; }
            
            /* 2. Fondo estático radial de la presentación */
            .stApp, [data-testid="stAppViewContainer"] {
                background: radial-gradient(ellipse at center, #0f1628 0%, #060a14 70%, #000000 100%) !important;
            }

            /* 3. Adaptación del Modo Luz (Persona 3) para fondo oscuro */
            /* Forzar textos principales a blanco para legibilidad */
            .stApp * {
                color: #ffffff !important;
            }
            
            /* Mantener el color Cyan vibrante como acento en títulos */
            h1, h2, h3, h4, .status-title {
                text-transform: uppercase !important;
                font-style: italic !important;
                font-weight: 900 !important;
                text-shadow: 2px 2px 0px #00BFFF !important;
            }

            /* Contenedores con bordes afilados (estilo modo luz) */
            .status-card, [data-testid="stMetric"], div[data-baseweb="select"] > div, textarea {
                background-color: rgba(30, 33, 44, 0.8) !important;
                border: 2px solid #00BFFF !important;
                border-radius: 0px !important; /* Esquinas afiladas */
            }

            /* Botón analizar agresivo e inclinado */
            .stButton > button {
                border-radius: 0px !important;
                border: 3px solid #00BFFF !important;
                background: rgba(0, 0, 0, 0.5) !important;
                color: #00BFFF !important;
                font-weight: 900 !important;
                font-style: italic !important;
                text-transform: uppercase !important;
                box-shadow: 4px 4px 0px rgba(0, 191, 255, 0.4) !important;
            }
            .stButton > button:hover {
                background-color: #00BFFF !important;
                color: #000000 !important;
                box-shadow: none !important;
                transform: translate(2px, 2px);
            }
            
            /* Tabs estilo P3 */
            .stTabs [data-baseweb="tab"] {
                border-radius: 0px !important;
                border: 2px solid transparent !important;
            }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                border: 2px solid #00BFFF !important;
                background-color: rgba(0, 191, 255, 0.2) !important;
            }
            
            /* Corregir flecha del selector */
            [data-testid="stSelectbox"] svg {
                fill: #00BFFF !important;
            }
        </style>
        """, unsafe_allow_html=True)

    
    input_col, output_col = st.columns([1.1, 1.5], gap="large")

    with input_col:
        st.subheader("Input")

        # ── Procesar flag de historial ANTES del widget ──
        _hist_idx = st.session_state.pop("_load_history_idx", None)
        if _hist_idx is not None:
            code_history = st.session_state.get("code_history", [])
            if 0 <= _hist_idx < len(code_history):
                st.session_state["source_code"] = code_history[_hist_idx]


        st.selectbox(
            "Samples",
            list(SAMPLE_CODE.keys()),
            key="sample_choice",
            on_change=_on_sample_change,
        )


        text_container = st.container()

        
        col_btn_analizar, col_btn_upload = st.columns(2, gap="small")
        
        with col_btn_upload:
            uploaded = st.file_uploader("Upload C code", type=["c", "txt"], label_visibility="collapsed")
            
        
        if uploaded is not None:
            uploaded_text = uploaded.getvalue().decode("utf-8", errors="ignore")
            if uploaded_text != st.session_state.get("last_uploaded_content", ""):
                st.session_state["source_code"] = uploaded_text
                st.session_state["last_uploaded_content"] = uploaded_text
                st.session_state["analysis_result"] = None
                
        with text_container:
            st.text_area("C source code", height=300, key="source_code")

        with col_btn_analizar:
            if st.button("Analyze", type="primary", width="stretch"):
                with st.spinner("Analyzing..."):
                    result = parse_source(st.session_state["source_code"])
                    st.session_state["analysis_result"] = result
                    # ── Historial de Sesión Volátil ──
                    if result.get("syntax_ok"):
                        history = st.session_state.get("code_history", [])
                        code_snap = st.session_state["source_code"]
                        # Evitar duplicados consecutivos
                        if not history or history[-1] != code_snap:
                            history.append(code_snap)
                            if len(history) > 3:
                                history = history[-3:]
                            st.session_state["code_history"] = history

        # ── Historial de análisis ──
        code_history = st.session_state.get("code_history", [])
        if code_history:
            with st.popover("History", icon=":material/history:", use_container_width=True):
                for i, code_snap in enumerate(reversed(code_history)):
                    real_idx = len(code_history) - 1 - i
                    preview = code_snap.strip().replace("\n", " ")
                    if len(preview) > 60:
                        preview = preview[:57] + "..."
                    label = f"**#{real_idx + 1}** — `{preview}`"
                    if st.button(
                        label,
                        key=f"hist_{real_idx}",
                        use_container_width=True,
                    ):
                        st.session_state["_load_history_idx"] = real_idx
                        st.rerun()

    with output_col:
        st.subheader("Output")
        result = st.session_state.get("analysis_result")
        if result is None:
            st.info("Select or edit a sample on the left, then click **Analyze**.")
        else:
            _status_block(result["syntax_ok"], result["semantic_ok"])
            
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "Lexical", "Semantic", "Visual SDT", "Optimized Code", "Intermediate Code(TAC)","Assembly Code"
                ])

            
            with tab1:
                st.subheader("Tokens")
                st_custom_table(_tokens_as_table(result["tokens"]))
            
            
            with tab2:
                st.subheader("Syntax errors")
                if result["syntax_errors"]:
                    for err in result["syntax_errors"]:
                        st.error(err)
                else:
                    st.success("No syntax errors.")

                st.subheader("Symbol table")
                if result["symbol_table"]:
                    st_custom_table(result["symbol_table"])
                else:
                    st.info("No symbols registered.")

                st.subheader("Semantic errors")
                if result["semantic_errors"]:
                    for err in result["semantic_errors"]:
                        st.error(err)
                elif result["syntax_ok"]:
                    st.success("No semantic errors.")

                st.subheader("SDT trace")
                if result.get("sdt_trace"):
                    st_custom_table(result["sdt_trace"])
                else:
                    st.info("No SDT trace available.")

            
            with tab3:
                st.subheader("AST graph")
                st.markdown(
                    '''
                    <div class="legend-row">
                        <span class="legend-badge green"><span class="legend-dot green"></span>Declarations / Assignments</span>
                        <span class="legend-badge blue"><span class="legend-dot blue"></span>Expressions / Operands</span>
                        <span class="legend-badge yellow"><span class="legend-dot yellow"></span>Control flow (if, while, for)</span>
                        <span class="legend-badge gray"><span class="legend-dot gray"></span>Other nodes</span>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )
                orientation = st.segmented_control(
                    "Orientation",
                    options=["Top-Down", "Bottom-Up"],
                    default="Top-Down",
                )
                rankdir = "TB" if orientation == "Top-Down" else "BT"
                
                if result["syntax_ok"] and result["ast_dict"]:
                    dot_graph = _ast_to_dot(result["ast_dict"], rankdir=rankdir)
                    st.graphviz_chart(dot_graph, width="stretch")

                    # ── Exportar AST como PNG (via JS — captura el SVG renderizado) ──
                    # El time.time() inyectado evita el error de WebSocket (Cached ForwardMsg MISS) en Streamlit Cloud
                    components.html(f"""<style>
                        .ast-export-btn {{
                            display: inline-flex; align-items: center; gap: 8px;
                            width: 100%; justify-content: center;
                            padding: 4px 12px; cursor: pointer;
                            font-family: 'Montserrat', sans-serif;
                            font-weight: 800; font-size: 16px;
                            text-transform: uppercase;
                            border-radius: 0px;
                            transition: all 0.2s;
                            box-sizing: border-box;
                            min-height: 42px;
                        }}
                    </style>
                    <button class="ast-export-btn" id="astExportBtn" onclick="exportAST()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        DOWNLOAD AST AS PNG
                    </button>
                    <script>
                    // Sync button style with parent's Streamlit download button
                    (function() {{
                        var btn = document.getElementById('astExportBtn');
                        var pdoc = window.parent.document;
                        var theme = pdoc.documentElement.getAttribute('data-cr-theme') || 'light';

                        // Read accent color from parent's download button or use defaults
                        var accentColor = 'rgb(0, 191, 255)';
                        try {{
                            var refBtn = pdoc.querySelector('.stDownloadButton > button');
                            if (refBtn) {{
                                var cs = window.parent.getComputedStyle(refBtn);
                                var shadowMatch = cs.boxShadow.match(/rgb\\([^)]+\\)/);
                                if (shadowMatch) accentColor = shadowMatch[0];
                            }}
                        }} catch(e) {{}}

                        if (theme === 'dark') {{
                            btn.style.background = 'rgba(0, 0, 0, 0.5)';
                            btn.style.color = accentColor;
                            btn.style.border = '2px solid ' + accentColor;
                            btn.style.boxShadow = '4px 4px 0px ' + accentColor.replace('rgb', 'rgba').replace(')', ', 0.4)');
                            btn.style.fontWeight = '900';
                            btn.style.fontStyle = 'italic';
                        }} else {{
                            btn.style.background = 'rgba(255, 255, 255, 0.85)';
                            btn.style.color = 'rgb(0, 0, 0)';
                            btn.style.border = '2px solid rgb(0, 0, 0)';
                            btn.style.boxShadow = accentColor + ' 4px 4px 0px 0px';
                        }}

                        btn.onmouseenter = function() {{
                            btn.style.backgroundColor = accentColor;
                            btn.style.borderColor = accentColor;
                            btn.style.color = '#000';
                            btn.style.boxShadow = 'none';
                            btn.style.transform = 'translate(2px, 2px)';
                        }};
                        btn.onmouseleave = function() {{
                            if (theme === 'dark') {{
                                btn.style.background = 'rgba(0, 0, 0, 0.5)';
                                btn.style.color = accentColor;
                                btn.style.border = '2px solid ' + accentColor;
                                btn.style.boxShadow = '4px 4px 0px ' + accentColor.replace('rgb', 'rgba').replace(')', ', 0.4)');
                            }} else {{
                                btn.style.background = 'rgba(255, 255, 255, 0.85)';
                                btn.style.color = 'rgb(0, 0, 0)';
                                btn.style.border = '2px solid rgb(0, 0, 0)';
                                btn.style.boxShadow = accentColor + ' 4px 4px 0px 0px';
                            }}
                            btn.style.transform = 'none';
                        }};
                    }})();
                    </script>
                    <script>
                    function exportAST() {{
                        try {{
                            var pdoc = window.parent.document;
                            // Buscar el SVG del graphviz_chart
                            var svgEls = pdoc.querySelectorAll('[data-testid="stGraphVizChart"] svg, .stGraphVizChart svg');
                            var svg = null;
                            if (svgEls.length > 0) svg = svgEls[svgEls.length - 1];
                            if (!svg) {{
                                // Fallback: buscar cualquier SVG grande dentro del tab panel activo
                                var panels = pdoc.querySelectorAll('[data-baseweb="tab-panel"]');
                                panels.forEach(function(p) {{
                                    if (p.offsetHeight > 0) {{
                                        var s = p.querySelector('svg');
                                        if (s && s.getBBox().width > 100) svg = s;
                                    }}
                                }});
                            }}
                            if (!svg) {{ alert('No se encontró el grafo AST.'); return; }}

                            var svgData = new XMLSerializer().serializeToString(svg);
                            var svgBlob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                            var url = URL.createObjectURL(svgBlob);
                            var img = new Image();
                            img.onload = function() {{
                                var canvas = document.createElement('canvas');
                                var scale = 2; // Alta resolución
                                canvas.width = img.width * scale;
                                canvas.height = img.height * scale;
                                var ctx = canvas.getContext('2d');
                                ctx.fillStyle = '#ffffff';
                                ctx.fillRect(0, 0, canvas.width, canvas.height);
                                ctx.scale(scale, scale);
                                ctx.drawImage(img, 0, 0);
                                canvas.toBlob(function(blob) {{
                                    var a = pdoc.createElement('a');
                                    a.href = URL.createObjectURL(blob);
                                    a.download = 'ast_graph.png';
                                    pdoc.body.appendChild(a);
                                    a.click();
                                    pdoc.body.removeChild(a);
                                    URL.revokeObjectURL(a.href);
                                }}, 'image/png');
                                URL.revokeObjectURL(url);
                            }};
                            img.src = url;
                        }} catch(err) {{
                            alert('Error al exportar: ' + err.message);
                        }}
                    }}
                    </script>
                    """, height=55)
                else:
                    st.info("Cannot build the graph when syntax errors exist.")
            
            
            with tab4:
                st.subheader("Optimized Code")
                if result.get("semantic_ok") and result.get("optimized_code") is not None:
                    count = result.get("optimizations_count", 0)
                    st.success(f"Optimized code generated with {count} optimization(s) applied.")
                    
                    
                    st.code(result["optimized_code"], language="c")
                else:
                    st.info("The optimization requires that the code passes syntax and semantic analysis without errors.")

            
            with tab5:
                st.subheader("Three-Address Code (TAC)")
                if result.get("semantic_ok") and result.get("tac_code"):
                    st.success("AST successfully transformed into Three-Address Code (TAC).")
                    
                    st.code(result["tac_code"], language="c")
                else:
                    st.info("TAC generation requires that the code passes the previous phases without errors.")

            
            with tab6:
                st.subheader("Assembly Code (x86_64)")
                if result.get("semantic_ok") and result.get("asm_code"):
                    st.success("Success generating x86_64 assembly code.")

                    st.code(result["asm_code"], language="nasm")

                    st.download_button(
                        label="Download Assembly (.asm)",
                        data=result["asm_code"],
                        file_name="source.asm",
                        mime="text/plain",
                        use_container_width=True,
                    )

                    st.markdown("### Link and Execute")
                    st.info("Run the code in the console.")
                    
                    user_input = ""
                    if "call scanf" in result["asm_code"]:
                        user_input = st.text_area(
                            "Standard Input (stdin)", 
                            placeholder="Enter the values that your scanf or read functions will request, separated by spaces or newlines...",
                            help="These values will be sent to the compiled program during execution."
                        )
                    
                    if st.button("LINK AND EXECUTE", type="primary", use_container_width=True):
                        with st.spinner("Processing code..."):
                            try:
                                exec_res = ExecutableGenerator.compile_and_run(result["asm_code"], user_input)
                            except TypeError:
                                exec_res = ExecutableGenerator.compile_and_run(result["asm_code"])
                            
                            if exec_res["success"]:
                                st.success("Program compiled")
                                st.markdown("**Terminal Output:**")
                                st.code(exec_res["output"] or "(No console output)", language="bash")
                                
                                if len(exec_res["binary"]) > 0:
                                    st.download_button(
                                        label="Download a.out",
                                        data=exec_res["binary"],
                                        file_name="a.out",
                                        mime="application/x-executable",
                                        use_container_width=True
                                    )
                                else:
                                    st.info("Executed via API (Cloud).")
                            else:
                                st.error("Error during compilation or execution:")
                                st.code(exec_res["output"], language="bash")
                else:
                    st.info("Assembler generation requires that the code passes the previous phases without errors.")
        
            st.divider()
            
            st.download_button(
                label="Download Analysis Report (JSON)",
                data=json.dumps(
                    {
                        "project": "C-Overcharged",
                        "syntax_ok": result["syntax_ok"],
                        "syntax_errors": result["syntax_errors"],
                        "semantic_ok": result["semantic_ok"],
                        "semantic_errors": result["semantic_errors"],
                        "symbol_table": result["symbol_table"],
                        "sdt_trace": result.get("sdt_trace", []),
                        "ast": result["ast_dict"],
                        "tokens": _tokens_as_table(result["tokens"]),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                file_name="COvercharged_report.json",
                mime="application/json",
                width="stretch",
            )

if __name__ == "__main__":
    main()