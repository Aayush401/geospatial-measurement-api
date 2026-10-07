import os
import subprocess
import tempfile


def test_startup_creates_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_data_dir = os.path.join(tmpdir, "missing_data")
        fake_db_path = os.path.join(fake_data_dir, "test.db")
        fake_db_url = f"sqlite:///{fake_db_path}"
        
        env = os.environ.copy()
        env["DATA_DIR"] = fake_data_dir
        env["DATABASE_URL"] = fake_db_url
        
        # Run a subprocess that imports the app, triggering module-level DB initialization
        script = "from app.main import app; print('OK')"
        
        result = subprocess.run(
            ["python", "-c", script],
            env=env,
            capture_output=True,
            text=True,
            check=False
        )
        
        assert result.returncode == 0, f"Startup failed: {result.stderr}"
        assert "OK" in result.stdout
        
        # Verify directories exist
        assert os.path.exists(fake_data_dir)
        assert os.path.exists(os.path.join(fake_data_dir, "uploads"))
        assert os.path.exists(fake_db_path)
