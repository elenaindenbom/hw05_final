# Yatube

Блог на Django с чтением и записью в БД(Django ORM).
Реализована возможность регистрации, авторизации и смены пароля. Разработан основной функционал: создание собственной страницы, добавление постов с картинками, их редактирование и удаление. Добавлены группы постов, комментарии и подписки на других пользователей. Реализована возможность выводить в ленту посты отдельных групп, авторов, на которых подписан пользователь, посты пользователя. Осуществлено покрытие тестами(Unittest).

---
### _Запуск проекта в dev-режиме_

* Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:elenaindenbom/hp05_final.git
```
* Перейти в папку с проектом:
```
cd yatube
```
* Создать и активировать виртуальное окружение

для Linux или MacOS:
```
python3 -m venv venv
```
```
source venv/bin/activate
```
для Windows:
```
python -m venv venv
```
```
source venv/Script/activate
```
* Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
* Перейти в папку yatube и выполнить миграции:
```
cd yatube
python3 manage.py migrate
```
* Создать суперюзера: 
```
python3 manage.py createsuperuser.
```
* Запустить проект:
```
python3 manage.py runserver
```

_*  в Windows вместо команды "python3" использовать "python"_

---
### _Автор проекта:_
Инденбом Елена 
