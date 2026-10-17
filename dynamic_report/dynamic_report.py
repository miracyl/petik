import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

list_of_messages = [
    [
        "      • total_operations       - общее количество операций",
        "      • total_revenue          - общая выручка",
        "      • avg_price              - средняя цена товара",
        "      • unique_clients         - количество уникальных клиентов",
        "      • unique_products        - количество уникальных товаров",
        "      • return_orders          - количество возвратов",
        "      • return_orders_percent  - доля возвратов (%)",
        "      • returns_amount         - сумма возвратов (в деньгах)",
        "      • returns_percent_of_revenue - доля возвратов в выручке (%)",
        "      • avg_order_value        - средняя стоимость заказа",
        "      • avg_items_per_order    - среднее количество товаров в заказе",
        "      • revenue_share_percent  - доля страны в общих продажах (%)",
        "      • first_sale_date        - дата первой продажи",
        "      • last_sale_date         - дата последней продажи",
        "      • active_months          - количество активных месяцев",
        "      • avg_monthly_revenue    - среднемесячная выручка",
        "      • avg_return_per_order   - средняя сумма возврата на заказ",
        "      • active_days            - количество активных дней",
    ],
    [
        "      • country                - страна",
        "      • year_month             - месяц (YYYY-MM или YYYY-MM-DD)",
        "      • monthly_revenue        - выручка за месяц",
        "      • monthly_orders         - количество заказов за месяц",
        "      • adoption_of_new_clients- доля новых клиентов (%)",
        "      • prev_month_revenue     - выручка за предыдущий месяц",
        "      • revenue_growth_percent - процент роста выручки (%)",
    ],
    [
        "      • country                - страна",
        "      • stock_code             - артикул товара",
        "      • description            - описание товара",
        "      • total_quantity_sold    - общее количество проданных единиц",
        "      • total_quantity_return  - общее количество возвращенных единиц",
        "      • total_revenue          - общая выручка от товара",
        "      • unique_buyers          - количество уникальных покупателей",
        "      • revenue_share_in_country - доля товара в продажах страны (%)",
        "      • avg_price              - средняя цена товара",
    ],
    [
        "      • country                - страна",
        "      • customer_id            - идентификатор клиента",
        "      • monetary               - общая выручка от клиента",
        "      • frequency              - количество заказов",
        "      • recency                - дней с последней покупки",
        "      • monetary_score         - балл по деньгам (1-3)",
        "      • frequency_score        - балл по частоте (1-3)",
        "      • recency_score          - балл по давности (1-3)",
        "      • segment                - сегмент клиента (VIP, Лояльный, Новый, ...)",
    ],
    [
        "      • country                - страна",
        "      • stock_code             - артикул товара",
        "      • avg_unit_price         - средняя цена товара",
        "      • total_sold             - всего продано (шт.)",
        "      • total_returns          - всего возвращено (шт.)",
        "      • return_rate_percent    - процент возвратов (%)",
        "      • revenue_lost_from_returns - потерянная выручка от возвратов",
    ],
]


def connect_to_db():
    user = os.environ.get("PGUSER", "user1")
    password = os.environ.get("PGPASSWORD", "641997")
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    database = os.environ.get("PGDATABASE", "petDB")

    url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(url)
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        print(f"\n❌ Ошибка подключения к базе данных ({host}:{port}/{database}): {e}")
        print("💡 Проверьте, запущен ли контейнер с PostgreSQL (команда: docker compose up -d postgres).")
        return None


def output_message(title, messages_list):
    print(title)
    print("   📌 Доступные показатели:")
    for item in messages_list:
        print(item)


# ==============================================================================
# Функции валидации ввода («Защита от дурака»)
# ==============================================================================

def ask_choice(prompt, allowed_choices, error_msg="Некорректный выбор. Попробуйте снова."):
    """Запрашивает значение из фиксированного списка допустимых вариантов."""
    while True:
        val = input(prompt).strip()
        if val in allowed_choices:
            return val
        print(f"  ⚠️  {error_msg} (Допустимо: {', '.join(allowed_choices)})")


