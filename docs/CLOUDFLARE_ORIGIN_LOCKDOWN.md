# Cloudflare Origin Lockdown

Bu görev production deploy yapmaz. Amaç, origin sunucuya 80/443 erişiminin yalnızca Cloudflare IP aralıklarından kabul edilmesi için uygulanabilir iskeleti repoda tutmaktır.

## Nginx

Production Nginx template:

- `nginx/default.cloudflare.conf`

Bu template yalnızca Cloudflare kaynaklı isteklere izin veren generated include dosyalarını bekler:

- `/etc/nginx/cloudflare/cloudflare-real-ip.conf`
- `/etc/nginx/cloudflare/cloudflare-origin-allow.conf`

Include dosyaları deploy sırasında resmi Cloudflare IP endpointlerinden üretilir:

```sh
ops/cloudflare/generate-nginx-cloudflare-allowlist.sh nginx/generated
```

Production compose veya host mount aşamasında `nginx/generated` içeriği `/etc/nginx/cloudflare/` altına read-only bağlanır. Local `nginx/default.conf` geliştirme için açık kalır.

## Host firewall

AlmaLinux/firewalld için referans script:

```sh
sudo ops/firewalld/cloudflare-origin-lockdown.sh public
```

Script Cloudflare IPv4/IPv6 listelerini resmi endpointlerden alır, public 80/443 servis/port açılışlarını kaldırır ve yalnızca Cloudflare CIDR aralıklarına rich rule ekler.

## Doğrulama

- Cloudflare proxy üzerinden site 200 dönmeli.
- Origin IP adresine doğrudan 80/443 erişim reddedilmeli.
- Django loglarında client IP Cloudflare adresi yerine gerçek ziyaretçi IP'sine dönmeli.
- `/health/` endpointleri Cloudflare üzerinden çalışmalı, origin doğrudan açık olmamalı.

## Operasyon notları

- Cloudflare IP listeleri zamanla değişebilir; deploy ve bakım sırasında generated dosyalar yenilenmelidir.
- Scriptler API token, zone ID, account ID veya gerçek origin IP değeri kullanmaz.
- SSH kısıtlaması, fail2ban ve genel firewall hardening ayrı Faz 7 maddesidir.
