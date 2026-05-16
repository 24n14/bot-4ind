import os
from dotenv import load_dotenv

load_dotenv()

#  ===== НАСТРОЙКИ ПОДКЛЮЧЕНИЯ =====
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
DEMO_TRADING = True  # True для демо-счета, False для реального
PROXY_HOST = '154.219.207.178'
PROXY_PORT = '63690'
PROXY_USER = os.getenv('PROXY_USER')
PROXY_PASS = os.getenv('PROXY_PASS')
USE_PROXY = True

#  ===== ПАРАМЕТРЫ ТОРГОВЛИ =====
SYMBOL = 'BTC/USDT:USDT'
CATEGORY = 'linear'
AMOUNT = 0.01
TIMEFRAME = '5m'
LIMIT = 200  # должен быть больше чем параметры MA/EMA
STOP_LOSS = 0.7
TAKE_PROFIT = 0.7
TRAILING_STOP_DISTANCE = 300

TS_TRIGGER_PRICE = 'entry_price'  # 'entry_price' , 'take_profit_price' ,
TPSL_SIZE = 100  # использует тейкпрофит, это его доля
REMAINING = 100  # использует трейлинг стоп
LEVERAGE = 10
MIN_AMOUNT = 0.001
MIN_CONFIDENCE = 0.5  # минимальная уверенность для входа

# ===== ПАРАМЕТРЫ OBV =====
OBV_SMA_PERIOD = 5  # период сглаживания OBV
EMA_50_PERIOD = 50  # период EMA для тренда
ATR_PERIOD = 14  # период ATR для волатильности
SMA_obv = 5

# ===== ПАРАМЕТРЫ MA/EMA =====
MA = 2
EMA = 50
# ===== ПАРАМЕТРЫ MACD =====
FAST_macd = 12
SLOW_macd = 26
SIGNAL_macd = 9
# ===== ПАРАМЕТРЫ СТОХАСТИК =====
FASTK = 14
SLOWK = 3
SLOWD = 3

# ===== ПАРАМЕТРЫ КОНСЕНСУСА =====
MIN_CONSENSUS_WEIGHT = 2.0
MIN_PARTICIPATION = 3

INDICATOR_WEIGHTS = {
    'ma_crossover': 1.0,      # Вес пересечения MA/EMA
    'macd': 1.0,              # Вес MACD
    'stochastic': 1.0,        # Вес Stochastic
    'obv': 1.0,               # Вес OBV тренда
    'position_filter': 1.0    # Вес фильтра позиции
}

# ===== ДИАПАЗОН ДЛЯ БЛОКИРОВКИ ВБЛИЗИ ЭКСТРЕМУМОВ И УРОВНЕЙ ======
ATR_MULTIPLIER = 1        # множитель ATR для зоны блокировки (0.5 = узко, 1.5 = широко)
EXTREME_WINDOW = 60     # количество свечей для поиска локальных экстремумов