def ask_int(prompt, min_val=None, max_val=None):
    """
    Запрашивает целое число с проверкой диапазона.
    Пустой ввод (Enter) возвращает None (пропуск фильтра).
    """
    while True:
        s = input(prompt).strip()
        if not s:
            return None
        try:
            val = int(s)
            if min_val is not None and val < min_val:
                print(f"  ⚠️  Число должно быть не меньше {min_val}. Попробуйте снова.")
                continue
            if max_val is not None and val > max_val:
                print(f"  ⚠️  Число должно быть не больше {max_val}. Попробуйте снова.")
                continue
            return val
        except ValueError:
            print(f"  ⚠️  '{s}' не является целым числом. Введите число (например, 10) или нажмите Enter для пропуска.")


def ask_float(prompt, min_val=None, max_val=None):
    """
    Запрашивает дробное число (поддерживает и точку, и запятую).
    Пустой ввод (Enter) возвращает None (пропуск фильтра).
    """
    while True:
        s = input(prompt).strip()
        if not s:
            return None
        # Заменяем запятую на точку для удобства пользователя
        normalized = s.replace(",", ".")
        try:
            val = float(normalized)
            if min_val is not None and val < min_val:
                print(f"  ⚠️  Число должно быть не меньше {min_val}. Попробуйте снова.")
                continue
            if max_val is not None and val > max_val:
                print(f"  ⚠️  Число должно быть не больше {max_val}. Попробуйте снова.")
                continue
            return val
        except ValueError:
            print(f"  ⚠️  '{s}' не является числом. Введите число (например, 150.5) или нажмите Enter для пропуска.")


def ask_date(prompt, min_date=None):
    """
    Запрашивает дату в формате YYYY-MM-DD.
    Пустой ввод (Enter) возвращает None.
    """
    while True:
        s = input(prompt).strip()
        if not s:
            return None
        try:
            d = datetime.strptime(s, "%Y-%m-%d").date()
            if min_date is not None and d < min_date:
                print(f"  ⚠️  Дата не может быть раньше начальной ({min_date}). Попробуйте снова.")
                continue
            return s
        except ValueError:
            print("  ⚠️  Неверный формат даты! Ожидается ГГГГ-ММ-ДД (например, 2011-03-25). Нажмите Enter для пропуска.")


def ask_year_month(prompt):
    """
    Запрашивает месяц/дату. Принимает формат YYYY-MM или YYYY-MM-DD.
    Автоматически дополняет YYYY-MM до первого числа месяца (YYYY-MM-01).
    Пустой ввод (Enter) возвращает None.
    """
    while True:
        s = input(prompt).strip()
        if not s:
            return None
        # Если ввели YYYY-MM (например, 2011-05), преобразуем в 2011-05-01
        if len(s) == 7 and s[4] == "-":
            s_test = s + "-01"
        else:
            s_test = s
        try:
            datetime.strptime(s_test, "%Y-%m-%d")
            return s_test
        except ValueError:
            print("  ⚠️  Неверный формат! Введите месяц в формате ГГГГ-ММ (например, 2011-05) или нажмите Enter для пропуска.")


def ask_item_from_list(prompt, valid_items, item_name="значение"):
    """
    Запрашивает элемент из базы (страна, сегмент).
    Регистронезависимо сопоставляет ввод со списком допустимых значений.
    Автоматически убирает лишние кавычки и запятые.
    Поддерживает автодополнение по уникальному началу слова (например, 'Bra' -> 'Brazil').
    Пустой ввод (Enter) возвращает None.
    """
    lookup = {item.strip().lower(): item.strip() for item in valid_items if item}

    while True:
        raw_s = input(prompt).strip()
        if not raw_s:
            return None

        # Очищаем от случайных кавычек и запятых (например: 'Australia' или Australia,)
        s = raw_s.strip("'\"`").rstrip(",").strip()
        key = s.lower()

        # Точное совпадение без учёта регистра
        if key in lookup:
            return lookup[key]

        # Автодополнение по началу слова (префикс), например "Bra" -> "Brazil"
        prefix_matches = [val for k, val in lookup.items() if k.startswith(key)]
        if len(prefix_matches) == 1:
            matched = prefix_matches[0]
            print(f"  👉 Выбрано: {matched}")
            return matched

        print(f"  ⚠️  {item_name.capitalize()} '{raw_s}' не найдена в базе данных.")
        if prefix_matches:
            print(f"      Возможно, вы имели в виду: {', '.join(prefix_matches[:8])}")
        else:
            sample = list(valid_items)[:8]
            print(f"      Примеры допустимых значений: {', '.join(sample)}...")
        print("      Введите название или нажмите Enter для выбора всех.")


