from flask import Flask, render_template, request
import requests
import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import numpy as np

app = Flask(__name__)

# Настройки API (замените на ваш реальный ключ)
API_KEY = '26cdbcfcb33ba430ba05d900'  # Получите на https://exchangerate-api.com
BASE_URL = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD'
HISTORICAL_URL = f'https://v6.exchangerate-api.com/v6/{API_KEY}/history/USD/'

# Данные о валютах
CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'RUB', 'CNY']
CURRENCY_NAMES = {
    'USD': 'Доллар США',
    'EUR': 'Евро',
    'GBP': 'Фунт стерлингов',
    'JPY': 'Японская иена',
    'RUB': 'Российский рубль',
    'CNY': 'Китайский юань'
}

def get_exchange_rates():
    try:
        response = requests.get(BASE_URL)
        data = response.json()
        if data['result'] == 'success':
            rates = data['conversion_rates']
            rates['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return rates
    except Exception as e:
        print(f"Ошибка при получении курсов: {e}")
    
    # Фоллбек данные
    return {
        "USD": 1.0,
        "EUR": 0.93,
        "GBP": 0.79,
        "JPY": 151.50,
        "RUB": 92.40,
        "CNY": 7.24,
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (оффлайн)"
    }

def get_historical_data(base_currency, target_currency, days=7):
    dates = []
    rates = []
    today = datetime.datetime.now()
    
    try:
        for i in range(days, 0, -1):
            date = (today - datetime.timedelta(days=i)).strftime("%Y%m%d")
            url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/history/{base_currency}/{date}"
            response = requests.get(url)
            data = response.json()
            
            if data['result'] == 'success' and target_currency in data['conversion_rates']:
                dates.append((today - datetime.timedelta(days=i)).strftime("%d.%m"))
                rates.append(data['conversion_rates'][target_currency])
    except Exception as e:
        print(f"Ошибка при получении исторических данных: {e}")
        # Генерируем фейковые данные для демонстрации
        dates = [(today - datetime.timedelta(days=i)).strftime("%d.%m") for i in range(days, 0, -1)]
        base_rate = 90 if base_currency == 'RUB' else 1.0
        target_rate = 1.0 if target_currency == 'USD' else 0.9
        rates = [base_rate * target_rate * (1 + 0.01 * np.sin(i)) for i in range(days)]
    
    return dates, rates

def create_plot(dates, rates, base_currency, target_currency):
    plt.figure(figsize=(10, 5))
    
    # Устанавливаем стиль
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Цвета для графика
    primary_color = '#4361ee'
    secondary_color = '#3a0ca3'
    background_color = '#f8f9fa'
    
    # Рассчитываем оптимальные границы для оси Y
    min_rate = min(rates)
    max_rate = max(rates)
    range_rate = max_rate - min_rate
    
    # Добавляем 15% от диапазона сверху и снизу для лучшего отображения
    padding = range_rate * 0.15 if range_rate > 0 else max_rate * 0.15
    y_min = max(0, min_rate - padding)  # Не ниже нуля
    y_max = max_rate + padding
    
    # Создаем график
    line, = plt.plot(dates, rates, 
                    color=primary_color, 
                    linewidth=3, 
                    marker='o',
                    markersize=8,
                    markerfacecolor='white',
                    markeredgewidth=2,
                    markeredgecolor=primary_color,
                    alpha=0.8)
    
    # Устанавливаем границы оси Y
    plt.ylim(y_min, y_max)
    
    # Заполнение под графиком
    plt.fill_between(dates, rates, y_min, color=primary_color, alpha=0.1)
    
    # Настройка заголовка и подписей
    plt.title(f'Динамика курса {base_currency} к {target_currency}', 
              fontsize=16, pad=20, fontweight='bold', color='#2b2d42')
    plt.xlabel('Дата', fontsize=12, labelpad=10, color='#495057')
    plt.ylabel(f'Курс ({target_currency})', fontsize=12, labelpad=10, color='#495057')
    
    # Настройка осей
    ax = plt.gca()
    ax.set_facecolor(background_color)
    
    # Убираем границы
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Добавляем горизонтальные линии сетки
    ax.yaxis.grid(True, linestyle='--', alpha=0.6, color='#adb5bd')
    ax.xaxis.grid(False)
    
    # Настройка тиков
    plt.xticks(rotation=45, ha='right', color='#6c757d')
    
    # Форматируем метки оси Y (2 знака после запятой)
    ax.yaxis.set_major_formatter('{x:.2f}')
    plt.yticks(color='#6c757d')
    
    # Добавляем аннотацию с текущим значением
    last_rate = rates[-1]
    ax.annotate(f'{last_rate:.4f}', 
                xy=(dates[-1], last_rate), 
                xytext=(10, 10),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', fc=primary_color, ec='none', alpha=0.3),
                fontsize=12,
                color='white')
    
    # Добавляем трендовую линию (если данных достаточно)
    if len(rates) > 2:
        z = np.polyfit(range(len(rates)), rates, 1)
        p = np.poly1d(z)
        plt.plot(dates, p(range(len(rates))), "--", 
                color=secondary_color, 
                linewidth=1.5,
                alpha=0.7)
        
        # Рассчитываем процент изменения за весь период
        first_rate = rates[0]
        change_percent = ((last_rate - first_rate) / first_rate) * 100
        trend_text = f"▲ {change_percent:.1f}%" if change_percent >= 0 else f"▼ {abs(change_percent):.1f}%"
        trend_color = '#4cc9f0' if change_percent >= 0 else '#f72585'
        
        # Добавляем аннотацию тренда
        ax.annotate(trend_text,
                   xy=(0.98, 0.95),
                   xycoords='axes fraction',
                   fontsize=12,
                   color=trend_color,
                   bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=trend_color, alpha=0.8),
                   horizontalalignment='right')
    
    # Настраиваем отступы
    plt.tight_layout()
    
    # Сохраняем в буфер
    buffer = BytesIO()
    plt.savefig(buffer, format='png', 
                dpi=120, 
                facecolor=background_color,
                bbox_inches='tight',
                transparent=False)
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return plot_data

