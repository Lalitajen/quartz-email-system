"""
Enhanced Auto-Reply Monitor Route
Shows detailed pipeline stages, attachments, and activity by category
"""

ENHANCED_AUTO_REPLY_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Auto-Reply Monitor - Quartz Email System</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <meta http-equiv="refresh" content="10">
    <style>
        .status-running { color: #28a745; font-weight: bold; }
        .status-stopped { color: #dc3545; font-weight: bold; }
        .result-sent { color: #28a745; font-weight: bold; }
        .result-skipped { color: #ffc107; }
        .result-failed { color: #dc3545; font-weight: bold; }
        .metric-card { border-left: 4px solid #007bff; transition: transform 0.2s; }
        .metric-card:hover { transform: translateY(-5px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .stage-card { margin-bottom: 15px; border-left: 4px solid; }
        .stage-card-1 { border-left-color: #17a2b8; }
        .stage-card-2 { border-left-color: #28a745; }
        .stage-card-3 { border-left-color: #ffc107; }
        .stage-card-4 { border-left-color: #fd7e14; }
        .stage-card-5 { border-left-color: #dc3545; }
        .stage-card-6 { border-left-color: #6610f2; }
        .stage-card-7 { border-left-color: #e83e8c; }
        .stage-card-8 { border-left-color: #20c997; }
        .stage-card-9 { border-left-color: #6f42c1; }
        .stage-card-10 { border-left-color: #007bff; }
        .attachment-badge { margin: 2px; font-size: 0.85em; }
        .nav-link.active { background-color: #0d6efd; }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="/"><i class="fas fa-envelope"></i> Quartz Email System</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/"><i class="fas fa-home"></i> Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/customers"><i class="fas fa-users"></i> Customers</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/research"><i class="fas fa-search"></i> Research</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/compose"><i class="fas fa-pencil-alt"></i> Compose</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/tracking"><i class="fas fa-chart-line"></i> Tracking</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link active" href="/auto-reply"><i class="fas fa-robot"></i> Auto-Reply Monitor</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/attachments"><i class="fas fa-paperclip"></i> Attachments</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/settings"><i class="fas fa-cog"></i> Settings</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <div class="row">
            <!-- Left Column: Status & Stats -->
            <div class="col-md-8">
                <!-- Header -->
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2><i class="fas fa-robot"></i> Auto-Reply Daemon Monitor</h2>
                    <span class="badge bg-info"><i class="fas fa-sync-alt"></i> Auto-refresh: 10s</span>
                </div>

                <!-- Daemon Status Card -->
                <div class="card mb-4">
                    <div class="card-header bg-dark text-white">
                        <h5 class="mb-0"><i class="fas fa-server"></i> Daemon Status</h5>
                    </div>
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-4">
                                <h4>
                                    <span class="status-{{ 'running' if daemon_status['running'] else 'stopped' }}">
                                        <i class="fas fa-circle"></i> {{ daemon_status['status'] }}
                                    </span>
                                </h4>
                                <p class="text-muted mb-0">
                                    {% if daemon_status['pid'] %}
                                        PID: {{ daemon_status['pid'] }}
                                    {% endif %}
                                </p>
                            </div>
                            <div class="col-md-8">
                                {% if daemon_status['running'] %}
                                    <div class="alert alert-success mb-0">
                                        <i class="fas fa-check-circle"></i> Monitoring emails every 5 seconds
                                        <br><small>System is actively processing incoming emails and sending auto-replies</small>
                                    </div>
                                {% else %}
                                    <div class="alert alert-danger mb-0">
                                        <i class="fas fa-exclamation-triangle"></i> Daemon not running
                                        <br><small>Start with: <code>./start_auto_reply.sh</code></small>
                                    </div>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Statistics Cards -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card metric-card text-center">
                            <div class="card-body">
                                <i class="fas fa-inbox fa-2x text-primary mb-2"></i>
                                <h3 class="text-primary">{{ statistics['total_processed'] }}</h3>
                                <p class="text-muted mb-0">Total Processed</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card text-center" style="border-left-color: #28a745;">
                            <div class="card-body">
                                <i class="fas fa-paper-plane fa-2x text-success mb-2"></i>
                                <h3 class="text-success">{{ statistics['successfully_sent'] }}</h3>
                                <p class="text-muted mb-0">Auto-Replies Sent</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card text-center" style="border-left-color: #ffc107;">
                            <div class="card-body">
                                <i class="fas fa-filter fa-2x text-warning mb-2"></i>
                                <h3 class="text-warning">{{ statistics['not_interested'] }}</h3>
                                <p class="text-muted mb-0">Filtered Out</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card text-center" style="border-left-color: #28a745;">
                            <div class="card-body">
                                <i class="fas fa-percentage fa-2x text-success mb-2"></i>
                                <h3 class="text-success">{{ statistics['success_rate'] }}%</h3>
                                <p class="text-muted mb-0">Success Rate</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Activity -->
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="fas fa-history"></i> Recent Activity</h5>
                    </div>
                    <div class="card-body" style="max-height: 500px; overflow-y: auto;">
                        {% if recent_activity %}
                        <div class="table-responsive">
                            <table class="table table-hover table-sm">
                                <thead class="table-light">
                                    <tr>
                                        <th><i class="fas fa-clock"></i> Time</th>
                                        <th><i class="fas fa-user"></i> From</th>
                                        <th><i class="fas fa-envelope"></i> Subject</th>
                                        <th><i class="fas fa-heart"></i> Interest</th>
                                        <th><i class="fas fa-layer-group"></i> Stage</th>
                                        <th><i class="fas fa-check"></i> Result</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for activity in recent_activity %}
                                    <tr>
                                        <td><small class="badge bg-secondary">{{ activity['timestamp'] }}</small></td>
                                        <td><small>{{ activity['from'][:35] }}</small></td>
                                        <td><small>{{ activity['subject'][:40] }}</small></td>
                                        <td><span class="badge bg-info">{{ activity['interest'] }}</span></td>
                                        <td><span class="badge bg-primary">{{ activity['stage'] }}</span></td>
                                        <td><span class="result-{{ activity['result']|lower }}">{{ activity['result'] }}</span></td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        {% else %}
                        <p class="text-muted text-center my-4">
                            <i class="fas fa-hourglass-half fa-3x mb-3"></i><br>
                            No activity yet. Daemon is waiting for emails...
                        </p>
                        {% endif %}
                    </div>
                </div>
            </div>

            <!-- Right Column: Pipeline Stages & Attachments -->
            <div class="col-md-4">
                <h4 class="mb-3"><i class="fas fa-layer-group"></i> Pipeline Stages & Attachments</h4>

                <!-- Stage Cards -->
                {% for stage_num, stage_info in pipeline_stages.items() %}
                <div class="card stage-card stage-card-{{ stage_num }}">
                    <div class="card-header py-2">
                        <strong>Stage {{ stage_num }}: {{ stage_info['name'] }}</strong>
                        {% if stage_dist.get(stage_num) %}
                        <span class="badge bg-primary float-end">{{ stage_dist[stage_num] }} emails</span>
                        {% endif %}
                    </div>
                    <div class="card-body py-2">
                        <p class="mb-2"><small><strong>Attachments:</strong></small></p>
                        {% if stage_info['attachments'] %}
                        <div class="mb-2">
                            {% for attachment in stage_info['attachments'] %}
                            <span class="badge bg-secondary attachment-badge">
                                <i class="fas fa-file-pdf"></i> {{ attachment }}
                            </span>
                            {% endfor %}
                        </div>
                        {% else %}
                        <p class="text-muted mb-2"><small><em>No attachments</em></small></p>
                        {% endif %}
                        <p class="mb-0"><small><strong>Triggers:</strong></small></p>
                        <p class="mb-0"><small class="text-muted">
                            {{ stage_info['trigger_keywords'][:3]|join(', ') }}...
                        </small></p>
                    </div>
                </div>
                {% endfor %}

                <!-- Quick Commands -->
                <div class="card mt-3">
                    <div class="card-header bg-dark text-white">
                        <h6 class="mb-0"><i class="fas fa-terminal"></i> Quick Commands</h6>
                    </div>
                    <div class="card-body">
                        <p><strong>Start:</strong><br><code>./start_auto_reply.sh</code></p>
                        <p><strong>Stop:</strong><br><code>./stop_auto_reply.sh</code></p>
                        <p><strong>Monitor:</strong><br><code>./monitor_status.sh</code></p>
                        <p class="mb-0"><strong>Live Log:</strong><br><code>tail -f /tmp/auto_reply.log</code></p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''
