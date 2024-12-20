import os
import sys

# 添加项目根目录到Python路径
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

try:
    application = get_wsgi_application()
except Exception as e:
    print(f"Error loading application: {e}")
    raise
