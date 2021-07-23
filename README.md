## Скачать записи университета
```bash
python download.py <id> <year_from> <year_to>
```
Необязательные аргументы:
- `--secret SECRET`  
Путь к файлу secret.json  
По умолчанию ищется в папке со скриптом
- `-l LOG`  
Лог-файл  
Значение по умолчанию: record.log
- `-o OUT`  
Куда сохранять результаты запроса  
Значение по умолчанию: out.txt

*Для доступа к api необходимо заполнить secret.json*
```json
{
  "ApiKey": "",
  "InstToken": ""
}
```
## Генерация Excel-файла
```bash
python generate.py <template> <id> \
      --fractions out.txt \
      --publications Publications.csv
```
- `--fractions FRACTIONS`  
Файл, сгенерированный download.py
- `--publications PUBLICATIONS`  
csv-файл, копируемый на лист 'публикации'

Необязательные агрументы:
- `-o OUT`  
Куда сохранять excel-файл  
