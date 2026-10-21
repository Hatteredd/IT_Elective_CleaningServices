"""Page registry.

Import every page here so the router can load them by name.
"""

from __future__ import annotations

from cleanhome.ui.pages.about import About
from cleanhome.ui.pages.admin_bookings import AdminBookings
from cleanhome.ui.pages.admin_customers import AdminCustomers
from cleanhome.ui.pages.admin_dashboard import AdminDashboard
from cleanhome.ui.pages.admin_promotions import AdminPromotions
from cleanhome.ui.pages.admin_reports import AdminReports
from cleanhome.ui.pages.admin_services import AdminServices
from cleanhome.ui.pages.book import Book
from cleanhome.ui.pages.change_password import ChangePassword
from cleanhome.ui.pages.contact import Contact
from cleanhome.ui.pages.create_admin import CreateAdmin
from cleanhome.ui.pages.home import Home
from cleanhome.ui.pages.login import Login
from cleanhome.ui.pages.my_bookings import MyBookings
from cleanhome.ui.pages.profile import Profile
from cleanhome.ui.pages.promotions import Promotions
from cleanhome.ui.pages.service_details import ServiceDetails
from cleanhome.ui.pages.services import Services
from cleanhome.ui.pages.signup import Signup

# The second item of each entry lists the roles that may open the page.
# An empty tuple means the page is public.
PAGES = {
    "CreateAdmin": (CreateAdmin, ()),
    "Home": (Home, ()),
    "Services": (Services, ()),
    "Promotions": (Promotions, ()),
    "About": (About, ()),
    "Contact": (Contact, ()),
    "ServiceDetails": (ServiceDetails, ()),
    "Login": (Login, ()),
    "Signup": (Signup, ()),
    "Book": (Book, ("customer",)),
    "MyBookings": (MyBookings, ("customer",)),
    "Profile": (Profile, ("customer", "admin")),
    "ChangePassword": (ChangePassword, ("customer", "admin")),
    "AdminDashboard": (AdminDashboard, ("admin",)),
    "AdminBookings": (AdminBookings, ("admin",)),
    "AdminServices": (AdminServices, ("admin",)),
    "AdminPromotions": (AdminPromotions, ("admin",)),
    "AdminCustomers": (AdminCustomers, ("admin",)),
    "AdminReports": (AdminReports, ("admin",)),
}
