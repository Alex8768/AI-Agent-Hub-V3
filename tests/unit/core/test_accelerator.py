import builtins
import importlib

def test_accelerator_without_torch(monkeypatch):
    """
    Accelerator must gracefully degrade if torch is not installed.
    We simulate ImportError for any torch import.
    """
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "torch" or name.startswith("torch."):
            raise ImportError("torch not installed")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    import src.core.accelerator as accel_mod
    importlib.reload(accel_mod)

    acc = accel_mod.accelerator
    assert acc.torch_available is False
    assert acc.device == "cpu"
    acc.empty_cache()  # should be no-op and not raise