def get_values_for_sorts(allowed_attributes, default_attribute):
    """
    Запрашивает атрибут сортировки, порядок (ASC/DESC) и лимит с полной валидацией.
    """
    allowed_lookup = {attr.lower(): attr for attr in allowed_attributes}

    # 1. Поле сортировки
    while True:
        raw_order = input(f"\nВведите поле для сортировки (Enter — {default_attribute}): ").strip()
        if not raw_order:
            p_order = default_attribute
            break
        if raw_order.lower() in allowed_lookup:
            p_order = allowed_lookup[raw_order.lower()]
            break
        print(f"  ⚠️  Поле '{raw_order}' недопустимо для сортировки.")
        print(f"      Доступные поля: {', '.join(allowed_attributes)}")

    # 2. Порядок сортировки (ASC / DESC)
    while True:
        raw_sort = input("Порядок сортировки: 1 - DESC (по убыванию), 2 - ASC (по возрастанию) [Enter — DESC]: ").strip().lower()
        if not raw_sort or raw_sort in ("1", "desc", "d", "убыв", "убывание"):
            p_sort_order = "DESC"
            break
        if raw_sort in ("2", "asc", "a", "возр", "возрастание"):
            p_sort_order = "ASC"
            break
        print("  ⚠️  Некорректный ввод. Введите 1 для DESC, 2 для ASC или нажмите Enter.")

    # 3. Лимит строк
    p_limit = ask_int("Сколько строк вывести (LIMIT, Enter — все): ", min_val=1)

    return p_order, p_sort_order, p_limit


def print_available_values(title, values):
    """Красиво выводит список доступных значений (стран, сегментов и т.д.)."""
    print(f"\n{title}")
    clean_values = []
    for v in values:
        if v is None:
            continue
        if isinstance(v, str):
            clean_values.append(v.strip())
        elif hasattr(v, "__getitem__"):
            # Извлекаем первый элемент из SQLAlchemy Row или tuple/list
            clean_values.append(str(v[0]).strip())
        else:
            clean_values.append(str(v).strip())

    clean_values = sorted(list(set(clean_values)))

    # Выводим в 3 колонки для компактности
    col_width = 24
    for i in range(0, len(clean_values), 3):
        row = clean_values[i:i + 3]
        print("   " + "".join(f"• {val:<{col_width}}" for val in row))
    return clean_values


def print_sorting_attributes(attributes):
    """Выводит список полей, доступных для сортировки."""
    print("\nДопустимые атрибуты для сортировки:")
    flat = []
    for group in attributes:
        flat.extend(group)
    for i in range(0, len(flat), 4):
        chunk = flat[i:i + 4]
        print("   " + "   ".join(f"• {col:<20}" for col in chunk))
    return flat


def select_type_of_report():
    """Интерактивное меню выбора отчета с валидацией."""
    print("\n" + "=" * 70)
    print("🌟 ДОБРО ПОЖАЛОВАТЬ В ГЕНЕРАТОР АНАЛИТИЧЕСКИХ ОТЧЁТОВ! 🌟")
    print("=" * 70)
    print("\n📊 Доступные типы отчётов:")
    output_message("\n🔹 1. СВОДКА ПО СТРАНАМ (sale_analysis_by_country)", list_of_messages[0])
    output_message("\n🔹 2. ДИНАМИКА ПО МЕСЯЦАМ (sale_monthly_trend)", list_of_messages[1])
    output_message("\n🔹 3. ТОВАРНАЯ АНАЛИТИКА (product_sale_analysis)", list_of_messages[2])
    output_message("\n🔹 4. RFM-СЕГМЕНТАЦИЯ КЛИЕНТОВ (customer_rfm_segments)", list_of_messages[3])
    output_message("\n🔹 5. АНАЛИЗ ВОЗВРАТОВ (return_analysis)", list_of_messages[4])
    print("\n" + "-" * 70)
    print("💡 Возможности:")
    print("   • Гибкая фильтрация по любым числовым, строковым и датовым параметрам")
    print("   • Сортировка по любому показателю (ASC / DESC)")
    print("   • Ограничение количества строк (LIMIT)")
    print("   • Экспорт результатов в Excel (.xlsx)")
    print("-" * 70)

    choice = ask_choice(
        "\n➡️  Введите номер отчёта (1-5, или 'q' для выхода): ",
        allowed_choices=["1", "2", "3", "4", "5", "q", "exit"],
        error_msg="Номер отчёта должен быть от 1 до 5!"
    )
    if choice in ("q", "exit"):
        return None
    return int(choice)


