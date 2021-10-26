from mycroft.lock import Lock
from mycroft.util import reset_sigint_handler, wait_for_exit_signal
from neon_core.skills.service import NeonSkillService


def main(*args, **kwargs):
    reset_sigint_handler()
    # Create PID file, prevent multiple instances of this service
    Lock('skills')
    service = NeonSkillService(*args, **kwargs)
    service.start()
    wait_for_exit_signal()
    service.shutdown()


if __name__ == "__main__":
    main()
