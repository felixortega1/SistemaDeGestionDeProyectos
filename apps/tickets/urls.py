from django.urls import path

from . import views

urlpatterns = [
    path("tickets/", views.page, name="tickets_page"),
    path("tickets/panel/", views.panel, name="tickets_panel"),
    path("tickets/new/", views.ticket_new, name="ticket_new"),
    path("tickets/<int:ticket_id>/toggle/", views.ticket_toggle, name="ticket_toggle"),
    path("tickets/<int:ticket_id>/delete/", views.ticket_delete, name="ticket_delete"),
]
