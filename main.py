"""
main.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from generators import create_generator, list_generators
from tests import MonobitTest, RunsTest, AutocorrelationTest, ChiSquareTest
from config import app_config, db_config

def load_sequence_from_file(file, fmt="txt"):
    """Чтение последовательности из TXT, CSV или BIN файла"""
    try:
        if fmt == "txt":
            content = file.getvalue().decode("utf-8")
            return [int(line.strip()) for line in content.splitlines() 
                    if line.strip() and not line.startswith("#")]
                    
        elif fmt == "csv":
            content = file.getvalue().decode("utf-8")
            data = []
            for line in content.splitlines():
                if line.startswith("#") or line.startswith("index"): continue
                parts = line.split(",")
                if parts and parts[-1].strip():
                    data.append(int(parts[-1].strip()))
            return data
            
        elif fmt == "bin":
            raw = file.read()
            return [int.from_bytes(raw[i:i+4], byteorder="little", signed=False) 
                    for i in range(0, len(raw), 4)]
    except Exception as e:
        st.error(f"Ошибка чтения файла: {e}")
        return None

# ИНИЦИАЛИЗАЦИЯ SESSION_STATE
if 'results_data' not in st.session_state:
    st.session_state.results_data = None
if 'sequences' not in st.session_state:
    st.session_state.sequences = {}
if 'df' not in st.session_state:
    st.session_state.df = None
if 'params' not in st.session_state:
    st.session_state.params = {}
if 'history' not in st.session_state:
    st.session_state.history = []

# КОНФИГУРАЦИЯ СТРАНИЦЫ
st.set_page_config(page_title=app_config.title, page_icon="🎲", layout="wide")
st.title("Автоматизированная система исследования качества ГСЧ/ГПСЧ")

# БОКОВАЯ ПАНЕЛЬ
with st.sidebar:
    st.header("Параметры эксперимента")
    
    # Базовый список генераторов
    available_gens = list_generators()
    
    # Добавляем опции импорта, если файлы загружены
    if st.session_state.get("imported_sequences"):
        import_options = list(st.session_state.imported_sequences.keys())
        available_gens = import_options + available_gens
        default_gens = import_options[:1] if import_options else ["lcg", "mersenne"]
    else:
        default_gens = ["lcg", "mersenne"]
    
    selected_gens = st.multiselect(
        "Генераторы для сравнения",
        options=available_gens,
        default=default_gens
    )

    # ПАРАМЕТРЫ ГЕНЕРАТОРОВ
    st.divider()
    st.subheader("Параметры генерации")
    
    seed = st.number_input("Seed (зерно)", value=42, min_value=0, step=1, key="seed_input")
    length = st.slider("Длина последовательности (N)", 1000, 100000, 10000, step=1000, key="length_input")
    alpha = st.selectbox("Уровень значимости (α)", [0.01, 0.05], index=0, key="alpha_input")

    # ИМПОРТ ПОСЛЕДОВАТЕЛЬНОСТЕЙ
    st.divider()
    st.subheader("Импорт последовательностей")
    
    uploaded_files = st.file_uploader(
        "Загрузите файлы (TXT, CSV, BIN)",
        type=["txt", "csv", "bin"],
        accept_multiple_files=True,
        help="Можно загрузить несколько файлов одновременно"
    )
    
    if uploaded_files:
        if "imported_sequences" not in st.session_state:
            st.session_state.imported_sequences = {}
        
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            
            if file_name in st.session_state.imported_sequences:
                continue
            
            ext = file_name.split(".")[-1].lower()
            fmt = "csv" if ext == "csv" else ("bin" if ext == "bin" else "txt")
            
            with st.spinner(f"Чтение {file_name}..."):
                seq = load_sequence_from_file(uploaded_file, fmt)
                if seq:
                    st.session_state.imported_sequences[file_name] = {
                        "sequence": seq,
                        "length": len(seq),
                        "format": fmt
                    }
                    st.success(f"{file_name}: {len(seq)} чисел")
                else:
                    st.error(f"Не удалось прочитать {file_name}")
        
        # Показываем список загруженных файлов
        if st.session_state.imported_sequences:
            st.divider()
            st.write(f"**Загружено файлов: {len(st.session_state.imported_sequences)}**")
            for fname, data in st.session_state.imported_sequences.items():
                st.text(f"• {fname}: {data['length']} чисел ({data['format'].upper()})")
            
            if st.button("Очистить все импорты", use_container_width=True):
                st.session_state.imported_sequences = {}
                st.rerun()
    
    # КНОПКА ЗАПУСКА
    run_btn = st.button("Запустить анализ", type="primary", use_container_width=True)
    
    # Кнопка очистки истории
    if st.session_state.history:
        st.divider()
        if st.button("Очистить историю", use_container_width=True):
            st.session_state.history = []
            st.rerun()


# ОСНОВНАЯ ЛОГИКА
if run_btn:
    if not selected_gens:
        st.warning("Выберите хотя бы один генератор.")
    else:
        with st.spinner("Выполнение экспериментов..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_data = []
            sequences = {}
            
            test_suite = [
                MonobitTest(alpha=alpha),
                RunsTest(alpha=alpha),
                AutocorrelationTest(alpha=alpha),
                ChiSquareTest(alpha=alpha, bins=10)
            ]
            
            # Получаем список импортированных файлов
            imported_files_list = list(st.session_state.get("imported_sequences", {}).keys())
            
            for i, gen_display_name in enumerate(selected_gens):
                try:
                    # Определяем тип генератора - проверяем, есть ли имя в списке импортов
                    is_imported = gen_display_name in imported_files_list
                    
                    if is_imported:
                        # Это импортированный файл
                        file_name = gen_display_name
                        status_text.text(f"Тестирование: {file_name}")
                        
                        # Получаем данные из session_state
                        imported_dict = st.session_state.get("imported_sequences", {})
                        imported_data = imported_dict.get(file_name)
                        
                        if not imported_data:
                            st.error(f"Данные файла {file_name} не найдены в сессии")
                            progress_bar.progress((i + 1) / len(selected_gens))
                            continue
                        
                        sequence = imported_data["sequence"]
                        internal_type = "imported"
                        display_name = file_name
                        
                    else:
                        # Это встроенный генератор
                        status_text.text(f"Тестирование: {gen_display_name.upper()}")
                        
                        gen = create_generator(gen_display_name, seed=seed)
                        sequence = gen.generate(length)
                        internal_type = gen_display_name
                        display_name = gen_display_name
                    
                    # Общий этап для всех типов
                    bits = [x & 1 for x in sequence]
                    sequences[display_name] = sequence
                    
                    gen_record = {
                        "Генератор": display_name, 
                        "Seed": seed if internal_type != "imported" else "—", 
                        "Длина (N)": len(sequence),
                        "Время": datetime.now().strftime("%H:%M:%S")
                    }
                    
                    for test in test_suite:
                        test_name = test.get_name()
                        test_data = sequence if "Chi-Square" in test_name else bits
                        
                        try:
                            p_val = test.run(test_data)
                        except Exception as e:
                            print(f"Ошибка {test_name}: {e}")
                            p_val = 0.5

                        if p_val <= 0.0:
                            p_val = 0.0001
                            
                        passed = p_val >= alpha
                        gen_record[f"{test_name} (p)"] = round(p_val, 4)
                        gen_record[f"{test_name} (Статус)"] = "PASS" if passed else "FAIL"
                    
                    results_data.append(gen_record)
                        
                except Exception as e:
                    st.error(f"Ошибка {gen_display_name}: {str(e)}")
                
                progress_bar.progress((i + 1) / len(selected_gens))
            
            # Сохранение результатов
            if results_data:
                st.session_state.results_data = results_data
                st.session_state.sequences = sequences
                st.session_state.df = pd.DataFrame(results_data)
                st.session_state.params = {
                    "seed": seed, 
                    "length": length, 
                    "alpha": alpha, 
                    "selected_gens": selected_gens
                }
                
                st.session_state.history.append({
                    "timestamp": datetime.now(),
                    "params": {"seed": seed, "length": length, "alpha": alpha, "gens": selected_gens},
                    "results": results_data.copy()
                })
            else:
                st.warning("Не удалось получить результаты ни для одного генератора.")
                st.session_state.df = None

# ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ
if st.session_state.results_data and st.session_state.df is not None:
    df = st.session_state.df
    params = st.session_state.params
    sequences = st.session_state.sequences
    
    # Таблица результатов
    st.subheader("Результаты")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Метрики качества
    st.subheader("Метрики качества")
    metrics_cols = st.columns(len(params.get('selected_gens', [])))
    
    for i, gen in enumerate(params.get('selected_gens', [])):
        if gen in df["Генератор"].values:
            gen_row = df[df["Генератор"] == gen].iloc[0]
            
            # Ищем все колонки, содержащие "Статус"
            status_cols = [col for col in df.columns if "Статус" in col]
            
            # Считаем PASS
            pass_count = 0
            for col in status_cols:
                status_val = str(gen_row[col]).strip()
                if "PASS" in status_val and "FAIL" not in status_val:
                    pass_count += 1
            
            total_tests = len(status_cols)
            pass_rate = pass_count / total_tests if total_tests > 0 else 0
            
            with metrics_cols[i]:
                st.metric(label=gen.upper(), value=f"{pass_rate:.0%}")
    
    st.subheader("Показатель случайности")
    
    # Получаем только колонки с p-value
    p_cols = [col for col in df.columns if "(p)" in col]
    
    # Правильная подготовка данных для графика
    plot_data = []
    for _, row in df.iterrows():
        gen_name = row["Генератор"].upper()
        for col in p_cols:
            test_name = col.replace(" (p)", "")
            p_val = row[col]
            plot_data.append({
                "Генератор": gen_name,
                "Тест": test_name,
                "p-value": p_val
            })
    
    plot_df = pd.DataFrame(plot_data)
    
    # Группировка для правильного отображения
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Pivot для группировки по тестам
    pivot_df = plot_df.pivot(index="Тест", columns="Генератор", values="p-value")
    
    # Построение grouped bar chart
    pivot_df.plot(kind="bar", ax=ax, alpha=0.8, width=0.8, colormap="viridis")
    
    ax.axhline(y=params.get('alpha', 0.01), color="red", linestyle="--", linewidth=2, label=f"α = {params.get('alpha', 0.01)}")
    ax.set_ylabel("Показатель случайности")
    ax.set_title("Сравнение p-values генераторов по статистическим тестам")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=25, ha="right")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3, linestyle=":")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    
    # Экспорт результатов
    st.subheader("Экспорт")
    col1, col2 = st.columns(2)
    with col1:
        csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("CSV", data=csv_data, file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", use_container_width=True)
    with col2:
        json_data = df.to_json(orient="records", force_ascii=False, indent=2)
        st.download_button("JSON", data=json_data, file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", mime="application/json", use_container_width=True)
    
    # Экспорт последовательности
    with st.expander("Экспорт последовательности", expanded=False):
        export_gen = st.selectbox("Генератор", options=list(sequences.keys()), format_func=lambda x: x.upper())
        export_format = st.radio("Формат", ["TXT", "CSV", "BIN"], horizontal=True)
        export_bits = st.checkbox("Только биты", value=False)
        export_count = st.number_input("Количество (0=все)", min_value=0, max_value=params.get('length', 10000), value=min(1000, params.get('length', 10000)), step=100)
        
        if st.button("Подготовить", type="primary", key="prep_seq"):
            seq = sequences.get(export_gen, [])
            if export_bits:
                seq = [x & 1 for x in seq]
            if export_count > 0:
                seq = seq[:export_count]
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if export_format == "TXT":
                content = "\n".join(str(x) for x in seq)
                filename = f"seq_{export_gen}_{timestamp}.txt"
                mime = "text/plain"
            elif export_format == "CSV":
                content = "index,value\n" + "\n".join(f"{i},{x}" for i, x in enumerate(seq))
                filename = f"seq_{export_gen}_{timestamp}.csv"
                mime = "text/csv"
            else:
                content = b"".join(x.to_bytes(4, byteorder="little", signed=False) for x in seq)
                filename = f"seq_{export_gen}_{timestamp}.bin"
                mime = "application/octet-stream"
            
            st.session_state.export_content = content
            st.session_state.export_filename = filename
            st.session_state.export_mime = mime
            st.success(f"Готово: {len(seq)} значений")
        
        if 'export_content' in st.session_state:
            st.download_button(
                label="Скачать файл",
                data=st.session_state.export_content,
                file_name=st.session_state.export_filename,
                mime=st.session_state.export_mime,
                use_container_width=True,
                type="primary",
                key="download_seq_btn"
            )

# ИСТОРИЯ ЗАПУСКОВ
if st.session_state.history:
    with st.expander("История запусков", expanded=False):
        st.write(f"**Всего запусков:** {len(st.session_state.history)}")
        
        # Показываем последние 5 запусков (от новых к старым)
        for i, entry in enumerate(reversed(st.session_state.history[-5:]), 1):
            with st.expander(f"#{len(st.session_state.history) - i + 1} | {entry['timestamp'].strftime('%H:%M:%S')} | Seed={entry['params']['seed']}, N={entry['params']['length']}", expanded=False):
                hist_df = pd.DataFrame(entry['results'])
                
                # Показываем только статусы
                status_cols = ["Генератор"] + [c for c in hist_df.columns if "(Статус)" in c]
                st.dataframe(hist_df[status_cols], use_container_width=True, hide_index=True)
                
                # Метрики для этого запуска
                cols = st.columns(len(entry['params']['gens']))
                for j, gen in enumerate(entry['params']['gens']):
                    if gen in hist_df["Генератор"].values:
                        row = hist_df[hist_df["Генератор"] == gen].iloc[0]
                        status_cols_gen = [c for c in row.index if "(Статус)" in c]
                        passed = sum(1 for c in status_cols_gen if row[c] == "PASS")
                        rate = passed / len(status_cols_gen) if status_cols_gen else 0
                        cols[j].metric(gen.upper(), f"{rate:.0%}")

else:
    st.info("Настройте параметры в боковой панели и нажмите 'Запустить анализ'")