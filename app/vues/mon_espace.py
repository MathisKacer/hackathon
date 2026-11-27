"""Page « Mon espace » : connexion facultative, profil et historique des recherches (T48, T49)."""

from __future__ import annotations

from commun import PAGES_DIR, PROFILE_LABELS, all_regions_of, get_offers, profile_keys
from compte import account_page

account_page(profile_keys(all_regions_of(get_offers())), PROFILE_LABELS, PAGES_DIR / "explorer.py")
