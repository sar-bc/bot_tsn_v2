import zipfile
import os
import xml.etree.ElementTree as ET


def parse_mxl(file_path):
    # Распаковываем .mxl файл
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall('extracted')  # Извлекаем содержимое в папку 'extracted'


if __name__ == "__main__":
    mxl_file_path = 'Отчет по лицевым счетам на 30.11.2024 г. ТСН Звездный-7.mxl'  # Замените на путь к вашему файлу .mxl
    parse_mxl(mxl_file_path)
