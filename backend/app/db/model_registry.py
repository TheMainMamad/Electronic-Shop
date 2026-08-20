"""Imports every ORM model module exactly once so SQLAlchemy's shared
Base.metadata has all tables registered before any ForeignKey needs
resolving.

The FastAPI app gets this for free by importing the full router tree at
startup. Alembic and the Celery worker process do not — Celery in
particular only imports whatever `celery_app.py`'s `include=[...]` names
plus their own imports, so a task module that references a table it
doesn't itself define (e.g. an audit log FK to `users.id`) would otherwise
crash at runtime with NoReferencedTableError. Import this module from
anywhere that needs the full model graph without needing the whole app.
"""

from app.common import idempotency_models  # noqa: F401
from app.modules.audit import models as audit_models  # noqa: F401
from app.modules.cart import models as cart_models  # noqa: F401
from app.modules.catalog import models as catalog_models  # noqa: F401
from app.modules.orders import models as orders_models  # noqa: F401
from app.modules.payments import models as payments_models  # noqa: F401
from app.modules.tickets import models as tickets_models  # noqa: F401
from app.modules.users import models as users_models  # noqa: F401
from app.modules.wallet import models as wallet_models  # noqa: F401
