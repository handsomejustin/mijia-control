def start_homekit_bridge(*args, **kwargs):
    from app.homekit.bridge import start_homekit_bridge as _start

    return _start(*args, **kwargs)


__all__ = ["start_homekit_bridge"]
