"""Manual UI checks: walk every screen and press every button that matters.

Run it by hand when the interface changes::

    python -m cleanhome.tests.ui.harness

The window needs a desktop. The unit suite in ``cleanhome/tests`` stays free
of Tkinter so it can run anywhere.
"""

from __future__ import annotations

import sys
import tempfile
import tkinter as tk
from datetime import date, datetime, time, timedelta
from pathlib import Path
from tkinter import messagebox

from cleanhome import config, db, security
from cleanhome.services import auth_service, booking_service, catalog_service
from cleanhome.ui import components
from cleanhome.ui.app import CleanHomeApp
from cleanhome.ui.pages.admin_customers import AddAdminDialog
from cleanhome.ui.pages.admin_promotions import PromoForm
from cleanhome.ui.pages.admin_services import ServiceForm

PASSWORD = "TestPass123"

failures: list[str] = []


def check(label: str, condition: bool, detail: object = "") -> None:
    if condition:
        print(f"  ok    {label}")
    else:
        failures.append(label)
        print(f"  FAIL  {label} {detail}")


def current_page(app: CleanHomeApp):
    app.update()
    return app.container.winfo_children()[0]


def find_button(root, text: str):
    """Find a button with this label anywhere under a widget."""
    for child in root.winfo_children():
        try:
            if child.winfo_class() in ("TButton", "Button") and child.cget("text") == text:
                return child
        except tk.TclError:
            pass
        found = find_button(child, text)
        if found is not None:
            return found
    return None


def find_dialogs(app: CleanHomeApp) -> list[tk.Toplevel]:
    """Every open Toplevel in the widget tree."""
    found: list[tk.Toplevel] = []

    def walk(widget) -> None:
        for child in widget.winfo_children():
            if isinstance(child, tk.Toplevel):
                found.append(child)
            walk(child)

    walk(app)
    return found


def click_button(app: CleanHomeApp, text: str) -> bool:
    """Press a button that lives in the top-most dialog."""
    for window in reversed(find_dialogs(app)):
        button = find_button(window, text)
        if button is not None:
            button.invoke()
            return True
    return False


def close_dialogs(app: CleanHomeApp) -> None:
    """Destroy anything that is still open, so a stuck dialog cannot hang."""
    for window in find_dialogs(app):
        try:
            window.destroy()
        except tk.TclError:
            pass


def select_row(page, row_id: int) -> bool:
    """Select the table row that belongs to this id."""
    for item in page.table.tree.get_children():
        values = page.table.tree.item(item, "values")
        if values and int(values[0]) == row_id:
            page.table.tree.selection_set(item)
            return True
    return False


def make_user(email: str, role: str, address: str = "", phone: str = "") -> None:
    salt, digest = security.hash_password(PASSWORD)
    db.execute(
        "INSERT INTO users (full_name, email, role, pw_salt, pw_hash, is_active, "
        "address, phone) VALUES (?, ?, ?, ?, ?, 1, ?, ?)",
        (email.split("@")[0].title(), email, role, salt, digest, address, phone),
    )


def fresh_database():
    """A throw-away database, so the checks never touch the real one."""
    folder = tempfile.TemporaryDirectory()
    config.DB_PATH = Path(folder.name) / "ui.db"
    db.close_connection()
    db.init_db()
    db.migrate()
    db.seed()
    return folder


def open_day(page, start: int = 4, days: int = 7) -> date | None:
    """Pick the first day in the next week that has open slots."""
    for offset in range(start, start + days):
        page.date_box.set_date(date.today() + timedelta(days=offset))
        page._load_slots()
        if page.slots:
            return page.date_box.get_date()
    return None


