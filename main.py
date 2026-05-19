from UI_components.user_interface import run_ui

def on_button_click(a, b, c):
    print(f"Values received: A={a}, B={b}, C={c}")


if __name__ == "__main__":
    run_ui(on_button_click)