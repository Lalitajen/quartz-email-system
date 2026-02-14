"""Route blueprints for the Quartz Email System."""

from .auth import auth_bp
from .oauth import oauth_bp
from .dashboard import dashboard_bp
from .customers import customers_bp
from .research import research_bp
from .compose import compose_bp
from .tracking import tracking_bp
from .batch_send import batch_send_bp
from .workflow import workflow_bp
from .attachments import attachments_bp
from .settings import settings_bp
from .auto_reply import auto_reply_bp
from .ai_insights import ai_insights_bp
from .setup import setup_bp
from .admin import admin_bp
from .smart_setup import smart_setup_bp

ALL_BLUEPRINTS = [
    auth_bp,
    oauth_bp,
    dashboard_bp,
    customers_bp,
    research_bp,
    compose_bp,
    tracking_bp,
    batch_send_bp,
    workflow_bp,
    attachments_bp,
    settings_bp,
    auto_reply_bp,
    ai_insights_bp,
    setup_bp,
    admin_bp,
    smart_setup_bp,
]