def check_first_run(app: CleanHomeApp) -> None:
    print("the first-run setup screen")
    app.go("Home")
    app.update()
    check("the app opens on the setup screen", app.current == "CreateAdmin", app.current)
    page = current_page(app)
    page.full_name.set("Setup Admin")
    page.email.set("admin@test.ph")
    page.password.set(PASSWORD)
    page.confirm.set(PASSWORD)
    page._create()
    app.update()
    check("the first admin was created", app.session.role == "admin", app.session.role)
    check("the admin lands on the dashboard", app.current == "AdminDashboard",
          app.current)

    app.session.sign_out()
    app.go("CreateAdmin")
    app.update()
    check("the setup screen refuses to reopen once an admin exists",
          app.current == "Login", app.current)


def check_components(app: CleanHomeApp) -> None:
    print("the reusable components")
    host = tk.Frame(app)
    host.pack()

    password = components.PasswordInput(host)
    password.pack()
    password.set("secret")
    check("a password starts hidden", password.cget("show") != "")
    password.toggle()
    check("the reveal toggle shows the text",
          password.revealed and password.cget("show") == "")
    password.toggle()
    check("the reveal toggle hides the text again", not password.revealed)

    pressed: list[bool] = []
    toggle = components.Toggle(host, command=lambda: pressed.append(True))
    toggle.pack()
    toggle._toggle()
    check("the toggle flips and calls back", bool(toggle.variable.get()) and pressed)

    box = components.CheckBox(host, text="Remember me")
    box.pack()
    box._toggle()
    check("the checkbox flips", bool(box.variable.get()))

    search = components.SearchBar(host, placeholder="Search", on_change=lambda value: None)
    search.pack()
    check("the search box starts empty", search.get() == "", search.get())
    search.set("abc")
    search.clear()
    check("clear empties the search box", search.get() == "", search.get())

    toast = components.Toast(app, app)
    toast.show("hello", "success")
    check("the toast appears", toast.winfo_manager() == "place")
    toast.hide()
    check("the toast hides", toast.winfo_manager() == "")

    host.destroy()


def check_every_screen(app: CleanHomeApp) -> None:
    print("every screen as guest")
    for name in ("Home", "Services", "Promotions", "About", "Contact", "Login", "Signup"):
        app.go(name)
        app.update()
        check(f"guest can open {name}", app.current == name, app.current)

    service_id = db.query_one("SELECT id FROM services WHERE is_active = 1 LIMIT 1")["id"]
    app.go("ServiceDetails", service_id=service_id)
    app.update()
    check("guest can open ServiceDetails", app.current == "ServiceDetails", app.current)

    app.go("Book")
    app.update()
    check("a guest is sent to the login page", app.current == "Login", app.current)

    print("every screen as admin")
    admin = auth_service.login("admin@test.ph", PASSWORD)
    app.sign_in(admin)
    app.update()
    for name in ("AdminDashboard", "AdminBookings", "AdminServices", "AdminPromotions",
                 "AdminCustomers", "AdminReports", "Profile", "ChangePassword",
                 "Home", "Services", "Promotions", "About", "Contact"):
        app.go(name)
        app.update()
        check(f"admin can open {name}", app.current == name, app.current)

    print("every screen as customer")
    app.session.sign_out()
    customer = auth_service.login("customer@test.ph", PASSWORD)
    app.sign_in(customer)
    app.update()
    for name in ("Book", "MyBookings", "Profile", "ChangePassword", "Home", "Services"):
        app.go(name)
        app.update()
        check(f"customer can open {name}", app.current == name, app.current)

    app.go("AdminDashboard")
    app.update()
    check("a customer is kept out of the admin pages", app.current == "Home", app.current)


def check_forced_password_change(app: CleanHomeApp) -> None:
    print("a generated password must be changed at first sign-in")
    make_user("forced@test.ph", "customer")
    db.execute("UPDATE users SET must_change_password = 1 WHERE email = ?",
               ("forced@test.ph",))
    app.session.sign_out()
    app.sign_in(auth_service.login("forced@test.ph", PASSWORD))
    app.update()
    check("the forced user is sent to ChangePassword",
          app.current == "ChangePassword", app.current)
    page = current_page(app)
    check("the forced screen hides the back link", page.forced)
    page.current.set(PASSWORD)
    page.new.set("ChangedPass456")
    page.confirm.set("ChangedPass456")
    page._update()
    app.update()
    check("the forced user reaches the home page after the change",
          app.current in ("Home", "MyBookings"), app.current)
    check("the flag is cleared", auth_service.login("forced@test.ph", "ChangedPass456")[
        "must_change_password"] is False)
    app.session.sign_out()


