# scripts/export_context.py
"""
Скрипт для подготовки чистого контекста проекта.
Собирает только важные файлы, игнорируя зависимости и кэши.
"""

import os
import sys
from pathlib import Path
from typing import List, Set, Tuple
import datetime


class ProjectExporter:
    """Экспортер структуры и кода проекта."""
    
    # Папки, которые нужно игнорировать (blacklist)
    IGNORE_DIRS = {
        '.venv', '.git', '__pycache__', '.idea', '.vscode',
        'dist', 'build', 'node_modules', '.pytest_cache',
        '.mypy_cache', '.ruff_cache', 'logs', 'data',
        'exports', 'workspace'
    }
    
    # Файлы, которые нужно игнорировать
    IGNORE_FILES = {
        '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.pyd',
        '*.so', '*.dll', '*.dylib', '*.db', '*.sqlite',
        '*.bin', '*.pkl', '*.pickle', '*.h5', '*.hdf5',
        '*.feather', '*.parquet', '*.npy', '*.npz'
    }
    
    # Папки, которые нужно включать (whitelist)
    INCLUDE_DIRS = {'src', 'tests', 'scripts', 'mcp_servers'}
    
    # Важные файлы в корне
    ROOT_FILES = {
        'pyproject.toml', 'requirements.txt', 'requirements-dev.txt',
        'Dockerfile', 'docker-compose.yml', '.env.example', 
        'README.md', 'ARCHITECTURE_V3.md', 'setup.py', 'setup.cfg',
        'Makefile', 'start.sh', 'run_simple.py', 'run_minimal.py',
        'MANIFEST.in', '.gitignore', '.python-version'
    }
    
    # Расширения текстовых файлов
    TEXT_EXTENSIONS = {
        '.py', '.md', '.txt', '.toml', '.yaml', '.yml', '.json',
        '.ini', '.cfg', '.sh', '.dockerfile', '.sql', '.html',
        '.css', '.js', '.ts', '.jsx', '.tsx', '.vue', '.rst'
    }
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root).resolve()
        self.output_file = self.project_root / 'project_snapshot_clean.txt'
        
    def should_ignore(self, path: Path) -> bool:
        """Проверяет, нужно ли игнорировать путь."""
        # Проверка папок
        if path.is_dir():
            return path.name in self.IGNORE_DIRS
        
        # Проверка файлов
        if path.is_file():
            # Проверка по имени
            if path.name in self.IGNORE_FILES:
                return True
            
            # Проверка по расширению
            if any(path.name.endswith(pattern.strip('*')) 
                   for pattern in self.IGNORE_FILES if '*' in pattern):
                return True
            
            # Игнорируем скрытые файлы (кроме .env.example)
            if path.name.startswith('.') and path.name not in self.ROOT_FILES:
                return True
        
        return False
    
    def should_include(self, path: Path) -> bool:
        """Проверяет, нужно ли включать путь."""
        # Всегда включаем файлы из списка ROOT_FILES
        if path.is_file() and path.name in self.ROOT_FILES:
            return True
        
        # Для папок: включаем только из INCLUDE_DIRS
        if path.is_dir():
            return path.name in self.INCLUDE_DIRS
        
        # Для файлов внутри папок: проверяем родительскую папку
        if path.is_file():
            # Проверяем, находится ли файл в include-папке
            for parent in path.parents:
                if parent.name in self.INCLUDE_DIRS:
                    # Проверяем расширение (только текстовые файлы)
                    return path.suffix in self.TEXT_EXTENSIONS
        
        return False
    
    def get_project_tree(self) -> str:
        """Генерирует дерево проекта."""
        tree_lines = ["📁 СТРУКТУРА ПРОЕКТА:", "=" * 50, ""]
        
        def walk_directory(dir_path: Path, prefix: str = "") -> List[str]:
            lines = []
            try:
                # Получаем элементы, сортируем: сначала папки, потом файлы
                items = sorted(dir_path.iterdir(), 
                             key=lambda x: (not x.is_dir(), x.name.lower()))
                
                for i, item in enumerate(items):
                    if self.should_ignore(item):
                        continue
                    
                    # Проверяем, нужно ли включать этот элемент
                    if not (self.should_include(item) or 
                           (item.is_dir() and any(self.should_include(p) 
                            for p in item.rglob('*') if not self.should_ignore(p)))):
                        continue
                    
                    # Определяем префикс для текущего элемента
                    connector = "├── " if i < len(items) - 1 else "└── "
                    
                    if item.is_dir():
                        lines.append(f"{prefix}{connector}{item.name}/")
                        # Рекурсивно обходим вложенные папки
                        extension = "│   " if i < len(items) - 1 else "    "
                        lines.extend(walk_directory(item, prefix + extension))
                    else:
                        lines.append(f"{prefix}{connector}{item.name}")
            except (PermissionError, OSError) as e:
                lines.append(f"{prefix}⚠️  Ошибка доступа: {e}")
            
            return lines
        
        tree_lines.extend(walk_directory(self.project_root))
        return "\n".join(tree_lines)
    
    def read_file_safely(self, file_path: Path) -> Tuple[bool, str]:
        """Безопасно читает файл, проверяя, является ли он текстовым."""
        try:
            # Проверяем размер файла (не более 1MB)
            if file_path.stat().st_size > 1024 * 1024:
                return False, f"⚠️ Файл слишком большой: {file_path.stat().st_size} байт"
            
            # Пробуем прочитать как текст
            content = file_path.read_text(encoding='utf-8')
            
            # Простая проверка на бинарный файл
            # Если файл содержит много null-байтов, это бинарный
            if '\x00' in content[:1024]:
                return False, "⚠️ Бинарный файл (содержит null-байты)"
            
            return True, content
            
        except UnicodeDecodeError:
            return False, "⚠️ Не удалось декодировать как UTF-8 (возможно, бинарный файл)"
        except Exception as e:
            return False, f"⚠️ Ошибка чтения: {e}"
    
    def collect_files(self) -> List[Path]:
        """Собирает все файлы для экспорта."""
        files = []
        
        # Добавляем важные файлы из корня
        for filename in self.ROOT_FILES:
            file_path = self.project_root / filename
            if file_path.exists() and file_path.is_file():
                files.append(file_path)
        
        # Добавляем файлы из include-папок
        for dir_name in self.INCLUDE_DIRS:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                for file_path in dir_path.rglob('*'):
                    if (file_path.is_file() and 
                        not self.should_ignore(file_path) and
                        self.should_include(file_path)):
                        files.append(file_path)
        
        # Удаляем дубликаты и сортируем
        files = sorted(set(files), key=lambda x: str(x))
        return files
    
    def export_project(self) -> str:
        """Экспортирует проект в текстовый формат."""
        print("🔄 Сборка контекста проекта...")
        
        output_lines = []
        
        # Добавляем заголовок с датой
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_lines.extend([
            f"📋 SNAPSHOT ПРОЕКТА: AI Agent Hub V3",
            f"📅 Дата: {timestamp}",
            "=" * 60,
            ""
        ])
        
        # Генерируем дерево проекта
        print("🌳 Генерация дерева проекта...")
        tree = self.get_project_tree()
        output_lines.append(tree)
        output_lines.append("\n" + "=" * 60 + "\n")
        
        # Собираем и читаем файлы
        print("📄 Чтение файлов...")
        files = self.collect_files()
        
        if not files:
            output_lines.append("⚠️ Не найдено файлов для экспорта")
            return "\n".join(output_lines)
        
        # Добавляем содержимое файлов
        total_lines = 0
        total_chars = 0
        files_processed = 0
        files_skipped = 0
        
        for file_path in files:
            relative_path = file_path.relative_to(self.project_root)
            
            print(f"  📝 Обработка: {relative_path}")
            output_lines.append(f"\n{'─' * 60}")
            output_lines.append(f"📄 ФАЙЛ: {relative_path}")
            output_lines.append(f"{'─' * 60}\n")
            
            success, content = self.read_file_safely(file_path)
            
            if success:
                output_lines.append(content)
                total_lines += content.count('\n') + 1
                total_chars += len(content)
                files_processed += 1
            else:
                output_lines.append(f"# {content}")
                files_skipped += 1
        
        # Добавляем статистику
        output_lines.append("\n" + "=" * 60)
        output_lines.append("📊 СТАТИСТИКА:")
        output_lines.append("=" * 60)
        output_lines.append(f"📁 Файлов обработано: {files_processed}")
        output_lines.append(f"⏭️  Файлов пропущено: {files_skipped}")
        output_lines.append(f"📈 Строк кода: {total_lines:,}")
        output_lines.append(f"🔤 Символов: {total_chars:,}")
        
        # Примерный расчет токенов (1 токен ≈ 4 символа)
        estimated_tokens = total_chars // 4
        output_lines.append(f"🧮 Примерно токенов: {estimated_tokens:,}")
        
        # Предупреждение о размере контекста
        if estimated_tokens > 100000:
            output_lines.append(f"⚠️  ВНИМАНИЕ: Контекст большой ({estimated_tokens:,} токенов)")
            output_lines.append("   Для DeepSeek рекомендую разделить на части")
        
        output_lines.append("\n" + "=" * 60)
        output_lines.append("✅ ЭКСПОРТ ЗАВЕРШЕН")
        output_lines.append("=" * 60)
        
        return "\n".join(output_lines)
    
    def save_to_file(self, content: str) -> None:
        """Сохраняет контент в файл."""
        try:
            self.output_file.write_text(content, encoding='utf-8')
            print(f"\n✅ Результат сохранен в: {self.output_file}")
            print(f"📏 Размер файла: {self.output_file.stat().st_size:,} байт")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            sys.exit(1)
    
    def print_summary(self) -> None:
        """Выводит краткую информацию о проекте."""
        print("\n" + "=" * 60)
        print("📋 КРАТКАЯ ИНФОРМАЦИЯ:")
        print("=" * 60)
        
        # Основные метрики
        files = self.collect_files()
        print(f"📁 Всего файлов для экспорта: {len(files)}")
        
        # Размеры папок
        print("\n📦 ВКЛЮЧЕННЫЕ ПАПКИ:")
        for dir_name in self.INCLUDE_DIRS:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                py_files = list(dir_path.rglob('*.py'))
                if py_files:
                    print(f"  {dir_name}/: {len(py_files)} Python файлов")
        
        print("\n📄 ВАЖНЫЕ ФАЙЛЫ В КОРНЕ:")
        for filename in sorted(self.ROOT_FILES):
            file_path = self.project_root / filename
            if file_path.exists():
                size_kb = file_path.stat().st_size / 1024
                print(f"  {filename}: {size_kb:.1f} KB")
        
        print("\n" + "=" * 60)


def main():
    """Основная функция."""
    print("🚀 AI Agent Hub V3 - Экспорт контекста проекта")
    print("=" * 60)
    
    # Создаем экземпляр экспортера
    exporter = ProjectExporter()
    
    # Печатаем краткую информацию
    exporter.print_summary()
    
    # Экспортируем проект
    content = exporter.export_project()
    
    # Сохраняем в файл
    exporter.save_to_file(content)
    
    # Дополнительная информация
    print("\n📋 ЧТО ВКЛЮЧЕНО В ЭКСПОРТ:")
    print("  ✅ Папки: src/, tests/, scripts/, mcp_servers/")
    print("  ✅ Конфигурационные файлы в корне")
    print("  ✅ Только текстовые файлы (.py, .md, .txt, .toml и т.д.)")
    print("\n🚫 ЧТО ИСКЛЮЧЕНО:")
    print("  ❌ .venv/, .git/, __pycache__/, node_modules/")
    print("  ❌ Бинарные файлы, базы данных, кэши")
    print("  ❌ Логи, данные, временные файлы")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Экспорт прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)