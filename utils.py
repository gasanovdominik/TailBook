import matplotlib.pyplot as plt

def generate_bar_chart(data: dict) -> str:
    animals = list(data.keys())
    counts = list(data.values())

    plt.figure(figsize=(10, 6))
    bars = plt.bar(animals, counts)
    plt.xlabel("Тип животного")
    plt.ylabel("Количество")
    plt.title("Консультации по типам животных")
    plt.tight_layout()

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, int(yval), ha='center', va='bottom')

    file_path = "bar_chart.png"
    plt.savefig(file_path)
    plt.close()
    return file_path

def generate_pie_chart(data: dict) -> str:
    labels = list(data.keys())
    sizes = list(data.values())

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title("Распределение консультаций по типу животных")
    plt.tight_layout()

    file_path = "pie_chart.png"
    plt.savefig(file_path)
    plt.close()
    return file_path
