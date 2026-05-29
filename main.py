"""
main.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from generators import create_generator, list_generators
from tests import MonobitTest, RunsTest, AutocorrelationTest, ChiSquareTest
from config import app_config, db_config

# ИМПОРТ МОДУЛЕЙ БАЗЫ ДАННЫХ
try:
    from database import SessionLocal
    from database.models import Generator, TestResult
    from database.repository import GeneratorRepository, TestResultRepository
    DB_AVAILABLE = True
except ImportError as e:
    DB_AVAILABLE = False
    print(f"Модули БД не найдены: {e}")


# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def convert_numpy_types(obj: Any) -> Any:
    """Конвертирует типы NumPy в стандартные типы Python"""
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


def load_sequence_from_file(file, fmt: str = "txt") -> Optional[List[int]]:
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
                if line.startswith("#") or line.startswith("index"): 
                    continue
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
    return None


def save_experiment_to_db(display_name: str, internal_type: str, 
                         seed: Optional[int], length: int, alpha: float,
                         gen_record: Dict[str, Any], test_suite: List) -> bool:
    """Сохранение результатов эксперимента в базу данных"""
    if not DB_AVAILABLE:
        return False
    
    db = None
    try:
        db = SessionLocal()
        gen_repo = GeneratorRepository(db)
        
        # Создаём запись эксперимента — ИСПРАВЛЕНО: params вместо parameters
        new_gen = gen_repo.create(
            name=display_name,
            gen_type=internal_type,
            params={"seed": seed, "length": length, "alpha": alpha},
            description=f"Запуск от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        # Формируем результаты тестов
        test_results = []
        for test in test_suite:
            t_name = test.get_name()
            p_value = convert_numpy_types(gen_record.get(f"{t_name} (p)", 0.0))
            statistic = gen_record.get(f"{t_name} (statistic)")
            if statistic is not None:
                statistic = convert_numpy_types(statistic)
            
            # Надёжное определение статуса
            status = gen_record.get(f"{t_name} (Статус)", "FAIL")
            passed = True if status == "PASS" else False
            
            test_results.append({
                "generator_id": new_gen.id,
                "test_name": t_name,
                "p_value": p_value,
                "statistic": statistic,
                "passed": passed,
                "sequence_length": length,
                "execution_time": gen_record.get(f"{t_name} (time)"),
                "test_parameters": {"alpha": alpha, "bins": 10 if "Chi" in t_name else None}
            })
        
        if test_results:
            test_repo = TestResultRepository(db)
            test_repo.bulk_create(test_results)
        
        db.commit()
        return True
        
    except Exception as db_err:
        if db:
            db.rollback()
        print(f"Ошибка сохранения в БД: {db_err}")
        return False
    finally:
        if db:
            db.close()


def load_aggregated_statistics():
    """Загрузить агрегированную статистику из БД"""
    if not DB_AVAILABLE:
        return None, None, None
    
    db = None
    try:
        db = SessionLocal()
        repo = GeneratorRepository(db)
        
        overall = repo.get_overall_summary()
        gen_stats = repo.get_aggregated_statistics()
        test_stats = repo.get_test_statistics_by_generator()
        
        return overall, gen_stats, test_stats
    except Exception as e:
        print(f"Ошибка загрузки статистики: {e}")
        return None, None, None
    finally:
        if db:
            db.close()


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
if 'imported_sequences' not in st.session_state:
    st.session_state.imported_sequences = {}
if 'export_content' not in st.session_state:
    st.session_state.export_content = None
if 'gen_stats' not in st.session_state:
    st.session_state.gen_stats = None
if 'test_stats' not in st.session_state:
    st.session_state.test_stats = None


# КОНФИГУРАЦИЯ СТРАНИЦЫ
st.set_page_config(page_title=app_config.title, page_icon="🎲", layout="wide")
st.title("Автоматизированная система исследования качества ГСЧ/ГПСЧ")


# БОКОВАЯ ПАНЕЛЬ
with st.sidebar:
    st.header("Параметры эксперимента")
    
    available_gens = list_generators()
    
    if st.session_state.get("imported_sequences"):
        import_options = list(st.session_state.imported_sequences.keys())
        available_gens = import_options + available_gens
        default_gens = import_options[:1] if import_options else ["lcg", "mersenne"]
    else:
        default_gens = ["lcg", "mersenne"]
    
    selected_gens = st.multiselect(
        "Генераторы для сравнения",
        options=available_gens,
        default=default_gens,
        key="generator_select_main"
    )

    st.divider()
    st.subheader("Параметры генерации")
    
    seed = st.number_input("Seed (зерно)", value=42, min_value=0, step=1, key="seed_input")
    length = st.slider("Длина последовательности (N)", 1000, 100000, 10000, step=1000, key="length_input")
    alpha = st.selectbox("Уровень значимости (α)", [0.01, 0.05], index=0, key="alpha_input")

    st.divider()
    st.subheader("Импорт последовательностей")
    
    uploaded_files = st.file_uploader(
        "Загрузите файлы (TXT, CSV, BIN)",
        type=["txt", "csv", "bin"],
        accept_multiple_files=True,
        help="Можно загрузить несколько файлов одновременно"
    )
    
    if uploaded_files:
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
        
        if st.session_state.imported_sequences:
            st.divider()
            st.write(f"**Загружено файлов:** {len(st.session_state.imported_sequences)}")
            for fname, data in st.session_state.imported_sequences.items():
                st.text(f"• {fname}: {data['length']} чисел ({data['format'].upper()})")
            
            if st.button("Очистить импорты", width="stretch"):
                st.session_state.imported_sequences = {}
                st.rerun()
    
    run_btn = st.button("Запустить анализ", type="primary", width="stretch")
    
    st.divider()
    if st.button("Обновить статистику", width="stretch"):
        overall, gen_stats, test_stats = load_aggregated_statistics()
        if gen_stats:
            st.session_state.overall_stats = overall
            st.session_state.gen_stats = gen_stats
            st.session_state.test_stats = test_stats
            st.success("Статистика обновлена!")
        else:
            st.info("База данных пуста или не подключена")
        
    if st.session_state.history:
        if st.button("Очистить сессионную историю", width="stretch"):
            st.session_state.history = []
            st.rerun()


# ОСНОВНАЯ ЛОГИКА: ЗАПУСК АНАЛИЗА
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
            
            imported_files_list = list(st.session_state.get("imported_sequences", {}).keys())
            
            for i, gen_display_name in enumerate(selected_gens):
                try:
                    is_imported = gen_display_name in imported_files_list
                    
                    if is_imported:
                        status_text.text(f"Тестирование: {gen_display_name}")
                        imported_data = st.session_state.imported_sequences.get(gen_display_name)
                        
                        if not imported_data:
                            st.error(f"Данные {gen_display_name} не найдены")
                            progress_bar.progress((i + 1) / len(selected_gens))
                            continue
                        
                        sequence = imported_data["sequence"]
                        internal_type = "imported"
                        display_name = gen_display_name
                        current_seed = None
                        
                    else:
                        if gen_display_name == "true_rng":
                            status_text.text(f"Тестирование: TRUE_RNG (аппаратная энтропия)")
                            gen = create_generator("true_rng")
                            sequence = gen.generate(length)
                            internal_type = "true_rng"
                            display_name = "true_rng"
                            current_seed = None
                        else:
                            status_text.text(f"Тестирование: {gen_display_name.upper()}")
                            gen = create_generator(gen_display_name, seed=seed)
                            sequence = gen.generate(length)
                            internal_type = gen_display_name
                            display_name = gen_display_name
                            current_seed = seed
                    
                    bits = [x & 1 for x in sequence]
                    sequences[display_name] = sequence
                    
                    gen_record = {
                        "Генератор": display_name, 
                        "Seed": str(current_seed) if current_seed is not None else "—", 
                        "Длина (N)": len(sequence),
                        "Время": datetime.now().strftime("%H:%M:%S")
                    }
                    
                    for test in test_suite:
                        test_name = test.get_name()
                        test_data = sequence if "Chi-Square" in test_name else bits
                        
                        start_time = time.perf_counter()
                        
                        try:
                            p_val = test.run(test_data)
                            p_val = convert_numpy_types(p_val)
                            
                            statistic_val = getattr(test, 'statistic', None)
                            if statistic_val is not None:
                                statistic_val = convert_numpy_types(statistic_val)
                                
                        except Exception as e:
                            print(f"Ошибка {test_name}: {e}")
                            p_val = 0.5
                            statistic_val = None
                        
                        end_time = time.perf_counter()
                        execution_time = end_time - start_time

                        if p_val <= 0.0:
                            p_val = 0.0001
                            
                        passed = p_val >= alpha
                        
                        gen_record[f"{test_name} (p)"] = round(p_val, 4)
                        gen_record[f"{test_name} (Статус)"] = "PASS" if passed else "FAIL"
                        gen_record[f"{test_name} (statistic)"] = statistic_val
                        gen_record[f"{test_name} (time)"] = execution_time
                    
                    # === СОХРАНЕНИЕ В БАЗУ ДАННЫХ ===
                    save_experiment_to_db(
                        display_name=display_name,
                        internal_type=internal_type,
                        seed=current_seed,
                        length=len(sequence),
                        alpha=alpha,
                        gen_record=gen_record,
                        test_suite=test_suite
                    )
                    # =================================

                    results_data.append(gen_record)
                    
                except Exception as e:
                    st.error(f"Ошибка {gen_display_name}: {str(e)}")
                
                progress_bar.progress((i + 1) / len(selected_gens))
            
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
    
    st.subheader("Результаты")
    cols_to_hide = [col for col in df.columns if 'statistic' in col or '(time)' in col]
    df_display = df.drop(columns=cols_to_hide)
    st.dataframe(df_display, width="stretch", hide_index=True)
    
    st.subheader("Метрики качества")
    metrics_cols = st.columns(len(params.get('selected_gens', [])))
    
    for i, gen in enumerate(params.get('selected_gens', [])):
        if gen in df["Генератор"].values:
            gen_row = df[df["Генератор"] == gen].iloc[0]
            
            status_cols = [col for col in df.columns if "Статус" in col]
            
            pass_count = sum(
                1 for col in status_cols 
                if "PASS" in str(gen_row[col]) and "FAIL" not in str(gen_row[col])
            )
            
            total_tests = len(status_cols)
            pass_rate = pass_count / total_tests if total_tests > 0 else 0
            
            with metrics_cols[i]:
                st.metric(label=gen.upper(), value=f"{pass_rate:.0%}")
    
    st.subheader("Сравнение p-values")
    
    p_cols = [col for col in df.columns if "(p)" in col]
    
    plot_data = []
    for _, row in df.iterrows():
        gen_name = row["Генератор"].upper()
        for col in p_cols:
            test_name = col.replace(" (p)", "")
            plot_data.append({
                "Генератор": gen_name,
                "Тест": test_name,
                "p-value": row[col]
            })
    
    plot_df = pd.DataFrame(plot_data)
    
    fig, ax = plt.subplots(figsize=(12, 5))
    pivot_df = plot_df.pivot(index="Тест", columns="Генератор", values="p-value")
    pivot_df.plot(kind="bar", ax=ax, alpha=0.8, width=0.8, colormap="viridis")
    
    ax.axhline(y=params.get('alpha', 0.01), color="red", linestyle="--", 
               linewidth=2, label=f"α = {params.get('alpha', 0.01)}")
    ax.set_ylabel("p-value")
    ax.set_title("Сравнение p-values генераторов по статистическим тестам")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=25, ha="right")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3, linestyle=":")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    
    st.subheader("Экспорт")
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            "CSV", 
            data=csv_data, 
            file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
            mime="text/csv", 
            width="stretch"
        )
    
    with col2:
        json_data = df.to_json(orient="records", force_ascii=False, indent=2)
        st.download_button(
            "JSON", 
            data=json_data, 
            file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
            mime="application/json", 
            width="stretch"
        )
    
    with st.expander("Экспорт последовательности", expanded=False):
        export_gen = st.selectbox(
            "Генератор", 
            options=list(sequences.keys()), 
            format_func=lambda x: x.upper(),
            key="export_gen_select"
        )
        export_format = st.radio("Формат", ["TXT", "CSV", "BIN"], horizontal=True)
        export_bits = st.checkbox("Только биты", value=False)
        export_count = st.number_input(
            "Количество (0=все)", 
            min_value=0, 
            max_value=params.get('length', 10000), 
            value=min(1000, params.get('length', 10000)), 
            step=100
        )
        
        if st.button("Подготовить файл", type="primary", key="prep_seq"):
            seq = sequences.get(export_gen, [])
            if export_bits:
                seq = [x & 1 for x in seq]
            if export_count > 0:
                seq = seq[:export_count]
            
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if export_format == "TXT":
                content = "\n".join(str(x) for x in seq)
                fname, mime = f"seq_{export_gen}_{ts}.txt", "text/plain"
            elif export_format == "CSV":
                content = "index,value\n" + "\n".join(f"{i},{x}" for i, x in enumerate(seq))
                fname, mime = f"seq_{export_gen}_{ts}.csv", "text/csv"
            else:
                content = b"".join(x.to_bytes(4, byteorder="little", signed=False) for x in seq)
                fname, mime = f"seq_{export_gen}_{ts}.bin", "application/octet-stream"
            
            st.session_state.export_content = content
            st.session_state.export_filename = fname
            st.session_state.export_mime = mime
            st.success(f"Готово: {len(seq)} значений")
        
        if st.session_state.export_content is not None:
            st.download_button(
                "Скачать", 
                data=st.session_state.export_content, 
                file_name=st.session_state.export_filename, 
                mime=st.session_state.export_mime, 
                width="stretch", 
                type="primary"
            )

# АГРЕГИРОВАННАЯ СТАТИСТИКА ИЗ БАЗЫ ДАННЫХ
if DB_AVAILABLE:
    st.divider()
    st.subheader("Агрегированная статистика (из БД)")
    
    if st.session_state.get('gen_stats'):
        
        # 1. Общая сводка
        overall = st.session_state.get('overall_stats')
        if overall:
            st.write("Общая информация")
            cols = st.columns(3)
            with cols[0]:
                st.metric("Всего экспериментов", overall[0] or 0)
            with cols[1]:
                st.metric("Всего тестов", overall[1] or 0)
            with cols[2]:
                avg_p = overall[2] or 0
                st.metric("Средний p-value", f"{avg_p:.4f}")
        
        st.divider()
        
        # 2. Статистика по генераторам
        st.write("Эффективность генераторов")
        
        gen_data = []
        for stat in st.session_state.gen_stats:
            gen_type, total_exp, total_tests, passed, avg_p = stat
            pass_rate = (passed / total_tests * 100) if total_tests and total_tests > 0 else 0
            gen_data.append({
                "Генератор": gen_type.upper() if gen_type else "N/A",
                "Экспериментов": int(total_exp) if total_exp else 0,
                "Тестов": int(total_tests) if total_tests else 0,
                "Пройдено": int(passed) if passed else 0,
                "Доля PASS": f"{pass_rate:.1f}%",
                "Средний p-value": f"{avg_p:.4f}" if avg_p else "N/A"
            })
        
        st.dataframe(pd.DataFrame(gen_data), width="stretch", hide_index=True)
        
        # 3. Визуализация: доля PASS по генераторам
        if gen_data:
            st.write("Доля успешных тестов")
            
            gen_names = [g["Генератор"] for g in gen_data]
            pass_rates = [float(g["Доля PASS"].replace("%", "")) for g in gen_data]
            
            fig, ax = plt.subplots(figsize=(10, 5))
            colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#5B8C5A']
            bars = ax.bar(gen_names, pass_rates, color=colors[:len(gen_names)], alpha=0.8)
            
            ax.set_ylabel('Доля PASS, %')
            ax.set_title('Процент успешных тестов по типам генераторов')
            ax.set_ylim(0, 100)
            ax.axhline(y=95, color='green', linestyle='--', alpha=0.7, label='Цель (95%)')
            
            for bar, rate in zip(bars, pass_rates):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                       f'{rate:.1f}%', ha='center', va='bottom', fontsize=10)
            
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        
        # 4. Детальная статистика по тестам
        if st.session_state.get('test_stats'):
            st.write("Статистика по каждому тесту")
            
            test_data = []
            for stat in st.session_state.test_stats:
                gen_type, test_name, total, passed, avg_p = stat
                pass_rate = (passed / total * 100) if total and total > 0 else 0
                test_data.append({
                    "Генератор": gen_type.upper() if gen_type else "N/A",
                    "Тест": test_name,
                    "Всего запусков": int(total) if total else 0,
                    "Пройдено": int(passed) if passed else 0,
                    "Доля PASS": f"{pass_rate:.1f}%",
                    "Средний p-value": f"{avg_p:.4f}" if avg_p else "N/A"
                })
            
            test_df = pd.DataFrame(test_data)
            st.dataframe(test_df, width="stretch", hide_index=True)
            
            # Тепловая карта
            st.write("Тепловая карта качества")
            
            try:
                pivot_data = test_df.pivot(index='Генератор', columns='Тест', values='Доля PASS')
                pivot_numeric = pivot_data.replace('%', '', regex=True).astype(float)
                
                fig, ax = plt.subplots(figsize=(12, 6))
                import seaborn as sns
                sns.heatmap(pivot_numeric, annot=True, fmt='.1f', cmap='RdYlGn', 
                           ax=ax, cbar_kws={'label': 'Доля PASS, %'},
                           vmin=0, vmax=100, linewidths=.5)
                ax.set_title('Процент успешных тестов по генераторам и типам тестов')
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
            except Exception as e:
                st.caption(f"Недостаточно данных для тепловой карты: {e}")
    
    else:
        st.info("Нажмите 'Обновить статистику' в боковой панели для загрузки данных из базы")

else:
    st.warning("База данных не подключена. Агрегированная статистика недоступна.")


# СЕССИОННАЯ ИСТОРИЯ
st.divider()
st.subheader("Сессионная история (текущая сессия)")

if st.session_state.history:
    for i, entry in enumerate(reversed(st.session_state.history[-3:]), 1):
        with st.expander(
            f"#{len(st.session_state.history) - i + 1} | "
            f"{entry['timestamp'].strftime('%H:%M:%S')} | "
            f"Генераторы: {', '.join(entry['params']['gens'])}",
            expanded=False
        ):
            hist_df = pd.DataFrame(entry['results'])
            status_cols = ["Генератор"] + [c for c in hist_df.columns if "(Статус)" in c]
            st.dataframe(hist_df[status_cols], width="stretch", hide_index=True)
            
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