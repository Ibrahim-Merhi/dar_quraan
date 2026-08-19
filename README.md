# Dar Quraan

A complete Quran institute management application for Frappe and ERPNext.

Developed and maintained by **Ibrahim Merhi**

Email: **ibrahim.m.merhy@gmail.com**

## Compatibility

This release targets Frappe/ERPNext version 15 and is prepared for:

| Component | Supported target |
|---|---|
| Frappe | 15.35.0 or newer version-15 release |
| ERPNext | 15.22.2 or newer version-15 release |
| Python | 3.10–3.12 |
| MariaDB | 10.6 or a version supported by Frappe 15 |

The app does not import ERPNext internals, but it is designed to run inside an ERPNext v15 bench.

## Installation

From the target bench:

```bash
cd ~/frappe-bench
bench get-app https://github.com/Ibrahim-Merhi/dar_quraan.git --branch develop
bench --site erp.itihad.org install-app dar_quraan
bench --site erp.itihad.org migrate
bench build --app dar_quraan
bench --site erp.itihad.org clear-cache
bench restart
```

Verify the installation:

```bash
bench version
bench --site erp.itihad.org list-apps
bench --site erp.itihad.org run-tests --app dar_quraan
```

After installation, **Dar Quraan** appears in Installed Applications with **Ibrahim Merhi** as its publisher. Roles, standard permissions, workspace, dashboard charts, KPI cards, reports, translations, and the user guide are shipped with the app.

## Updating

```bash
cd ~/frappe-bench
bench update --apps dar_quraan
bench --site erp.itihad.org migrate
bench build --app dar_quraan
bench --site erp.itihad.org clear-cache
bench restart
```

## Documentation

- [Role-based user guide](docs/user-guide.md)
- [Student lifecycle](docs/student-lifecycle.md)
- [Release checklist](docs/release-checklist.md)

## Development

Install and run the configured checks:

```bash
cd apps/dar_quraan
pre-commit install
pre-commit run --all-files
cd ../..
bench --site your-site run-tests --app dar_quraan
```

## License

MIT
