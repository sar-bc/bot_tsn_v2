import pandas as pd
from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Определяем базовый класс для моделей
Base = declarative_base()


# Определяем модель для таблицы Users
class Users(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ls = Column(Integer, nullable=False, unique=True)
    home = Column(Integer, nullable=False)
    kv = Column(Integer, nullable=False)
    address = Column(Text)


# Создаем соединение с базой данных
DATABASE_URL = 'sqlite:///../mydatabase.db'  # Замените на вашу строку подключения
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def add_data_from_csv(file_path):
    # Читаем данные из CSV-файла
    df = pd.read_csv(file_path)

    # Выводим заголовки для отладки
    print("Заголовки столбцов:", df.columns.tolist())

    # Создаем сессию
    with Session() as session:
        for index, row in df.iterrows():
            try:
                # user = Users(
                #     ls=row['ls'],
                #     home=row['home'],
                #     kv=row['kv'],
                #     address=row.get('address')
                # )
                # session.add(user)
                print(f"ls:{row['ls']};home:{row['home']};kv:{row['kv']};address:{row['address']}")
            except KeyError as e:
                print(f"Ошибка: отсутствует столбец {e}")

    # Сохраняем изменения в базе данных
    session.commit()


# Пример использования
if __name__ == "__main__":
    # Создаем таблицы в базе данных
    Base.metadata.create_all(engine)

    # Путь к вашему CSV-файлу
    csv_file_path = 'Users_home7.csv'  # Замените на путь к вашему файлу
    add_data_from_csv(csv_file_path)
    print("Данные успешно добавлены в таблицу Users.")
