import json
import os

# --- CONFIGURAÇÕES ---
INPUT_FILE = "raw_data.json"       # O ficheiro com o json estranho que arranjaste
OUTPUT_FILE = "collections.json"   # O ficheiro que a UI vai ler

def convert_collections():
    print(f"🔄 A ler dados brutos de {INPUT_FILE}...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERRO: Cria o ficheiro '{INPUT_FILE}' e cola lá o json novo primeiro!")
        return

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        clean_collections = {}
        count_skins = 0
        
        # O raw_data é uma lista de objetos de coleção
        for collection_obj in raw_data:
            col_name = collection_obj.get('name')
            
            # Ignora coleções sem nome
            if not col_name: continue
            
            # Inicializa a coleção no novo dicionário
            clean_collections[col_name] = {}
            
            # Itera sobre as skins dentro de "contains"
            if 'contains' in collection_obj:
                for item in collection_obj['contains']:
                    skin_name = item.get('name')
                    rarity_obj = item.get('rarity', {})
                    rarity_name = rarity_obj.get('name')
                    
                    if skin_name and rarity_name:
                        # --- NORMALIZAÇÃO DE RARIDADE ---
                        # O nosso app usa "Mil-Spec" mas o json pode ter "Mil-Spec Grade"
                        if rarity_name == "Mil-Spec Grade": 
                            rarity_clean = "Mil-Spec"
                        elif rarity_name == "Industrial Grade": 
                            rarity_clean = "Industrial Grade"
                        elif rarity_name == "Consumer Grade": 
                            rarity_clean = "Consumer Grade"
                        else:
                            # Mantém Restricted, Classified, Covert como estão
                            rarity_clean = rarity_name

                        # Cria a lista se não existir
                        if rarity_clean not in clean_collections[col_name]:
                            clean_collections[col_name][rarity_clean] = []
                        
                        # Adiciona a skin
                        clean_collections[col_name][rarity_clean].append(skin_name)
                        count_skins += 1

        # Salva o ficheiro formatado para a UI usar
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(clean_collections, f, indent=4)
            
        print(f"✅ SUCESSO! {len(clean_collections)} coleções e {count_skins} skins processadas.")
        print(f"📂 Ficheiro '{OUTPUT_FILE}' atualizado e pronto para o Trade Up Analyzer.")

    except json.JSONDecodeError:
        print("❌ ERRO: O ficheiro raw_data.json tem erros de sintaxe. Verifica se colaste tudo bem.")
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    convert_collections()