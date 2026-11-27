"""Page « Administration » (T79, D39) : visible et utilisable par les administrateurs seulement."""

from __future__ import annotations

from admin_ui import admin_page
from compte import _con, _validated_user

admin_page(_con(), _validated_user())
