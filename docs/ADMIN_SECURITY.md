# Admin Security

HibeRota public kullanıcı hesabı oluşturmaz. Yönetici erişimi yalnızca Django staff hesapları içindir.

## TOTP 2FA

Admin login formu `apps.security.forms.SecureAdminAuthenticationForm` ile genişletilir ve staff kullanıcıdan parola sonrası 6 haneli TOTP kodu ister.

TOTP cihazı runtime komutu ile oluşturulur:

```sh
python manage.py provision_admin_totp <staff-username>
```

Mevcut cihazı döndürmek için:

```sh
python manage.py provision_admin_totp <staff-username> --rotate
```

Komut otpauth URI üretir. Bu değer secret içerdiği için yalnızca güvenli kanaldan ilgili staff kullanıcıya iletilir; repoya veya log toplama sistemine yazılmaz.

## Brute-force koruması

Admin login denemeleri IP + kullanıcı adı parmak izi ile cache üzerinde izlenir.

Varsayılanlar:

- `ADMIN_LOGIN_RATE_LIMIT_ATTEMPTS=5`
- `ADMIN_LOGIN_RATE_LIMIT_WINDOW_SECONDS=300`
- `ADMIN_LOGIN_RATE_LIMIT_LOCKOUT_SECONDS=900`

Hata mesajları generic tutulur; parola, kullanıcı varlığı veya TOTP durumu ayrıştırılamaz.

## Acil erişim

`ADMIN_TOTP_REQUIRED=false` yalnızca kontrollü acil erişim penceresinde kullanılabilir. Olay sonrası tekrar `true` yapılmalı, ilgili admin secretları rotate edilmeli ve oturumlar incelenmelidir.
