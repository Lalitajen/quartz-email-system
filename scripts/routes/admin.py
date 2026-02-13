"""Admin panel routes - User management for administrators."""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app_core import login_required, admin_required, get_current_user, logger, safe_flash_error

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard showing all users and system stats."""
    from models import User, get_db

    try:
        with get_db() as db:
            users_data = db.execute('''
                SELECT id, email, display_name, role, setup_complete, created_at
                FROM users
                ORDER BY created_at DESC
            ''').fetchall()

        users = []
        for row in users_data:
            users.append({
                'id': row[0],
                'email': row[1],
                'display_name': row[2],
                'role': row[3],
                'setup_complete': bool(row[4]),
                'created_at': row[5],
            })

        return render_template('admin.html',
            active_page='admin',
            users=users,
            total_users=len(users),
        )

    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return render_template('admin.html',
            active_page='admin',
            error=str(e),
            users=[],
            total_users=0,
        )


@admin_bp.route('/admin/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """View and manage a specific user."""
    from models import User

    user = User.get_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    credentials = {
        'anthropic_api_key': user.has_credential('anthropic_api_key'),
        'service_account': user.has_credential('service_account'),
        'gmail_token': user.has_credential('gmail_token'),
        'google_sheets_id': user.has_credential('google_sheets_id'),
    }

    settings = user.get_all_settings()

    return render_template('admin_user_detail.html',
        active_page='admin',
        user=user,
        credentials=credentials,
        settings=settings,
    )


@admin_bp.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user role or display name."""
    from models import User, get_db

    user = User.get_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    current_user = get_current_user()
    if user.id == current_user.id and request.form.get('role') != 'admin':
        flash('You cannot remove your own admin role.', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user_id))

    try:
        display_name = request.form.get('display_name', '').strip()
        role = request.form.get('role', '').strip()

        if role not in ('user', 'admin'):
            flash('Invalid role. Must be "user" or "admin".', 'danger')
            return redirect(url_for('admin.user_detail', user_id=user_id))

        with get_db() as db:
            db.execute('''
                UPDATE users
                SET display_name = ?, role = ?
                WHERE id = ?
            ''', (display_name, role, user_id))

        logger.info(f"Admin {current_user.email} updated user {user.email}: role={role}, display_name={display_name}")
        flash('User updated successfully!', 'success')

    except Exception as e:
        logger.error(f"Edit user {user_id} failed: {e}")
        safe_flash_error(e, 'Edit user')

    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user account (WARNING: irreversible)."""
    from models import User, get_db

    user = User.get_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    current_user = get_current_user()
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user_id))

    try:
        with get_db() as db:
            db.execute('DELETE FROM users WHERE id = ?', (user_id,))

        logger.warning(f"Admin {current_user.email} deleted user {user.email} (ID: {user_id})")
        flash(f'User "{user.email}" deleted successfully.', 'warning')

    except Exception as e:
        logger.error(f"Delete user {user_id} failed: {e}")
        safe_flash_error(e, 'Delete user')

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/users/<int:user_id>/reset-setup', methods=['POST'])
@login_required
@admin_required
def reset_user_setup(user_id):
    """Reset a user's setup_complete flag to allow them to re-run the onboarding wizard."""
    from models import User, get_db

    user = User.get_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    try:
        with get_db() as db:
            db.execute('UPDATE users SET setup_complete = 0 WHERE id = ?', (user_id,))

        current_user = get_current_user()
        logger.info(f"Admin {current_user.email} reset setup for user {user.email}")
        flash(f'Setup reset for "{user.email}". They will see the onboarding wizard on next login.', 'success')

    except Exception as e:
        logger.error(f"Reset setup for user {user_id} failed: {e}")
        safe_flash_error(e, 'Reset setup')

    return redirect(url_for('admin.user_detail', user_id=user_id))
