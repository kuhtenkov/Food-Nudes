import os

def create_project_structure():
    structure = {
        'src': {
            'config': {
                '__init__.py': '',
                'settings.py': ''
            },
            'database': {
                '__init__.py': '',
                'db_manager.py': ''
            },
            'handlers': {
                '__init__.py': '',
                'meal_analysis.py': '',
                'profile.py': '',
                'payment.py': '',
                'progress.py': ''
            },
            'services': {
                '__init__.py': '',
                'image_service.py': '',
                'openai_service.py': ''
            },
            'utils': {
                '__init__.py': '',
                'keyboards.py': ''
            },
            '__init__.py': '',
            'main.py': ''
        }
    }

    def create_structure(base_path, structure):
        for name, content in structure.items():
            path = os.path.join(base_path, name)
            if isinstance(content, dict):
                # Если это директория
                os.makedirs(path, exist_ok=True)
                create_structure(path, content)
            else:
                # Если это файл
                with open(path, 'w') as f:
                    f.write(content)

    # Создаем структуру
    create_structure('.', structure)
    print("Структура проекта успешно создана!")

if __name__ == "__main__":
    create_project_structure()