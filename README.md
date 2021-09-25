# PJATK cat guard
Bot do weryfikacji studentów.

## Oficjalna instalacja
[https://verify.kpostek.dev/](https://verify.kpostek.dev/)

## Instalacja
 - git clone https://github.com/kpostekk/pjatk-cat-guard
 - docker-compose up -d

## Zmienne konfiguracyjne
Można ustawić przez .env albo bezpośrednio w docker-compose.yml

 - DISCORD_TOKEN - token dla bota
 - MONGODB_URL - połączenie z Mongo
 - SENDGRID_APIKEY - klucz api dla sendgrid, gdzieś w kodzie jest również template id kiedyś zmienię
 - VERIFICATION_URL - podstawowy adres dla usługi webowej, powinien zawierać / na końcu
 - FAIL_REDIRECT - adres gdzie będzie redirect, jeżeli kod jest niepoprawny lub przestarzały
 - INVITATION - zaproszenie do discorda

## FAQ

### Czy ten bot jest stabilny?
Poniekąd

### Czy będzie miał update'y?
Tak

### Czy potrzebuję dockera?
Nie, ale łatwiej z dockerem.

### Czy RODO costam costam
Nie, nie trzymamy danych osobistych
