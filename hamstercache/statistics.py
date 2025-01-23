from pathlib import Path

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

def get_directory_sizes(cache_folder='cache/'):
    directory_sizes = []
    for directory in Path(cache_folder).iterdir():
        if directory.is_dir():
            size = sum(f.stat().st_size for f in directory.glob('**/*') if f.is_file())
            directory_sizes.append({
                "path": str(directory),
                "name": directory.name,
                "size": size,
                "size_readable": format_size(size)
            })
    return directory_sizes
