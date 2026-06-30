#!/usr/bin/env sh
set -eu

output_dir="${1:-nginx/generated}"
real_ip_file="${output_dir}/cloudflare-real-ip.conf"
allow_file="${output_dir}/cloudflare-origin-allow.conf"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

mkdir -p "${output_dir}"

curl -fsS https://www.cloudflare.com/ips-v4 -o "${tmp_dir}/ips-v4"
curl -fsS https://www.cloudflare.com/ips-v6 -o "${tmp_dir}/ips-v6"
cat "${tmp_dir}/ips-v4" "${tmp_dir}/ips-v6" | sed '/^[[:space:]]*$/d' > "${tmp_dir}/ips"

{
    echo "# Generated from Cloudflare published IP ranges. Do not edit by hand."
    echo "# Source: https://www.cloudflare.com/ips/"
    while IFS= read -r cidr; do
        echo "set_real_ip_from ${cidr};"
    done < "${tmp_dir}/ips"
    echo "real_ip_header CF-Connecting-IP;"
    echo "real_ip_recursive on;"
} > "${real_ip_file}"

{
    echo "# Generated from Cloudflare published IP ranges. Do not edit by hand."
    echo "# Source: https://www.cloudflare.com/ips/"
    while IFS= read -r cidr; do
        echo "allow ${cidr};"
    done < "${tmp_dir}/ips"
    echo "deny all;"
} > "${allow_file}"

printf '%s\n' "${real_ip_file}"
printf '%s\n' "${allow_file}"
