import matplotlib.pyplot as plt
from io import BytesIO
import tempfile

def generate_horizontal_chart(data: dict, title: str = "Консультации по животным") -> str:
    fig, ax = plt.subplots(figsize=(8, 4))
    animals = list(data.keys())
    counts = list(data.values())

    ax.barh(animals, counts)
    ax.set_title(title)
    ax.set_xlabel("Количество")
    ax.invert_yaxis()
    plt.tight_layout()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_file.name, format="png")
    plt.close()
    return temp_file.name
