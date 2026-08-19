#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${GITHUB_WORKSPACE}"
BENCH_ROOT="${RUNNER_TEMP}/frappe-bench"
python -m pip install frappe-bench
bench init --skip-assets --frappe-branch v15.35.0 "${BENCH_ROOT}"
cd "${BENCH_ROOT}"
bench get-app --branch v15.22.2 erpnext https://github.com/frappe/erpnext
ln -s "${APP_ROOT}" apps/dar_quraan
./env/bin/pip install --quiet --editable apps/erpnext --editable apps/dar_quraan
bench new-site test_site --db-root-password root --admin-password admin --no-mariadb-socket
bench --site test_site install-app erpnext
bench --site test_site install-app dar_quraan
bench --site test_site migrate
bench --site test_site run-tests --app dar_quraan
