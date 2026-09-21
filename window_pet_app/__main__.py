"""WindowPet 模块主入口，支持 python -m window_pet_app 或直接运行"""
import sys
from pathlib import Path

if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from window_pet_app.app import main

    main()
else:
    from .app import main

    if __name__ == "__main__":
        main()
