import matplotlib.pyplot as plt
from io import BytesIO

def generate_horizontal_chart(data: dict, title: str = "Консультации по животным") -> BytesIO:
    fig, ax = plt.subplots(figsize=(8, 4))
    animals = list(data.keys())
    counts = list(data.values())

    ax.barh(animals, counts)
    ax.set_title(title)
    ax.set_xlabel("Количество")
    ax.invert_yaxis()
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plt.close()
    return buffer

