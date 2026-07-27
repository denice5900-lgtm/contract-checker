# app.py - веб-версия для Streamlit Cloud
import streamlit as st
import re
import json
from datetime import datetime

# Инициализация состояния приложения
def init_state():
    if 'all_contracts' not in st.session_state:
        st.session_state.all_contracts = {}
    if 'available_contracts' not in st.session_state:
        st.session_state.available_contracts = {}
    if 'sellers' not in st.session_state:
        st.session_state.sellers = set()

def load_data():
    """Загружает данные из JSON файла"""
    try:
        with open('contracts_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            st.session_state.all_contracts = data.get('all_contracts', {})
            st.session_state.available_contracts = data.get('available_contracts', {})
            update_sellers()
            return True
    except:
        return False

def save_data():
    """Сохраняет данные в JSON файл"""
    try:
        data = {
            'all_contracts': st.session_state.all_contracts,
            'available_contracts': st.session_state.available_contracts
        }
        with open('contracts_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        update_sellers()
        return True
    except:
        return False

def update_sellers():
    """Обновляет список уникальных продавцов"""
    st.session_state.sellers = set(st.session_state.all_contracts.values())
    st.session_state.sellers.discard('')
    st.session_state.sellers.discard(None)

def main():
    st.set_page_config(page_title="Сверка договоров", page_icon="📋", layout="wide")
    
    # Загружаем данные
    init_state()
    load_data()
    
    st.title("📋 Сверка договоров")
    
    # Информация о данных
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего договоров", len(st.session_state.all_contracts))
    with col2:
        st.metric("В наличии", len(st.session_state.available_contracts))
    with col3:
        st.metric("Продавцов", len(st.session_state.sellers))
    
    # Меню
    menu = st.sidebar.selectbox(
        "Выберите действие",
        ["Внести договора", "Проверить договор", "Сверить договора"]
    )
    
    if menu == "Внести договора":
        show_enter_contracts()
    elif menu == "Проверить договор":
        show_check_contract()
    else:
        show_compare_contracts()
    
    # Кнопки управления
    st.sidebar.markdown("---")
    if st.sidebar.button("💾 Сохранить данные"):
        if save_data():
            st.sidebar.success("✅ Данные сохранены!")
        else:
            st.sidebar.error("❌ Ошибка сохранения!")
    
    if st.sidebar.button("🗑️ Удалить все данные"):
        if st.sidebar.checkbox("Подтвердить удаление"):
            st.session_state.all_contracts = {}
            st.session_state.available_contracts = {}
            st.session_state.sellers = set()
            save_data()
            st.sidebar.success("✅ Все данные удалены!")
            st.rerun()

def show_enter_contracts():
    st.header("📝 Внести договора")
    
    st.markdown("""
    **Формат:** номер договора (табуляция или 2+ пробелов) продавец
    
    **Пример:** `2455    butick_auto`
    """)
    
    # Текстовое поле для ввода
    default_text = ""
    if st.session_state.all_contracts:
        default_text = "\n".join([f"{k}\t{v}" for k, v in st.session_state.all_contracts.items()])
    
    text_input = st.text_area(
        "Введите договора (каждый с новой строки):",
        value=default_text,
        height=300,
        key="contracts_input"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Сохранить", use_container_width=True):
            if text_input.strip():
                new_contracts = parse_contracts(text_input)
                if new_contracts:
                    st.session_state.all_contracts = new_contracts
                    update_sellers()
                    save_data()
                    st.success(f"✅ Сохранено {len(new_contracts)} договоров!")
                    st.rerun()
                else:
                    st.warning("⚠️ Не найдены номера договоров!")
            else:
                st.warning("⚠️ Введите хотя бы один договор!")
    
    with col2:
        if st.button("🗑️ Очистить", use_container_width=True):
            st.session_state.contracts_input = ""
            st.rerun()
    
    with col3:
        if st.button("📋 Загрузить из файла", use_container_width=True):
            uploaded_file = st.file_uploader("Выберите файл", type=['txt'])
            if uploaded_file:
                content = uploaded_file.read().decode('utf-8')
                st.session_state.contracts_input = content
                st.rerun()

def parse_contracts(text):
    """Парсит введенный текст в договора"""
    lines = text.split('\n')
    new_contracts = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = re.split(r'\t+|\s{2,}', line)
        if len(parts) >= 2:
            contract_num = parts[0].strip()
            seller = parts[1].strip()
            if re.match(r'^\d{1,5}$', contract_num):
                new_contracts[contract_num] = seller
        else:
            contract_num = line.strip()
            if re.match(r'^\d{1,5}$', contract_num):
                new_contracts[contract_num] = ""
    
    return new_contracts

def show_check_contract():
    st.header("🔍 Проверка договора")
    
    if not st.session_state.all_contracts:
        st.warning("⚠️ Сначала внесите договора!")
        return
    
    # Поиск договора
    contract_num = st.text_input("Введите номер договора:", key="check_input")
    
    if st.button("🔍 Проверить", use_container_width=True):
        if contract_num.strip():
            if re.match(r'^\d{1,5}$', contract_num.strip()):
                found = contract_num in st.session_state.all_contracts
                seller = st.session_state.all_contracts.get(contract_num, "")
                
                if found:
                    st.success(f"✅ Договор {contract_num} найден!")
                    if seller:
                        st.info(f"👤 Продавец: {seller}")
                    
                    # Добавляем в наличие
                    if contract_num not in st.session_state.available_contracts:
                        st.session_state.available_contracts[contract_num] = seller
                        save_data()
                        st.success("✅ Добавлен в список наличия!")
                else:
                    st.error(f"❌ Договор {contract_num} НЕ НАЙДЕН в базе!")
            else:
                st.warning("⚠️ Номер должен содержать от 1 до 5 цифр!")
        else:
            st.warning("⚠️ Введите номер договора!")

def show_compare_contracts():
    st.header("📊 Сверка договоров")
    
    if not st.session_state.all_contracts:
        st.warning("⚠️ Сначала внесите договора!")
        return
    
    # Фильтр по продавцам
    seller_list = ["Все продавцы"] + sorted(st.session_state.sellers)
    selected_seller = st.selectbox("Фильтр по продавцу:", seller_list)
    
    # Фильтруем договора
    filtered_contracts = {}
    for contract, seller in st.session_state.all_contracts.items():
        if selected_seller == "Все продавцы" or seller == selected_seller:
            filtered_contracts[contract] = seller
    
    # Создаем таблицу
    if filtered_contracts:
        data = []
        for contract in sorted(filtered_contracts.keys(), key=int):
            seller = filtered_contracts[contract]
            status = "✅ В наличии" if contract in st.session_state.available_contracts else "❌ Нет в наличии"
            data.append({
                "Номер": contract,
                "Продавец": seller,
                "Статус": status
            })
        
        # Отображаем таблицу
        st.dataframe(data, use_container_width=True)
        
        # Статистика
        total = len(filtered_contracts)
        found = len([c for c in filtered_contracts.keys() if c in st.session_state.available_contracts])
        not_found = total - found
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего", total)
        with col2:
            st.metric("В наличии", found, delta=f"{found/total*100:.1f}%" if total > 0 else "")
        with col3:
            st.metric("Отсутствуют", not_found, delta=f"-{not_found/total*100:.1f}%" if total > 0 else "")
        
        # Кнопки управления
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Удалить все из наличия", use_container_width=True):
                if st.checkbox("Подтвердить удаление из наличия"):
                    to_delete = [c for c in filtered_contracts.keys() if c in st.session_state.available_contracts]
                    for contract in to_delete:
                        del st.session_state.available_contracts[contract]
                    save_data()
                    st.success(f"✅ Удалено {len(to_delete)} договоров из наличия!")
                    st.rerun()
        
        with col2:
            if st.button("📋 Экспорт результатов", use_container_width=True):
                export_text = create_export_text(filtered_contracts, selected_seller)
                st.download_button(
                    label="📥 Скачать файл",
                    data=export_text,
                    file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        with col3:
            if st.button("🔄 Обновить", use_container_width=True):
                st.rerun()
        
        # Экспорт отсутствующих договоров
        missing = [c for c in filtered_contracts.keys() if c not in st.session_state.available_contracts]
        if missing:
            st.warning(f"⚠️ Отсутствуют {len(missing)} договоров")
            if st.button("📋 Скопировать отсутствующие"):
                st.code("\n".join(missing))
    else:
        st.info("Нет договоров для выбранного продавца")

def create_export_text(filtered_contracts, selected_seller):
    """Создает текст для экспорта"""
    lines = []
    lines.append("=" * 60)
    lines.append("РЕЗУЛЬТАТЫ СВЕРКИ ДОГОВОРОВ")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Фильтр: {selected_seller}")
    lines.append("")
    
    # Договора в наличии
    lines.append("ДОГОВОРА В НАЛИЧИИ:")
    found = []
    not_found = []
    
    for c, seller in filtered_contracts.items():
        if c in st.session_state.available_contracts:
            found.append((c, seller))
        else:
            not_found.append((c, seller))
    
    if found:
        for c, seller in sorted(found, key=lambda x: int(x[0])):
            seller_text = f" (продавец: {seller})" if seller else ""
            lines.append(f"  ✅ {c}{seller_text}")
    else:
        lines.append("  - Нет договоров в наличии")
    
    lines.append("")
    lines.append("ОТСУТСТВУЮЩИЕ ДОГОВОРА:")
    if not_found:
        for c, seller in sorted(not_found, key=lambda x: int(x[0])):
            seller_text = f" (продавец: {seller})" if seller else ""
            lines.append(f"  ❌ {c}{seller_text}")
    else:
        lines.append("  - Все договора в наличии")
    
    lines.append("")
    lines.append("=" * 60)
    lines.append("СТАТИСТИКА:")
    total = len(filtered_contracts)
    lines.append(f"  📊 Всего договоров: {total}")
    lines.append(f"  ✅ В наличии: {len(found)}")
    lines.append(f"  ❌ Отсутствуют: {len(not_found)}")
    lines.append("=" * 60)
    
    return "\n".join(lines)

if __name__ == "__main__":
    main()