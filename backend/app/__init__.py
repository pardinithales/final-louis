# Arquivo app/__init__.py

# Este arquivo pode estar vazio, ele serve para indicar ao Python
# que o diretório 'app' deve ser tratado como um pacote.
import logging

# Configuração básica do logging para o pacote app
# É uma boa prática configurar o logging o mais cedo possível.
# No entanto, a configuração principal pode ser feita em main.py
# para garantir que ela seja aplicada quando a aplicação rodar.
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')