def check_dialogs(app: CleanHomeApp, admin) -> None:
    print("the admin dialogs")
    app.go("AdminPromotions")
    app.update()
    page = current_page(app)
    form = PromoForm(page, admin, None, lambda: None)
    app.update()
    check("the promotion form opens", form.winfo_exists())
    check("the promotion form fits on screen",
          0 < form.winfo_height() <= config.WINDOW_MIN_HEIGHT, form.winfo_height())
    check("the start date defaults to today", form.start_date.get_date() == date.today())
    check("the end date defaults a month out",
          form.end_date.get_date()
          == date.today() + timedelta(days=config.PROMO_DEFAULT_DAYS))
    form.title_field.set("UI Test Promo")
    form.value.set("10")
    form._submit()
    app.update()
    made = [p for p in catalog_service.list_promotions(active_only=False)
            if p["title"] == "UI Test Promo"]
    check("the promotion was saved", len(made) == 1, len(made))
    check("the promotion form closes after saving", not form.winfo_exists())
    if made:
        check("the saved start uses the picked date and time",
              made[0]["start_date"] == f"{date.today().isoformat()} 08:00:00",
              made[0]["start_date"])

    app.go("AdminServices")
    app.update()
    page = current_page(app)
    form = ServiceForm(page, admin, None, lambda: None)
    app.update()
    form.name.set("UI Test Service")
    form.description.set("Made by the harness")
    form.price.set("1500")
    form.duration.set("60")
    form._submit()
    app.update()
    made = [s for s in catalog_service.list_services(include_inactive=True)
            if s["name"] == "UI Test Service"]
    check("the service was saved", len(made) == 1, len(made))
    service = made[0] if made else None

    app.go("AdminCustomers")
    app.update()
    page = current_page(app)
    dialog = AddAdminDialog(page, admin, lambda: None)
    app.update()
    check("the add admin dialog opens", dialog.winfo_exists())
    dialog.close()
    app.update()

    if service:
        app.go("AdminServices")
        app.update()
        page = current_page(app)
        select_row(page, service["id"])
        page.active_toggle.variable.set(False)
        page._toggle()
        app.update()
        check("archiving asks for confirmation", len(find_dialogs(app)) == 1,
              len(find_dialogs(app)))
        click_button(app, "Archive")
        app.update()
        check("the service was archived",
              not catalog_service.get_service(service["id"])["is_active"])
        select_row(page, service["id"])
        page.active_toggle.variable.set(True)
        page._toggle()
        app.update()
        check("the service was restored",
              bool(catalog_service.get_service(service["id"])["is_active"]))


