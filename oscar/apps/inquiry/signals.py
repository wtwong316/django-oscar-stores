import django.dispatch

inquiry_placed = django.dispatch.Signal()

inquiry_status_changed = django.dispatch.Signal()

inquiry_line_status_changed = django.dispatch.Signal()
