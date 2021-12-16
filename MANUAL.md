# Manual

## Rejestracja

Bot po wykryciu nowego członka na serwerze wyśle mu link do wykonania weryfikacji.
Jeżeli użytkownik ma zablokowane DM, będzie mógł wykonać komendę `/verify`.

W przypadku gdy użytkownik będzie chciał się wyrejestrować, może wywołać komendę `/manage sign-out`.

## Archiwum

Bot daje możliwość archiwizowania plików i ułatwionego ich wyszukiwania. Domyślnie bot **nie** indeksuje wszystkich plików.
Żeby zindeksować plik, trzeba dodać do wiadomości reakcję `:dividers:` `🗂`. Bot wtedy hashuje plik i przesyła go do Apache Tika OCR.

Pliki można otagować odpowiadając, na wiadomość z plikiem, `tags: <tagi odzielone spacją>`.
![Przykładowe tagowanie](https://github.com/pjatk21/pjatk-cat-guard/blob/main/.github/tagging.png?raw=true)

Zindeksowane pliki można przeglądać przy użyciu komendy `/arc search <zapytanie>`.
Wyszukuje się pliki według:
 - Nazwa (zawiera zapytanie)
 - Hash pliku (zaczyna się zapytaniem)
 - Type mime (jest równy zapytaniu)
 - Tagi (zapytanie jest równe dowolnemu tagowi)
 - Transkrypcja (zawiera zapytanie)
   - W przypadku dokumentów i zdjęć jest dokonywany OCR/data extraction
   - W przypadku archiwów ZIP uwzględnia się ścieżki i nazwy plików
 - Metadane (zawiera zapytanie)
