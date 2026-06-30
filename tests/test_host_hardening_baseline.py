from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sshd_hardening_disables_root_and_password_login() -> None:
    sshd = (ROOT / "ops/host-hardening/sshd_hiberota.conf").read_text()

    assert "PermitRootLogin no" in sshd
    assert "PasswordAuthentication no" in sshd
    assert "KbdInteractiveAuthentication no" in sshd
    assert "PubkeyAuthentication yes" in sshd
    assert "AuthenticationMethods publickey" in sshd


def test_fail2ban_sshd_jail_is_enabled() -> None:
    jail = (ROOT / "ops/fail2ban/jail.d/hiberota-sshd.conf").read_text()

    assert "[sshd]" in jail
    assert "enabled = true" in jail
    assert "backend = systemd" in jail
    assert "maxretry = 5" in jail
    assert "bantime = 1h" in jail


def test_almalinux_baseline_requires_runtime_admin_cidr_and_configures_firewalld() -> None:
    script = (ROOT / "ops/host-hardening/almalinux9-baseline.sh").read_text()

    assert "ADMIN_SSH_CIDR" in script
    assert "Set ADMIN_SSH_CIDR" in script
    assert "dnf -y install firewalld fail2ban" in script
    assert "systemctl enable --now firewalld" in script
    assert "--remove-service=ssh" in script
    assert "firewall-cmd --permanent --add-rich-rule" in script
    assert "systemctl enable --now fail2ban" in script
    assert "sshd -t" in script
