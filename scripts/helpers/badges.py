"""Badge rendering helpers for Jinja2 templates."""

from markupsafe import Markup
from .constants import ENGAGEMENT_COLORS, STAGE_COLORS


def engagement_badge(level):
    level = str(level).upper() if level else ''
    info = ENGAGEMENT_COLORS.get(level, {'bg': 'light text-dark', 'icon': 'question-circle'})
    if not level:
        return Markup('<span class="badge bg-light text-muted">N/A</span>')
    return Markup(f'<span class="badge bg-{info["bg"]}"><i class="bi bi-{info["icon"]} me-1"></i>{level}</span>')


def stage_badge(stage, pipeline_stages=None):
    stage_str = str(stage)
    name = ''
    if pipeline_stages and stage_str.isdigit():
        name = pipeline_stages.get(int(stage_str), {}).get('name', stage_str)
    color = STAGE_COLORS.get(int(stage_str) if stage_str.isdigit() else 0, 'secondary')
    label = f'{stage_str} - {name}' if name else stage_str
    return Markup(f'<span class="badge bg-{color} badge-stage">{label}</span>')
