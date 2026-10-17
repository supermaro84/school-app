# School App – Component Specification

This document describes the components of the School App (Django project in `school_app/`).
Each section has two parts:

- **Current behaviour**: what the code does today.
- **Gaps / open questions**: places where the code and the intended design may not match yet, to be resolved as the spec matures.

Components:

1. [Users](#1-users)
2. Groups – *TODO*
3. Announcements – *TODO*
4. Events / Calendar – *TODO*
5. Messages – *TODO*
6. Media (images & documents) – *TODO*
7. Landing / Dashboard – *TODO*
8. [Theme and layout](#8-theme-and-layout)

---

## 1. Users

### 1.1 Overview

A user is a person with a login to the app: an administrator, a teacher, a student, or a guardian (parent). Users are built from two layers:

| Layer | Model | Source | Purpose |
|---|---|---|---|
| Identity & authentication | `django.contrib.auth.models.User` | Django built-in | username, password, first/last name, email, `is_staff`, `is_superuser`, `is_active` |
| School profile | `accounts.UserProfile` | `accounts/models.py` | birthdate, phone, role, affiliated users |

Every `User` has exactly one `UserProfile` (`user.profile`). A `post_save` signal on `User` creates it automatically, so code can assume it exists.

### 1.2 Data model

#### `User` (Django built-in)

| Field | Required | Notes |
|---|---|---|
| `username` | yes | Unique login name |
| `password` | yes | Hashed; Django password validators apply |
| `first_name`, `last_name` | required at sign-up | |
| `email` | required at sign-up | Used for password reset |
| `is_staff` | – | Gives access to Django admin (`/admin/`) |
| `is_superuser` | – | All permissions in Django admin |
| `is_active` | – | Inactive users cannot log in |

#### `UserProfile` (`accounts/models.py`)

| Field | Type | Notes |
|---|---|---|
| `user` | OneToOne → `User` | `related_name="profile"`, cascade delete |
| `birthdate` | Date, optional | Used to compute `age` |
| `phone_number` | Char(15), optional | |
| `user_role` | FK → `UserRoles`, optional | `SET_NULL` on role deletion |
| `affiliated_users` | M2M → `User` | Users whose content this user can see (see 1.4) |

Derived properties:

| Property | Returns |
|---|---|
| `age` | Age in whole years from `birthdate`, or `None` |
| `affiliated_usernames` | Comma-separated usernames of affiliated users |
| `user_and_affiliated_usernames` | List of `User` objects: the user followed by their affiliated users (despite the name, it returns users, not usernames) |
| `group_profiles` | `GroupProfile`s where the user is an admin or a member |

#### `UserRoles` (`accounts/models.py`)

A lookup table of role names. Default value: `"Guardian"`. The fixtures (`fixtures/userroles.json`) seed these roles:

| pk | Role |
|---|---|
| 1 | Admin |
| 2 | Teacher |
| 3 | Student |
| 4 | Guardian |

### 1.3 User roles

| Role | Who | Typical traits (from fixtures) | Intended capabilities |
|---|---|---|---|
| **Admin** | School / system administrator | `is_staff` and `is_superuser` | Manage users, roles, groups and all content; Django admin access |
| **Teacher** | Teaching staff | `is_staff`; admin of class groups | Create groups, announcements and events for their groups; message students and guardians |
| **Student** | Child enrolled in the school | Not staff; member of class groups; no phone | Read announcements and events for their groups; comment; message |
| **Guardian** | Parent or legal guardian | Not staff; affiliated with one or more students | See everything their affiliated students see; message teachers |

**Current behaviour:** the role is **descriptive only**. It is shown on the user list and user detail pages and can be used to filter the user list, but no view checks it to grant or deny access. What a user can do is decided by:

- authentication (`@login_required` on some views),
- group membership (admin/member of a `GroupProfile`),
- authorship (e.g. only the author sees Edit/Delete on an announcement),
- affiliations (see 1.4),
- Django's `is_staff` / `is_superuser` flags (Django admin only).

### 1.4 Affiliated users (guardian ↔ student)

`UserProfile.affiliated_users` links a user to other users whose information they may see. The main use is linking a guardian to their children.

**Semantics:** if user A has user B among their affiliated users, A sees the content that reaches B, as well as their own:

| Area | Behaviour |
|---|---|
| Announcements (`announcements_page`) | Shows every announcement that reaches the user **or** any affiliated user; each entry is labelled with which of those users it applies to |
| Events API (`/api/events/`) | Returns events involving the user or any affiliated user; the event title is suffixed with the username it applies to, e.g. `Field trip (emma_wilson)` |
| Landing page (`/`) | One tab per user (self + affiliated) with events in the next 2 days and a per-user event count |

**Direction:** the relation is one-way (stored on A's profile only); B does not automatically see A's content. The fixtures set links in both directions by hand, e.g.:

| User | Role | Affiliated with |
|---|---|---|
| emma_wilson | Student | lisa_thompson |
| james_anderson | Student | robert_davis |
| sophia_martinez | Student | lisa_thompson, robert_davis |
| lisa_thompson | Guardian | emma_wilson |
| robert_davis | Guardian | james_anderson, sophia_martinez |

Note that sophia_martinez lists lisa_thompson, but lisa_thompson does not list sophia_martinez, so the data is already asymmetric.

### 1.5 User lifecycle

| Stage | How | Details |
|---|---|---|
| **Sign-up** | `/signup/` (`landing.views.SignUpView`, `CustomUserCreationForm`) | Open to anyone. Collects username, first/last name, email, optional birthdate, password ×2. Creates `User` + `UserProfile` with birthdate. **No role and no affiliations are set.** Redirects to login with a success message. |
| **Bulk import** | `manage.py import_users <file.csv>` | Columns: `username, first_name, last_name, email, role`, optional `birthdate, phone_number, affiliated_users` (`;`-separated usernames). Each new user gets the temporary password `<username>-<6 random chars>` and `must_change_password=True`. Passwords go to `credentials.csv` (git-ignored). Optional `is_staff` / `is_superuser` columns (`yes`/`no`) grant Django admin access. Existing usernames are skipped; any other error rolls back the whole import. Example: `fixtures/users_import_example.csv`. |
| **Bulk group import** | `manage.py import_groups <file.csv>` | Columns: `name, description, admins, members` (`;`-separated usernames, which must already exist). Creates the `Group` and its `GroupProfile`. Existing group names are skipped; an unknown username rolls back the whole import. |
| **Event types & statuses import** | `manage.py import_event_options <file.csv>` | Columns: `kind` (`type` or `status`), `name`. Fills the `EventType` / `EventStatus` lookup tables that events require. Existing names (case-insensitive) are skipped; an unknown kind or empty name rolls back the whole import. |
| **Bulk event import** | `manage.py import_events <file.csv>` | Columns: `owner` (username), `name, description`, `type`, `status` (existing names), `start, end` (`YYYY-MM-DD HH:MM`, local time), `groups` (`;`-separated group names), `users` (`;`-separated usernames), optional `repeat_weekly_until` (`YYYY-MM-DD`) to create one event per week up to that date. The owner is always added to the users. An event with the same owner, name and start is skipped; any invalid value rolls back the whole import. Used for one-off events and for the weekly lesson timetable. |
| **Bulk announcement import** | `manage.py import_announcements <file.csv>` | Columns: `author, title, text` (HTML allowed), `groups` (`;`-separated group names), `users` (`;`-separated usernames), optional `pub_date` / `exp_date` (`YYYY-MM-DD [HH:MM]`). No groups and no users makes the announcement public. An announcement with the same author and title is skipped; an unknown author, group, user or bad date rolls back the whole import. |
| **Roles import** | `manage.py import_roles <file.csv>` | Column: `name`. Fills the `UserRoles` lookup table; run before `import_users`. Existing names (case-insensitive) are skipped. |
| **Test data sets** | `imports/load_imports.sh [en\|pl]` | One folder per language (`imports/en/`, `imports/pl/`) with `roles.csv`, `event_options.csv`, `users.csv`, `groups.csv`, `announcements.csv`, `events.csv` and `timetable.csv`. The script runs all imports for the chosen folder (default `en`) into the current database; temporary passwords go to `imports/<lang>/credentials.csv` (git-ignored). The Polish set has its own people and stores roles, event types and statuses in Polish. |
| **Forced password change** | `/password_change/` (`CustomPasswordChangeView`, `ForcePasswordChangeMiddleware`) | While `must_change_password` is set, every page except password change and logout redirects to `/password_change/`. A successful change clears the flag. |
| **Login** | `/login/` (`CustomLoginView`) | Username + password. Already logged-in users are redirected. Redirects to `/` on success. |
| **Logout** | `/logout/` (`CustomLogoutView`) | GET or POST; redirects to `/`. |
| **Password reset** | `/password_reset/` → `/reset/<uidb64>/<token>/` | Standard Django flow; in development, emails go to the console backend. |
| **Role & affiliation assignment** | Django admin / fixtures | No in-app UI. The `UserProfile` admin (`accounts/admin.py`) shows user, birthdate, age, phone. |
| **Deactivation / deletion** | Django admin | Deleting a `User` cascades to its profile, authored announcements, comments, messages, owned events and media. |

### 1.6 User-facing pages

| URL | View | Access | Description |
|---|---|---|---|
| `/users/` | `accounts.views.user_list` | Logged in | Paginated list of all users (5 per page), sorted by username. Search `q` matches username, first/last name, email. Filter `role` by role name. Shows a role badge. |
| `/users/<pk>/` | `accounts.views.user_detail` | Logged in | Username, birthdate, phone, role, affiliated usernames. |

### 1.7 Seed data

`load_fixtures.sh` resets the SQLite database and loads fixtures. The default login is `marek` / `marek` (Admin, superuser).

| Username | Role | Staff | Superuser |
|---|---|---|---|
| marek | Admin | ✓ | ✓ |
| sarah_johnson | Teacher | ✓ | |
| michael_chen | Teacher | ✓ | |
| maria_garcia | Teacher | ✓ | |
| david_miller | Teacher | ✓ | ✓ |
| jennifer_lee | Teacher | ✓ | |
| emma_wilson | Student | | |
| james_anderson | Student | | |
| sophia_martinez | Student | | |
| lisa_thompson | Guardian | | |
| robert_davis | Guardian | | |

### 1.8 Gaps / open questions

1. **Roles aren't enforced.** Decide which actions each role may do (e.g. may students create groups, announcements or events?) and enforce that in views, not only in templates.
2. **Default role.** Sign-up leaves `user_role` empty, though the model default suggests `"Guardian"`. Should a new user get a role, or wait for admin approval?
3. **Open sign-up.** Anyone can register. For a school app, consider invitation-only accounts or admin approval.
4. **Affiliation direction.** Should affiliations be symmetric, or strictly guardian → student? Should students see their guardians' content at all?
5. **Privacy.** Any logged-in user can list all users and see their birthdate, phone and affiliations. Visibility should probably depend on role and relationship.
6. **Missing login checks.** Several views lack `@login_required` / `LoginRequiredMixin`, including announcements, events API, calendar, messages, media, and the group create/edit views. Anonymous access to these currently fails or leaks data.
7. **No profile self-service.** Users can't edit their own profile (phone, birthdate) or change their password in the app.
8. **Two kinds of "admin".** `Admin` role, `is_staff`/`is_superuser` and group admin (`GroupProfile.admins`) are separate concepts; the spec should define how they relate.
9. **Small code issues:** `user_detail` raises a 500 for an unknown `pk` (use `get_object_or_404`); a comment in `user_list` says "15 per page" but the code uses 5; `user_and_affiliated_usernames` returns users, not usernames.

---

## 8. Theme and layout

### 8.1 Layout

| Part | Where | Behaviour |
|---|---|---|
| Page shell | `templates/base.html` | Sticky navbar (collapses into a menu below 1200 px), flash messages, page content in a centred container, footer. Pages scroll normally. |
| Shared `<head>` | `templates/includes/head.html` | Bootstrap 5.3, Bootstrap Icons, `static/css/app.css` and the theme's CSS variables. |
| Auth pages | `templates/auth_base.html` | Login, sign-up and password pages: a centred card with brand and language switcher. |
| List and detail pages | Announcements, Messages, Groups | List (left) and detail (right) side by side on large screens, each scrolling on its own. On phones, list pages show only the list and detail pages only the detail, with a Back link (`list_visibility` / `detail_visibility` blocks). |
| Calendar | `events/templates/calendar.html` | Month view with a side panel on desktop; list view below 768 px; the panel appears under the calendar on phones. |
| Styles | `static/css/app.css` | All app styles; templates use Bootstrap classes and avoid inline styles. |

### 8.2 Deployment theme

Each deployment sets its look with environment variables (in `.env`; documented in `.env.example`). Nothing is stored in the database; restart the app after a change. `school_app/theme.py` reads them once at startup into `settings.THEME`, and the `theme` context processor gives every template `theme`, `app_name` and `nav_section`.

| Variable | Values | Default |
|---|---|---|
| `APP_NAME` | Any text, shown as entered | "School App", translated |
| `THEME_PRESET` | `default`, `ocean`, `forest`, `sunset`, `plum` | `default` |
| `THEME_PRIMARY_COLOR`, `THEME_SECONDARY_COLOR` | Hex colour (`#2563eb`, `#26e`) | From the preset |
| `THEME_NAVBAR` | `dark`, `light`, `primary` | `dark` |
| `THEME_MODE` | `auto` (follows the device), `light`, `dark`: the default before a viewer picks one with the theme toggle | `auto` |
| `THEME_LOGO_URL`, `THEME_FAVICON_URL` | URL | Graduation cap icon |
| `THEME_FOOTER_TEXT` | Any text | "© year app name. All rights reserved." |

- Colours are mapped onto Bootstrap's CSS variables (buttons, links, badges, form focus, pagination, calendar), so the whole app follows the primary colour.
- Text on primary-coloured surfaces turns dark or white depending on the colour's contrast.
- Invalid values fall back to the default and log a warning at startup.
- The theme toggle (sun / moon / half-circle button in the navbar and on the auth pages) lets each viewer choose Light, Dark or System. The choice is saved in the browser (`localStorage`, key `theme-mode`) and applied before the page is drawn; System follows the device and changes with it.
- For production, run `manage.py collectstatic` (files go to `STATIC_ROOT`, `school_app/staticfiles/`, git-ignored) and serve them from the web server.

