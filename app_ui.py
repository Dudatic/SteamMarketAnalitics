import streamlit as st
import pandas as pd
import json
import os

# --- CONFIGURAÇÕES ---
COLLECTIONS_FILE = "collections.json"
PRICE_CACHE_FILE = "price_cache.json"
STEAM_TAX_FACTOR = 0.869565 

# Ordem das Raridades
RARITY_ORDER = ["Consumer Grade", "Industrial Grade", "Mil-Spec", "Restricted", "Classified", "Covert"]

# Mapeamento de Abreviaturas
WEAR_NAMES_MAP = {
    "FN": "Factory New", 
    "MW": "Minimal Wear", 
    "FT": "Field-Tested",
    "WW": "Well-Worn", 
    "BS": "Battle-Scarred"
}

# Lista ordenada para o loop
ALL_WEARS = ["FN", "MW", "FT", "WW", "BS"]

GLOBAL_PRICES_CACHE = {} 

# --- FUNÇÕES ---

def load_cache():
    global GLOBAL_PRICES_CACHE
    if not os.path.exists(PRICE_CACHE_FILE):
        st.error("❌ Cache não encontrada. Corra o '01_process_data.py' primeiro.")
        return False
    try:
        with open(PRICE_CACHE_FILE, 'r', encoding='utf-8') as f:
            GLOBAL_PRICES_CACHE = json.load(f)
        return True
    except:
        return False

def get_price(skin_name, wear_abbr, is_stattrak):
    """Constrói a chave exata e procura na cache."""
    # 1. Limpeza de caracteres especiais
    clean_name = skin_name.replace("ö", "o").replace("Ö", "O")
    clean_name = clean_name.replace("★", "").replace("\u2605", "").strip()
    
    # 2. Obter nome completo do desgaste
    wear_full = WEAR_NAMES_MAP.get(wear_abbr)
    
    # 3. Construir a chave final
    prefix = "ST | " if is_stattrak else ""
    key = f"{prefix}{clean_name} ({wear_full})"
    
    return GLOBAL_PRICES_CACHE.get(key)

def calculate_tradeups(debug_mode):
    if not load_cache(): return [], []
    
    if not os.path.exists(COLLECTIONS_FILE):
        st.error("Falta collections.json")
        return [], []

    with open(COLLECTIONS_FILE, 'r', encoding='utf-8') as f:
        collections = json.load(f)

    results = []
    debug_logs = []

    # Loop Coleções
    for col_name, rarities in collections.items():
        
        # Loop Transições de Raridade
        for i in range(len(RARITY_ORDER) - 1):
            input_rarity = RARITY_ORDER[i]
            output_rarity = RARITY_ORDER[i+1]
            
            if input_rarity not in rarities or output_rarity not in rarities:
                continue
                
            inputs_list = rarities[input_rarity]
            outputs_list = rarities[output_rarity]
            
            # Loop StatTrak (Normal vs ST)
            for is_st in [False, True]:
                status_label = "StatTrak" if is_st else "Normal"
                
                # 🔥 Analisar CADA estado de desgaste individualmente
                for wear_code in ALL_WEARS:
                    wear_name = WEAR_NAMES_MAP[wear_code]
                    
                    # --- 1. CALCULAR CUSTO (INPUT no estado atual) ---
                    best_input_skin = None
                    min_input_price = float('inf')
                    
                    for skin in inputs_list:
                        price = get_price(skin, wear_code, is_st)
                        if price:
                            if price < min_input_price:
                                min_input_price = price
                                best_input_skin = skin
                    
                    if min_input_price == float('inf'):
                        continue 

                    cost = min_input_price * 10
                    
                    # --- 2. CALCULAR RECEITA (OUTPUT no mesmo estado) ---
                    total_out_value = 0
                    valid_outs = 0
                    out_details = []
                    min_output_val = float('inf') # Pior caso
                    
                    for skin in outputs_list:
                        # Procura preço no MESMO estado do input
                        price = get_price(skin, wear_code, is_st)
                        
                        if price:
                            net_price = price * STEAM_TAX_FACTOR
                            total_out_value += net_price
                            valid_outs += 1
                            
                            if net_price < min_output_val: min_output_val = net_price
                            
                            out_details.append({
                                'Skin': skin, 
                                'Preço Venda': f"${price:.2f}",
                                'Valor Líquido': net_price, 
                                'Lucro': net_price - cost
                            })
                    
                    if valid_outs == 0:
                        continue

                    # --- 3. RESULTADOS ---
                    avg_out_value = total_out_value / valid_outs
                    profit_avg = avg_out_value - cost
                    profit_worst = min_output_val - cost
                    roi = (profit_avg / cost) * 100
                    
                    # 🔥 FILTRO: SÓ MOSTRA SE O PIOR CASO TIVER LUCRO POSITIVO
                    if profit_worst > 0:
                        results.append({
                            'id': f"{col_name}_{input_rarity}_{is_st}_{wear_code}",
                            'Coleção': col_name,
                            'Transição': f"{input_rarity} -> {output_rarity}",
                            'Tipo': status_label,
                            'Estado': wear_name,
                            'Input': best_input_skin,
                            'Custo': cost,
                            'Lucro Médio': profit_avg,
                            'Pior Caso': profit_worst,
                            'ROI': roi,
                            'Detalhes': out_details
                        })

    return results, debug_logs

# --- INTERFACE ---

st.set_page_config(layout="wide")
st.title("💰 CS2 Trade Up Calculator (Risco Zero)")
st.caption("A mostrar APENAS Trade Ups onde é impossível perder dinheiro (Pior Caso > 0).")

st.sidebar.header("Opções")
debug_mode = st.sidebar.checkbox("Ativar Debug", value=False)

if st.button("🔄 Calcular Oportunidades Seguras"):
    st.session_state['logs'] = []
    data, logs = calculate_tradeups(debug_mode)
    st.session_state['data'] = data
    st.session_state['logs'] = logs

# Resultados
if 'data' in st.session_state:
    df = pd.DataFrame(st.session_state['data'])
    
    if not df.empty:
        # Ordenar pelo Pior Caso (o mais seguro primeiro)
        df = df.sort_values(by="Pior Caso", ascending=False)
        st.success(f"{len(df)} Trade Ups 'Risco Zero' encontrados!")
        
        for index, row in df.iterrows():
            roi_color = "green"
            
            title = f"{row['Coleção']} | {row['Estado']} | {row['Tipo']} | {row['Transição']} | Custo: ${row['Custo']:.2f} | Lucro Mínimo (Pior Caso): :{roi_color}[${row['Pior Caso']:.2f}]"
            
            with st.expander(title):
                c1, c2 = st.columns(2)
                c1.info(f"📥 **Input (10x):** {row['Input']}")
                c2.metric("Lucro Médio (EV)", f"${row['Lucro Médio']:.2f}")
                
                det_df = pd.DataFrame(row['Detalhes'])
                
                def color_profit(val):
                    # Tudo deve ser verde aqui, mas caso haja erro de arredondamento...
                    color = 'red' if val < 0 else 'green'
                    return f'color: {color}'

                st.dataframe(
                    det_df.style.format({'Valor Líquido': '${:.2f}', 'Lucro': '${:.2f}'})
                    .applymap(color_profit, subset=['Lucro']),
                    use_container_width=True
                )
    else:
        st.warning("Não foram encontradas oportunidades de 'Risco Zero' com os preços atuais. O mercado é eficiente e raramente deixa estas margens livres.")