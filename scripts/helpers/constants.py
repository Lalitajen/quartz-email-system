"""Shared constants for the Quartz Email System."""

ENGAGEMENT_COLORS = {
    'HOT': {'bg': 'danger', 'icon': 'fire'},
    'WARM': {'bg': 'warning text-dark', 'icon': 'thermometer-half'},
    'INTERESTED': {'bg': 'info', 'icon': 'eye'},
    'COLD': {'bg': 'secondary', 'icon': 'snow'},
    'UNRESPONSIVE': {'bg': 'dark', 'icon': 'x-circle'},
}

STATUS_COLORS = {
    'sent': 'success',
    'queued': 'primary',
    'draft': 'secondary',
    'failed': 'danger',
    'replied': 'info',
    'followed_up': 'dark',
}

STAGE_COLORS = {
    1: 'primary', 2: 'info', 3: 'warning', 4: 'success',
    5: 'danger', 6: 'dark', 7: 'secondary',
}
