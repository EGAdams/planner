
import os
from letta import settings
from letta.settings import settings as letta_settings, telemetry_settings

print(f"Database Engine: {letta_settings.database_engine}")
print(f"Telemetry Opt Out: {telemetry_settings.opt_out}")
print(f"DD Profiling: {telemetry_settings.enable_datadog}")
print(f"Sentry Enabled: {os.getenv('SENTRY_DSN')}")
