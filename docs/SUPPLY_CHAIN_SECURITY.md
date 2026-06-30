# Supply Chain Security

HibeRota dependency ve container taraması CI hattında bloklayıcı güvenlik kontrolü olarak çalışır.

## Python dependencies

Ana CI içinde:

```sh
bandit -r apps config automation
pip-audit
```

`pip-audit` yüksek/kritik Python dependency açıklarını yakalar. Yeni paket eklenirse gerekçe PR açıklamasında yazılır ve `requirements/*.txt` kapsamı kontrol edilir.

## Container image

Ana CI Docker image üretir ve Trivy ile tarar:

- image: `hiberota:ci`
- severity: `CRITICAL,HIGH`
- `ignore-unfixed: true`
- `exit-code: 1`

Bu yapı registry credential veya production image tag'i gerektirmez.

## Dependency review

Pull request'lerde GitHub Dependency Review çalışır:

- `fail-on-severity: high`
- GPL-3.0 ve AGPL-3.0 lisansları bloklanır

## Update cadence

Dependabot haftalık olarak şu ekosistemleri izler:

- pip
- Docker base image
- GitHub Actions

## Release gate

Production deploy öncesi şu kontroller yeşil olmalıdır:

- `pip-audit`
- Bandit
- Trivy container scan
- Dependency Review
- Secret scan

Yüksek veya kritik CVE, açıkça kabul edilmiş risk kaydı olmadan deployment'ı bloke eder.