def check_booking_flow(app: CleanHomeApp, customer) -> None:
    print("the customer booking flow")
    app.go("Book")
    app.update()
    page = current_page(app)
    check("the service list is filled", len(page.service_map) > 0)

    day = open_day(page)
    check("slots are offered for a chosen day", day is not None, page.slots)
    if day is None:
        return
    page.time_var.set(page.time_box.cget("values")[0])
    page.address.set("12 Quezon Ave")
    page._update_quote()
    app.update()
    check("the price is quoted", "Total:" in page.total_label.cget("text"),
          page.total_label.cget("text"))

    before = len(booking_service.list_bookings_for_user(customer["id"]))
    page._submit()
    app.update()
    after = len(booking_service.list_bookings_for_user(customer["id"]))
    check("the booking was created", after == before + 1, f"{before} -> {after}")
    check("the customer lands on My Bookings", app.current == "MyBookings", app.current)

    page = current_page(app)
    check("the booking is listed", len(page.frames["Upcoming"].winfo_children()) > 0)
    bookings = [b for b in booking_service.list_bookings_for_user(customer["id"])
                if b["status"] in ("pending", "confirmed")]
    booking = max(bookings, key=lambda b: b["id"])
    original_when = booking["scheduled_at"]

    def pick_new_time() -> None:
        dialogs = find_dialogs(app)
        if not dialogs:
            return
        dialog = dialogs[-1]
        for offset in range(5, 12):
            dialog.date.set_date(date.today() + timedelta(days=offset))
            dialog._refresh_slots()
            if dialog._slots:
                break
        if dialog._slots:
            click_button(app, "Confirm New Time")
        else:
            click_button(app, "Close")

    guard = app.after(5000, lambda: close_dialogs(app))
    app.after(200, pick_new_time)
    page._reschedule(booking)
    try:
        app.after_cancel(guard)
    except tk.TclError:
        pass
    app.update()
    moved = booking_service.get_booking(booking["id"])
    check("the booking was rescheduled", moved["scheduled_at"] != original_when,
          moved["scheduled_at"])
    check("the reschedule dialog closed", not find_dialogs(app))

    app.go("MyBookings")
    app.update()
    page = current_page(app)
    guard = app.after(5000, lambda: close_dialogs(app))
    app.after(200, lambda: click_button(app, "Cancel Booking"))
    page._cancel(booking)
    try:
        app.after_cancel(guard)
    except tk.TclError:
        pass
    app.update()
    check("the booking was cancelled",
          booking_service.get_booking(booking["id"])["status"] == "cancelled",
          booking_service.get_booking(booking["id"])["status"])
    check("the cancel dialog closed", not find_dialogs(app))


def check_admin_flow(app: CleanHomeApp, admin) -> None:
    print("the admin booking flow")
    customer = auth_service.get_user(
        db.query_one("SELECT id FROM users WHERE email = 'customer@test.ph'")["id"])
    services = catalog_service.list_services()
    when = datetime.combine(date.today() + timedelta(days=6),
                            time(config.BUSINESS_OPEN_HOUR))
    fresh = booking_service.create_booking(customer, services[0]["id"], when,
                                           "12 Quezon Ave", "note")
    booking_id = fresh["id"]

    app.go("AdminBookings")
    app.update()
    page = current_page(app)
    page.status.set("All")
    page.date_from.current(0)
    page.date_to.current(0)
    page._refresh()
    app.update()
    check("the admin booking filters load",
          len(page.table.tree.get_children()) >= 1,
          len(page.table.tree.get_children()))

    for status in ("confirmed", "in_progress", "completed"):
        select_row(page, booking_id)
        page._change(status)
        app.update()
        check(f"the booking is {status}",
              booking_service.get_booking(booking_id)["status"] == status,
              booking_service.get_booking(booking_id)["status"])

    select_row(page, booking_id)
    page._change("cancelled")
    app.update()
    check("a completed booking cannot be cancelled again",
          booking_service.get_booking(booking_id)["status"] == "completed",
          booking_service.get_booking(booking_id)["status"])

    page.status.set("completed")
    page._refresh()
    app.update()
    check("the filter keeps the completed booking",
          len(page.table.tree.get_children()) == 1,
          len(page.table.tree.get_children()))


def check_reports(app: CleanHomeApp) -> None:
    print("the admin reports")
    app.go("AdminReports")
    app.update()
    page = current_page(app)
    page._run()
    app.update()
    check("the report table is filled", len(page.table_frame.winfo_children()) > 0)
    page._copy_summary()
    app.update()
    check("the report summary can be copied",
          "CleanHome revenue report" in app.clipboard_get())


def check_admin_pages(app: CleanHomeApp) -> None:
    print("the admin customer and service screens")
    app.go("AdminCustomers")
    app.update()
    page = current_page(app)
    page._refresh()
    app.update()
    check("the customers are listed", len(page.table.tree.get_children()) > 0)

    app.go("AdminServices")
    app.update()
    page = current_page(app)
    page._refresh()
    app.update()
    check("the services are listed", len(page.table.tree.get_children()) > 0)

    app.go("AdminPromotions")
    app.update()
    page = current_page(app)
    check("the promotions are listed", len(page.table.tree.get_children()) > 0)


