# TODO

- [ ] **Password reset emails are not sent.** `EMAIL_BACKEND` is the console
  backend (`school_app/school_app/settings.py`), so reset links only appear in
  the server log (`journalctl -u school-app`). Configure a real email service
  (SMTP settings from `.env`, e.g. a transactional provider) and a
  `DEFAULT_FROM_EMAIL`. Until then, reset passwords from the Django admin.
