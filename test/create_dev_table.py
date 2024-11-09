import csv


def read_file(file_path, output_file_path):
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        rows = csv.reader(csv_file, delimiter=';')
        if next(rows) != ['ls', 'home', 'kv', 'address']:
            print("Неверные заголовки файла")
            return False

        # Открываем выходной файл для записи
        with open(output_file_path, 'w', encoding='utf-8', newline='') as output_file:
            writer = csv.writer(output_file, delimiter=';')

            for row in rows:
                ls, home, kv, address = row
                # Записываем данные в формате ls;hv
                writer.writerow([ls, '', '', '', '', 'hv'])
                # Записываем данные в формате ls;gv
                writer.writerow([ls, '', '', '', '', 'gv'])
                # Записываем данные в формате ls;e
                writer.writerow([ls, '', '', '', '', 'e'])

    print(f"Данные успешно записаны в файл {output_file_path}")


# Пример использования
if __name__ == "__main__":
    input_file_path = 'Users_home7.csv'  # Путь к вашему входному файлу
    output_file_path = 'output.csv'  # Путь к выходному файлу
    read_file(input_file_path, output_file_path)