def check_accounts(app: CleanHomeApp) -> None:
    print("sign-up, sign-in, profile and password")
    app.session.sign_out()
    app.go("Signup")
    app.update()
    page = current_page(app)
    page.full_name.set("New Person")
    page.email.set("new.person@test.ph")
    page.phone.set("09181234567")
    page.password.set("NewPass456")
    page.confirm.set("NewPass456")
    page._create_account()
    app.update()
    check("the new customer is signed in", app.session.role == "customer", app.session.role)
    check("the new account exists",
          db.query_one("SELECT id FROM users WHERE email = 'new.person@test.ph'") is not None)

    app.session.sign_out()
    app.go("Signup")
    app.update()
    page = current_page(app)
    page.full_name.set("Bad Person")
    page.email.set("bad.person@test.ph")
    page.password.set("abc")
    page.confirm.set("abc")
    page._create_account()
    app.update()
    check("a weak password is refused", not app.session.is_authenticated)

    app.go("Login")
    app.update()
    page = current_page(app)
    page.email.set("customer@test.ph")
    page.password.set("WrongPass123")
    page._sign_in()
    app.update()
    check("a wrong password is refused", not app.session.is_authenticated)
    check("the error is shown", page.error_label.cget("text") != "")

    app.sign_in(auth_service.login("customer@test.ph", PASSWORD))
    app.update()
    app.go("Profile")
    app.update()
    page = current_page(app)
    page.full_name.set("Updated Name")
    page.phone.set("09181234567")
    page.address.set("24 Roxas Ave")
    page._save()
    app.update()
    customer = auth_service.get_user(
        db.query_one("SELECT id FROM users WHERE email = 'customer@test.ph'")["id"])
    check("the profile was saved", customer["full_name"] == "Updated Name",
          customer["full_name"])
    check("the phone was saved", customer["phone"] == "09181234567", customer["phone"])

    app.go("ChangePassword")
    app.update()
    page = current_page(app)
    page.current.set(PASSWORD)
    page.new.set("NewPass456")
    page.confirm.set("NewPass456")
    page._update()
    app.update()
    check("the new password works",
          auth_service.login("customer@test.ph", "NewPass456") is not None)


def check_logout(app: CleanHomeApp, admin) -> None:
    print("logging out")
    app.sign_in(admin)
    app.update()
    check("the admin is signed in", app.session.role == "admin", app.session.role)

    original = messagebox.askyesno
    messagebox.askyesno = lambda *args, **kwargs: True
    try:
        app.logout()
    finally:
        messagebox.askyesno = original
    app.update()
    check("the session is cleared", not app.session.is_authenticated)
    check("the guest lands on the home page", app.current == "Home", app.current)
    check("the navigation bar shows the guest links",
          find_button(app, "Log In") is not None)

    app.go("AdminDashboard")
    app.update()
    check("the admin pages are closed to guests", app.current == "Login", app.current)


def main() -> int:
    folder = fresh_database()
    try:
        make_user("customer@test.ph", "customer",
                  address="12 Quezon Ave", phone="09171234567")
        app = CleanHomeApp()
        app.update()
        try:
            check_first_run(app)
            check_components(app)
            check_every_screen(app)
            admin = auth_service.login("admin@test.ph", PASSWORD)
            app.sign_in(admin)
            app.update()
            check_dialogs(app, admin)
            customer = auth_service.login("customer@test.ph", PASSWORD)
            app.sign_in(customer)
            app.update()
            check_booking_flow(app, customer)
            app.sign_in(admin)
            app.update()
            check_admin_flow(app, admin)
            check_reports(app)
            check_admin_pages(app)
            check_forced_password_change(app)
            check_accounts(app)
            check_logout(app, admin)
        finally:
            app.on_close()
    finally:
        db.close_connection()
        folder.cleanup()

    print()
    print("FAILURES:", failures if failures else "none")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