def load_sql_files_with_functions(engine, paths):
    """Загружает SQL функции из файлов в базу данных."""
    with engine.begin() as conn:
        for path in paths:
            file_path = Path(path)
            if not file_path.exists():
                raise FileNotFoundError(f"SQL-файл не найден: {file_path}")
            sql = file_path.read_text(encoding='utf-8')
            conn.execute(text(sql))


def transform_to_xlsx(result, default_filename="report.xlsx"):
    """Преобразует результат SQLAlchemy в Excel файл с информированием пользователя."""
    rows = result.fetchall()
    if not rows:
        print("\n⚠️  По заданным критериям не найдено ни одной записи. Сформирован пустой файл.")
        df = pd.DataFrame(columns=result.keys())
    else:
        df = pd.DataFrame(rows, columns=result.keys())

    output_path = Path(default_filename)
    df.to_excel(output_path, index=False, sheet_name="Отчёт")
    print(f"\n✅ Успешно! Выгружено строк: {len(df)}.")
    print(f"📁 Отчёт сохранён в файл: {output_path.resolve()}")


# ==============================================================================
# Основная логика программы
# ==============================================================================

def main():
    engine = connect_to_db()
    if engine is None:
        return

    base_dir = Path(__file__).resolve().parent
    sql_files = [
        base_dir / 'data' / 'sale_analysis_by_country_report.sql',
        base_dir / 'data' / 'sale_monthly_trend_report.sql',
        base_dir / 'data' / 'product_sale_analysis_report.sql',
        base_dir / 'data' / 'customer_rfm_segments_report.sql',
        base_dir / 'data' / 'return_analysis_report.sql',
    ]

    try:
        load_sql_files_with_functions(engine, sql_files)
    except Exception as e:
        print(f"\n❌ Ошибка загрузки SQL-функций отчётов: {e}")
        return

    while True:
        report_type = select_type_of_report()
        if report_type is None:
            print("\nДо свидания! 👋")
            break

        # ----------------------------------------------------------------------
        # 1. СВОДКА ПО СТРАНАМ
        # ----------------------------------------------------------------------
        if report_type == 1:
            with engine.begin() as conn:
                db_countries = conn.execute(
                    text("SELECT DISTINCT country FROM sale_analysis_by_country WHERE country IS NOT NULL ORDER BY country")
                ).fetchall()
                available_countries = print_available_values("📍 Доступные страны в базе данных:", db_countries)

                print("\n📋 Задайте параметры фильтрации (нажмите Enter, чтобы пропустить фильтр):")
                p_country = ask_item_from_list("Страна (Enter — все страны): ", available_countries, item_name="страна")
                p_min_active_month = ask_int("Минимальное количество активных месяцев (>= 1): ", min_val=1)
                p_max_active_month = ask_int("Максимальное количество активных месяцев: ", min_val=p_min_active_month or 1)

                p_first_sale_from = ask_date("Первая продажа ОТ (ГГГГ-ММ-ДД, например 2010-12-01): ")
                min_first_sale = datetime.strptime(p_first_sale_from, "%Y-%m-%d").date() if p_first_sale_from else None
                p_first_sale_to = ask_date("Первая продажа ДО (ГГГГ-ММ-ДД): ", min_date=min_first_sale)

                p_last_sale_from = ask_date("Последняя продажа ОТ (ГГГГ-ММ-ДД): ")
                min_last_sale = datetime.strptime(p_last_sale_from, "%Y-%m-%d").date() if p_last_sale_from else None
                p_last_sale_to = ask_date("Последняя продажа ДО (ГГГГ-ММ-ДД): ", min_date=min_last_sale)

                p_min_revenue = ask_float("Минимальная общая выручка (>= 0): ", min_val=0.0)
                p_min_operations = ask_int("Минимальное количество операций (>= 0): ", min_val=0)
                p_min_unique_clients = ask_int("Минимальное количество уникальных клиентов (>= 0): ", min_val=0)
                p_max_return_percent = ask_float("Максимальная доля возвратов в выручке (% от 0 до 100): ", min_val=0.0, max_val=100.0)

                sort_columns_grouped = [
                    ["country", "total_operations", "total_revenue", "avg_price"],
                    ["unique_clients", "unique_products", "return_orders", "return_orders_percent"],
                    ["returns_amount", "returns_percent_of_revenue", "avg_order_value", "avg_items_per_order"],
                    ["revenue_share_percent", "first_sale_date", "last_sale_date", "active_months", "avg_monthly_revenue"],
                    ["avg_return_per_order", "active_days"],
                ]
                allowed_cols = print_sorting_attributes(sort_columns_grouped)
                p_order_by, p_sort_order, p_limit = get_values_for_sorts(allowed_cols, default_attribute="total_revenue")

                result = conn.execute(
                    text("""
                         SELECT *
                         FROM sale_analysis_by_country_report(
                                 p_country => :p_country,
                                 p_min_active_month => :p_min_active_month,
                                 p_max_active_month => :p_max_active_month,
                                 p_first_sale_from => :p_first_sale_from,
                                 p_first_sale_to => :p_first_sale_to,
                                 p_last_sale_from => :p_last_sale_from,
                                 p_last_sale_to => :p_last_sale_to,
                                 p_min_revenue => :p_min_revenue,
                                 p_min_operations => :p_min_operations,
                                 p_min_unique_clients => :p_min_unique_clients,
                                 p_max_return_percent => :p_max_return_percent,
                                 p_order_by => :p_order_by,
                                 p_sort_order => :p_sort_order,
                                 p_limit => :p_limit
                              )
                    """),
                    {
                        "p_country": p_country,
                        "p_min_active_month": p_min_active_month,
                        "p_max_active_month": p_max_active_month,
                        "p_first_sale_from": p_first_sale_from,
                        "p_first_sale_to": p_first_sale_to,
                        "p_last_sale_from": p_last_sale_from,
                        "p_last_sale_to": p_last_sale_to,
                        "p_min_revenue": p_min_revenue,
                        "p_min_operations": p_min_operations,
                        "p_min_unique_clients": p_min_unique_clients,
                        "p_max_return_percent": p_max_return_percent,
                        "p_order_by": p_order_by,
                        "p_sort_order": p_sort_order,
                        "p_limit": p_limit,
                    },
                )
                transform_to_xlsx(result, "report_country_summary.xlsx")

        # ----------------------------------------------------------------------
        # 2. ДИНАМИКА ПО МЕСЯЦАМ
        # ----------------------------------------------------------------------
        elif report_type == 2:
            with engine.begin() as conn:
                db_countries = conn.execute(
                    text("SELECT DISTINCT country FROM sale_monthly_trend WHERE country IS NOT NULL ORDER BY country")
                ).fetchall()
                available_countries = print_available_values("📍 Доступные страны в базе данных:", db_countries)

                print("\n📋 Задайте параметры фильтрации (нажмите Enter, чтобы пропустить фильтр):")
                p_country = ask_item_from_list("Страна (Enter — все страны): ", available_countries, item_name="страна")
                p_year_month = ask_year_month("Месяц (ГГГГ-ММ, например 2011-03, Enter — все месяцы): ")
                p_min_revenue = ask_float("Минимальная выручка за месяц (>= 0): ", min_val=0.0)
                p_min_growth_percent = ask_float("Минимальный процент роста выручки (%): ")

                sort_columns_grouped = [
                    ["country", "year_month", "monthly_revenue", "prev_month_revenue"],
                    ["monthly_orders", "adoption_of_new_clients", "revenue_growth_percent"],
                ]
                allowed_cols = print_sorting_attributes(sort_columns_grouped)
                p_order_by, p_sort_order, p_limit = get_values_for_sorts(allowed_cols, default_attribute="monthly_revenue")

                result = conn.execute(
                    text("""
                        SELECT *
                        FROM sale_monthly_trend_report(
                            p_country => :p_country,
                            p_year_month => :p_year_month,
                            p_min_revenue => :p_min_revenue,
                            p_min_growth_percent => :p_min_growth_percent,
                            p_order_by => :p_order_by,
                            p_sort_order => :p_sort_order,
                            p_limit => :p_limit
                        )
                    """),
                    {
                        "p_country": p_country,
                        "p_year_month": p_year_month,
                        "p_min_revenue": p_min_revenue,
                        "p_min_growth_percent": p_min_growth_percent,
                        "p_order_by": p_order_by,
                        "p_limit": p_limit,
                        "p_sort_order": p_sort_order,
                    },
                )
                transform_to_xlsx(result, "report_monthly_trend.xlsx")

        # ----------------------------------------------------------------------
        # 3. ТОВАРНАЯ АНАЛИТИКА
        # ----------------------------------------------------------------------
        elif report_type == 3:
            with engine.begin() as conn:
                db_countries = conn.execute(
                    text("SELECT DISTINCT country FROM product_sale_analysis WHERE country IS NOT NULL ORDER BY country")
                ).fetchall()
                available_countries = print_available_values("📍 Доступные страны в базе данных:", db_countries)

                print("\n📋 Задайте параметры фильтрации (нажмите Enter, чтобы пропустить фильтр):")
                p_country = ask_item_from_list("Страна (Enter — все страны): ", available_countries, item_name="страна")
                p_min_revenue = ask_float("Минимальная выручка от товара (>= 0): ", min_val=0.0)
                p_min_sold = ask_float("Минимальное количество проданных единиц (>= 0): ", min_val=0.0)
                p_min_unique_buyers = ask_int("Минимальное количество покупателей (>= 0): ", min_val=0)
                p_min_share_percent = ask_float("Минимальная доля в продажах страны (% от 0 до 100): ", min_val=0.0, max_val=100.0)
                p_max_returns = ask_float("Максимальное количество возвратов (>= 0): ", min_val=0.0)

                sort_columns_grouped = [
                    ["country", "stock_code", "description", "total_quantity_sold"],
                    ["total_quantity_return", "total_revenue", "unique_buyers", "revenue_share_in_country", "avg_price"],
                ]
                allowed_cols = print_sorting_attributes(sort_columns_grouped)
                p_order_by, p_sort_order, p_limit = get_values_for_sorts(allowed_cols, default_attribute="total_revenue")

                result = conn.execute(
                    text("""
                        SELECT *
                        FROM product_sale_analysis_report(
                                p_country => :p_country,
                                p_min_revenue => :p_min_revenue,
                                p_min_sold => :p_min_sold,
                                p_min_unique_buyers => :p_min_unique_buyers,
                                p_min_share_percent => :p_min_share_percent,
                                p_max_returns => :p_max_returns,
                                p_order_by => :p_order_by,
                                p_sort_order => :p_sort_order,
                                p_limit  => :p_limit
                        )
                    """),
                    {
                        "p_country": p_country,
                        "p_min_revenue": p_min_revenue,
                        "p_min_sold": p_min_sold,
                        "p_min_unique_buyers": p_min_unique_buyers,
                        "p_min_share_percent": p_min_share_percent,
                        "p_max_returns": p_max_returns,
                        "p_order_by": p_order_by,
                        "p_sort_order": p_sort_order,
                        "p_limit": p_limit,
                    },
                )
                transform_to_xlsx(result, "report_product_analysis.xlsx")

        # ----------------------------------------------------------------------
        # 4. RFM-СЕГМЕНТАЦИЯ КЛИЕНТОВ
        # ----------------------------------------------------------------------
        elif report_type == 4:
            with engine.begin() as conn:
                db_countries = conn.execute(
                    text("SELECT DISTINCT country FROM customer_rfm_segments WHERE country IS NOT NULL ORDER BY country")
                ).fetchall()
                available_countries = print_available_values("📍 Доступные страны в базе данных:", db_countries)

                db_segments = conn.execute(
                    text("SELECT DISTINCT segment FROM customer_rfm_segments WHERE segment IS NOT NULL ORDER BY segment")
                ).fetchall()
                available_segments = print_available_values("👥 Доступные сегменты клиентов:", db_segments)

                print("\n📋 Задайте параметры фильтрации (нажмите Enter, чтобы пропустить фильтр):")
                p_country = ask_item_from_list("Страна (Enter — все страны): ", available_countries, item_name="страна")
                p_segment = ask_item_from_list("Сегмент (Enter — все сегменты): ", available_segments, item_name="сегмент")
                p_customer_id = ask_int("Идентификатор клиента (CustomerID, например 12345): ", min_val=1)
                p_min_monetary = ask_float("Минимальная выручка от клиента (>= 0): ", min_val=0.0)
                p_min_frequency = ask_int("Минимальное количество заказов (>= 1): ", min_val=1)
                p_max_recency = ask_float("Максимум дней с последней покупки (>= 0): ", min_val=0.0)

                sort_columns_grouped = [
                    ["country", "customer_id", "monetary", "frequency", "recency"],
                    ["monetary_score", "frequency_score", "recency_score", "segment"],
                ]
                allowed_cols = print_sorting_attributes(sort_columns_grouped)
                p_order_by, p_sort_order, p_limit = get_values_for_sorts(allowed_cols, default_attribute="monetary")

                result = conn.execute(
                    text("""
                        SELECT *
                        FROM customer_rfm_segments_report(
                            p_country => :p_country,
                            p_segment => :p_segment,
                            p_customer_id => :p_customer_id,
                            p_min_monetary => :p_min_monetary,
                            p_min_frequency => :p_min_frequency,
                            p_max_recency => :p_max_recency,
                            p_order_by => :p_order_by,
                            p_sort_order => :p_sort_order,
                            p_limit => :p_limit
                        )
                    """),
                    {
                        "p_country": p_country,
                        "p_segment": p_segment,
                        "p_customer_id": p_customer_id,
                        "p_min_monetary": p_min_monetary,
                        "p_min_frequency": p_min_frequency,
                        "p_max_recency": p_max_recency,
                        "p_order_by": p_order_by,
                        "p_sort_order": p_sort_order,
                        "p_limit": p_limit,
                    },
                )
                transform_to_xlsx(result, "report_rfm_segments.xlsx")

        # ----------------------------------------------------------------------
        # 5. АНАЛИЗ ВОЗВРАТОВ
        # ----------------------------------------------------------------------
        elif report_type == 5:
            with engine.begin() as conn:
                db_countries = conn.execute(
                    text("SELECT DISTINCT country FROM return_analysis WHERE country IS NOT NULL ORDER BY country")
                ).fetchall()
                available_countries = print_available_values("📍 Доступные страны в базе данных:", db_countries)

                print("\n📋 Задайте параметры фильтрации (нажмите Enter, чтобы пропустить фильтр):")
                p_country = ask_item_from_list("Страна (Enter — все страны): ", available_countries, item_name="страна")
                p_stock_code = input("Артикул товара (StockCode, Enter — все товары): ").strip() or None
                p_min_sold = ask_int("Минимальное количество проданных единиц (>= 0): ", min_val=0)
                p_min_returns = ask_int("Минимальное количество возвратов (>= 0): ", min_val=0)
                p_min_return_rate = ask_float("Минимальный процент возвратов (% от 0 до 100): ", min_val=0.0, max_val=100.0)
                p_min_revenue_lost = ask_float("Минимальная сумма потерянной выручки (>= 0): ", min_val=0.0)

                sort_columns_grouped = [
                    ["country", "stock_code", "avg_unit_price", "total_sold"],
                    ["total_returns", "return_rate_percent", "revenue_lost_from_returns"],
                ]
                allowed_cols = print_sorting_attributes(sort_columns_grouped)
                p_order_by, p_sort_order, p_limit = get_values_for_sorts(allowed_cols, default_attribute="return_rate_percent")

                result = conn.execute(
                    text("""
                        SELECT *
                        FROM return_analysis_report(
                                p_country => :p_country,
                                p_stock_code => :p_stock_code,
                                p_min_sold => :p_min_sold,
                                p_min_returns  => :p_min_returns,
                                p_min_return_rate => :p_min_return_rate,
                                p_min_revenue_lost => :p_min_revenue_lost,
                                p_order_by => :p_order_by,
                                p_sort_order => :p_sort_order,
                                p_limit => :p_limit
                        )
                    """),
                    {
                        "p_country": p_country,
                        "p_stock_code": p_stock_code,
                        "p_min_sold": p_min_sold,
                        "p_min_returns": p_min_returns,
                        "p_min_return_rate": p_min_return_rate,
                        "p_min_revenue_lost": p_min_revenue_lost,
                        "p_order_by": p_order_by,
                        "p_sort_order": p_sort_order,
                        "p_limit": p_limit,
                    },
                )
                transform_to_xlsx(result, "report_returns_analysis.xlsx")


if __name__ == "__main__":
    main()
