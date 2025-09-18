import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuraciones de Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = str(os.getenv('TELEGRAM_CHAT_ID'))

print(f"Chat ID configurado: {TELEGRAM_CHAT_ID}")

# Imprimir configuración al iniciar (quitar en producción)
print("Configuración cargada:")
print(f"TELEGRAM_BOT_TOKEN: {'Configurado' if TELEGRAM_BOT_TOKEN else 'No configurado'}")
print(f"TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID if TELEGRAM_CHAT_ID else 'No configurado'}")
