# Host Hardening Baseline

Bu belge AlmaLinux 9 production host için SSH key-only, root login kapalı, firewall ve fail2ban iskeletini tarif eder. Gerçek yönetici IP/CIDR, SSH public key veya bastion bilgisi repoya yazılmaz.

## Dosyalar

- `ops/host-hardening/sshd_hiberota.conf`
- `ops/fail2ban/jail.d/hiberota-sshd.conf`
- `ops/host-hardening/almalinux9-baseline.sh`

## Uygulama öncesi

- En az bir sudo yetkili deployment kullanıcısı açılmış olmalı.
- Bu kullanıcının SSH public key erişimi ayrı bir güvenli kanaldan host üzerinde doğrulanmalı.
- Aktif bir ikinci SSH oturumu açık tutulmalı.
- `ADMIN_SSH_CIDR` gerçek sabit admin IP, VPN CIDR veya bastion CIDR olarak runtime ortamında verilmeli.

## Referans uygulama

```sh
sudo ADMIN_SSH_CIDR="203.0.113.10/32" SSH_PORT="22" ops/host-hardening/almalinux9-baseline.sh
```

Örnek CIDR dokümantasyon amaçlıdır; production değeri repoya yazılmaz.

## Beklenen sonuç

- `PermitRootLogin no`
- `PasswordAuthentication no`
- `AuthenticationMethods publickey`
- firewalld aktif
- SSH yalnızca onaylı admin/VPN/bastion CIDR üzerinden açık
- fail2ban `sshd` jail aktif

## Doğrulama

- `sshd -t`
- Yeni SSH oturumu key ile başarılı
- Root ile SSH reddedilir
- Parola ile SSH reddedilir
- `firewall-cmd --list-all`
- `fail2ban-client status sshd`

## Rollback

Aktif oturumu kapatmadan önce:

```sh
sudo rm -f /etc/ssh/sshd_config.d/50-hiberota-hardening.conf
sudo sshd -t
sudo systemctl reload sshd
```

Firewall rollback, yalnızca olay müdahalesi veya erişim kaybı durumunda onaylı yönetici tarafından yapılır.
