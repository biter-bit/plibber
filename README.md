Инструкция по запуску:

1. Клонировать репозиторий к себе на локальную машину.
2. Установить python и его зависимости: pip install -r requirements.txt.
3. Запустить на локально машине бд mongodb с портом 27017.
4. В папку data добавить 2 файла: accounts_data.txt, proxys_data.txt. Это файлы, в которых будут хранится токены вк и прокси сервера
5. Добавить в accounts_data.txt токены в формате: <>:<>:<токен>. Каждый токен должен начинаться с новой строки
6. Добавить в proxys.txt прокси сервера в формате: <логин>:<пароль>@<ip>:<port>.
7. В корень проекта добавить файл .env и добавить в него инструкции так, как описано в файле environ.txt
8. Запустить проект командой: python -m runner.py
