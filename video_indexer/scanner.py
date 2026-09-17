from pathlib import Path

from .config import VIDEO_EXTENSIONS


def scan(root: Path):
    root = root.resolve()
    if not root.is_dir() or not root.exists():
        raise FileNotFoundError(f"素材根目录不可读: {root}")
    videos = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            resolved = path.resolve()
            if root != resolved and root not in resolved.parents:
                continue
            stat = resolved.stat()
            videos.append({
                "filename": resolved.name,
                "path": str(resolved),
                "relative_path": str(resolved.relative_to(root)),
                "folder": str(resolved.parent.relative_to(root)) if resolved.parent != root else ".",
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
                "mtime_ns": stat.st_mtime_ns,
                "status": "pending",
            })
    videos.sort(key=lambda item: item["relative_path"].casefold())
    return videos
