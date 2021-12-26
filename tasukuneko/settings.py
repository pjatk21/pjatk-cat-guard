import os
from dotenv import load_dotenv

load_dotenv()

broker_url = os.getenv('REDIS')
result_backend = os.getenv('REDIS')
# result_backend = 'db+' + os.getenv('MONGODB_URL')
# result_backend = 'db+sqlite:///results.db'
# include = 'tasukuneko.tasks.bruh',