def calculate_trend(previous_rates):
    if len(previous_rates) < 2:
        return 'neutral', 0.0
    
    current = previous_rates[-1]
    previous = previous_rates[-2]
    change = ((current - previous) / previous) * 100
    
    if change > 0.1:
        return 'up', change
    elif change < -0.1:
        return 'down', abs(change)
    else:
        return 'neutral', abs(change)

@app.route('/')
def index():
    rates = get_exchange_rates()
    from_currency = request.args.get('from_currency', 'RUB')
    to_currency = request.args.get('to_currency', 'USD')
    amount = request.args.get('amount', '1')
    
    # Конвертация
    try:
        amount_float = float(amount)
        result = round((amount_float / rates[from_currency]) * rates[to_currency], 4)
    except:
        result = ""
    
    # Обмен валют местами
    if 'swap' in request.args:
        from_currency, to_currency = to_currency, from_currency
    
    # Получение исторических данных
    dates, historical_rates = get_historical_data(from_currency, to_currency)
    plot_url = create_plot(dates, historical_rates, from_currency, to_currency) if dates and historical_rates else None
    
    # Популярные курсы с трендами
    popular_rates = []
    for currency in CURRENCIES:
        if currency != from_currency:
            _, currency_rates = get_historical_data(from_currency, currency, 2)
            trend, change = calculate_trend(currency_rates) if len(currency_rates) >= 2 else ('neutral', 0.0)
            
            popular_rates.append({
                'from_currency': from_currency,
                'to_currency': currency,
                'rate': round(rates[from_currency] / rates[currency], 4),
                'trend': trend,
                'change': round(change, 2)
            })
    
    return render_template('index.html', 
                         rates=rates,
                         currencies=CURRENCIES,
                         currency_names=CURRENCY_NAMES,
                         from_currency=from_currency,
                         to_currency=to_currency,
                         amount=amount,
                         result=result,
                         popular_rates=popular_rates,
                         plot_url=plot_url)

@app.route('/convert', methods=['GET'])
def convert():
    return index()

if __name__ == '__main__':
    app.run(debug=True)