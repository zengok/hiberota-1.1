#!/usr/bin/env sh
set -eu

ssh_port="${SSH_PORT:-22}"
admin_cidr="${ADMIN_SSH_CIDR:-}"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root on the production host." >&2
    exit 1
fi

if [ -z "${admin_cidr}" ]; then
    echo "Set ADMIN_SSH_CIDR to the approved admin IP, VPN CIDR, or bastion CIDR before running." >&2
    exit 1
fi

dnf -y install firewalld fail2ban
systemctl enable --now firewalld

install -m 0644 ops/host-hardening/sshd_hiberota.conf /etc/ssh/sshd_config.d/50-hiberota-hardening.conf
sshd -t

firewall-cmd --permanent --remove-service=ssh >/dev/null 2>&1 || true
firewall-cmd --permanent --add-rich-rule="rule family=\"ipv4\" source address=\"${admin_cidr}\" port port=\"${ssh_port}\" protocol=\"tcp\" accept"
firewall-cmd --permanent --add-rich-rule="rule family=\"ipv6\" source address=\"${admin_cidr}\" port port=\"${ssh_port}\" protocol=\"tcp\" accept" >/dev/null 2>&1 || true
firewall-cmd --reload

install -d -m 0755 /etc/fail2ban/jail.d
install -m 0644 ops/fail2ban/jail.d/hiberota-sshd.conf /etc/fail2ban/jail.d/hiberota-sshd.conf
systemctl enable --now fail2ban
systemctl reload sshd

firewall-cmd --list-all
fail2ban-client status sshd
