## Przetwarzanie danych

### Jakie dane zbieramy?

Na potrzeby weryfikacji, zbieramy takie dane jak:

- ID użytkownika Discord
- ID serwera Discord
- Numer studencki
- Imię i nazwisko
- Email w ramach domeny pjwstk.edu.pl
- Data rejestracji
- (Opcjonalnie) Ocenzurowane zdjęcia legitymacji studenckiej lub innych dokumentów potwierdzających bycie studentem PJATK

### Po co zbieramy te dane?

- Potwierdzenie tożsamości
- Zapobieganie podszywania się pod studentów

## Przekazywanie danych do usług zewnętrznych

W przypadku wystąpienia błędu, przekazujemy dane diagnostyczne do usługi Sentry

- ID użytkownika
- ID wywołania komendy

## Usuwanie danych

Wraz z wywołaniem komendy `/manage sign-out` zostają usunięte wszystkie dane
