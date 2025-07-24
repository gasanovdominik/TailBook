import matplotlib.pyplot as plt

def generate_horizontal_chart(data: dict) -> str:
    animals = list(data.keys())
    counts = list(data.values())

    plt.figure(figsize=(10, 5))
    plt.barh(animals, counts)
    plt.xlabel("Количество консультаций")
    plt.ylabel("Тип животного")
    plt.title("Консультации по типам животных")
    plt.tight_layout()
    file_path = "horizontal_chart.png"
    plt.savefig(file_path)
    plt.close()
    return file_path

def generate_line_chart(data: dict) -> str:
    weeks = list(data.keys())
    counts = list(data.values())

    plt.figure(figsize=(10, 5))
    plt.plot(weeks, counts, marker="o")
    plt.title("Динамика консультаций по неделям")
    plt.xlabel("Номер недели")
    plt.ylabel("Количество консультаций")
    plt.grid(True)

    file_path = "weekly_chart.png"
    plt.savefig(file_path)
    plt.close()
    return file_path
