from UI import run_ui
from preparation import prepare
from capture import capture


def on_button_click(a, b, c):
    print(f"Values received: A={a}, B={b}, C={c}")
    prepare()
    capture()


if __name__ == "__main__":
    run_ui(on_button_click)