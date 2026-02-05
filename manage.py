import os
import sys


def main():
    # Auto-detect and use virtual environment if present and not already active
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(base_dir, 'venv', 'bin', 'python')
    if os.path.exists(venv_python) and sys.executable != venv_python and 'venv' not in sys.prefix:
        os.execv(venv_python, [venv_python] + sys.argv)

    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_treinamento.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
