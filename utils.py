import matplotlib.pyplot as plt
from io import BytesIO

def generate_horizontal_chart(data: dict, title: str = "График") -> BytesIO:
    animals = list(data.keys())
    counts = list(data.values())

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(animals, counts)

    ax.set_xlabel("Количество консультаций")
    ax.set_title(title)
    ax.invert_yaxis()  # Самые большие сверху

    # Добавим значения справа от полос
    for bar in bars:
        width = bar.get_width()
        ax.annotate(f'{width}',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    va='center', ha='left', fontsize=10)

    plt.tight_layout()

    # Сохраняем в буфер
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    return buffer
