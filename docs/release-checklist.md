# Dar Quraan release checklist

## Before deployment

- [ ] Back up the database and public/private files and verify restoration.
- [ ] Confirm compatible Frappe and ERPNext version-15 releases.
- [ ] Run `pre-commit run --all-files` and `bench --site SITE run-tests --app dar_quraan`.
- [ ] Confirm outgoing email, Redis, workers, and scheduler are healthy.

## Staging and user acceptance

- [ ] Migrate staging and test Manager, Supervisor, Teacher, Data Entry, and Viewer access.
- [ ] Complete the student flow from registration through next assignment.
- [ ] Test supervision, follow-ups, exception creation, and one test email.
- [ ] Validate all four analytics reports with known data.
- [ ] Review desktop/mobile layouts, printing, and exports with institute users.
- [ ] Obtain business-owner approval.

## Production

- [ ] Schedule a maintenance window and take a fresh verified backup.
- [ ] Deploy the exact approved commit/tag and run `bench --site SITE migrate`.
- [ ] Clear cache, restart processes, and repeat critical smoke tests.
- [ ] Monitor web, workers, scheduler, database, Redis, and email logs.

## Rollback

Stop writes, restore the pre-deployment database and files, restore the previous application commit, migrate, restart, and document the incident.
