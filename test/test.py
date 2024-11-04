import csv
from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from database.models import Users

# Настроим логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Создаем соединение с базой данных
DATABASE_URL = 'sqlite:///../db.sqlite3'  # Замените на вашу строку подключения
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def add_data_from_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=';')  # Используем DictReader для удобного доступа к полям

        # Создаем сессию для добавления данных
        with Session() as session:
            for row in reader:
                # Проверяем, что все необходимые поля присутствуют
                if 'ls' in row and 'home' in row and 'kv' in row and 'address' in row:
                    # Создаем объект Users для каждой строки
                    user = Users(
                        ls=int(row['ls']),
                        home=int(row['home']),
                        kv=int(row['kv']),
                        address=row['address']
                    )
                    session.add(user)  # Добавляем пользователя в сессию
                else:
                    logger.error("Ошибка в строке: %s. Все поля должны быть заполнены.", row)

            # Сохраняем изменения в базе данных
            session.commit()
            logger.info("Данные успешно добавлены в таблицу Users.")


if __name__ == "__main__":
    # Пример использования
    csv_file_path = 'Users_home7.csv'  # Замените на путь к вашему файлу
    add_data_from_csv(csv_file_path)
