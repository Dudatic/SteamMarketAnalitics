import json
import os
import sys

# --- CONFIGURAÇÕES ---
PRICES_DUMP_FILE = "v2.json" 
PRICE_CACHE_FILE = "price_cache.json"

# FILTROS (Blacklist) - Inclui Facas, Luvas e outros itens
EXCLUIR_ITENS = [
    "Sticker", "Graffiti", "Case", "Key", "Capsule", "Container", 
    "Music Kit", "Tool", "Souvenir", "Agent", "crate", "musickit", "Patch", "Pin",
    "Knife", "Glove", "Bayonet", "Karambit", "Daggers", "Wraps", "Pass", 
    "Holo", "Foil", "Contenders", "Challengers", "Legends"
]

def get_price_value(price_data):
    """Extrai o preço (24h > 7d > 30d > all_time)."""
    price = price_data.get('24_hours', {}).get('average', 0)
    
    if price == 0 or isinstance(price, str): price = price_data.get('7_days', {}).get('average', 0)
    if price == 0 or isinstance(price, str): price = price_data.get('30_days', {}).get('median', 0)
    if price == 0 or isinstance(price, str): price = price_data.get('all_time', {}).get('average', 0)
        
    try:
        return float(price) if price else 0.0
    except:
        return 0.0

def clean_and_format_name(full_name):
    """
    Transforma nomes sujos em nomes padronizados.
    Ex: '★ StatTrak™ Karambit | Fade (FN)' -> 'ST | Karambit | Fade (FN)'
    Ex: 'Negev | Mjölnir' -> 'Negev | Mjolnir'
    """
    if not full_name: return None # <--- CORREÇÃO DO ERRO AQUI
    
    # 1. Deteta se é StatTrak ANTES de limpar
    is_stattrak = "StatTrak" in full_name
    
    # 2. Remove lixo (Estrelas, TM, StatTrak sujo)
    clean = full_name.replace("StatTrak™", "").replace("StatTrak", "").replace("\u2122", "")
    clean = clean.replace("★", "").replace("\u2605", "")
    
    # 3. Normalização de caracteres especiais (Ex: Mjölnir -> Mjolnir)
    clean = clean.replace("ö", "o").replace("Ö", "O")
    
    # 4. Remove espaços extras nas pontas e no meio
    clean = clean.strip()
    while "  " in clean: clean = clean.replace("  ", " ")
    
    # 5. Reconstrói a chave limpa
    if is_stattrak:
        return f"ST | {clean}"
    else:
        return clean

def process_and_create_cache():
    print("🔄 A processar dump e a limpar nomes...")
    
    if not os.path.exists(PRICES_DUMP_FILE):
        print("❌ Dump não encontrado.")
        return

    try:
        with open(PRICES_DUMP_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        items = data.get('items_list', data)
        price_cache = {}
        count_st = 0
        
        for key, details in items.items():
            raw_name = details.get('name')
            if not raw_name: continue

            # Filtro de exclusão
            if any(bad in raw_name for bad in EXCLUIR_ITENS):
                continue
                
            price = get_price_value(details.get('price', {}))
            
            if price > 0:
                # CRIA A CHAVE PADRONIZADA
                final_key = clean_and_format_name(raw_name)
                price_cache[final_key] = price
                
                if "ST |" in final_key:
                    count_st += 1
        
        with open(PRICE_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(price_cache, f, indent=4)
            
        print(f"✅ Sucesso! Cache criada com {len(price_cache)} itens (StatTrak: {count_st}).")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    process_and_create_cache()