import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = os.path.join(BASE_DIR, "static")

print(BASE_DIR)
print(STATIC_ROOT)
print(os.path.abspath(__file__))