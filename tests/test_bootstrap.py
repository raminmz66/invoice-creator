"""Tests for scripts/bootstrap.sh.

The bootstrap script installs uv, syncs Python dependencies and verifies the
WeasyPrint system libraries. Tests source it into bash with a stubbed PATH so
no real installer, network call or package sync ever runs.
"""

import subprocess
import textwrap
from pathlib import Path

import pytest

BOOTSTRAP = Path(__file__).resolve().parent.parent / "scripts" / "bootstrap.sh"


def write_stub(bin_dir: Path, name: str, body: str) -> Path:
    """Create an executable stub on the fake PATH."""
    stub = bin_dir / name
    stub.write_text("#!/usr/bin/env bash\n" + textwrap.dedent(body))
    stub.chmod(0o755)
    return stub


def uv_stub(bin_dir: Path, log: Path, run_exit: int = 0) -> None:
    """Stub `uv` that records its arguments and controls `uv run`'s exit code."""
    write_stub(
        bin_dir,
        "uv",
        f"""
        echo "$@" >> "{log}"
        if [[ "$1" == "run" ]]; then exit {run_exit}; fi
        exit 0
        """,
    )


@pytest.fixture
def env(tmp_path):
    """A fake project root, HOME and PATH for running bootstrap.sh."""

    class Env:
        def __init__(self):
            self.root = tmp_path / "project"
            self.home = tmp_path / "home"
            self.bin = tmp_path / "bin"
            self.local_bin = self.home / ".local" / "bin"
            for directory in (self.root, self.home, self.bin, self.local_bin):
                directory.mkdir(parents=True)
            (self.root / "pyproject.toml").write_text('[project]\nname = "invoice-creator"\n')
            self.tmp = tmp_path
            self.uv_log = tmp_path / "uv.log"
            self.curl_log = tmp_path / "curl.log"
            self.notify_log = tmp_path / "notify.log"
            write_stub(self.bin, "notify-send", f'echo "$@" >> "{self.notify_log}"')

        def has_venv(self):
            (self.root / ".venv").mkdir()

        def read(self, log: Path) -> str:
            return log.read_text() if log.exists() else ""

        def run(self, func="bootstrap"):
            return subprocess.run(
                ["bash", "-c", f'source "{BOOTSTRAP}"; {func}'],
                env={
                    "PATH": f"{self.bin}:/usr/bin:/bin",
                    "HOME": str(self.home),
                    "ROOT": str(self.root),
                    "BOOTSTRAP_LOG": str(self.root / ".server.log"),
                },
                capture_output=True,
                text=True,
            )

    return Env()


def test_syncs_dependencies_without_installing_uv_when_uv_present(env):
    uv_stub(env.bin, env.uv_log)
    env.has_venv()
    write_stub(env.bin, "curl", f'echo "$@" >> "{env.curl_log}"')

    result = env.run()

    assert result.returncode == 0, result.stderr
    assert env.read(env.curl_log) == "", "must not fetch the uv installer when uv is already present"
    assert "sync" in env.read(env.uv_log)


def fake_uv_installer(env, script_name="install.sh") -> Path:
    """A stand-in for astral.sh/uv/install.sh that drops a uv stub in ~/.local/bin."""
    installer = env.tmp / script_name
    installer.write_text(
        "#!/usr/bin/env bash\n"
        f'cat > "{env.local_bin}/uv" <<"STUB"\n'
        "#!/usr/bin/env bash\n"
        f'echo "$@" >> "{env.uv_log}"\n'
        "STUB\n"
        f'chmod +x "{env.local_bin}/uv"\n'
    )
    return installer


def test_installs_uv_when_missing_then_syncs(env):
    env.has_venv()
    installer = fake_uv_installer(env)
    write_stub(env.bin, "curl", f'echo "$@" >> "{env.curl_log}"; cat "{installer}"')

    result = env.run()

    assert result.returncode == 0, result.stderr
    assert "astral.sh" in env.read(env.curl_log), "should fetch the official uv installer"
    assert "sync" in env.read(env.uv_log), "should sync dependencies with the freshly installed uv"


def test_reports_manual_instructions_when_uv_install_does_not_produce_uv(env):
    env.has_venv()
    write_stub(env.bin, "curl", f'echo "$@" >> "{env.curl_log}"; echo ":"')

    result = env.run()

    assert result.returncode != 0, "must not continue when uv is still unavailable"
    assert "astral.sh/uv/install.sh" in result.stderr, "error must tell the user how to install uv by hand"


def test_reports_apt_command_when_weasyprint_libraries_are_missing(env):
    uv_stub(env.bin, env.uv_log, run_exit=1)
    env.has_venv()

    result = env.run()

    assert result.returncode != 0, "must not report success when WeasyPrint cannot load"
    assert "import weasyprint" in env.read(env.uv_log), "should verify WeasyPrint actually imports"
    assert "sudo apt install" in result.stderr, "error must give the exact install command"
    assert "libpangoft2-1.0-0" in result.stderr, "error must name the packages WeasyPrint 69 needs"


def test_notifies_desktop_when_dependencies_must_be_installed(env):
    uv_stub(env.bin, env.uv_log)  # uv is present but .venv does not exist yet

    result = env.run()

    assert result.returncode == 0, result.stderr
    assert "Setting up" in env.read(env.notify_log), "a silent launcher must announce a slow first run"


def test_stays_silent_when_dependencies_are_already_installed(env):
    uv_stub(env.bin, env.uv_log)
    env.has_venv()

    result = env.run()

    assert result.returncode == 0, result.stderr
    assert "Setting up" not in env.read(env.notify_log), "routine launches must not pop up a notification"


def test_records_setup_output_in_the_log_file(env):
    write_stub(env.bin, "uv", f'echo "$@" >> "{env.uv_log}"; echo "resolved 41 packages"')
    env.has_venv()

    result = env.run()

    assert result.returncode == 0, result.stderr
    log = env.root / ".server.log"
    assert log.exists(), "setup output must be captured for a launcher with no terminal"
    assert "resolved 41 packages" in log.read_text()


LAUNCH = Path(__file__).resolve().parent.parent / "scripts" / "launch.sh"


def test_launcher_aborts_with_bootstrap_guidance_when_uv_cannot_be_installed(env):
    # launch.sh puts $HOME/.local/bin first on PATH, so stubs must live there.
    write_stub(env.local_bin, "curl", f'echo "$@" >> "{env.curl_log}"; echo ":"')
    write_stub(env.local_bin, "notify-send", f'echo "$@" >> "{env.notify_log}"')

    result = subprocess.run(
        ["bash", str(LAUNCH)],
        env={
            "PATH": f"{env.local_bin}:/usr/bin:/bin",
            "HOME": str(env.home),
            "BOOTSTRAP_LOG": str(env.root / ".server.log"),
        },
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0, "launcher must not start a server without dependencies"
    assert "astral.sh/uv/install.sh" in result.stderr, "launcher must surface bootstrap's guidance"
    assert not (LAUNCH.parent.parent / ".server.pid").exists(), "must not leave a pidfile behind"


def test_sync_leaves_packages_outside_the_lock_installed(env):
    """A launch must not uninstall a developer's `uv sync --extra dev` tools."""
    uv_stub(env.bin, env.uv_log)
    env.has_venv()

    result = env.run()

    assert result.returncode == 0, result.stderr
    sync_command = next(line for line in env.read(env.uv_log).splitlines() if line.startswith("sync"))
    assert "--inexact" in sync_command, "syncing without --inexact prunes dev extras from the venv"
