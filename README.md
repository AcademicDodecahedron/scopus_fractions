Скачать записи из api:
```bash
python download.py <id> <year_from> <year_to> \
  --secret secret.json \
  --log record.log \
  -o out.txt
```
В аргумент secret передать json-файл вида:
```json
{
  "ApiKey": "",
  "InstToken": ""
}
```
