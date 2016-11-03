import os

abs_cwd = os.path.join(os.getcwd(), os.path.dirname("downloads"))
print(abs_cwd)
print(os.getcwd())
print(os.path.dirname(__file__))
