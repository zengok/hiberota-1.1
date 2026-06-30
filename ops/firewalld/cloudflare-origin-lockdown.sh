#!/usr/bin/env sh
set -eu

zone="${1:-public}"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root on the production host." >&2
    exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

curl -fsS https://www.cloudflare.com/ips-v4 -o "${tmp_dir}/ips-v4"
curl -fsS https://www.cloudflare.com/ips-v6 -o "${tmp_dir}/ips-v6"
cat "${tmp_dir}/ips-v4" "${tmp_dir}/ips-v6" | sed '/^[[:space:]]*$/d' > "${tmp_dir}/ips"

firewall-cmd --permanent --zone="${zone}" --remove-service=http >/dev/null 2>&1 || true
firewall-cmd --permanent --zone="${zone}" --remove-service=https >/dev/null 2>&1 || true
firewall-cmd --permanent --zone="${zone}" --remove-port=80/tcp >/dev/null 2>&1 || true
firewall-cmd --permanent --zone="${zone}" --remove-port=443/tcp >/dev/null 2>&1 || true

while IFS= read -r cidr; do
    firewall-cmd --permanent --zone="${zone}" --add-rich-rule="rule family=\"ipv4\" source address=\"${cidr}\" port port=\"80\" protocol=\"tcp\" accept" >/dev/null 2>&1 || true
    firewall-cmd --permanent --zone="${zone}" --add-rich-rule="rule family=\"ipv4\" source address=\"${cidr}\" port port=\"443\" protocol=\"tcp\" accept" >/dev/null 2>&1 || true
done < "${tmp_dir}/ips-v4"

while IFS= read -r cidr; do
    firewall-cmd --permanent --zone="${zone}" --add-rich-rule="rule family=\"ipv6\" source address=\"${cidr}\" port port=\"80\" protocol=\"tcp\" accept" >/dev/null 2>&1 || true
    firewall-cmd --permanent --zone="${zone}" --add-rich-rule="rule family=\"ipv6\" source address=\"${cidr}\" port port=\"443\" protocol=\"tcp\" accept" >/dev/null 2>&1 || true
done < "${tmp_dir}/ips-v6"

firewall-cmd --reload
firewall-cmd --zone="${zone}" --list-rich-rules
